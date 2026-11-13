import math
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.player import Player
from app.models.stats import PointsTable
from app.models.team import Team, TournamentTeam
from app.models.tournament import MatchFormat, Tournament, TournamentLevel
from app.schemas.common import PaginatedResponse
from app.schemas.team import TeamResponse
from app.schemas.tournament import (
    TournamentCreate,
    TournamentResponse,
    TournamentUpdate,
)


def _get_team_counts(
    db: Session, tournament_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    if not tournament_ids:
        return {}
    query = (
        select(TournamentTeam.tournament_id, func.count(TournamentTeam.team_id))
        .where(TournamentTeam.tournament_id.in_(tournament_ids))
        .group_by(TournamentTeam.tournament_id)
    )
    rows = db.execute(query).all()
    return {row[0]: row[1] for row in rows}


def get_tournaments(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    q: Optional[str] = None,
    level: Optional[TournamentLevel] = None,
    format: Optional[MatchFormat] = None,
) -> PaginatedResponse[TournamentResponse]:
    query = select(Tournament)

    if q:
        query = query.where(Tournament.name.ilike(f"%{q.strip()}%"))
    if level:
        query = query.where(Tournament.level == level)
    if format:
        query = query.where(Tournament.format == format)

    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    offset = (page - 1) * page_size
    tournaments = db.scalars(
        query.order_by(Tournament.start_date.desc()).offset(offset).limit(page_size)
    ).all()

    pages = math.ceil(total / page_size) if total > 0 else 0

    t_ids = [t.tournament_id for t in tournaments]
    team_counts = _get_team_counts(db, t_ids)

    items = [
        TournamentResponse(
            tournament_id=t.tournament_id,
            name=t.name,
            level=t.level,
            format=t.format,
            start_date=t.start_date,
            end_date=t.end_date,
            created_by=t.created_by,
            created_at=t.created_at,
            team_count=team_counts.get(t.tournament_id, 0),
        )
        for t in tournaments
    ]

    return PaginatedResponse[TournamentResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def get_tournament_by_id(
    db: Session, tournament_id: uuid.UUID
) -> TournamentResponse:
    t = db.get(Tournament, tournament_id)
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament with id '{tournament_id}' not found",
        )

    team_count = (
        db.scalar(
            select(func.count())
            .select_from(TournamentTeam)
            .where(TournamentTeam.tournament_id == tournament_id)
        )
        or 0
    )

    return TournamentResponse(
        tournament_id=t.tournament_id,
        name=t.name,
        level=t.level,
        format=t.format,
        start_date=t.start_date,
        end_date=t.end_date,
        created_by=t.created_by,
        created_at=t.created_at,
        team_count=team_count,
    )


def create_tournament(
    db: Session, tournament_in: TournamentCreate, created_by: Optional[uuid.UUID] = None
) -> TournamentResponse:
    tournament = Tournament(
        name=tournament_in.name,
        level=tournament_in.level,
        format=tournament_in.format,
        start_date=tournament_in.start_date,
        end_date=tournament_in.end_date,
        created_by=created_by,
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)

    return TournamentResponse(
        tournament_id=tournament.tournament_id,
        name=tournament.name,
        level=tournament.level,
        format=tournament.format,
        start_date=tournament.start_date,
        end_date=tournament.end_date,
        created_by=tournament.created_by,
        created_at=tournament.created_at,
        team_count=0,
    )


def update_tournament(
    db: Session, tournament_id: uuid.UUID, tournament_in: TournamentUpdate
) -> TournamentResponse:
    t = db.get(Tournament, tournament_id)
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament with id '{tournament_id}' not found",
        )

    update_data = tournament_in.model_dump(exclude_unset=True)
    # Check date consistency if only one date is updated
    new_start = update_data.get("start_date", t.start_date)
    new_end = update_data.get("end_date", t.end_date)
    if new_start and new_end and new_end < new_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date cannot be earlier than start_date",
        )

    for field, value in update_data.items():
        setattr(t, field, value)

    db.commit()
    db.refresh(t)

    team_count = (
        db.scalar(
            select(func.count())
            .select_from(TournamentTeam)
            .where(TournamentTeam.tournament_id == tournament_id)
        )
        or 0
    )

    return TournamentResponse(
        tournament_id=t.tournament_id,
        name=t.name,
        level=t.level,
        format=t.format,
        start_date=t.start_date,
        end_date=t.end_date,
        created_by=t.created_by,
        created_at=t.created_at,
        team_count=team_count,
    )


def delete_tournament(db: Session, tournament_id: uuid.UUID) -> None:
    t = db.get(Tournament, tournament_id)
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament with id '{tournament_id}' not found",
        )

    db.delete(t)
    db.commit()


def register_team_to_tournament(
    db: Session, tournament_id: uuid.UUID, team_id: uuid.UUID
) -> dict:
    t = db.get(Tournament, tournament_id)
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament with id '{tournament_id}' not found",
        )

    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team with id '{team_id}' not found",
        )

    # Check if team already registered
    existing_reg = db.scalar(
        select(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament_id,
            TournamentTeam.team_id == team_id,
        )
    )
    if existing_reg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Team '{team.team_name}' is already registered in this tournament",
        )

    # Check unique team name per tournament
    duplicate_name_team = db.scalar(
        select(Team)
        .join(TournamentTeam, Team.team_id == TournamentTeam.team_id)
        .where(
            TournamentTeam.tournament_id == tournament_id,
            func.lower(Team.team_name) == func.lower(team.team_name),
        )
    )
    if duplicate_name_team:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A team with the name '{team.team_name}' is already registered in this tournament",
        )

    # Register team
    tt = TournamentTeam(tournament_id=tournament_id, team_id=team_id)
    db.add(tt)

    # Initialize PointsTable row if not exists
    existing_points = db.scalar(
        select(PointsTable).where(
            PointsTable.tournament_id == tournament_id,
            PointsTable.team_id == team_id,
        )
    )
    if not existing_points:
        points_row = PointsTable(
            tournament_id=tournament_id,
            team_id=team_id,
            played=0,
            won=0,
            lost=0,
            tied=0,
            nr=0,
            points=0,
            nrr=0.000,
        )
        db.add(points_row)

    db.commit()
    return {"message": f"Team '{team.team_name}' registered successfully to tournament '{t.name}'"}


def unregister_team_from_tournament(
    db: Session, tournament_id: uuid.UUID, team_id: uuid.UUID
) -> None:
    t = db.get(Tournament, tournament_id)
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament with id '{tournament_id}' not found",
        )

    tt = db.scalar(
        select(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament_id,
            TournamentTeam.team_id == team_id,
        )
    )
    if not tt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team is not registered in this tournament",
        )

    # Check if team has played matches in this tournament
    matches_in_tournament = db.scalar(
        select(func.count())
        .select_from(Match)
        .where(
            Match.tournament_id == tournament_id,
            or_(Match.team1_id == team_id, Match.team2_id == team_id),
        )
    )
    if matches_in_tournament and matches_in_tournament > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot unregister team with matches in this tournament",
        )

    # Remove points table entry
    points_row = db.scalar(
        select(PointsTable).where(
            PointsTable.tournament_id == tournament_id,
            PointsTable.team_id == team_id,
        )
    )
    if points_row:
        db.delete(points_row)

    db.delete(tt)
    db.commit()


def get_tournament_teams(
    db: Session, tournament_id: uuid.UUID
) -> List[TeamResponse]:
    t = db.get(Tournament, tournament_id)
    if not t:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament with id '{tournament_id}' not found",
        )

    query = (
        select(Team)
        .join(TournamentTeam, Team.team_id == TournamentTeam.team_id)
        .where(TournamentTeam.tournament_id == tournament_id)
        .order_by(Team.team_name.asc())
    )
    teams = db.scalars(query).all()

    team_ids = [team.team_id for team in teams]
    player_counts = {}
    if team_ids:
        counts = db.execute(
            select(Player.team_id, func.count(Player.player_id))
            .where(Player.team_id.in_(team_ids))
            .group_by(Player.team_id)
        ).all()
        player_counts = {row[0]: row[1] for row in counts}

    return [
        TeamResponse(
            team_id=team.team_id,
            team_name=team.team_name,
            city=team.city,
            short_code=team.short_code,
            coach_name=team.coach_name,
            logo_url=team.logo_url,
            created_at=team.created_at,
            player_count=player_counts.get(team.team_id, 0),
        )
        for team in teams
    ]
