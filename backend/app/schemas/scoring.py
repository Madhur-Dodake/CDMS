import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.match import MatchStatus, TossDecision


class MatchStartRequest(BaseModel):
    toss_winner_id: uuid.UUID
    toss_decision: TossDecision
    team1_xi: List[uuid.UUID] = Field(..., min_length=2)
    team2_xi: List[uuid.UUID] = Field(..., min_length=2)
    striker_id: uuid.UUID
    non_striker_id: uuid.UUID
    opening_bowler_id: uuid.UUID


class BallRequest(BaseModel):
    striker_id: uuid.UUID
    non_striker_id: uuid.UUID
    bowler_id: uuid.UUID
    runs_batter: int = Field(0, ge=0, le=6)
    extras_type: Optional[str] = None  # "wide", "no_ball", "bye", "leg_bye", "penalty", None
    extras_runs: int = Field(0, ge=0)
    is_wicket: bool = False
    wicket_type: Optional[str] = None
    dismissed_player_id: Optional[uuid.UUID] = None
    next_batter_id: Optional[uuid.UUID] = None


class ScoringStateResponse(BaseModel):
    match_id: uuid.UUID
    match_status: MatchStatus
    innings_id: uuid.UUID
    innings_no: int
    batting_team_id: uuid.UUID
    bowling_team_id: uuid.UUID
    total_runs: int
    wickets: int
    legal_balls: int
    overs_formatted: str
    striker_id: str
    non_striker_id: str
    current_bowler_id: Optional[str] = None
    current_run_rate: float
    required_run_rate: Optional[float] = None
    recent_balls: List[str] = Field(default_factory=list)
    is_completed: bool
    target_runs: Optional[int] = None
    result_summary: Optional[str] = None
    batters: Dict[str, Any] = Field(default_factory=dict)
    bowlers: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
