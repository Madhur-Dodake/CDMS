import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.tournament import MatchFormat, TournamentLevel


class TournamentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    level: TournamentLevel
    format: MatchFormat
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> "TournamentBase":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class TournamentCreate(TournamentBase):
    pass


class TournamentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    level: Optional[TournamentLevel] = None
    format: Optional[MatchFormat] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "TournamentUpdate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class TournamentResponse(TournamentBase):
    tournament_id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    team_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TournamentTeamRegister(BaseModel):
    team_id: uuid.UUID
