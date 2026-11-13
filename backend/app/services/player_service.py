import math
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.player import Player
from app.models.stats import PlayerStats
from app.models.team import Team
from app.schemas.common import PaginatedResponse
from app.schemas.player import (
    PlayerCreate,
    PlayerResponse,
    PlayerStatsResponse,
    PlayerUpdate,
)


def get_players(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    q: Optional[str] = None,
    team_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None,
    batting_style: Optional[str] = None,
    bowling_style: Optional[str] = None,
) -> PaginatedResponse[PlayerResponse]:
    query = (
        select(Player)
        .options(joinedload(Player.team), joinedload(Player.stats))
    )

    if q:
        query = query.where(Player.name.ilike(f"%{q.strip()}%"))
    if team_id:
        query = query.where(Player.team_id == team_id)
    if role:
        query = query.where(Player.role.ilike(f"%{role.strip()}%"))
    if batting_style:
        query = query.where(Player.batting_style.ilike(f"%{batting_style.strip()}%"))
    if bowling_style:
        query = query.where(Player.bowling_style.ilike(f"%{bowling_style.strip()}%"))

    count_query = select(func.count()).select_from(
        query.options(joinedload(Player.team)).subquery()
    )
    total = db.scalar(count_query) or 0

    offset = (page - 1) * page_size
    players = db.scalars(
        query.order_by(Player.name.asc()).offset(offset).limit(page_size)
    ).unique().all()

    pages = math.ceil(total / page_size) if total > 0 else 0

    items = [
        PlayerResponse(
            player_id=p.player_id,
            name=p.name,
            team_id=p.team_id,
            dob=p.dob,
            batting_style=p.batting_style,
            bowling_style=p.bowling_style,
            role=p.role,
            created_at=p.created_at,
            team_name=p.team.team_name if p.team else None,
            stats=PlayerStatsResponse.model_validate(p.stats) if p.stats else None,
        )
        for p in players
    ]

    return PaginatedResponse[PlayerResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def get_player_by_id(db: Session, player_id: uuid.UUID) -> PlayerResponse:
    query = (
        select(Player)
        .options(joinedload(Player.team), joinedload(Player.stats))
        .where(Player.player_id == player_id)
    )
    player = db.scalars(query).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found",
        )

    return PlayerResponse(
        player_id=player.player_id,
        name=player.name,
        team_id=player.team_id,
        dob=player.dob,
        batting_style=player.batting_style,
        bowling_style=player.bowling_style,
        role=player.role,
        created_at=player.created_at,
        team_name=player.team.team_name if player.team else None,
        stats=PlayerStatsResponse.model_validate(player.stats) if player.stats else None,
    )


def create_player(db: Session, player_in: PlayerCreate) -> PlayerResponse:
    if player_in.team_id:
        team = db.get(Team, player_in.team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with id '{player_in.team_id}' not found",
            )
        team_name = team.team_name
    else:
        team_name = None

    player = Player(
        name=player_in.name,
        team_id=player_in.team_id,
        dob=player_in.dob,
        batting_style=player_in.batting_style,
        bowling_style=player_in.bowling_style,
        role=player_in.role,
    )
    db.add(player)
    db.flush()

    stats = PlayerStats(player_id=player.player_id)
    db.add(stats)
    db.commit()
    db.refresh(player)

    return PlayerResponse(
        player_id=player.player_id,
        name=player.name,
        team_id=player.team_id,
        dob=player.dob,
        batting_style=player.batting_style,
        bowling_style=player.bowling_style,
        role=player.role,
        created_at=player.created_at,
        team_name=team_name,
        stats=PlayerStatsResponse.model_validate(stats),
    )


def update_player(
    db: Session, player_id: uuid.UUID, player_in: PlayerUpdate
) -> PlayerResponse:
    query = (
        select(Player)
        .options(joinedload(Player.team), joinedload(Player.stats))
        .where(Player.player_id == player_id)
    )
    player = db.scalars(query).first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found",
        )

    update_data = player_in.model_dump(exclude_unset=True)
    if "team_id" in update_data and update_data["team_id"] is not None:
        team = db.get(Team, update_data["team_id"])
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with id '{update_data['team_id']}' not found",
            )

    for field, value in update_data.items():
        setattr(player, field, value)

    db.commit()
    db.refresh(player)

    return PlayerResponse(
        player_id=player.player_id,
        name=player.name,
        team_id=player.team_id,
        dob=player.dob,
        batting_style=player.batting_style,
        bowling_style=player.bowling_style,
        role=player.role,
        created_at=player.created_at,
        team_name=player.team.team_name if player.team else None,
        stats=PlayerStatsResponse.model_validate(player.stats) if player.stats else None,
    )


def delete_player(db: Session, player_id: uuid.UUID) -> None:
    player = db.get(Player, player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player with id '{player_id}' not found",
        )

    db.delete(player)
    db.commit()
