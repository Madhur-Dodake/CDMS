import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TeamBase(BaseModel):
    team_name: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    short_code: Optional[str] = Field(None, max_length=10)
    coach_name: Optional[str] = Field(None, max_length=100)
    logo_url: Optional[str] = Field(None, max_length=255)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    team_name: Optional[str] = Field(None, min_length=1, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    short_code: Optional[str] = Field(None, max_length=10)
    coach_name: Optional[str] = Field(None, max_length=100)
    logo_url: Optional[str] = Field(None, max_length=255)


class TeamResponse(TeamBase):
    team_id: uuid.UUID
    created_at: datetime
    player_count: int = 0

    model_config = ConfigDict(from_attributes=True)
