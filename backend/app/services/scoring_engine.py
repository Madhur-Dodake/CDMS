import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
# HELPER / PURE CALCULATION FUNCTIONS
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


def get_ball_display_token(ball: BallInput) -> str:
    """Convert delivery parameters into a standard recent-balls ribbon token."""
    if ball.is_wicket:
        if ball.extras_type == "no_ball":
            return f"W+Nb"
        return "W"
    if ball.extras_type == "wide":
        w = ball.extras_runs if ball.extras_runs > 1 else 1
        return "Wd" if w == 1 else f"{w}Wd"
    if ball.extras_type == "no_ball":
        nb = ball.extras_runs if ball.extras_runs > 0 else 1
        total_nb = ball.runs_batter + nb
        return f"{total_nb}Nb" if total_nb > 1 else "Nb"
    if ball.extras_type == "bye":
        b = ball.extras_runs if ball.extras_runs > 0 else 1
        return f"{b}B"
    if ball.extras_type == "leg_bye":
        lb = ball.extras_runs if ball.extras_runs > 0 else 1
        return f"{lb}Lb"
    return str(ball.runs_batter)


# -------------------------------------------------------------
# CORE PURE SCORING ENGINE
# -------------------------------------------------------------

def apply_ball(state: InningsState, ball: BallInput) -> InningsState:
    """Pure domain function applying a single delivery to an innings state.

    Returns a new InningsState instance. Leaves input state completely untouched.
    """
    if state.is_completed:
        raise ValueError("Cannot apply delivery to an already completed innings")

    # Clone state deeply to ensure pure functional immutability
    new_state = copy.deepcopy(state)

    # Ensure batters exist in stats
    if ball.striker_id not in new_state.batters:
        new_state.batters[ball.striker_id] = BatterStats(player_id=ball.striker_id)
    if ball.non_striker_id not in new_state.batters:
        new_state.batters[ball.non_striker_id] = BatterStats(player_id=ball.non_striker_id)

    # Ensure bowler exists in stats
    if ball.bowler_id not in new_state.bowlers:
        new_state.bowlers[ball.bowler_id] = BowlerStats(player_id=ball.bowler_id)

    striker = new_state.batters[ball.striker_id]
    bowler = new_state.bowlers[ball.bowler_id]

    new_state.current_bowler_id = ball.bowler_id
    new_state.total_deliveries += 1

    # 1. Extras and Legal Ball Evaluation
    is_legal = True
    runs_added_to_total = 0
    runs_off_bat = ball.runs_batter
    rotates_on_runs = False

    if ball.extras_type == "wide":
        is_legal = False
        extra_amt = ball.extras_runs if ball.extras_runs > 0 else 1
        new_state.extras.wides += extra_amt
        new_state.extras.total += extra_amt
        runs_added_to_total = extra_amt
        bowler.wides += 1
        bowler.runs_conceded += extra_amt
        # Batter balls faced does NOT increment on wide

    elif ball.extras_type == "no_ball":
        is_legal = False
        extra_amt = ball.extras_runs if ball.extras_runs > 0 else 1
        new_state.extras.no_balls += extra_amt
        new_state.extras.total += extra_amt
        runs_added_to_total = runs_off_bat + extra_amt

        # Batter gets runs off bat and faces a delivery
        striker.runs += runs_off_bat
        striker.balls_faced += 1
        if runs_off_bat == 4:
            striker.fours += 1
        elif runs_off_bat == 6:
            striker.sixes += 1

        bowler.no_balls += 1
        bowler.runs_conceded += (runs_off_bat + extra_amt)

        # Strike rotates on odd runs off the bat
        if runs_off_bat % 2 == 1:
            rotates_on_runs = True

    elif ball.extras_type == "bye":
        is_legal = True
        extra_amt = ball.extras_runs if ball.extras_runs > 0 else 1
        new_state.extras.byes += extra_amt
        new_state.extras.total += extra_amt
        runs_added_to_total = extra_amt

        striker.balls_faced += 1
        bowler.balls_bowled += 1
        # Byes do NOT count against bowler's runs conceded
        if extra_amt % 2 == 1:
            rotates_on_runs = True

    elif ball.extras_type == "leg_bye":
        is_legal = True
        extra_amt = ball.extras_runs if ball.extras_runs > 0 else 1
        new_state.extras.leg_byes += extra_amt
        new_state.extras.total += extra_amt
        runs_added_to_total = extra_amt

        striker.balls_faced += 1
        bowler.balls_bowled += 1
        # Leg-byes do NOT count against bowler's runs conceded
        if extra_amt % 2 == 1:
            rotates_on_runs = True

    elif ball.extras_type == "penalty":
        is_legal = False
        extra_amt = ball.extras_runs if ball.extras_runs > 0 else 5
        new_state.extras.penalty += extra_amt
        new_state.extras.total += extra_amt
        runs_added_to_total = extra_amt

    else:
        # Standard delivery off the bat (no extras)
        is_legal = True
        runs_added_to_total = runs_off_bat
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

        if runs_off_bat % 2 == 1:
            rotates_on_runs = True

    new_state.total_runs += runs_added_to_total

    if is_legal:
        new_state.legal_balls += 1

    # 2. Check Target Chased Before Wicket/End
    target_chased = (
        new_state.innings_no == 2
        and new_state.target_runs is not None
        and new_state.total_runs >= new_state.target_runs
    )

    # 3. Wicket Evaluation
    active_striker_id = ball.striker_id
    active_non_striker_id = ball.non_striker_id

    if ball.is_wicket:
        new_state.wickets += 1
        dismissed_id = ball.dismissed_player_id or ball.striker_id
        new_state.dismissed_players.append(dismissed_id)

        # Update dismissed batter
        if dismissed_id in new_state.batters:
            dismissed_batter = new_state.batters[dismissed_id]
            dismissed_batter.is_out = True
            dismissed_batter.dismissal_type = ball.wicket_type or "out"
            dismissed_batter.bowler_id = ball.bowler_id

        # Credit bowler with wicket (except for run outs / retired)
        if ball.wicket_type not in ("run_out", "retired"):
            bowler.wickets += 1

        # Check if innings has ended
        all_out = (new_state.wickets >= 10)
        overs_done = (new_state.legal_balls >= new_state.max_overs * 6)

        if not all_out and not overs_done and not target_chased:
            if not ball.next_batter_id:
                raise ValueError(
                    "next_batter_id is required when a wicket falls and innings is not ended"
                )
            # Replace the dismissed player
            if dismissed_id == active_striker_id:
                active_striker_id = ball.next_batter_id
            else:
                active_non_striker_id = ball.next_batter_id

            if ball.next_batter_id not in new_state.batters:
                new_state.batters[ball.next_batter_id] = BatterStats(player_id=ball.next_batter_id)

    # 4. Strike Rotation Mechanics
    # Strike rotates on odd runs (bat or bye/leg-bye), AND rotates at the end of each over (6 legal balls).
    # If both occur, they cancel each other out.
    over_ended = is_legal and (new_state.legal_balls % 6 == 0)

    swaps = 0
    if rotates_on_runs:
        swaps += 1
    if over_ended:
        swaps += 1

    if swaps % 2 == 1:
        active_striker_id, active_non_striker_id = active_non_striker_id, active_striker_id

    new_state.striker_id = active_striker_id
    new_state.non_striker_id = active_non_striker_id

    # 5. Innings Completion Check
    if new_state.wickets >= 10:
        new_state.is_completed = True
    elif new_state.legal_balls >= new_state.max_overs * 6:
        new_state.is_completed = True
    elif target_chased:
        new_state.is_completed = True

    # 6. Recent Balls Ribbon (Keep last 6 deliveries)
    token = get_ball_display_token(ball)
    new_state.recent_balls.append(token)
    new_state.recent_balls = new_state.recent_balls[-6:]

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
