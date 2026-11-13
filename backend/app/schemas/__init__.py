"""Pydantic v2 schemas package."""
from app.schemas.health import HealthResponse
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.common import PaginatedResponse
from app.schemas.venue import VenueCreate, VenueUpdate, VenueResponse
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse
from app.schemas.tournament import (
    TournamentCreate,
    TournamentUpdate,
    TournamentResponse,
    TournamentTeamRegister,
)
from app.schemas.player import (
    PlayerCreate,
    PlayerUpdate,
    PlayerResponse,
    PlayerStatsResponse,
)
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.dashboard import DashboardSummary, ActivityItem
from app.schemas.match import (
    GenerateScheduleResponse,
    MatchCreate,
    MatchResponse,
    MatchTransitionRequest,
    MatchUpdate,
)
from app.schemas.scoring import (
    BallRequest,
    MatchStartRequest,
    ScoringStateResponse,
)

__all__ = [
    "HealthResponse",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "PaginatedResponse",
    "VenueCreate",
    "VenueUpdate",
    "VenueResponse",
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "TournamentCreate",
    "TournamentUpdate",
    "TournamentResponse",
    "TournamentTeamRegister",
    "PlayerCreate",
    "PlayerUpdate",
    "PlayerResponse",
    "PlayerStatsResponse",
    "DashboardSummary",
    "ActivityItem",
    "MatchCreate",
    "MatchUpdate",
    "MatchResponse",
    "MatchTransitionRequest",
    "GenerateScheduleResponse",
    "MatchStartRequest",
    "BallRequest",
    "ScoringStateResponse",
]
