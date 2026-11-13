import pytest
from app.services.scoring_engine import (
    BallInput,
    InningsState,
    apply_ball,
    current_run_rate,
    overs_display,
    replay,
    required_run_rate,
)


@pytest.fixture
def fresh_t20_state() -> InningsState:
    """Return a fresh 1st innings state for T20."""
    return InningsState(
        innings_no=1,
        max_overs=20,
        striker_id="batter_1",
        non_striker_id="batter_2",
    )


# -------------------------------------------------------------
# 1. DOT BALL & RUNS OFF THE BAT
# -------------------------------------------------------------

def test_dot_ball_increments_deliveries_and_legal_balls_with_zero_runs(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", runs_batter=0)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 0
    assert state.legal_balls == 1
    assert state.total_deliveries == 1
    assert state.batters["batter_1"].runs == 0
    assert state.batters["batter_1"].balls_faced == 1
    assert state.bowlers["bowler_1"].dots == 1
    assert state.striker_id == "batter_1"
    assert state.recent_balls == ["0"]


def test_single_run_off_bat_rotates_strike(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", runs_batter=1)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 1
    assert state.batters["batter_1"].runs == 1
    assert state.striker_id == "batter_2"  # Rotated
    assert state.non_striker_id == "batter_1"


def test_two_runs_off_bat_does_not_rotate_strike(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", runs_batter=2)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 2
    assert state.striker_id == "batter_1"
    assert state.non_striker_id == "batter_2"


def test_three_runs_off_bat_rotates_strike(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", runs_batter=3)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 3
    assert state.striker_id == "batter_2"
    assert state.non_striker_id == "batter_1"


def test_boundary_four_off_bat_increments_fours_and_maintains_strike(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", runs_batter=4)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 4
    assert state.batters["batter_1"].fours == 1
    assert state.striker_id == "batter_1"
    assert state.recent_balls == ["4"]


def test_boundary_six_off_bat_increments_sixes_and_maintains_strike(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", runs_batter=6)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 6
    assert state.batters["batter_1"].sixes == 1
    assert state.striker_id == "batter_1"
    assert state.recent_balls == ["6"]


# -------------------------------------------------------------
# 2. EXTRAS (WIDE, NO-BALL, BYE, LEG-BYE, PENALTY)
# -------------------------------------------------------------

def test_wide_adds_run_without_incrementing_legal_balls_or_facing_count(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", extras_type="wide", extras_runs=1)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 1
    assert state.legal_balls == 0
    assert state.total_deliveries == 1
    assert state.extras.wides == 1
    assert state.batters["batter_1"].balls_faced == 0
    assert state.bowlers["bowler_1"].wides == 1
    assert state.bowlers["bowler_1"].runs_conceded == 1
    assert state.striker_id == "batter_1"
    assert state.recent_balls == ["Wd"]


def test_multi_run_wide_adds_all_runs_to_extras_and_bowler(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", extras_type="wide", extras_runs=5)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 5
    assert state.extras.wides == 5
    assert state.bowlers["bowler_1"].runs_conceded == 5
    assert state.recent_balls == ["5Wd"]


def test_no_ball_adds_penalty_and_does_not_increment_legal_balls(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", extras_type="no_ball", extras_runs=1)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 1
    assert state.legal_balls == 0
    assert state.extras.no_balls == 1
    assert state.batters["batter_1"].balls_faced == 1
    assert state.bowlers["bowler_1"].no_balls == 1
    assert state.recent_balls == ["Nb"]


def test_no_ball_with_runs_off_bat_credits_batter_and_penalizes_bowler(fresh_t20_state: InningsState) -> None:
    # Batter hits 4 off a no-ball -> total 5 runs
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", runs_batter=4, extras_type="no_ball", extras_runs=1)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 5
    assert state.legal_balls == 0
    assert state.batters["batter_1"].runs == 4
    assert state.batters["batter_1"].fours == 1
    assert state.bowlers["bowler_1"].runs_conceded == 5
    assert state.striker_id == "batter_1"  # 4 runs off bat = no rotation
    assert state.recent_balls == ["5Nb"]


def test_no_ball_with_single_run_rotates_strike(fresh_t20_state: InningsState) -> None:
    # Batter runs 1 off a no-ball -> total 2 runs
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", runs_batter=1, extras_type="no_ball", extras_runs=1)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 2
    assert state.batters["batter_1"].runs == 1
    assert state.striker_id == "batter_2"  # Odd run off bat rotated strike
    assert state.non_striker_id == "batter_1"


def test_bye_is_legal_ball_and_does_not_credit_batter_or_debit_bowler(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", extras_type="bye", extras_runs=1)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 1
    assert state.legal_balls == 1
    assert state.extras.byes == 1
    assert state.batters["batter_1"].runs == 0
    assert state.batters["batter_1"].balls_faced == 1
    assert state.bowlers["bowler_1"].runs_conceded == 0  # Bowler not charged for byes
    assert state.recent_balls == ["1B"]


def test_bye_odd_runs_rotates_strike(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", extras_type="bye", extras_runs=1)
    state = apply_ball(fresh_t20_state, ball)

    assert state.striker_id == "batter_2"


def test_bye_even_runs_does_not_rotate_strike(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", extras_type="bye", extras_runs=2)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 2
    assert state.striker_id == "batter_1"


def test_leg_bye_is_legal_ball_and_does_not_debit_bowler(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", extras_type="leg_bye", extras_runs=1)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 1
    assert state.legal_balls == 1
    assert state.extras.leg_byes == 1
    assert state.bowlers["bowler_1"].runs_conceded == 0
    assert state.recent_balls == ["1Lb"]


def test_leg_bye_odd_runs_rotates_strike(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", extras_type="leg_bye", extras_runs=3)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 3
    assert state.striker_id == "batter_2"


def test_penalty_runs_adds_to_total_without_legal_ball(fresh_t20_state: InningsState) -> None:
    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", extras_type="penalty", extras_runs=5)
    state = apply_ball(fresh_t20_state, ball)

    assert state.total_runs == 5
    assert state.legal_balls == 0
    assert state.extras.penalty == 5


# -------------------------------------------------------------
# 3. OVER COMPLETION & STRIKE ROTATION
# -------------------------------------------------------------

def test_over_end_on_dot_ball_rotates_strike(fresh_t20_state: InningsState) -> None:
    # Bowl 5 dot balls
    s = fresh_t20_state
    for _ in range(5):
        s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=0))
    assert s.legal_balls == 5
    assert s.striker_id == "batter_1"

    # 6th dot ball ends the over
    s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=0))
    assert s.legal_balls == 6
    assert s.striker_id == "batter_2"  # Rotated at end of over
    assert s.non_striker_id == "batter_1"


def test_over_end_on_two_runs_rotates_strike(fresh_t20_state: InningsState) -> None:
    s = fresh_t20_state
    for _ in range(5):
        s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=0))

    # 6th ball: 2 runs scored (even) + over ends -> strike rotates due to over end
    s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=2))
    assert s.striker_id == "batter_2"
    assert s.non_striker_id == "batter_1"


def test_over_end_on_boundary_four_rotates_strike(fresh_t20_state: InningsState) -> None:
    s = fresh_t20_state
    for _ in range(5):
        s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=0))

    s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=4))
    assert s.striker_id == "batter_2"


def test_over_end_on_odd_run_cancels_both_swaps_maintaining_striker(fresh_t20_state: InningsState) -> None:
    s = fresh_t20_state
    for _ in range(5):
        s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=0))
    assert s.striker_id == "batter_1"

    # 6th ball: 1 run scored (odd run swap + over end swap cancel out!)
    s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=1))
    assert s.legal_balls == 6
    assert s.striker_id == "batter_1"  # Unchanged!
    assert s.non_striker_id == "batter_2"


def test_over_end_on_three_runs_cancels_both_swaps(fresh_t20_state: InningsState) -> None:
    s = fresh_t20_state
    for _ in range(5):
        s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=0))

    s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=3))
    assert s.striker_id == "batter_1"  # 3 runs + over end cancel out


def test_over_does_not_end_on_wide_as_sixth_delivery(fresh_t20_state: InningsState) -> None:
    s = fresh_t20_state
    for _ in range(5):
        s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=0))

    # 6th delivery is a wide
    s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", extras_type="wide", extras_runs=1))
    assert s.legal_balls == 5  # Still 5 legal balls
    assert s.striker_id == "batter_1"  # No over end swap


def test_over_does_not_end_on_no_ball_as_sixth_delivery(fresh_t20_state: InningsState) -> None:
    s = fresh_t20_state
    for _ in range(5):
        s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", runs_batter=0))

    s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="b1", extras_type="no_ball", extras_runs=1))
    assert s.legal_balls == 5
    assert s.striker_id == "batter_1"


# -------------------------------------------------------------
# 4. WICKETS & DISMISSALS
# -------------------------------------------------------------

def test_wicket_bowled_credits_bowler_and_dismisses_striker(fresh_t20_state: InningsState) -> None:
    ball = BallInput(
        striker_id="batter_1",
        non_striker_id="batter_2",
        bowler_id="bowler_1",
        is_wicket=True,
        wicket_type="bowled",
        next_batter_id="batter_3",
    )
    state = apply_ball(fresh_t20_state, ball)

    assert state.wickets == 1
    assert state.batters["batter_1"].is_out is True
    assert state.batters["batter_1"].dismissal_type == "bowled"
    assert state.bowlers["bowler_1"].wickets == 1
    assert state.striker_id == "batter_3"  # Replaced at striker
    assert state.non_striker_id == "batter_2"
    assert state.recent_balls == ["W"]


def test_wicket_caught_credits_bowler_and_dismisses_striker(fresh_t20_state: InningsState) -> None:
    ball = BallInput(
        striker_id="batter_1",
        non_striker_id="batter_2",
        bowler_id="bowler_1",
        is_wicket=True,
        wicket_type="caught",
        next_batter_id="batter_3",
    )
    state = apply_ball(fresh_t20_state, ball)

    assert state.wickets == 1
    assert state.batters["batter_1"].is_out is True
    assert state.batters["batter_1"].dismissal_type == "caught"
    assert state.bowlers["bowler_1"].wickets == 1


def test_wicket_lbw_credits_bowler_and_dismisses_striker(fresh_t20_state: InningsState) -> None:
    ball = BallInput(
        striker_id="batter_1",
        non_striker_id="batter_2",
        bowler_id="bowler_1",
        is_wicket=True,
        wicket_type="lbw",
        next_batter_id="batter_3",
    )
    state = apply_ball(fresh_t20_state, ball)

    assert state.wickets == 1
    assert state.batters["batter_1"].dismissal_type == "lbw"
    assert state.bowlers["bowler_1"].wickets == 1


def test_wicket_stumped_credits_bowler_and_dismisses_striker(fresh_t20_state: InningsState) -> None:
    ball = BallInput(
        striker_id="batter_1",
        non_striker_id="batter_2",
        bowler_id="bowler_1",
        is_wicket=True,
        wicket_type="stumped",
        next_batter_id="batter_3",
    )
    state = apply_ball(fresh_t20_state, ball)

    assert state.batters["batter_1"].dismissal_type == "stumped"
    assert state.bowlers["bowler_1"].wickets == 1


def test_wicket_hit_wicket_credits_bowler_and_dismisses_striker(fresh_t20_state: InningsState) -> None:
    ball = BallInput(
        striker_id="batter_1",
        non_striker_id="batter_2",
        bowler_id="bowler_1",
        is_wicket=True,
        wicket_type="hit_wicket",
        next_batter_id="batter_3",
    )
    state = apply_ball(fresh_t20_state, ball)

    assert state.batters["batter_1"].dismissal_type == "hit_wicket"
    assert state.bowlers["bowler_1"].wickets == 1


def test_run_out_of_striker_does_not_credit_bowler_wicket(fresh_t20_state: InningsState) -> None:
    ball = BallInput(
        striker_id="batter_1",
        non_striker_id="batter_2",
        bowler_id="bowler_1",
        is_wicket=True,
        wicket_type="run_out",
        dismissed_player_id="batter_1",
        next_batter_id="batter_3",
    )
    state = apply_ball(fresh_t20_state, ball)

    assert state.wickets == 1
    assert state.bowlers["bowler_1"].wickets == 0  # No wicket credited to bowler
    assert state.batters["batter_1"].is_out is True
    assert state.striker_id == "batter_3"


def test_run_out_of_non_striker_replaces_non_striker(fresh_t20_state: InningsState) -> None:
    ball = BallInput(
        striker_id="batter_1",
        non_striker_id="batter_2",
        bowler_id="bowler_1",
        is_wicket=True,
        wicket_type="run_out",
        dismissed_player_id="batter_2",
        next_batter_id="batter_3",
    )
    state = apply_ball(fresh_t20_state, ball)

    assert state.wickets == 1
    assert state.batters["batter_2"].is_out is True
    assert state.striker_id == "batter_1"  # Striker remains striker
    assert state.non_striker_id == "batter_3"  # Non-striker replaced


def test_run_out_with_odd_run_swaps_strike_after_replacement(fresh_t20_state: InningsState) -> None:
    # 1 run completed, striker run out
    ball = BallInput(
        striker_id="batter_1",
        non_striker_id="batter_2",
        bowler_id="bowler_1",
        runs_batter=1,
        is_wicket=True,
        wicket_type="run_out",
        dismissed_player_id="batter_1",
        next_batter_id="batter_3",
    )
    state = apply_ball(fresh_t20_state, ball)

    # 1 run completed -> Batter 2 is on strike, new Batter 3 at non-striker
    assert state.total_runs == 1
    assert state.striker_id == "batter_2"
    assert state.non_striker_id == "batter_3"


def test_wicket_missing_next_batter_raises_error_when_innings_active(fresh_t20_state: InningsState) -> None:
    ball = BallInput(
        striker_id="batter_1",
        non_striker_id="batter_2",
        bowler_id="bowler_1",
        is_wicket=True,
        wicket_type="bowled",
        next_batter_id=None,  # Missing!
    )
    with pytest.raises(ValueError) as exc:
        apply_ball(fresh_t20_state, ball)
    assert "next_batter_id is required" in str(exc.value)


# -------------------------------------------------------------
# 5. INNINGS COMPLETION (ALL OUT, OVERS, TARGET CHASED)
# -------------------------------------------------------------

def test_tenth_wicket_falls_ends_innings_all_out(fresh_t20_state: InningsState) -> None:
    s = fresh_t20_state
    # Take 9 wickets
    for i in range(1, 10):
        s = apply_ball(
            s,
            BallInput(
                striker_id=s.striker_id,
                non_striker_id=s.non_striker_id,
                bowler_id="b1",
                is_wicket=True,
                wicket_type="bowled",
                next_batter_id=f"batter_{i+2}",
            ),
        )
    assert s.wickets == 9
    assert s.is_completed is False

    # 10th wicket: does not require next_batter_id
    s10 = apply_ball(
        s,
        BallInput(
            striker_id=s.striker_id,
            non_striker_id=s.non_striker_id,
            bowler_id="b1",
            is_wicket=True,
            wicket_type="bowled",
            next_batter_id=None,
        ),
    )
    assert s10.wickets == 10
    assert s10.is_completed is True


def test_overs_complete_ends_innings() -> None:
    # 1-over match (6 legal balls)
    s = InningsState(innings_no=1, max_overs=1, striker_id="b1", non_striker_id="b2")
    for _ in range(5):
        s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="bowl", runs_batter=1))
        assert s.is_completed is False

    # 6th ball finishes the allocated over quota
    s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="bowl", runs_batter=1))
    assert s.legal_balls == 6
    assert s.is_completed is True


def test_target_chased_in_second_innings_ends_innings_immediately() -> None:
    # Innings 2 with target of 100 runs
    s = InningsState(innings_no=2, max_overs=20, target_runs=100, striker_id="b1", non_striker_id="b2", total_runs=96)
    assert s.is_completed is False

    # Batter hits a boundary four -> reaches 100 runs >= target
    s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="bowl", runs_batter=4))
    assert s.total_runs == 100
    assert s.is_completed is True


def test_target_not_yet_reached_leaves_innings_active() -> None:
    s = InningsState(innings_no=2, max_overs=20, target_runs=100, striker_id="b1", non_striker_id="b2", total_runs=96)
    s = apply_ball(s, BallInput(striker_id=s.striker_id, non_striker_id=s.non_striker_id, bowler_id="bowl", runs_batter=2))
    assert s.total_runs == 98
    assert s.is_completed is False


def test_cannot_apply_ball_to_completed_innings_raises_error() -> None:
    s = InningsState(innings_no=1, max_overs=20, is_completed=True, striker_id="b1", non_striker_id="b2")
    with pytest.raises(ValueError) as exc:
        apply_ball(s, BallInput(striker_id="b1", non_striker_id="b2", bowler_id="b", runs_batter=1))
    assert "already completed" in str(exc.value)


# -------------------------------------------------------------
# 6. RUN RATES & OVER DISPLAY UTILITIES
# -------------------------------------------------------------

def test_current_run_rate_with_zero_balls_returns_zero() -> None:
    assert current_run_rate(total_runs=0, legal_balls=0) == 0.0
    assert current_run_rate(total_runs=10, legal_balls=0) == 0.0


def test_current_run_rate_calculates_accurately_with_balls() -> None:
    # 60 runs in 36 legal balls (6.0 overs) = 10.00 CRR
    assert current_run_rate(total_runs=60, legal_balls=36) == 10.0
    # 10 runs in 6 legal balls = 10.00
    assert current_run_rate(total_runs=10, legal_balls=6) == 10.0
    # 14 runs in 15 balls = 14 / 2.5 = 5.6
    assert current_run_rate(total_runs=14, legal_balls=15) == 5.6


def test_required_run_rate_with_zero_balls_returns_none_or_zero() -> None:
    assert required_run_rate(runs_needed=10, balls_remaining=0) is None
    assert required_run_rate(runs_needed=0, balls_remaining=0) == 0.0
    assert required_run_rate(runs_needed=-5, balls_remaining=10) == 0.0


def test_required_run_rate_calculates_accurately_with_remaining_balls() -> None:
    # 36 runs needed in 24 balls (4.0 overs) = 9.00 RRR
    assert required_run_rate(runs_needed=36, balls_remaining=24) == 9.0


def test_overs_display_formats_zero_and_partial_and_complete_overs() -> None:
    assert overs_display(0) == "0.0"
    assert overs_display(1) == "0.1"
    assert overs_display(5) == "0.5"
    assert overs_display(6) == "1.0"
    assert overs_display(11) == "1.5"
    assert overs_display(12) == "2.0"
    assert overs_display(99) == "16.3"


def test_recent_balls_ribbon_maintains_last_six_deliveries(fresh_t20_state: InningsState) -> None:
    s = fresh_t20_state
    # Bowl 8 deliveries: 0, 1, 4, 6, W, Wd, 2, 1
    deliveries = [
        BallInput(striker_id="b1", non_striker_id="b2", bowler_id="bowler", runs_batter=0),
        BallInput(striker_id="b1", non_striker_id="b2", bowler_id="bowler", runs_batter=1),
        BallInput(striker_id="b2", non_striker_id="b1", bowler_id="bowler", runs_batter=4),
        BallInput(striker_id="b2", non_striker_id="b1", bowler_id="bowler", runs_batter=6),
        BallInput(striker_id="b2", non_striker_id="b1", bowler_id="bowler", is_wicket=True, wicket_type="bowled", next_batter_id="b3"),
        BallInput(striker_id="b3", non_striker_id="b1", bowler_id="bowler", extras_type="wide", extras_runs=1),
        BallInput(striker_id="b3", non_striker_id="b1", bowler_id="bowler", runs_batter=2),
        BallInput(striker_id="b3", non_striker_id="b1", bowler_id="bowler", runs_batter=1),
    ]
    for d in deliveries:
        s = apply_ball(s, d)

    # Total 8 balls bowled, recent_balls contains only the last 6:
    # [4, 6, W, Wd, 2, 1]
    assert len(s.recent_balls) == 6
    assert s.recent_balls == ["4", "6", "W", "Wd", "2", "1"]


# -------------------------------------------------------------
# 7. UNDO VIA REPLAY & PURE IMMUTABILITY
# -------------------------------------------------------------

def test_undo_via_replay_equals_state_before_last_ball() -> None:
    """Verify that replaying balls[:k-1] matches the exact state prior to ball k."""
    events = [
        BallInput(striker_id="b1", non_striker_id="b2", bowler_id="bowler", runs_batter=0),
        BallInput(striker_id="b1", non_striker_id="b2", bowler_id="bowler", runs_batter=1),
        BallInput(striker_id="b2", non_striker_id="b1", bowler_id="bowler", runs_batter=4),
        BallInput(striker_id="b2", non_striker_id="b1", bowler_id="bowler", extras_type="wide", extras_runs=1),
        BallInput(striker_id="b2", non_striker_id="b1", bowler_id="bowler", runs_batter=2),
    ]

    # Replay up to ball 4
    state_at_4 = replay(events[:4], striker_id="b1", non_striker_id="b2")

    # Replay up to ball 5
    state_at_5 = replay(events[:5], striker_id="b1", non_striker_id="b2")
    assert state_at_5.total_runs == state_at_4.total_runs + 2

    # Undo ball 5 by replaying events[:4]
    undone_state = replay(events[:4], striker_id="b1", non_striker_id="b2")

    # State after undo must exactly match state_at_4
    assert undone_state.total_runs == state_at_4.total_runs
    assert undone_state.legal_balls == state_at_4.legal_balls
    assert undone_state.striker_id == state_at_4.striker_id
    assert undone_state.non_striker_id == state_at_4.non_striker_id
    assert undone_state.extras == state_at_4.extras
    assert undone_state.recent_balls == state_at_4.recent_balls


def test_pure_immutability_original_state_remains_unchanged(fresh_t20_state: InningsState) -> None:
    """Verify that apply_ball does not mutate the passed input state."""
    initial_runs = fresh_t20_state.total_runs
    initial_balls = fresh_t20_state.legal_balls
    initial_striker = fresh_t20_state.striker_id

    ball = BallInput(striker_id="batter_1", non_striker_id="batter_2", bowler_id="bowler_1", runs_batter=6)
    new_state = apply_ball(fresh_t20_state, ball)

    # Input state remains identical
    assert fresh_t20_state.total_runs == initial_runs
    assert fresh_t20_state.legal_balls == initial_balls
    assert fresh_t20_state.striker_id == initial_striker

    # New state has new values
    assert new_state.total_runs == 6
    assert new_state.legal_balls == 1
