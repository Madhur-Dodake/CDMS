import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlayerStatsResponse(BaseModel):
    matches_played: int = 0
    runs: int = 0
    balls_faced: int = 0
    wickets: int = 0
    runs_conceded: int = 0
    overs_bowled: Decimal = Decimal("0.0")
    strike_rate: Decimal = Decimal("0.00")
    economy: Decimal = Decimal("0.00")

    model_config = ConfigDict(from_attributes=True)


class PlayerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    team_id: Optional[uuid.UUID] = None
    dob: Optional[date] = None
    batting_style: Optional[str] = Field(None, max_length=50)
    bowling_style: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(None, max_length=50)

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("Date of birth (dob) cannot be in the future")
        return v


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    team_id: Optional[uuid.UUID] = None
    dob: Optional[date] = None
    batting_style: Optional[str] = Field(None, max_length=50)
    bowling_style: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(None, max_length=50)

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("Date of birth (dob) cannot be in the future")
        return v


class PlayerResponse(PlayerBase):
    player_id: uuid.UUID
    created_at: datetime
    team_name: Optional[str] = None
    stats: Optional[PlayerStatsResponse] = None

    model_config = ConfigDict(from_attributes=True)
