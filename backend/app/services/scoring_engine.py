import copy
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class BallInput:
    """Input payload representing a single delivery event."""

    striker_id: str
    non_striker_id: str
    bowler_id: str
    runs_batter: int = 0
    extras_type: Optional[str] = None  # "wide", "no_ball", "bye", "leg_bye", "penalty", None
    extras_runs: int = 0
    is_wicket: bool = False
    wicket_type: Optional[str] = None  # "bowled", "caught", "lbw", "run_out", "stumped", "hit_wicket", etc.
    dismissed_player_id: Optional[str] = None
    next_batter_id: Optional[str] = None


@dataclass
class BatterStats:
    """Individual batter figures within the innings."""

    player_id: str
    runs: int = 0
    balls_faced: int = 0
    fours: int = 0
    sixes: int = 0
    is_out: bool = False
    dismissal_type: Optional[str] = None
    bowler_id: Optional[str] = None


@dataclass
class BowlerStats:
    """Individual bowler figures within the innings."""

    player_id: str
    balls_bowled: int = 0  # legal deliveries
    runs_conceded: int = 0
    wickets: int = 0
    maidens: int = 0
    wides: int = 0
    no_balls: int = 0
    dots: int = 0


@dataclass
class ExtrasBreakdown:
    """Breakdown of extras conceded during the innings."""

    wides: int = 0
    no_balls: int = 0
    byes: int = 0
    leg_byes: int = 0
    penalty: int = 0
    total: int = 0


@dataclass
class InningsState:
    """Complete immutable snapshot of an innings at any delivery point."""

    innings_no: int = 1
    max_overs: int = 20
    target_runs: Optional[int] = None
    total_runs: int = 0
    wickets: int = 0
    legal_balls: int = 0
    total_deliveries: int = 0
    striker_id: str = ""
    non_striker_id: str = ""
    current_bowler_id: Optional[str] = None
    is_completed: bool = False
    batters: Dict[str, BatterStats] = field(default_factory=dict)
    bowlers: Dict[str, BowlerStats] = field(default_factory=dict)
    dismissed_players: List[str] = field(default_factory=list)
    recent_balls: List[str] = field(default_factory=list)
    extras: ExtrasBreakdown = field(default_factory=ExtrasBreakdown)


# -------------------------------------------------------------
# HELPER / PURE CALCULATION FUNCTIONS (V(G) <= 5)
# -------------------------------------------------------------

def overs_display(balls: int) -> str:
    """Format integer legal balls into cricket over notation (e.g. 99 -> '16.3')."""
    if balls < 0:
        return "0.0"
    overs = balls // 6
    remainder = balls % 6
    return f"{overs}.{remainder}"


def current_run_rate(total_runs: int, legal_balls: int) -> float:
    """Calculate Current Run Rate (CRR). Protected against division by zero."""
    if legal_balls <= 0:
        return 0.0
    overs_decimal = legal_balls / 6.0
    return round(total_runs / overs_decimal, 2)


def required_run_rate(runs_needed: int, balls_remaining: int) -> Optional[float]:
    """Calculate Required Run Rate (RRR) for 2nd innings. Protected against division by zero."""
    if runs_needed <= 0:
        return 0.0
    if balls_remaining <= 0:
        return None
    overs_decimal = balls_remaining / 6.0
    return round(runs_needed / overs_decimal, 2)


def _format_wicket_token(ball: BallInput) -> str:
    """Format recent-ball token for wicket delivery."""
    if ball.extras_type == "no_ball":
        return "W+Nb"
    return "W"


def _format_wide_token(ball: BallInput) -> str:
    """Format recent-ball token for wide delivery."""
    w = ball.extras_runs if ball.extras_runs > 1 else 1
    return "Wd" if w == 1 else f"{w}Wd"


def _format_no_ball_token(ball: BallInput) -> str:
    """Format recent-ball token for no-ball delivery."""
    nb = ball.extras_runs if ball.extras_runs > 0 else 1
    total_nb = ball.runs_batter + nb
    return f"{total_nb}Nb" if total_nb > 1 else "Nb"


def _format_bye_token(ball: BallInput, suffix: str) -> str:
    """Format recent-ball token for bye or leg-bye delivery."""
    b = ball.extras_runs if ball.extras_runs > 0 else 1
    return f"{b}{suffix}"


def get_ball_display_token(ball: BallInput) -> str:
    """Convert delivery parameters into a standard recent-balls ribbon token."""
    if ball.is_wicket:
        return _format_wicket_token(ball)
    if ball.extras_type == "wide":
        return _format_wide_token(ball)
    if ball.extras_type == "no_ball":
        return _format_no_ball_token(ball)
    if ball.extras_type == "bye":
        return _format_bye_token(ball, "B")
    if ball.extras_type == "leg_bye":
        return _format_bye_token(ball, "Lb")
    return str(ball.runs_batter)


# -------------------------------------------------------------
# INTERNAL ATOMIC DELIVERY HELPERS (V(G) <= 5)
# -------------------------------------------------------------

def _init_ball_participants(state: InningsState, ball: BallInput) -> Tuple[BatterStats, BowlerStats]:
    """Ensure participants exist in innings state dictionaries."""
    if ball.striker_id not in state.batters:
        state.batters[ball.striker_id] = BatterStats(player_id=ball.striker_id)
    if ball.non_striker_id not in state.batters:
        state.batters[ball.non_striker_id] = BatterStats(player_id=ball.non_striker_id)
    if ball.bowler_id not in state.bowlers:
        state.bowlers[ball.bowler_id] = BowlerStats(player_id=ball.bowler_id)
    return state.batters[ball.striker_id], state.bowlers[ball.bowler_id]


def _process_wide(state: InningsState, bowler: BowlerStats, ball: BallInput) -> Tuple[bool, int, bool]:
    """Process wide delivery outcomes: illegal ball, runs added to extras and bowler."""
    extra_amt = ball.extras_runs if ball.extras_runs > 0 else 1
    state.extras.wides += extra_amt
    state.extras.total += extra_amt
    bowler.wides += 1
    bowler.runs_conceded += extra_amt
    return False, extra_amt, False


def _process_no_ball(
    state: InningsState, striker: BatterStats, bowler: BowlerStats, ball: BallInput
) -> Tuple[bool, int, bool]:
    """Process no-ball delivery outcomes: illegal ball, batter runs and bowler conceded."""
    extra_amt = ball.extras_runs if ball.extras_runs > 0 else 1
    state.extras.no_balls += extra_amt
    state.extras.total += extra_amt

    runs_off_bat = ball.runs_batter
    striker.runs += runs_off_bat
    striker.balls_faced += 1
    if runs_off_bat == 4:
        striker.fours += 1
    elif runs_off_bat == 6:
        striker.sixes += 1

    bowler.no_balls += 1
    bowler.runs_conceded += (runs_off_bat + extra_amt)
    return False, runs_off_bat + extra_amt, (runs_off_bat % 2 == 1)


def _process_bye_or_leg_bye(
    state: InningsState,
    striker: BatterStats,
    bowler: BowlerStats,
    ball: BallInput,
    is_leg_bye: bool,
) -> Tuple[bool, int, bool]:
    """Process bye or leg-bye outcomes: legal ball, bowler conceded runs untouched."""
    extra_amt = ball.extras_runs if ball.extras_runs > 0 else 1
    if is_leg_bye:
        state.extras.leg_byes += extra_amt
    else:
        state.extras.byes += extra_amt
    state.extras.total += extra_amt

    striker.balls_faced += 1
    bowler.balls_bowled += 1
    return True, extra_amt, (extra_amt % 2 == 1)


def _process_penalty(state: InningsState, ball: BallInput) -> Tuple[bool, int, bool]:
    """Process penalty runs: illegal ball, added directly to extras."""
    extra_amt = ball.extras_runs if ball.extras_runs > 0 else 5
    state.extras.penalty += extra_amt
    state.extras.total += extra_amt
    return False, extra_amt, False


def _process_standard_delivery(
    striker: BatterStats, bowler: BowlerStats, ball: BallInput
) -> Tuple[bool, int, bool]:
    """Process standard delivery off the bat."""
    runs_off_bat = ball.runs_batter
    striker.runs += runs_off_bat
    striker.balls_faced += 1
    if runs_off_bat == 4:
        striker.fours += 1
    elif runs_off_bat == 6:
        striker.sixes += 1

    bowler.balls_bowled += 1
    bowler.runs_conceded += runs_off_bat
    if runs_off_bat == 0 and not ball.is_wicket:
        bowler.dots += 1

    return True, runs_off_bat, (runs_off_bat % 2 == 1)


def _process_delivery_outcome(
    state: InningsState, striker: BatterStats, bowler: BowlerStats, ball: BallInput
) -> Tuple[bool, int, bool]:
    """Dispatch outcome processing based on extras_type."""
    if ball.extras_type == "wide":
        return _process_wide(state, bowler, ball)
    if ball.extras_type == "no_ball":
        return _process_no_ball(state, striker, bowler, ball)
    if ball.extras_type == "bye":
        return _process_bye_or_leg_bye(state, striker, bowler, ball, is_leg_bye=False)
    if ball.extras_type == "leg_bye":
        return _process_bye_or_leg_bye(state, striker, bowler, ball, is_leg_bye=True)
    if ball.extras_type == "penalty":
        return _process_penalty(state, ball)
    return _process_standard_delivery(striker, bowler, ball)


def _is_target_chased(state: InningsState) -> bool:
    """Check if 2nd innings target has been successfully chased."""
    return (
        state.innings_no == 2
        and state.target_runs is not None
        and state.total_runs >= state.target_runs
    )


def _record_dismissal(
    state: InningsState, bowler: BowlerStats, ball: BallInput, dismissed_id: str
) -> None:
    """Update dismissed batter record and bowler wicket count."""
    if dismissed_id in state.batters:
        dismissed_batter = state.batters[dismissed_id]
        dismissed_batter.is_out = True
        dismissed_batter.dismissal_type = ball.wicket_type or "out"
        dismissed_batter.bowler_id = ball.bowler_id

    if ball.wicket_type not in ("run_out", "retired"):
        bowler.wickets += 1


def _replace_dismissed_batter(
    state: InningsState,
    ball: BallInput,
    active_striker_id: str,
    active_non_striker_id: str,
    dismissed_id: str,
    innings_ended: bool,
) -> Tuple[str, str]:
    """Handle batter substitution on wicket fall."""
    if innings_ended:
        return active_striker_id, active_non_striker_id

    if not ball.next_batter_id:
        raise ValueError(
            "next_batter_id is required when a wicket falls and innings is not ended"
        )

    if dismissed_id == active_striker_id:
        active_striker_id = ball.next_batter_id
    else:
        active_non_striker_id = ball.next_batter_id

    if ball.next_batter_id not in state.batters:
        state.batters[ball.next_batter_id] = BatterStats(player_id=ball.next_batter_id)

    return active_striker_id, active_non_striker_id


def _process_wicket(
    state: InningsState,
    bowler: BowlerStats,
    ball: BallInput,
    active_striker_id: str,
    active_non_striker_id: str,
    target_chased: bool,
) -> Tuple[str, str]:
    """Process wicket event, records dismissal, and substitutes the next batter."""
    if not ball.is_wicket:
        return active_striker_id, active_non_striker_id

    state.wickets += 1
    dismissed_id = ball.dismissed_player_id or ball.striker_id
    state.dismissed_players.append(dismissed_id)

    _record_dismissal(state, bowler, ball, dismissed_id)

    innings_ended = (
        state.wickets >= 10
        or (state.legal_balls >= state.max_overs * 6)
        or target_chased
    )

    return _replace_dismissed_batter(
        state, ball, active_striker_id, active_non_striker_id, dismissed_id, innings_ended
    )


def _compute_strike_rotation(
    striker_id: str, non_striker_id: str, rotates_on_runs: bool, over_ended: bool
) -> Tuple[str, str]:
    """Compute strike swapping at ball conclusion."""
    swaps = (1 if rotates_on_runs else 0) + (1 if over_ended else 0)
    if swaps % 2 == 1:
        return non_striker_id, striker_id
    return striker_id, non_striker_id


def _check_innings_completion(state: InningsState, target_chased: bool) -> bool:
    """Check whether innings has terminated under any cricket rule."""
    if state.wickets >= 10:
        return True
    if state.legal_balls >= state.max_overs * 6:
        return True
    return target_chased


def _update_recent_balls(state: InningsState, ball: BallInput) -> None:
    """Append delivery token and maintain 6-ball rolling window."""
    token = get_ball_display_token(ball)
    state.recent_balls.append(token)
    state.recent_balls = state.recent_balls[-6:]


# -------------------------------------------------------------
# CORE PURE SCORING ENGINE (V(G) <= 5)
# -------------------------------------------------------------

def apply_ball(state: InningsState, ball: BallInput) -> InningsState:
    """Pure domain function applying a single delivery to an innings state.

    Returns a new InningsState instance. Leaves input state completely untouched.
    """
    if state.is_completed:
        raise ValueError("Cannot apply delivery to an already completed innings")

    # Clone state deeply to ensure pure functional immutability
    new_state = copy.deepcopy(state)

    striker, bowler = _init_ball_participants(new_state, ball)
    new_state.current_bowler_id = ball.bowler_id
    new_state.total_deliveries += 1

    is_legal, runs_added, rotates_on_runs = _process_delivery_outcome(
        new_state, striker, bowler, ball
    )
    new_state.total_runs += runs_added
    if is_legal:
        new_state.legal_balls += 1

    target_chased = _is_target_chased(new_state)

    act_striker, act_non_striker = _process_wicket(
        new_state, bowler, ball, ball.striker_id, ball.non_striker_id, target_chased
    )

    over_ended = is_legal and (new_state.legal_balls % 6 == 0)
    new_state.striker_id, new_state.non_striker_id = _compute_strike_rotation(
        act_striker, act_non_striker, rotates_on_runs, over_ended
    )

    new_state.is_completed = _check_innings_completion(new_state, target_chased)
    _update_recent_balls(new_state, ball)

    return new_state


def replay(
    events: List[BallInput],
    initial_state: Optional[InningsState] = None,
    max_overs: int = 20,
    target_runs: Optional[int] = None,
    striker_id: str = "player_1",
    non_striker_id: str = "player_2",
    innings_no: int = 1,
) -> InningsState:
    """Deterministically replay a sequence of delivery events from ball zero.

    Used by Undo functionality: undoing the last delivery is simply replaying
    all delivery events up to index len(events) - 1.
    """
    if initial_state:
        current_state = copy.deepcopy(initial_state)
    else:
        current_state = InningsState(
            innings_no=innings_no,
            max_overs=max_overs,
            target_runs=target_runs,
            striker_id=striker_id,
            non_striker_id=non_striker_id,
        )

    for event in events:
        current_state = apply_ball(current_state, event)

    return current_state
