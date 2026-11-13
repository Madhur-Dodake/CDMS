import math
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.venue import Venue
from app.schemas.common import PaginatedResponse
from app.schemas.venue import VenueCreate, VenueResponse, VenueUpdate


def get_venues(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    q: Optional[str] = None,
    city: Optional[str] = None,
) -> PaginatedResponse[VenueResponse]:
    query = select(Venue)

    if q:
        search = f"%{q.strip()}%"
        query = query.where(
            (Venue.venue_name.ilike(search)) | (Venue.city.ilike(search))
        )
    if city:
        query = query.where(Venue.city.ilike(f"%{city.strip()}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    # Paginate
    offset = (page - 1) * page_size
    venues = db.scalars(
        query.order_by(Venue.venue_name.asc()).offset(offset).limit(page_size)
    ).all()

    pages = math.ceil(total / page_size) if total > 0 else 0
    items = [VenueResponse.model_validate(v) for v in venues]

    return PaginatedResponse[VenueResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def get_venue_by_id(db: Session, venue_id: uuid.UUID) -> Venue:
    venue = db.get(Venue, venue_id)
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venue with id '{venue_id}' not found",
        )
    return venue


def create_venue(db: Session, venue_in: VenueCreate) -> Venue:
    venue = Venue(
        venue_name=venue_in.venue_name,
        city=venue_in.city,
        capacity=venue_in.capacity,
    )
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


def update_venue(
    db: Session, venue_id: uuid.UUID, venue_in: VenueUpdate
) -> Venue:
    venue = get_venue_by_id(db, venue_id)
    update_data = venue_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(venue, field, value)

    db.commit()
    db.refresh(venue)
    return venue


def delete_venue(db: Session, venue_id: uuid.UUID) -> None:
    venue = get_venue_by_id(db, venue_id)

    # Check if venue is linked to any matches
    matches_count = db.scalar(
        select(func.count()).select_from(Match).where(Match.venue_id == venue_id)
    )
    if matches_count and matches_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete venue with associated matches",
        )

    db.delete(venue)
    db.commit()
