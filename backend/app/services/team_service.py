import math
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.player import Player
from app.models.team import Team
from app.schemas.common import PaginatedResponse
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate


def _get_player_counts(db: Session, team_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not team_ids:
        return {}
    query = (
        select(Player.team_id, func.count(Player.player_id))
        .where(Player.team_id.in_(team_ids))
        .group_by(Player.team_id)
    )
    rows = db.execute(query).all()
    return {row[0]: row[1] for row in rows}


def get_teams(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    q: Optional[str] = None,
    city: Optional[str] = None,
) -> PaginatedResponse[TeamResponse]:
    query = select(Team)

    if q:
        search = f"%{q.strip()}%"
        query = query.where(
            (Team.team_name.ilike(search)) | (Team.city.ilike(search))
        )
    if city:
        query = query.where(Team.city.ilike(f"%{city.strip()}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    offset = (page - 1) * page_size
    teams = db.scalars(
        query.order_by(Team.team_name.asc()).offset(offset).limit(page_size)
    ).all()

    pages = math.ceil(total / page_size) if total > 0 else 0

    team_ids = [t.team_id for t in teams]
    counts = _get_player_counts(db, team_ids)

    items = [
        TeamResponse(
            team_id=t.team_id,
            team_name=t.team_name,
            city=t.city,
            short_code=t.short_code,
            coach_name=t.coach_name,
            logo_url=t.logo_url,
            created_at=t.created_at,
            player_count=counts.get(t.team_id, 0),
        )
        for t in teams
    ]

    return PaginatedResponse[TeamResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def get_team_by_id(db: Session, team_id: uuid.UUID) -> TeamResponse:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id '{team_id}' not found",
        )

    player_count = (
        db.scalar(
            select(func.count()).select_from(Player).where(Player.team_id == team_id)
        )
        or 0
    )

    return TeamResponse(
        team_id=team.team_id,
        team_name=team.team_name,
        city=team.city,
        short_code=team.short_code,
        coach_name=team.coach_name,
        logo_url=team.logo_url,
        created_at=team.created_at,
        player_count=player_count,
    )


def create_team(db: Session, team_in: TeamCreate) -> TeamResponse:
    team = Team(
        team_name=team_in.team_name,
        city=team_in.city,
        short_code=team_in.short_code,
        coach_name=team_in.coach_name,
        logo_url=team_in.logo_url,
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    return TeamResponse(
        team_id=team.team_id,
        team_name=team.team_name,
        city=team.city,
        short_code=team.short_code,
        coach_name=team.coach_name,
        logo_url=team.logo_url,
        created_at=team.created_at,
        player_count=0,
    )


def update_team(
    db: Session, team_id: uuid.UUID, team_in: TeamUpdate
) -> TeamResponse:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id '{team_id}' not found",
        )

    update_data = team_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    db.commit()
    db.refresh(team)

    player_count = (
        db.scalar(
            select(func.count()).select_from(Player).where(Player.team_id == team_id)
        )
        or 0
    )

    return TeamResponse(
        team_id=team.team_id,
        team_name=team.team_name,
        city=team.city,
        short_code=team.short_code,
        coach_name=team.coach_name,
        logo_url=team.logo_url,
        created_at=team.created_at,
        player_count=player_count,
    )


def delete_team(db: Session, team_id: uuid.UUID) -> None:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id '{team_id}' not found",
        )

    # Check if team has matches
    matches_count = db.scalar(
        select(func.count())
        .select_from(Match)
        .where(or_(Match.team1_id == team_id, Match.team2_id == team_id))
    )
    if matches_count and matches_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete team with associated matches",
        )

    db.delete(team)
    db.commit()
