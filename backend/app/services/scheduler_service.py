import itertools
import math
import uuid
from datetime import datetime, time, timedelta, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.match import Match, MatchStatus
from app.models.team import Team, TournamentTeam
from app.models.tournament import MatchFormat, Tournament
from app.models.user import User, UserRole
from app.models.venue import Venue
from app.schemas.common import PaginatedResponse
from app.schemas.match import (
    GenerateScheduleResponse,
    MatchCreate,
    MatchResponse,
    MatchUpdate,
)
from app.services.match_state import transition


def get_conflict_buffer(match_format: Optional[MatchFormat], overs: int = 20) -> timedelta:
    """Return venue conflict buffer: 9 hours for ODI, 4 hours for T20 and others."""
    if match_format == MatchFormat.ODI or overs > 20:
        return timedelta(hours=9)
    return timedelta(hours=4)


def _to_match_response(m: Match) -> MatchResponse:
    return MatchResponse(
        match_id=m.match_id,
        tournament_id=m.tournament_id,
        tournament_name=m.tournament.name if m.tournament else None,
        team1_id=m.team1_id,
        team1_name=m.team1.team_name if m.team1 else None,
        team2_id=m.team2_id,
        team2_name=m.team2.team_name if m.team2 else None,
        venue_id=m.venue_id,
        venue_name=m.venue.venue_name if m.venue else None,
        scorer_id=m.scorer_id,
        match_date=m.match_date,
        overs=m.overs,
        status=m.status,
        toss_winner_id=m.toss_winner_id,
        toss_decision=m.toss_decision,
        winner_id=m.winner_id,
        result_summary=m.result_summary,
        created_at=m.created_at,
    )


def check_venue_double_booking(
    db: Session,
    venue_id: uuid.UUID,
    match_date: datetime,
    buffer: timedelta,
    exclude_match_id: Optional[uuid.UUID] = None,
) -> None:
    """Check if venue is double-booked within +/- buffer window."""
    window_start = match_date - buffer
    window_end = match_date + buffer

    query = (
        select(Match)
        .where(
            Match.venue_id == venue_id,
            Match.status != MatchStatus.ABANDONED,
            Match.match_date >= window_start,
            Match.match_date <= window_end,
        )
    )
    if exclude_match_id:
        query = query.where(Match.match_id != exclude_match_id)

    conflicting_match = db.scalars(query).first()
    if conflicting_match:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Venue is already booked for another match at {conflicting_match.match_date.isoformat()} "
                f"(conflict window +/- {int(buffer.total_seconds() // 3600)} hours)"
            ),
        )


def create_match(db: Session, match_in: MatchCreate) -> MatchResponse:
    """Admin only: Create and schedule an individual match with full conflict validation."""
    if match_in.team1_id == match_in.team2_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="team1 and team2 must be different teams",
        )

    # 1. Verify tournament exists
    tournament = db.get(Tournament, match_in.tournament_id)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament with id '{match_in.tournament_id}' not found",
        )

    # 2. Verify both teams exist
    team1 = db.get(Team, match_in.team1_id)
    if not team1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team 1 with id '{match_in.team1_id}' not found",
        )
    team2 = db.get(Team, match_in.team2_id)
    if not team2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team 2 with id '{match_in.team2_id}' not found",
        )

    # 3. Verify both teams are registered in the tournament
    t1_reg = db.scalar(
        select(TournamentTeam).where(
            TournamentTeam.tournament_id == match_in.tournament_id,
            TournamentTeam.team_id == match_in.team1_id,
        )
    )
    t2_reg = db.scalar(
        select(TournamentTeam).where(
            TournamentTeam.tournament_id == match_in.tournament_id,
            TournamentTeam.team_id == match_in.team2_id,
        )
    )
    if not t1_reg or not t2_reg:
        unregistered = []
        if not t1_reg:
            unregistered.append(f"Team 1 '{team1.team_name}'")
        if not t2_reg:
            unregistered.append(f"Team 2 '{team2.team_name}'")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{' and '.join(unregistered)} not registered in this tournament",
        )

    # 4. Verify venue and check double booking
    if match_in.venue_id:
        venue = db.get(Venue, match_in.venue_id)
        if not venue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Venue with id '{match_in.venue_id}' not found",
            )
        buffer = get_conflict_buffer(tournament.format, match_in.overs)
        check_venue_double_booking(
            db=db,
            venue_id=match_in.venue_id,
            match_date=match_in.match_date,
            buffer=buffer,
        )

    # 5. Verify scorer if provided
    if match_in.scorer_id:
        scorer = db.get(User, match_in.scorer_id)
        if not scorer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scorer user with id '{match_in.scorer_id}' not found",
            )

    match = Match(
        tournament_id=match_in.tournament_id,
        team1_id=match_in.team1_id,
        team2_id=match_in.team2_id,
        venue_id=match_in.venue_id,
        scorer_id=match_in.scorer_id,
        match_date=match_in.match_date,
        overs=match_in.overs,
        status=MatchStatus.SCHEDULED,
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    return _to_match_response(match)


def generate_round_robin_schedule(
    db: Session, tournament_id: uuid.UUID
) -> GenerateScheduleResponse:
    """Generate round-robin fixtures n(n-1)/2, assigning dates/venues, shifting to next free slot on conflicts."""
    tournament = db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tournament with id '{tournament_id}' not found",
        )

    # Fetch registered teams
    registered_rows = db.scalars(
        select(TournamentTeam)
        .where(TournamentTeam.tournament_id == tournament_id)
    ).all()
    team_ids = [row.team_id for row in registered_rows]
    n = len(team_ids)
    if n < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tournament requires at least 2 registered teams to generate a schedule",
        )

    # Venues
    venues = db.scalars(select(Venue).order_by(Venue.venue_name.asc())).all()
    if not venues:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No venues available to generate schedule",
        )

    # Conflict settings
    is_odi = (tournament.format == MatchFormat.ODI)
    overs = 50 if is_odi else 20
    buffer = timedelta(hours=9) if is_odi else timedelta(hours=4)

    # Collect existing booked slots from DB: list of dicts {venue_id, match_date, teams}
    existing_matches = db.scalars(
        select(Match).where(Match.status != MatchStatus.ABANDONED)
    ).all()

    booked_slots = [
        {
            "venue_id": m.venue_id,
            "match_date": m.match_date,
            "teams": {m.team1_id, m.team2_id},
        }
        for m in existing_matches
        if m.venue_id is not None
    ]

    # Generate round-robin pairings: n*(n-1)/2
    pairings = list(itertools.combinations(team_ids, 2))
    expected_count = (n * (n - 1)) // 2
    assert len(pairings) == expected_count

    # Scheduling slot cursor
    current_date = tournament.start_date
    current_hour = 9 if is_odi else 10
    venue_index = 0
    created_matches: List[Match] = []

    for team1_id, team2_id in pairings:
        slot_assigned = False

        while not slot_assigned:
            slot_datetime = datetime.combine(
                current_date, time(current_hour, 0), tzinfo=timezone.utc
            )
            candidate_venue = venues[venue_index % len(venues)]

            # Check conflicts against existing DB matches and newly booked matches
            conflict = False
            for booked in booked_slots:
                # Venue conflict
                if booked["venue_id"] == candidate_venue.venue_id:
                    if abs((booked["match_date"] - slot_datetime).total_seconds()) < buffer.total_seconds():
                        conflict = True
                        break
                # Team conflict (neither team can play two matches within the duration buffer)
                if team1_id in booked["teams"] or team2_id in booked["teams"]:
                    if abs((booked["match_date"] - slot_datetime).total_seconds()) < buffer.total_seconds():
                        conflict = True
                        break

            if not conflict:
                # Slot is free! Book it.
                booked_slots.append(
                    {
                        "venue_id": candidate_venue.venue_id,
                        "match_date": slot_datetime,
                        "teams": {team1_id, team2_id},
                    }
                )
                match = Match(
                    tournament_id=tournament_id,
                    team1_id=team1_id,
                    team2_id=team2_id,
                    venue_id=candidate_venue.venue_id,
                    match_date=slot_datetime,
                    overs=overs,
                    status=MatchStatus.SCHEDULED,
                )
                db.add(match)
                created_matches.append(match)
                slot_assigned = True

                # Advance venue index for fair distribution
                venue_index += 1
            else:
                # Shift to next venue or next time slot
                venue_index += 1
                if venue_index % len(venues) == 0:
                    # All venues exhausted at this time slot, advance time
                    if is_odi:
                        current_date += timedelta(days=1)
                        current_hour = 9
                    else:
                        if current_hour == 10:
                            current_hour = 15  # Second slot on same day
                        else:
                            current_date += timedelta(days=1)
                            current_hour = 10

    db.commit()

    # Refresh created matches to load relationships
    for m in created_matches:
        db.refresh(m)

    items = [_to_match_response(m) for m in created_matches]
    return GenerateScheduleResponse(
        tournament_id=tournament.tournament_id,
        tournament_name=tournament.name,
        fixtures_count=len(items),
        matches=items,
    )


def get_matches(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    tournament_id: Optional[uuid.UUID] = None,
    status_filter: Optional[MatchStatus] = None,
    team_id: Optional[uuid.UUID] = None,
) -> PaginatedResponse[MatchResponse]:
    """Public: List matches with pagination and optional filters."""
    query = (
        select(Match)
        .options(
            joinedload(Match.tournament),
            joinedload(Match.team1),
            joinedload(Match.team2),
            joinedload(Match.venue),
        )
    )

    if tournament_id:
        query = query.where(Match.tournament_id == tournament_id)
    if status_filter:
        query = query.where(Match.status == status_filter)
    if team_id:
        query = query.where(
            or_(Match.team1_id == team_id, Match.team2_id == team_id)
        )

    count_query = select(func.count()).select_from(
        query.options(
            joinedload(Match.tournament),
            joinedload(Match.team1),
            joinedload(Match.team2),
            joinedload(Match.venue),
        ).subquery()
    )
    total = db.scalar(count_query) or 0

    offset = (page - 1) * page_size
    matches = (
        db.scalars(
            query.order_by(Match.match_date.asc())
            .offset(offset)
            .limit(page_size)
        )
        .unique()
        .all()
    )

    pages = math.ceil(total / page_size) if total > 0 else 0
    items = [_to_match_response(m) for m in matches]

    return PaginatedResponse[MatchResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def get_match_by_id(db: Session, match_id: uuid.UUID) -> MatchResponse:
    """Public: Get match details by ID."""
    match = (
        db.scalars(
            select(Match)
            .options(
                joinedload(Match.tournament),
                joinedload(Match.team1),
                joinedload(Match.team2),
                joinedload(Match.venue),
            )
            .where(Match.match_id == match_id)
        )
        .first()
    )
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{match_id}' not found",
        )
    return _to_match_response(match)


def transition_match(
    db: Session,
    match_id: uuid.UUID,
    event: str,
) -> MatchResponse:
    """Scorer or Admin: Transition match state via pure state machine."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{match_id}' not found",
        )

    try:
        new_status = transition(match.status, event)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    match.status = new_status
    db.commit()
    db.refresh(match)
    return _to_match_response(match)
