import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.tournament import MatchFormat, TournamentLevel
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.match import GenerateScheduleResponse
from app.schemas.team import TeamResponse
from app.schemas.tournament import (
    PointsTableRowResponse,
    TournamentCreate,
    TournamentResponse,
    TournamentTeamRegister,
    TournamentUpdate,
)
from app.services import scheduler_service, tournament_service

router = APIRouter(prefix="/tournaments", tags=["Tournaments"])


@router.get("", response_model=PaginatedResponse[TournamentResponse])
def list_tournaments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Search tournament name"),
    level: Optional[TournamentLevel] = Query(None, description="Filter by level"),
    format: Optional[MatchFormat] = Query(None, description="Filter by match format"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[TournamentResponse]:
    """Public: List tournaments with optional filters and pagination."""
    return tournament_service.get_tournaments(
        db=db, page=page, page_size=page_size, q=q, level=level, format=format
    )


@router.get("/{tournament_id}", response_model=TournamentResponse)
def get_tournament(
    tournament_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> TournamentResponse:
    """Public: Get tournament details by ID."""
    return tournament_service.get_tournament_by_id(
        db=db, tournament_id=tournament_id
    )


@router.post(
    "", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED
)
def create_tournament(
    tournament_in: TournamentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TournamentResponse:
    """Admin only: Create a new tournament."""
    return tournament_service.create_tournament(
        db=db, tournament_in=tournament_in, created_by=current_user.user_id
    )


@router.put("/{tournament_id}", response_model=TournamentResponse)
def update_tournament(
    tournament_id: uuid.UUID,
    tournament_in: TournamentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TournamentResponse:
    """Admin only: Update an existing tournament."""
    return tournament_service.update_tournament(
        db=db, tournament_id=tournament_id, tournament_in=tournament_in
    )


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament(
    tournament_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Admin only: Delete a tournament."""
    tournament_service.delete_tournament(db=db, tournament_id=tournament_id)


# --- Tournament <-> Team Registration Endpoints (M:N) ---


@router.get("/{tournament_id}/teams", response_model=List[TeamResponse])
def get_tournament_teams(
    tournament_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[TeamResponse]:
    """Public: List all teams registered in a tournament."""
    return tournament_service.get_tournament_teams(
        db=db, tournament_id=tournament_id
    )


@router.get(
    "/{tournament_id}/points-table",
    response_model=List[PointsTableRowResponse],
)
def get_points_table(
    tournament_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[PointsTableRowResponse]:
    """Public: Get tournament points table sorted by points, NRR, and wins."""
    from app.services import post_match_service

    return post_match_service.get_tournament_points_table(
        db=db, tournament_id=tournament_id
    )


@router.post("/{tournament_id}/teams", status_code=status.HTTP_201_CREATED)
def register_team_to_tournament(
    tournament_id: uuid.UUID,
    payload: TournamentTeamRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Admin only: Register a team into a tournament."""
    return tournament_service.register_team_to_tournament(
        db=db, tournament_id=tournament_id, team_id=payload.team_id
    )


@router.delete(
    "/{tournament_id}/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT
)
def unregister_team_from_tournament(
    tournament_id: uuid.UUID,
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Admin only: Unregister a team from a tournament."""
    tournament_service.unregister_team_from_tournament(
        db=db, tournament_id=tournament_id, team_id=team_id
    )


# --- Automatic Round-Robin Fixture Generation ---


@router.post(
    "/{tournament_id}/generate-schedule",
    response_model=GenerateScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_schedule(
    tournament_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> GenerateScheduleResponse:
    """Admin only: Generate round-robin tournament fixtures with automatic conflict resolution."""
    return scheduler_service.generate_round_robin_schedule(
        db=db, tournament_id=tournament_id
    )
