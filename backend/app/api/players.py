import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.player import (
    PlayerCareerDetailedStatsResponse,
    PlayerCreate,
    PlayerResponse,
    PlayerUpdate,
)
from app.services import player_service

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("", response_model=PaginatedResponse[PlayerResponse])
def list_players(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Search player name"),
    team_id: Optional[uuid.UUID] = Query(None, description="Filter by team"),
    role: Optional[str] = Query(None, description="Filter by role"),
    batting_style: Optional[str] = Query(None, description="Filter by batting style"),
    bowling_style: Optional[str] = Query(None, description="Filter by bowling style"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PlayerResponse]:
    """Public: List players with optional filters and pagination."""
    return player_service.get_players(
        db=db,
        page=page,
        page_size=page_size,
        q=q,
        team_id=team_id,
        role=role,
        batting_style=batting_style,
        bowling_style=bowling_style,
    )


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(
    player_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> PlayerResponse:
    """Public: Get player profile including career stats."""
    return player_service.get_player_by_id(db=db, player_id=player_id)


@router.get(
    "/{player_id}/stats", response_model=PlayerCareerDetailedStatsResponse
)
def get_player_stats(
    player_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> PlayerCareerDetailedStatsResponse:
    """Public: Get player career statistical figures and milestones."""
    from app.services import post_match_service

    return post_match_service.get_player_detailed_stats(
        db=db, player_id=player_id
    )


@router.post("", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(
    player_in: PlayerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> PlayerResponse:
    """Admin only: Create a new player."""
    return player_service.create_player(db=db, player_in=player_in)


@router.put("/{player_id}", response_model=PlayerResponse)
def update_player(
    player_id: uuid.UUID,
    player_in: PlayerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> PlayerResponse:
    """Admin only: Update player details."""
    return player_service.update_player(
        db=db, player_id=player_id, player_in=player_in
    )


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(
    player_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Admin only: Delete a player."""
    player_service.delete_player(db=db, player_id=player_id)
