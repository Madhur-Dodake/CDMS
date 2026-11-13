import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.match import MatchStatus, TossDecision


class MatchCreate(BaseModel):
    tournament_id: uuid.UUID
    team1_id: uuid.UUID
    team2_id: uuid.UUID
    venue_id: Optional[uuid.UUID] = None
    match_date: datetime
    overs: int = Field(20, ge=1, le=100)
    scorer_id: Optional[uuid.UUID] = None

    @model_validator(mode="after")
    def validate_different_teams(self) -> "MatchCreate":
        if self.team1_id == self.team2_id:
            raise ValueError("team1 and team2 must be different teams")
        return self


class MatchUpdate(BaseModel):
    venue_id: Optional[uuid.UUID] = None
    match_date: Optional[datetime] = None
    overs: Optional[int] = Field(None, ge=1, le=100)
    scorer_id: Optional[uuid.UUID] = None
    status: Optional[MatchStatus] = None
    toss_winner_id: Optional[uuid.UUID] = None
    toss_decision: Optional[TossDecision] = None
    winner_id: Optional[uuid.UUID] = None
    result_summary: Optional[str] = None


class MatchResponse(BaseModel):
    match_id: uuid.UUID
    tournament_id: uuid.UUID
    tournament_name: Optional[str] = None
    team1_id: uuid.UUID
    team1_name: Optional[str] = None
    team2_id: uuid.UUID
    team2_name: Optional[str] = None
    venue_id: Optional[uuid.UUID] = None
    venue_name: Optional[str] = None
    scorer_id: Optional[uuid.UUID] = None
    match_date: datetime
    overs: int
    status: MatchStatus
    toss_winner_id: Optional[uuid.UUID] = None
    toss_decision: Optional[TossDecision] = None
    winner_id: Optional[uuid.UUID] = None
    result_summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchTransitionRequest(BaseModel):
    event: str


class GenerateScheduleResponse(BaseModel):
    tournament_id: uuid.UUID
    tournament_name: str
    fixtures_count: int
    matches: List[MatchResponse]

    model_config = ConfigDict(from_attributes=True)
