import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate
from app.services import team_service

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("", response_model=PaginatedResponse[TeamResponse])
def list_teams(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Search team name or city"),
    city: Optional[str] = Query(None, description="Filter by city"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[TeamResponse]:
    """Public: List teams with optional search and pagination."""
    return team_service.get_teams(
        db=db, page=page, page_size=page_size, q=q, city=city
    )


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> TeamResponse:
    """Public: Get team details by ID."""
    return team_service.get_team_by_id(db=db, team_id=team_id)


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team_in: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TeamResponse:
    """Admin only: Create a new team."""
    return team_service.create_team(db=db, team_in=team_in)


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: uuid.UUID,
    team_in: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> TeamResponse:
    """Admin only: Update an existing team."""
    return team_service.update_team(
        db=db, team_id=team_id, team_in=team_in
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Admin only: Delete a team (cannot delete if it has matches)."""
    team_service.delete_team(db=db, team_id=team_id)
