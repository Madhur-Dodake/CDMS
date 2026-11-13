from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token,
    get_current_user,
    require_admin,
    require_scorer_or_admin,
    verify_password,
)
from app.core.database import get_db
from app.core.rate_limit import login_rate_limiter
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user with role selection",
)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Authenticate credentials and verify selected role matches user account."""
    # Enforce in-memory sliding window rate limit (10 attempts/min per IP)
    login_rate_limiter.check_rate_limit(request)

    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.role != login_data.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role selected for account",
        )

    access_token = create_access_token(
        data={
            "user_id": str(user.user_id),
            "role": user.role.value,
            "sub": user.email,
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated user profile",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return profile details for currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.get(
    "/admin-only",
    summary="Admin-only protected route",
)
def admin_only_check(
    admin: User = Depends(require_admin),
) -> dict:
    """Protected endpoint verifying require_admin guard."""
    return {"status": "ok", "message": f"Welcome Admin {admin.name}"}


@router.get(
    "/scorer-or-admin",
    summary="Scorer or Admin protected route",
)
def scorer_or_admin_check(
    operator: User = Depends(require_scorer_or_admin),
) -> dict:
    """Protected endpoint verifying require_scorer_or_admin guard."""
    return {"status": "ok", "message": f"Welcome {operator.name}"}
