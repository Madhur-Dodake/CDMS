import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_admin, require_scorer_or_admin
from app.core.database import get_db
from app.models.match import MatchStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.match import (
    MatchCreate,
    MatchResponse,
    MatchTransitionRequest,
)
from app.services import scheduler_service

router = APIRouter(prefix="/matches", tags=["Matches"])


@router.get("", response_model=PaginatedResponse[MatchResponse])
def list_matches(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tournament_id: Optional[uuid.UUID] = Query(None, description="Filter by tournament"),
    status: Optional[MatchStatus] = Query(None, description="Filter by match status"),
    team_id: Optional[uuid.UUID] = Query(None, description="Filter by team"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[MatchResponse]:
    """Public: List scheduled and completed matches with filtering and pagination."""
    return scheduler_service.get_matches(
        db=db,
        page=page,
        page_size=page_size,
        tournament_id=tournament_id,
        status_filter=status,
        team_id=team_id,
    )


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> MatchResponse:
    """Public: Get match details by ID."""
    return scheduler_service.get_match_by_id(db=db, match_id=match_id)


@router.post("", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
def schedule_match(
    match_in: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> MatchResponse:
    """Admin only: Schedule an individual match with full venue and team registration conflict validation."""
    return scheduler_service.create_match(db=db, match_in=match_in)


@router.post("/{match_id}/transition", response_model=MatchResponse)
def transition_match_state(
    match_id: uuid.UUID,
    request: MatchTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scorer_or_admin),
) -> MatchResponse:
    """Scorer or Admin: Transition match state via pure state machine."""
    return scheduler_service.transition_match(
        db=db, match_id=match_id, event=request.event
    )
