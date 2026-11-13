import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.venue import VenueCreate, VenueResponse, VenueUpdate
from app.services import venue_service

router = APIRouter(prefix="/venues", tags=["Venues"])


@router.get("", response_model=PaginatedResponse[VenueResponse])
def list_venues(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Search venue name or city"),
    city: Optional[str] = Query(None, description="Filter by city"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[VenueResponse]:
    """Public: List venues with optional search and pagination."""
    return venue_service.get_venues(
        db=db, page=page, page_size=page_size, q=q, city=city
    )


@router.get("/{venue_id}", response_model=VenueResponse)
def get_venue(
    venue_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> VenueResponse:
    """Public: Get venue details by ID."""
    return venue_service.get_venue_by_id(db=db, venue_id=venue_id)


@router.post("", response_model=VenueResponse, status_code=status.HTTP_201_CREATED)
def create_venue(
    venue_in: VenueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> VenueResponse:
    """Admin only: Create a new venue."""
    return venue_service.create_venue(db=db, venue_in=venue_in)


@router.put("/{venue_id}", response_model=VenueResponse)
def update_venue(
    venue_id: uuid.UUID,
    venue_in: VenueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> VenueResponse:
    """Admin only: Update an existing venue."""
    return venue_service.update_venue(
        db=db, venue_id=venue_id, venue_in=venue_in
    )


@router.delete("/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_venue(
    venue_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> None:
    """Admin only: Delete a venue (must have no associated matches)."""
    venue_service.delete_venue(db=db, venue_id=venue_id)
