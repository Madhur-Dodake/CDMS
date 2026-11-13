from dataclasses import dataclass, field
import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ball_event import BallEvent, ExtrasType, WicketType
from app.models.innings import Innings
from app.models.match import Match, MatchStatus, TossDecision
from app.models.player import Player
from app.models.stats import PointsTable
from app.models.team import Team
from app.models.user import User, UserRole
from app.schemas.scoring import BallRequest, MatchStartRequest, ScoringStateResponse
from app.services.match_state import MatchEvent, transition
from app.services.scoring_engine import (
    BallInput,
    InningsState,
    apply_ball,
    current_run_rate,
    overs_display,
    replay,
    required_run_rate,
)


@dataclass
class LiveMatchSession:
    """In-memory live session state for an active match."""

    match_id: uuid.UUID
    team1_xi: List[uuid.UUID]
    team2_xi: List[uuid.UUID]
    batting_team_id: uuid.UUID
    bowling_team_id: uuid.UUID
    current_innings_id: uuid.UUID
    current_innings_no: int
    innings_state: InningsState
    previous_over_bowler_id: Optional[uuid.UUID] = None
    current_over_bowler_id: Optional[uuid.UUID] = None


# In-memory cache holding active LiveMatchSessions per match
LIVE_MATCH_CACHE: Dict[uuid.UUID, LiveMatchSession] = {}


def verify_match_scorer(match: Match, current_user: User) -> None:
    """Validate that the user is an admin or the assigned scorer for this match."""
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.SCORER:
        if match.scorer_id is None or match.scorer_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the assigned scorer for this match",
            )
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Scorer or Admin access required",
    )


def _map_extras_type_to_enum(val: Optional[str]) -> ExtrasType:
    if not val:
        return ExtrasType.NONE
    mapping = {
        "wide": ExtrasType.WIDE,
        "no_ball": ExtrasType.NO_BALL,
        "bye": ExtrasType.BYE,
        "leg_bye": ExtrasType.LEG_BYE,
        "penalty": ExtrasType.PENALTY,
    }
    return mapping.get(val.lower(), ExtrasType.NONE)


def _map_wicket_type_to_enum(val: Optional[str]) -> WicketType:
    if not val:
        return WicketType.NONE
    mapping = {
        "bowled": WicketType.BOWLED,
        "caught": WicketType.CAUGHT,
        "lbw": WicketType.LBW,
        "run_out": WicketType.RUN_OUT,
        "stumped": WicketType.STUMPED,
        "hit_wicket": WicketType.HIT_WICKET,
    }
    return mapping.get(val.lower(), WicketType.NONE)


def _ball_event_to_ball_input(e: BallEvent) -> BallInput:
    extras_type_str = None
    if e.extras_type != ExtrasType.NONE:
        extras_type_str = e.extras_type.value

    wicket_type_str = None
    if e.wicket_type != WicketType.NONE:
        wicket_type_str = e.wicket_type.value

    return BallInput(
        striker_id=str(e.striker_id),
        non_striker_id=str(e.non_striker_id),
        bowler_id=str(e.bowler_id),
        runs_batter=e.runs_scored,
        extras_type=extras_type_str,
        extras_runs=e.extras_runs,
        is_wicket=e.is_wicket,
        wicket_type=wicket_type_str,
        dismissed_player_id=str(e.dismissed_player_id) if e.dismissed_player_id else None,
    )


def _get_or_load_session(db: Session, match_id: uuid.UUID) -> LiveMatchSession:
    """Retrieve match session from in-memory cache or rebuild from DB on cache miss."""
    if match_id in LIVE_MATCH_CACHE:
        return LIVE_MATCH_CACHE[match_id]

    # Cache miss: rebuild from database
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{match_id}' not found",
        )

    # Find the active innings
    innings = (
        db.scalars(
            select(Innings)
            .where(Innings.match_id == match_id)
            .order_by(Innings.innings_no.desc())
        ).first()
    )
    if not innings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match has no initialized innings; please call /start first",
        )

    # Load all ball events for this innings
    ball_events = (
        db.scalars(
            select(BallEvent)
            .where(BallEvent.innings_id == innings.innings_id)
            .order_by(BallEvent.sequence_no.asc())
        ).all()
    )

    # Fetch team players for playing XI fallback
    t1_players = [p.player_id for p in db.scalars(select(Player).where(Player.team_id == match.team1_id)).all()]
    t2_players = [p.player_id for p in db.scalars(select(Player).where(Player.team_id == match.team2_id)).all()]

    ball_inputs = [_ball_event_to_ball_input(e) for e in ball_events]

    # Replay all events
    striker_id = ball_inputs[0].striker_id if ball_inputs else str(t1_players[0] if t1_players else uuid.uuid4())
    non_striker_id = ball_inputs[0].non_striker_id if ball_inputs else str(t1_players[1] if len(t1_players) > 1 else uuid.uuid4())

    state = replay(
        events=ball_inputs,
        max_overs=match.overs,
        target_runs=innings.target_runs,
        striker_id=striker_id,
        non_striker_id=non_striker_id,
        innings_no=innings.innings_no,
    )

    # Previous over bowler
    previous_over_bowler = None
    if ball_events:
        last_ball = ball_events[-1]
        if last_ball.over_no > 0 and (last_ball.over_no * 6 <= innings.balls_bowled):
            # Find bowler of previous over
            prev_balls = [b for b in ball_events if b.over_no == last_ball.over_no - 1]
            if prev_balls:
                previous_over_bowler = prev_balls[-1].bowler_id

    session = LiveMatchSession(
        match_id=match_id,
        team1_xi=t1_players,
        team2_xi=t2_players,
        batting_team_id=innings.batting_team_id,
        bowling_team_id=innings.bowling_team_id,
        current_innings_id=innings.innings_id,
        current_innings_no=innings.innings_no,
        innings_state=state,
        previous_over_bowler_id=previous_over_bowler,
    )
    LIVE_MATCH_CACHE[match_id] = session
    return session


def _build_state_response(
    match: Match, innings: Innings, state: InningsState
) -> ScoringStateResponse:
    rem_balls = max(0, (state.max_overs * 6) - state.legal_balls)
    runs_needed = (state.target_runs - state.total_runs) if state.target_runs is not None else 0

    crr = current_run_rate(state.total_runs, state.legal_balls)
    rrr = required_run_rate(runs_needed, rem_balls) if state.innings_no == 2 else None

    # Batters and Bowlers dictionaries for client view
    batters_dict = {
        pid: {
            "runs": b.runs,
            "balls": b.balls_faced,
            "fours": b.fours,
            "sixes": b.sixes,
            "is_out": b.is_out,
            "dismissal_type": b.dismissal_type,
        }
        for pid, b in state.batters.items()
    }
    bowlers_dict = {
        pid: {
            "balls": bw.balls_bowled,
            "overs": overs_display(bw.balls_bowled),
            "runs": bw.runs_conceded,
            "wickets": bw.wickets,
            "wides": bw.wides,
            "no_balls": bw.no_balls,
            "dots": bw.dots,
        }
        for pid, bw in state.bowlers.items()
    }

    return ScoringStateResponse(
        match_id=match.match_id,
        match_status=match.status,
        innings_id=innings.innings_id,
        innings_no=innings.innings_no,
        batting_team_id=innings.batting_team_id,
        bowling_team_id=innings.bowling_team_id,
        total_runs=state.total_runs,
        wickets=state.wickets,
        legal_balls=state.legal_balls,
        overs_formatted=overs_display(state.legal_balls),
        striker_id=state.striker_id,
        non_striker_id=state.non_striker_id,
        current_bowler_id=state.current_bowler_id,
        current_run_rate=crr,
        required_run_rate=rrr,
        recent_balls=state.recent_balls,
        is_completed=state.is_completed,
        target_runs=state.target_runs,
        result_summary=match.result_summary,
        batters=batters_dict,
        bowlers=bowlers_dict,
    )


# -------------------------------------------------------------
# SCORING API WORKFLOW FUNCTIONS
# -------------------------------------------------------------

def start_match(
    db: Session,
    match_id: uuid.UUID,
    payload: MatchStartRequest,
    current_user: User,
) -> ScoringStateResponse:
    """Scorer or Admin: Record toss and playing XIs, transition match to LIVE, initialize Innings 1."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match with id '{match_id}' not found",
        )

    verify_match_scorer(match, current_user)

    if match.status != MatchStatus.SCHEDULED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match cannot be started from status '{match.status.value}' (must be 'scheduled')",
        )

    # 1. Validate Toss
    if payload.toss_winner_id not in (match.team1_id, match.team2_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Toss winner must be one of the match teams",
        )

    # Determine batting & bowling teams for Innings 1
    if payload.toss_winner_id == match.team1_id:
        if payload.toss_decision == TossDecision.BAT:
            batting_team_id, bowling_team_id = match.team1_id, match.team2_id
        else:
            batting_team_id, bowling_team_id = match.team2_id, match.team1_id
    else:
        if payload.toss_decision == TossDecision.BAT:
            batting_team_id, bowling_team_id = match.team2_id, match.team1_id
        else:
            batting_team_id, bowling_team_id = match.team1_id, match.team2_id

    # 2. Validate Playing XIs
    if len(payload.team1_xi) != len(set(payload.team1_xi)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate players in Team 1 XI")
    if len(payload.team2_xi) != len(set(payload.team2_xi)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate players in Team 2 XI")

    batting_xi = payload.team1_xi if batting_team_id == match.team1_id else payload.team2_xi
    bowling_xi = payload.team2_xi if batting_team_id == match.team1_id else payload.team1_xi

    if payload.striker_id not in batting_xi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Striker must be in batting playing XI")
    if payload.non_striker_id not in batting_xi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Non-striker must be in batting playing XI")
    if payload.striker_id == payload.non_striker_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Striker and non-striker must be different players")
    if payload.opening_bowler_id not in bowling_xi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Opening bowler must be in bowling playing XI")

    # 3. Update Match
    match.toss_winner_id = payload.toss_winner_id
    match.toss_decision = payload.toss_decision
    match.status = transition(match.status, MatchEvent.START_TOSS)

    # 4. Create Innings 1
    innings1 = Innings(
        match_id=match.match_id,
        batting_team_id=batting_team_id,
        bowling_team_id=bowling_team_id,
        innings_no=1,
        total_runs=0,
        wickets=0,
        balls_bowled=0,
        is_completed=False,
        target_runs=None,
    )
    db.add(innings1)
    db.commit()
    db.refresh(innings1)
    db.refresh(match)

    # 5. Initialize Live Match Session
    initial_state = InningsState(
        innings_no=1,
        max_overs=match.overs,
        target_runs=None,
        striker_id=str(payload.striker_id),
        non_striker_id=str(payload.non_striker_id),
        current_bowler_id=str(payload.opening_bowler_id),
    )

    session = LiveMatchSession(
        match_id=match_id,
        team1_xi=payload.team1_xi,
        team2_xi=payload.team2_xi,
        batting_team_id=batting_team_id,
        bowling_team_id=bowling_team_id,
        current_innings_id=innings1.innings_id,
        current_innings_no=1,
        innings_state=initial_state,
        previous_over_bowler_id=None,
        current_over_bowler_id=payload.opening_bowler_id,
    )
    LIVE_MATCH_CACHE[match_id] = session

    return _build_state_response(match, innings1, initial_state)


def record_ball(
    db: Session,
    match_id: uuid.UUID,
    payload: BallRequest,
    current_user: User,
) -> ScoringStateResponse:
    """Scorer or Admin: Record a delivery event with validation, state computation, and atomic persistence."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Match with id '{match_id}' not found")

    verify_match_scorer(match, current_user)

    if match.status != MatchStatus.LIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Deliveries can only be recorded when match is LIVE (current status: '{match.status.value}')",
        )

    session = _get_or_load_session(db, match_id)
    innings = db.get(Innings, session.current_innings_id)
    if not innings or innings.is_completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current innings is already completed")

    # 1. Playing XI Validation
    batting_xi = session.team1_xi if session.batting_team_id == match.team1_id else session.team2_xi
    bowling_xi = session.team2_xi if session.batting_team_id == match.team1_id else session.team1_xi

    if payload.striker_id not in batting_xi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Striker is not in the batting playing XI")
    if payload.non_striker_id not in batting_xi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Non-striker is not in the batting playing XI")
    if payload.bowler_id not in bowling_xi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bowler is not in the bowling playing XI")
    if payload.next_batter_id and payload.next_batter_id not in batting_xi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Next batter is not in the batting playing XI")

    # 2. Consecutive Overs Validation
    # If the previous over was bowled by this bowler, they cannot bowl the current over.
    if session.previous_over_bowler_id and payload.bowler_id == session.previous_over_bowler_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bowler cannot bowl consecutive overs",
        )

    # 3. Apply Pure Scoring Engine
    ball_input = BallInput(
        striker_id=str(payload.striker_id),
        non_striker_id=str(payload.non_striker_id),
        bowler_id=str(payload.bowler_id),
        runs_batter=payload.runs_batter,
        extras_type=payload.extras_type,
        extras_runs=payload.extras_runs,
        is_wicket=payload.is_wicket,
        wicket_type=payload.wicket_type,
        dismissed_player_id=str(payload.dismissed_player_id) if payload.dismissed_player_id else None,
        next_batter_id=str(payload.next_batter_id) if payload.next_batter_id else None,
    )

    try:
        new_state = apply_ball(session.innings_state, ball_input)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 4. Atomic Database Persistence
    current_legal = session.innings_state.legal_balls
    over_no = current_legal // 6
    ball_no = (current_legal % 6) + 1

    next_seq = (
        db.scalar(
            select(func.max(BallEvent.sequence_no))
            .where(BallEvent.innings_id == innings.innings_id)
        )
        or 0
    ) + 1

    is_legal = (payload.extras_type not in ("wide", "no_ball", "penalty"))

    ball_event = BallEvent(
        innings_id=innings.innings_id,
        sequence_no=next_seq,
        over_no=over_no,
        ball_no=ball_no,
        striker_id=payload.striker_id,
        non_striker_id=payload.non_striker_id,
        bowler_id=payload.bowler_id,
        runs_scored=payload.runs_batter,
        extras_type=_map_extras_type_to_enum(payload.extras_type),
        extras_runs=payload.extras_runs,
        is_legal=is_legal,
        is_wicket=payload.is_wicket,
        wicket_type=_map_wicket_type_to_enum(payload.wicket_type),
        dismissed_player_id=payload.dismissed_player_id,
    )
    db.add(ball_event)

    # Update Innings Totals
    innings.total_runs = new_state.total_runs
    innings.wickets = new_state.wickets
    innings.balls_bowled = new_state.legal_balls
    innings.is_completed = new_state.is_completed

    # Check for over completion to manage consecutive bowler tracking
    if is_legal and (new_state.legal_balls > 0) and (new_state.legal_balls % 6 == 0):
        session.previous_over_bowler_id = payload.bowler_id
        session.current_over_bowler_id = None
    else:
        session.current_over_bowler_id = payload.bowler_id

    # If Innings completed
    if new_state.is_completed:
        if innings.innings_no == 1:
            match.status = MatchStatus.INNINGS_BREAK
        elif innings.innings_no == 2:
            match.status = MatchStatus.COMPLETED
            _compute_and_save_result(db, match)

    db.commit()
    db.refresh(innings)
    db.refresh(match)

    session.innings_state = new_state
    return _build_state_response(match, innings, new_state)


def undo_last_ball(
    db: Session,
    match_id: uuid.UUID,
    current_user: User,
) -> ScoringStateResponse:
    """Scorer or Admin: Delete last ball event and deterministically replay innings from ball zero."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Match with id '{match_id}' not found")

    verify_match_scorer(match, current_user)

    session = _get_or_load_session(db, match_id)
    innings = db.get(Innings, session.current_innings_id)
    if not innings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active innings not found")

    # Find the last recorded ball event in this innings
    last_event = (
        db.scalars(
            select(BallEvent)
            .where(BallEvent.innings_id == innings.innings_id)
            .order_by(BallEvent.sequence_no.desc())
        ).first()
    )
    if not last_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No delivery events to undo in the active innings",
        )

    # Delete last ball event
    db.delete(last_event)
    db.flush()

    # Replay all remaining events
    remaining_events = (
        db.scalars(
            select(BallEvent)
            .where(BallEvent.innings_id == innings.innings_id)
            .order_by(BallEvent.sequence_no.asc())
        ).all()
    )
    ball_inputs = [_ball_event_to_ball_input(e) for e in remaining_events]

    # Replay from ball 0
    batting_xi = session.team1_xi if session.batting_team_id == match.team1_id else session.team2_xi
    striker_id = str(batting_xi[0])
    non_striker_id = str(batting_xi[1])

    new_state = replay(
        events=ball_inputs,
        max_overs=match.overs,
        target_runs=innings.target_runs,
        striker_id=striker_id,
        non_striker_id=non_striker_id,
        innings_no=innings.innings_no,
    )

    # Update Innings in DB
    innings.total_runs = new_state.total_runs
    innings.wickets = new_state.wickets
    innings.balls_bowled = new_state.legal_balls
    innings.is_completed = new_state.is_completed

    # Revert match status to LIVE if it had completed on that undone ball
    if match.status in (MatchStatus.COMPLETED, MatchStatus.INNINGS_BREAK):
        match.status = MatchStatus.LIVE
        match.winner_id = None
        match.result_summary = None

    # Recalculate previous over bowler
    previous_over_bowler = None
    if remaining_events:
        last_remaining = remaining_events[-1]
        if last_remaining.over_no > 0 and (last_remaining.over_no * 6 <= innings.balls_bowled):
            prev_balls = [b for b in remaining_events if b.over_no == last_remaining.over_no - 1]
            if prev_balls:
                previous_over_bowler = prev_balls[-1].bowler_id

    session.previous_over_bowler_id = previous_over_bowler
    session.innings_state = new_state

    db.commit()
    db.refresh(innings)
    db.refresh(match)

    return _build_state_response(match, innings, new_state)


def end_innings(
    db: Session,
    match_id: uuid.UUID,
    current_user: User,
) -> ScoringStateResponse:
    """Scorer or Admin: Conclude Innings 1, set target for Innings 2, and switch match to INNINGS_BREAK."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Match with id '{match_id}' not found")

    verify_match_scorer(match, current_user)

    session = _get_or_load_session(db, match_id)
    innings1 = db.get(Innings, session.current_innings_id)

    if innings1.innings_no != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot call end-innings on Innings 2; use /complete instead",
        )

    # Complete Innings 1
    innings1.is_completed = True
    session.innings_state.is_completed = True
    match.status = MatchStatus.INNINGS_BREAK

    # Prepare Innings 2
    target_runs = innings1.total_runs + 1

    # Check if Innings 2 record already exists
    existing_i2 = db.scalar(
        select(Innings).where(Innings.match_id == match_id, Innings.innings_no == 2)
    )
    if not existing_i2:
        innings2 = Innings(
            match_id=match_id,
            batting_team_id=innings1.bowling_team_id,
            bowling_team_id=innings1.batting_team_id,
            innings_no=2,
            total_runs=0,
            wickets=0,
            balls_bowled=0,
            is_completed=False,
            target_runs=target_runs,
        )
        db.add(innings2)
        db.commit()
        db.refresh(innings2)
    else:
        innings2 = existing_i2
        innings2.target_runs = target_runs
        db.commit()

    db.refresh(match)
    db.refresh(innings1)

    # Update session in cache to point to Innings 2
    i2_batting_xi = session.team2_xi if session.batting_team_id == match.team1_id else session.team1_xi
    i2_bowling_xi = session.team1_xi if session.batting_team_id == match.team1_id else session.team2_xi

    i2_state = InningsState(
        innings_no=2,
        max_overs=match.overs,
        target_runs=target_runs,
        striker_id=str(i2_batting_xi[0]),
        non_striker_id=str(i2_batting_xi[1]),
        current_bowler_id=str(i2_bowling_xi[0]),
    )

    session.batting_team_id = innings2.batting_team_id
    session.bowling_team_id = innings2.bowling_team_id
    session.current_innings_id = innings2.innings_id
    session.current_innings_no = 2
    session.innings_state = i2_state
    session.previous_over_bowler_id = None
    session.current_over_bowler_id = i2_bowling_xi[0]

    return _build_state_response(match, innings2, i2_state)


def complete_match(
    db: Session,
    match_id: uuid.UUID,
    current_user: User,
) -> ScoringStateResponse:
    """Scorer or Admin: Officially conclude the match and declare official result summary."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Match with id '{match_id}' not found")

    verify_match_scorer(match, current_user)

    session = _get_or_load_session(db, match_id)
    active_innings = db.get(Innings, session.current_innings_id)

    active_innings.is_completed = True
    session.innings_state.is_completed = True
    match.status = MatchStatus.COMPLETED

    _compute_and_save_result(db, match)

    db.commit()
    db.refresh(match)
    db.refresh(active_innings)

    return _build_state_response(match, active_innings, session.innings_state)


def _compute_and_save_result(db: Session, match: Match) -> None:
    """Helper to compute result summary and update tournament standings."""
    all_innings = (
        db.scalars(
            select(Innings)
            .where(Innings.match_id == match.match_id)
            .order_by(Innings.innings_no.asc())
        ).all()
    )
    if len(all_innings) < 2:
        return

    i1 = all_innings[0]
    i2 = all_innings[1]

    t1 = db.get(Team, i1.batting_team_id)
    t2 = db.get(Team, i2.batting_team_id)

    t1_name = t1.team_name if t1 else "Team 1"
    t2_name = t2.team_name if t2 else "Team 2"

    if i2.total_runs > i1.total_runs:
        # Team 2 (chasing) won
        wickets_in_hand = 10 - i2.wickets
        suffix = "wicket" if wickets_in_hand == 1 else "wickets"
        match.winner_id = i2.batting_team_id
        match.result_summary = f"{t2_name} won by {wickets_in_hand} {suffix}"
    elif i1.total_runs > i2.total_runs:
        # Team 1 (defending) won
        margin = i1.total_runs - i2.total_runs
        suffix = "run" if margin == 1 else "runs"
        match.winner_id = i1.batting_team_id
        match.result_summary = f"{t1_name} won by {margin} {suffix}"
    else:
        # Match Tied
        match.winner_id = None
        match.result_summary = "Match tied"

    # Update Points Table for tournament
    if match.tournament_id:
        p1 = db.scalar(select(PointsTable).where(PointsTable.tournament_id == match.tournament_id, PointsTable.team_id == i1.batting_team_id))
        p2 = db.scalar(select(PointsTable).where(PointsTable.tournament_id == match.tournament_id, PointsTable.team_id == i2.batting_team_id))

        if p1 and p2:
            p1.played += 1
            p2.played += 1
            if match.winner_id == i1.batting_team_id:
                p1.won += 1
                p1.points += 2
                p2.lost += 1
            elif match.winner_id == i2.batting_team_id:
                p2.won += 1
                p2.points += 2
                p1.lost += 1
            else:
                p1.tied += 1
                p2.tied += 1
                p1.points += 1
                p2.points += 1


def suspend_match(
    db: Session,
    match_id: uuid.UUID,
    current_user: User,
) -> ScoringStateResponse:
    """Scorer or Admin: Suspend match due to rain or bad light."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Match with id '{match_id}' not found")

    verify_match_scorer(match, current_user)
    match.status = transition(match.status, MatchEvent.SUSPEND)

    session = _get_or_load_session(db, match_id)
    innings = db.get(Innings, session.current_innings_id)

    db.commit()
    db.refresh(match)
    return _build_state_response(match, innings, session.innings_state)


def resume_match(
    db: Session,
    match_id: uuid.UUID,
    current_user: User,
) -> ScoringStateResponse:
    """Scorer or Admin: Resume suspended match."""
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Match with id '{match_id}' not found")

    verify_match_scorer(match, current_user)
    match.status = transition(match.status, MatchEvent.RESUME)

    session = _get_or_load_session(db, match_id)
    innings = db.get(Innings, session.current_innings_id)

    db.commit()
    db.refresh(match)
    return _build_state_response(match, innings, session.innings_state)
