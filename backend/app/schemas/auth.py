import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Payload for user login with mandatory role selection."""

    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=1, max_length=128)
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

