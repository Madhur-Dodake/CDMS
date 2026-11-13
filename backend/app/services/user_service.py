import math
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import get_password_hash
from app.models.user import User, UserRole
from app.schemas.auth import UserResponse
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserUpdate


def get_users(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    q: Optional[str] = None,
    role: Optional[UserRole] = None,
) -> PaginatedResponse[UserResponse]:
    query = select(User)

    if q:
        search = f"%{q.strip()}%"
        query = query.where((User.name.ilike(search)) | (User.email.ilike(search)))
    if role:
        query = query.where(User.role == role)

    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    offset = (page - 1) * page_size
    users = db.scalars(
        query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    ).all()

    pages = math.ceil(total / page_size) if total > 0 else 0
    items = [UserResponse.model_validate(u) for u in users]

    return PaginatedResponse[UserResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def get_user_by_id(db: Session, user_id: uuid.UUID) -> UserResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )
    return UserResponse.model_validate(user)


def create_user(db: Session, user_in: UserCreate) -> UserResponse:
    # Check if email is already registered
    existing_user = db.scalar(
        select(User).where(func.lower(User.email) == user_in.email.lower())
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with email '{user_in.email}' already exists",
        )

    user = User(
        name=user_in.name,
        email=user_in.email,
        password=get_password_hash(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


def update_user(
    db: Session, user_id: uuid.UUID, user_in: UserUpdate
) -> UserResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    update_data = user_in.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"]:
        new_email = update_data["email"].lower()
        if new_email != user.email.lower():
            existing = db.scalar(
                select(User).where(func.lower(User.email) == new_email)
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A user with email '{update_data['email']}' already exists",
                )
            user.email = update_data["email"]

    if "name" in update_data and update_data["name"]:
        user.name = update_data["name"]

    if "role" in update_data and update_data["role"]:
        user.role = update_data["role"]

    if "password" in update_data and update_data["password"]:
        user.password = get_password_hash(update_data["password"])

    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


def delete_user(db: Session, user_id: uuid.UUID) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id '{user_id}' not found",
        )

    db.delete(user)
    db.commit()
