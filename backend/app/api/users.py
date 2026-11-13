import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import UserResponse
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Search user name or email"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> PaginatedResponse[UserResponse]:
    """Admin only: List users with optional role and search filters."""
    return user_service.get_users(
        db=db, page=page, page_size=page_size, q=q, role=role
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserResponse:
    """Admin only: Get user details by ID."""
    return user_service.get_user_by_id(db=db, user_id=user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserResponse:
    """Admin only: Create a new user (e.g. scorer account)."""
    return user_service.create_user(db=db, user_in=user_in)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserResponse:
    """Admin only: Update an existing user."""
    return user_service.update_user(db=db, user_id=user_id, user_in=user_in)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Admin only: Delete a user."""
    user_service.delete_user(db=db, user_id=user_id)
