import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import require_scorer_or_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.scoring import (
    BallRequest,
    MatchStartRequest,
    ScoringStateResponse,
)
from app.services import scoring_service

router = APIRouter(prefix="/matches", tags=["Scoring"])


@router.post("/{match_id}/start", response_model=ScoringStateResponse, status_code=status.HTTP_200_OK)
def start_match(
    match_id: uuid.UUID,
    payload: MatchStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scorer_or_admin),
) -> ScoringStateResponse:
    """Scorer or Admin: Record toss and playing XIs, transition match to LIVE, initialize Innings 1."""
    return scoring_service.start_match(
        db=db, match_id=match_id, payload=payload, current_user=current_user
    )


@router.post("/{match_id}/ball", response_model=ScoringStateResponse, status_code=status.HTTP_200_OK)
def record_ball(
    match_id: uuid.UUID,
    payload: BallRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scorer_or_admin),
) -> ScoringStateResponse:
    """Scorer or Admin: Record a delivery event with validation, state computation, and persistence."""
    return scoring_service.record_ball(
        db=db, match_id=match_id, payload=payload, current_user=current_user
    )


@router.post("/{match_id}/undo", response_model=ScoringStateResponse, status_code=status.HTTP_200_OK)
def undo_ball(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scorer_or_admin),
) -> ScoringStateResponse:
    """Scorer or Admin: Delete last ball event and replay innings from ball zero."""
    return scoring_service.undo_last_ball(
        db=db, match_id=match_id, current_user=current_user
    )


@router.post("/{match_id}/end-innings", response_model=ScoringStateResponse, status_code=status.HTTP_200_OK)
def end_innings(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scorer_or_admin),
) -> ScoringStateResponse:
    """Scorer or Admin: Conclude Innings 1, set target for Innings 2, and switch to INNINGS_BREAK."""
    return scoring_service.end_innings(
        db=db, match_id=match_id, current_user=current_user
    )


@router.post("/{match_id}/complete", response_model=ScoringStateResponse, status_code=status.HTTP_200_OK)
def complete_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scorer_or_admin),
) -> ScoringStateResponse:
    """Scorer or Admin: Officially conclude the match and declare official result summary."""
    return scoring_service.complete_match(
        db=db, match_id=match_id, current_user=current_user
    )


@router.post("/{match_id}/suspend", response_model=ScoringStateResponse, status_code=status.HTTP_200_OK)
def suspend_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scorer_or_admin),
) -> ScoringStateResponse:
    """Scorer or Admin: Suspend match due to rain or interruption."""
    return scoring_service.suspend_match(
        db=db, match_id=match_id, current_user=current_user
    )


@router.post("/{match_id}/resume", response_model=ScoringStateResponse, status_code=status.HTTP_200_OK)
def resume_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scorer_or_admin),
) -> ScoringStateResponse:
    """Scorer or Admin: Resume suspended match."""
    return scoring_service.resume_match(
        db=db, match_id=match_id, current_user=current_user
    )
