import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Payload for user login with mandatory role selection."""

    email: EmailStr
    password: str
    role: UserRole


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    name: str
    email: str
    role: UserRole


class UserResponse(BaseModel):
    """Schema for returning user profile details."""

    user_id: uuid.UUID
    name: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
