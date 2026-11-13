from decimal import Decimal
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.ball_event import BallEvent, ExtrasType, WicketType
from app.models.innings import Innings
from app.models.match import Match, MatchStatus
from app.models.player import Player
from app.models.stats import PlayerStats, PointsTable
from app.models.team import Team, TournamentTeam
from app.models.tournament import MatchFormat, Tournament
from app.services.nrr_calculator import (
    MatchNRREntry,
    balls_to_decimal_overs,
    calculate_cumulative_nrr,
    calculate_nrr,
    decimal_to_overs,
    overs_to_decimal,
)
from app.services.post_match_service import (
    get_player_detailed_stats,
    get_tournament_points_table,
    process_completed_match,
    update_tournament_points_table,
)
from app.services.stats_engine import (
    batting_average,
    batting_strike_rate,
    bowling_average,
    bowling_economy,
    count_milestones,
)


# =====================================================================
# 1. PURE NRR CALCULATOR UNIT TESTS
# =====================================================================

def test_overs_to_decimal_standard_conversion():
    """Verify overs_to_decimal converts cricket overs string to float correctly."""
    # 45.3 -> 45 + 3/6 = 45.5
    assert overs_to_decimal("45.3") == 45.5
    # 20.0 -> 20.0
    assert overs_to_decimal("20.0") == 20.0
    assert overs_to_decimal("20") == 20.0
    # 0.0 -> 0.0
    assert overs_to_decimal("0.0") == 0.0
    assert overs_to_decimal("0") == 0.0
    # 14.2 -> 14 + 2/6 = 14.333333
    assert abs(overs_to_decimal("14.2") - (14 + 2 / 6)) < 1e-5
    # 19.5 -> 19 + 5/6 = 19.833333
    assert abs(overs_to_decimal("19.5") - (19 + 5 / 6)) < 1e-5


def test_overs_to_decimal_validates_balls_part_0_to_5():
    """Balls component must be between 0 and 5; balls >= 6 or < 0 raises ValueError."""
    # Balls == 6 is invalid in cricket notation (should be next over 46.0)
    with pytest.raises(ValueError, match="between 0 and 5"):
        overs_to_decimal("45.6")

    with pytest.raises(ValueError, match="between 0 and 5"):
        overs_to_decimal("45.7")

    with pytest.raises(ValueError, match="between 0 and 5"):
        overs_to_decimal("12.9")

    with pytest.raises(ValueError):
        overs_to_decimal("-2.3")

    with pytest.raises(ValueError):
        overs_to_decimal("invalid.format")


def test_decimal_to_overs_conversion():
    """decimal_to_overs converts decimal overs back to cricket string notation."""
    assert decimal_to_overs(45.5) == "45.3"
    assert decimal_to_overs(20.0) == "20.0"
    assert decimal_to_overs(0.0) == "0.0"
    assert decimal_to_overs(14 + 2 / 6) == "14.2"


def test_balls_to_decimal_overs():
    """balls_to_decimal_overs converts integer balls to decimal overs."""
    assert balls_to_decimal_overs(120) == 20.0
    assert balls_to_decimal_overs(60) == 10.0
    assert balls_to_decimal_overs(3) == 0.5
    assert balls_to_decimal_overs(0) == 0.0


def test_calculate_nrr_standard_case_180_20_vs_150_20():
    """180/20 vs 150/20 = +1.500 (9.000 - 7.500 = +1.500)."""
    nrr = calculate_nrr(
        runs_scored=180,
        overs_faced=20.0,
        runs_conceded=150,
        overs_bowled=20.0,
    )
    assert nrr == 1.500


def test_calculate_nrr_all_out_capped_at_full_quota():
    """If a team is all out in 14.2 of 20 overs, overs_faced counts as full quota (20)."""
    # 120 all out in 14.2 overs of a 20-over match vs 150/20
    # Effective overs faced = 20.0 (not 14.333)
    # NRR = (120/20.0) - (150/20.0) = 6.000 - 7.500 = -1.500
    nrr = calculate_nrr(
        runs_scored=120,
        overs_faced=overs_to_decimal("14.2"),
        runs_conceded=150,
        overs_bowled=20.0,
        is_all_out=True,
        max_overs=20.0,
    )
    assert nrr == -1.500


def test_calculate_nrr_zero_overs_division_guard():
    """Zero overs returns 0.0 without ZeroDivisionError."""
    assert calculate_nrr(0, 0.0, 0, 0.0) == 0.0
    assert calculate_nrr(100, 0.0, 50, 0.0) == 0.0
    assert calculate_nrr(0, 0.0, 100, 20.0) == -5.000


def test_cumulative_nrr_across_multiple_matches():
    """Recomputes cumulative NRR non-incrementally across all completed matches."""
    # Match 1: Scored 160 in 20.0 ov, conceded 140 in 20.0 ov
    # Match 2: Scored 100 in 15.0 ov (all out, max 20 ov -> 20.0 ov), conceded 180 in 20.0 ov
    # Total Runs Scored = 160 + 100 = 260
    # Total Effective Overs Faced = 20.0 + 20.0 = 40.0
    # Total Runs Conceded = 140 + 180 = 320
    # Total Effective Overs Bowled = 20.0 + 20.0 = 40.0
    # Cumulative NRR = (260 / 40.0) - (320 / 40.0) = 6.500 - 8.000 = -1.500
    entries = [
        MatchNRREntry(
            runs_scored=160,
            overs_faced=20.0,
            is_all_out=False,
            max_overs=20.0,
            runs_conceded=140,
            overs_bowled=20.0,
            opponent_all_out=False,
        ),
        MatchNRREntry(
            runs_scored=100,
            overs_faced=15.0,
            is_all_out=True,
            max_overs=20.0,
            runs_conceded=180,
            overs_bowled=20.0,
            opponent_all_out=False,
        ),
    ]
    cum_nrr = calculate_cumulative_nrr(entries)
    assert cum_nrr == -1.500


# =====================================================================
# 2. PURE STATS ENGINE UNIT TESTS
# =====================================================================

def test_batting_strike_rate():
    """Strike rate calculation and zero balls safety."""
    assert batting_strike_rate(runs=75, balls_faced=50) == 150.00
    assert batting_strike_rate(runs=33, balls_faced=22) == 150.00
    assert batting_strike_rate(runs=0, balls_faced=10) == 0.00
    assert batting_strike_rate(runs=0, balls_faced=0) == 0.00


def test_batting_average():
    """Batting average with dismissals and not-out edge cases."""
    assert batting_average(runs=250, dismissals=5) == 50.00
    assert batting_average(runs=100, dismissals=0) == 100.00
    assert batting_average(runs=0, dismissals=0) == 0.00
    assert batting_average(runs=0, dismissals=2) == 0.00


def test_bowling_economy():
    """Bowling economy rate calculation and zero balls safety."""
    # 24 runs in 24 balls (4.0 overs) = 6.00
    assert bowling_economy(runs_conceded=24, balls_bowled=24) == 6.00
    # 35 runs in 30 balls (5.0 overs) = 7.00
    assert bowling_economy(runs_conceded=35, balls_bowled=30) == 7.00
    assert bowling_economy(runs_conceded=0, balls_bowled=12) == 0.00
    assert bowling_economy(runs_conceded=15, balls_bowled=0) == 0.00


def test_bowling_average():
    """Bowling average calculation and zero wickets safety."""
    assert bowling_average(runs_conceded=60, wickets=3) == 20.00
    assert bowling_average(runs_conceded=45, wickets=0) == 0.00
    assert bowling_average(runs_conceded=0, wickets=2) == 0.00


def test_count_milestones():
    """Verify 50s (50-99) and 100s (>=100) are counted accurately."""
    scores = [15, 49, 50, 75, 99, 100, 145, 0, 88]
    fifties, hundreds = count_milestones(scores)
    # Fifties: 50, 75, 99, 88 -> 4
    assert fifties == 4
    # Hundreds: 100, 145 -> 2
    assert hundreds == 2


# =====================================================================
# 3. POINTS TABLE & POST-MATCH INTEGRATION TESTS
# =====================================================================

@pytest.fixture
def tournament_and_teams(db_session: Session):
    """Fixture creating a tournament with 3 registered teams."""
    now = datetime.now(timezone.utc)
    t = Tournament(
        name=f"NRR League {uuid.uuid4().hex[:4]}",
        level="local",
        format=MatchFormat.T20,
        start_date=now.date(),
        end_date=(now + timedelta(days=10)).date(),
    )
    db_session.add(t)
    db_session.flush()

    team_a = Team(team_name=f"Alpha {uuid.uuid4().hex[:4]}", city="City A", short_code="ALP")
    team_b = Team(team_name=f"Beta {uuid.uuid4().hex[:4]}", city="City B", short_code="BET")
    team_c = Team(team_name=f"Gamma {uuid.uuid4().hex[:4]}", city="City C", short_code="GAM")
    db_session.add_all([team_a, team_b, team_c])
    db_session.flush()

    db_session.add(TournamentTeam(tournament_id=t.tournament_id, team_id=team_a.team_id))
    db_session.add(TournamentTeam(tournament_id=t.tournament_id, team_id=team_b.team_id))
    db_session.add(TournamentTeam(tournament_id=t.tournament_id, team_id=team_c.team_id))
    db_session.commit()

    return {
        "tournament": t,
        "team_a": team_a,
        "team_b": team_b,
        "team_c": team_c,
    }


def test_points_table_tie_scenario(db_session: Session, client: TestClient, tournament_and_teams):
    """Tied match awards 1 point to each team (2 win / 1 tie / 0 loss)."""
    t = tournament_and_teams["tournament"]
    team_a = tournament_and_teams["team_a"]
    team_b = tournament_and_teams["team_b"]

    now = datetime.now(timezone.utc)
    match = Match(
        tournament_id=t.tournament_id,
        team1_id=team_a.team_id,
        team2_id=team_b.team_id,
        match_date=now,
        overs=20,
        status=MatchStatus.COMPLETED,
        winner_id=None,
        result_summary="Match tied",
    )
    db_session.add(match)
    db_session.flush()

    # Innings 1: Team A 150/5 in 20.0 overs (120 balls)
    inn1 = Innings(
        match_id=match.match_id,
        innings_no=1,
        batting_team_id=team_a.team_id,
        bowling_team_id=team_b.team_id,
        total_runs=150,
        wickets=5,
        balls_bowled=120,
    )
    # Innings 2: Team B 150/7 in 20.0 overs (120 balls)
    inn2 = Innings(
        match_id=match.match_id,
        innings_no=2,
        batting_team_id=team_b.team_id,
        bowling_team_id=team_a.team_id,
        total_runs=150,
        wickets=7,
        balls_bowled=120,
    )
    db_session.add_all([inn1, inn2])
    db_session.commit()

    # Recompute points table
    update_tournament_points_table(db_session, t.tournament_id)
    db_session.commit()

    # Query GET /api/tournaments/{id}/points-table
    res = client.get(f"/api/tournaments/{t.tournament_id}/points-table")
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 3

    row_a = next(r for r in rows if r["team_id"] == str(team_a.team_id))
    row_b = next(r for r in rows if r["team_id"] == str(team_b.team_id))

    assert row_a["played"] == 1
    assert row_a["tied"] == 1
    assert row_a["points"] == 1
    assert row_a["nrr"] == 0.000

    assert row_b["played"] == 1
    assert row_b["tied"] == 1
    assert row_b["points"] == 1
    assert row_b["nrr"] == 0.000


def test_points_table_sorting_tie_break_by_nrr(db_session: Session, client: TestClient, tournament_and_teams):
    """When teams have equal points, sorting tie-break is determined by NRR DESC."""
    t = tournament_and_teams["tournament"]
    team_a = tournament_and_teams["team_a"]
    team_b = tournament_and_teams["team_b"]
    team_c = tournament_and_teams["team_c"]

    now = datetime.now(timezone.utc)

    # Match 1: Team A beats Team C heavily
    # Team A 180/4 in 20 ov vs Team C 120/10 in 18 ov
    # Team A: 2 pts, NRR = (180/20) - (120/20 [capped]) = 9.0 - 6.0 = +3.000
    m1 = Match(
        tournament_id=t.tournament_id,
        team1_id=team_a.team_id,
        team2_id=team_c.team_id,
        match_date=now - timedelta(days=2),
        overs=20,
        status=MatchStatus.COMPLETED,
        winner_id=team_a.team_id,
        result_summary="Alpha won by 60 runs",
    )
    db_session.add(m1)
    db_session.flush()

    inn1_m1 = Innings(match_id=m1.match_id, innings_no=1, batting_team_id=team_a.team_id, bowling_team_id=team_c.team_id, total_runs=180, wickets=4, balls_bowled=120)
    inn2_m1 = Innings(match_id=m1.match_id, innings_no=2, batting_team_id=team_c.team_id, bowling_team_id=team_a.team_id, total_runs=120, wickets=10, balls_bowled=108)
    db_session.add_all([inn1_m1, inn2_m1])

    # Match 2: Team B beats Team C closely
    # Team B 150/6 in 20 ov vs Team C 145/8 in 20 ov
    # Team B: 2 pts, NRR = (150/20) - (145/20) = 7.5 - 7.25 = +0.250
    m2 = Match(
        tournament_id=t.tournament_id,
        team1_id=team_b.team_id,
        team2_id=team_c.team_id,
        match_date=now - timedelta(days=1),
        overs=20,
        status=MatchStatus.COMPLETED,
        winner_id=team_b.team_id,
        result_summary="Beta won by 5 runs",
    )
    db_session.add(m2)
    db_session.flush()

    inn1_m2 = Innings(match_id=m2.match_id, innings_no=1, batting_team_id=team_b.team_id, bowling_team_id=team_c.team_id, total_runs=150, wickets=6, balls_bowled=120)
    inn2_m2 = Innings(match_id=m2.match_id, innings_no=2, batting_team_id=team_c.team_id, bowling_team_id=team_b.team_id, total_runs=145, wickets=8, balls_bowled=120)
    db_session.add_all([inn1_m2, inn2_m2])
    db_session.commit()

    # Recompute points table
    update_tournament_points_table(db_session, t.tournament_id)
    db_session.commit()

    # Both Team A and Team B have 2 points, but Team A has higher NRR (+3.000 vs +0.250)
    res = client.get(f"/api/tournaments/{t.tournament_id}/points-table")
    assert res.status_code == 200
    rows = res.json()
    assert len(rows) == 3

    # Ranking 1: Team A (2 pts, NRR +3.000)
    assert rows[0]["team_id"] == str(team_a.team_id)
    assert rows[0]["points"] == 2
    assert rows[0]["nrr"] == 3.000

    # Ranking 2: Team B (2 pts, NRR +0.250)
    assert rows[1]["team_id"] == str(team_b.team_id)
    assert rows[1]["points"] == 2
    assert rows[1]["nrr"] == 0.250

    # Ranking 3: Team C (0 pts, lost 2 matches)
    assert rows[2]["team_id"] == str(team_c.team_id)
    assert rows[2]["points"] == 0


def test_get_player_detailed_stats_endpoint(db_session: Session, client: TestClient):
    """GET /api/players/{id}/stats returns player profile with milestones and career metrics."""
    # Create player
    p = Player(name="Sachin Tendulkar", role="Top-order Batter")
    db_session.add(p)
    db_session.flush()

    ps = PlayerStats(
        player_id=p.player_id,
        matches_played=10,
        runs=520,
        balls_faced=400,
        wickets=5,
        runs_conceded=180,
        overs_bowled=Decimal("25.0"),
        strike_rate=Decimal("130.00"),
        economy=Decimal("7.20"),
    )
    db_session.add(ps)
    db_session.commit()

    res = client.get(f"/api/players/{p.player_id}/stats")
    assert res.status_code == 200
    data = res.json()

    assert data["player_id"] == str(p.player_id)
    assert data["name"] == "Sachin Tendulkar"
    assert data["matches_played"] == 10
    assert data["runs"] == 520
    assert data["balls_faced"] == 400
    assert data["strike_rate"] == 130.0
    assert data["wickets"] == 5
    assert data["runs_conceded"] == 180
    assert "batting_average" in data
    assert "bowling_average" in data
    assert "fifties" in data
    assert "hundreds" in data
