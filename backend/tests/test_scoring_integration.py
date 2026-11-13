import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.ball_event import BallEvent
from app.models.innings import Innings
from app.models.match import Match, MatchStatus
from app.models.player import Player
from app.models.stats import PlayerStats
from app.models.team import Team, TournamentTeam
from app.models.tournament import MatchFormat, Tournament
from app.models.user import User, UserRole
from app.services.scoring_service import LIVE_MATCH_CACHE


@pytest.fixture
def match_fixture(db_session: Session, admin_headers: dict, scorer_user: User):
    """Create a 2-over T20 match with registered teams, 11 players each, and assigned scorer."""
    # 1. Create Tournament
    now = datetime.now(timezone.utc)
    t = Tournament(
        name=f"2-Over Scoring League {uuid.uuid4().hex[:4]}",
        level="local",
        format=MatchFormat.T20,
        start_date=now.date(),
        end_date=(now + timedelta(days=5)).date(),
    )
    db_session.add(t)
    db_session.flush()

    # 2. Create 2 Teams
    team1 = Team(team_name=f"Eagles {uuid.uuid4().hex[:4]}", city="Mumbai")
    team2 = Team(team_name=f"Hawks {uuid.uuid4().hex[:4]}", city="Delhi")
    db_session.add_all([team1, team2])
    db_session.flush()

    # Register teams to tournament
    db_session.add(TournamentTeam(tournament_id=t.tournament_id, team_id=team1.team_id))
    db_session.add(TournamentTeam(tournament_id=t.tournament_id, team_id=team2.team_id))
    db_session.flush()

    # 3. Create 5 players for Team 1 and 5 players for Team 2
    t1_players = []
    for i in range(1, 6):
        p = Player(name=f"Eagles Player {i}", team_id=team1.team_id)
        db_session.add(p)
        db_session.flush()
        ps = PlayerStats(player_id=p.player_id, matches_played=0, runs=0, balls_faced=0, wickets=0, runs_conceded=0)
        db_session.add(ps)
        t1_players.append(p.player_id)

    t2_players = []
    for i in range(1, 6):
        p = Player(name=f"Hawks Player {i}", team_id=team2.team_id)
        db_session.add(p)
        db_session.flush()
        ps = PlayerStats(player_id=p.player_id, matches_played=0, runs=0, balls_faced=0, wickets=0, runs_conceded=0)
        db_session.add(ps)
        t2_players.append(p.player_id)

    # 4. Create 2-over match assigned to scorer_user
    match = Match(
        tournament_id=t.tournament_id,
        team1_id=team1.team_id,
        team2_id=team2.team_id,
        scorer_id=scorer_user.user_id,
        match_date=now + timedelta(hours=1),
        overs=2,
        status=MatchStatus.SCHEDULED,
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)

    return {
        "match": match,
        "team1": team1,
        "team2": team2,
        "t1_players": t1_players,
        "t2_players": t2_players,
        "scorer_id": scorer_user.user_id,
    }


# -------------------------------------------------------------
# 1. SCORER RBAC & ASSIGNMENT PERMISSION TESTS
# -------------------------------------------------------------

def test_unassigned_scorer_cannot_score_match(
    client: TestClient, match_fixture: dict, db_session: Session
) -> None:
    """Scorer who is NOT the assigned scorer receives 403 Forbidden."""
    # Create another scorer user
    other_scorer = User(
        name="Other Scorer",
        email=f"other_{uuid.uuid4().hex[:6]}@cdms.com",
        password="hashedpassword",
        role=UserRole.SCORER,
    )
    db_session.add(other_scorer)
    db_session.commit()

    from app.core.auth import create_access_token
    other_token = create_access_token(
        data={"user_id": str(other_scorer.user_id), "role": "scorer", "sub": other_scorer.email}
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}

    match_id = str(match_fixture["match"].match_id)
    payload = {
        "toss_winner_id": str(match_fixture["team1"].team_id),
        "toss_decision": "bat",
        "team1_xi": [str(p) for p in match_fixture["t1_players"]],
        "team2_xi": [str(p) for p in match_fixture["t2_players"]],
        "striker_id": str(match_fixture["t1_players"][0]),
        "non_striker_id": str(match_fixture["t1_players"][1]),
        "opening_bowler_id": str(match_fixture["t2_players"][0]),
    }

    # Attempt start
    response = client.post(f"/api/matches/{match_id}/start", headers=other_headers, json=payload)
    assert response.status_code == 403
    assert "not the assigned scorer" in response.json()["detail"].lower()


def test_admin_can_score_any_match(
    client: TestClient, match_fixture: dict, admin_headers: dict
) -> None:
    """Admin can start and score any match regardless of assigned scorer_id."""
    match_id = str(match_fixture["match"].match_id)
    payload = {
        "toss_winner_id": str(match_fixture["team1"].team_id),
        "toss_decision": "bat",
        "team1_xi": [str(p) for p in match_fixture["t1_players"]],
        "team2_xi": [str(p) for p in match_fixture["t2_players"]],
        "striker_id": str(match_fixture["t1_players"][0]),
        "non_striker_id": str(match_fixture["t1_players"][1]),
        "opening_bowler_id": str(match_fixture["t2_players"][0]),
    }

    res = client.post(f"/api/matches/{match_id}/start", headers=admin_headers, json=payload)
    assert res.status_code == 200
    assert res.json()["match_status"] == "live"


# -------------------------------------------------------------
# 2. START MATCH VALIDATIONS
# -------------------------------------------------------------

def test_start_match_validations(
    client: TestClient, match_fixture: dict, scorer_headers: dict
) -> None:
    """Validates toss winner, striker/non-striker identicality, and playing XIs."""
    match_id = str(match_fixture["match"].match_id)

    # 1. Invalid toss winner
    bad_toss = {
        "toss_winner_id": str(uuid.uuid4()),
        "toss_decision": "bat",
        "team1_xi": [str(p) for p in match_fixture["t1_players"]],
        "team2_xi": [str(p) for p in match_fixture["t2_players"]],
        "striker_id": str(match_fixture["t1_players"][0]),
        "non_striker_id": str(match_fixture["t1_players"][1]),
        "opening_bowler_id": str(match_fixture["t2_players"][0]),
    }
    r1 = client.post(f"/api/matches/{match_id}/start", headers=scorer_headers, json=bad_toss)
    assert r1.status_code == 400
    assert "toss winner" in r1.json()["detail"].lower()

    # 2. Striker == Non-striker
    same_batter = {
        "toss_winner_id": str(match_fixture["team1"].team_id),
        "toss_decision": "bat",
        "team1_xi": [str(p) for p in match_fixture["t1_players"]],
        "team2_xi": [str(p) for p in match_fixture["t2_players"]],
        "striker_id": str(match_fixture["t1_players"][0]),
        "non_striker_id": str(match_fixture["t1_players"][0]),  # Same!
        "opening_bowler_id": str(match_fixture["t2_players"][0]),
    }
    r2 = client.post(f"/api/matches/{match_id}/start", headers=scorer_headers, json=same_batter)
    assert r2.status_code == 400
    assert "different players" in r2.json()["detail"].lower()


# -------------------------------------------------------------
# 3. CONSECUTIVE OVERS VALIDATION & UNDO
# -------------------------------------------------------------

def test_bowler_cannot_bowl_consecutive_overs(
    client: TestClient, match_fixture: dict, scorer_headers: dict
) -> None:
    """Bowler who bowled over 1 cannot bowl over 2."""
    match_id = str(match_fixture["match"].match_id)
    t1_p = match_fixture["t1_players"]
    t2_p = match_fixture["t2_players"]

    # Start match
    client.post(
        f"/api/matches/{match_id}/start",
        headers=scorer_headers,
        json={
            "toss_winner_id": str(match_fixture["team1"].team_id),
            "toss_decision": "bat",
            "team1_xi": [str(p) for p in t1_p],
            "team2_xi": [str(p) for p in t2_p],
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "opening_bowler_id": str(t2_p[0]),
        },
    )

    # Bowl 6 legal balls in Over 1 with Bowler t2_p[0]
    for _ in range(6):
        b_res = client.post(
            f"/api/matches/{match_id}/ball",
            headers=scorer_headers,
            json={
                "striker_id": str(t1_p[0]),
                "non_striker_id": str(t1_p[1]),
                "bowler_id": str(t2_p[0]),
                "runs_batter": 0,
            },
        )
        assert b_res.status_code == 200

    assert b_res.json()["legal_balls"] == 6

    # Attempt ball 7 (Over 2) with the SAME bowler -> 400 Bad Request
    consec_res = client.post(
        f"/api/matches/{match_id}/ball",
        headers=scorer_headers,
        json={
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "bowler_id": str(t2_p[0]),  # Consecutive over attempt!
            "runs_batter": 0,
        },
    )
    assert consec_res.status_code == 400
    assert "consecutive overs" in consec_res.json()["detail"].lower()

    # Bowl with different bowler t2_p[1] -> 200 OK
    ok_res = client.post(
        f"/api/matches/{match_id}/ball",
        headers=scorer_headers,
        json={
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "bowler_id": str(t2_p[1]),
            "runs_batter": 1,
        },
    )
    assert ok_res.status_code == 200
    assert ok_res.json()["legal_balls"] == 7


def test_undo_and_cache_rebuild_from_db(
    client: TestClient, match_fixture: dict, scorer_headers: dict
) -> None:
    """Test undoing a delivery and cache rebuild on cache miss."""
    match_id = str(match_fixture["match"].match_id)
    t1_p = match_fixture["t1_players"]
    t2_p = match_fixture["t2_players"]

    # Start match
    client.post(
        f"/api/matches/{match_id}/start",
        headers=scorer_headers,
        json={
            "toss_winner_id": str(match_fixture["team1"].team_id),
            "toss_decision": "bat",
            "team1_xi": [str(p) for p in t1_p],
            "team2_xi": [str(p) for p in t2_p],
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "opening_bowler_id": str(t2_p[0]),
        },
    )

    # Ball 1: 4 runs
    r1 = client.post(
        f"/api/matches/{match_id}/ball",
        headers=scorer_headers,
        json={
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "bowler_id": str(t2_p[0]),
            "runs_batter": 4,
        },
    )
    assert r1.json()["total_runs"] == 4

    # Ball 2: 6 runs -> total 10
    r2 = client.post(
        f"/api/matches/{match_id}/ball",
        headers=scorer_headers,
        json={
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "bowler_id": str(t2_p[0]),
            "runs_batter": 6,
        },
    )
    assert r2.json()["total_runs"] == 10

    # Simulate Cache Miss by invalidating in-memory cache
    if uuid.UUID(match_id) in LIVE_MATCH_CACHE:
        del LIVE_MATCH_CACHE[uuid.UUID(match_id)]

    # Call /undo on cache miss -> should rebuild state from DB and undo Ball 2!
    undo_res = client.post(f"/api/matches/{match_id}/undo", headers=scorer_headers)
    assert undo_res.status_code == 200
    assert undo_res.json()["total_runs"] == 4  # Reverted back to 4
    assert undo_res.json()["legal_balls"] == 1


# -------------------------------------------------------------
# 4. SUSPEND AND RESUME
# -------------------------------------------------------------

def test_suspend_and_resume_lifecycle(
    client: TestClient, match_fixture: dict, scorer_headers: dict
) -> None:
    """Test match suspension and resumption."""
    match_id = str(match_fixture["match"].match_id)
    t1_p = match_fixture["t1_players"]
    t2_p = match_fixture["t2_players"]

    client.post(
        f"/api/matches/{match_id}/start",
        headers=scorer_headers,
        json={
            "toss_winner_id": str(match_fixture["team1"].team_id),
            "toss_decision": "bat",
            "team1_xi": [str(p) for p in t1_p],
            "team2_xi": [str(p) for p in t2_p],
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "opening_bowler_id": str(t2_p[0]),
        },
    )

    # Suspend
    s_res = client.post(f"/api/matches/{match_id}/suspend", headers=scorer_headers)
    assert s_res.status_code == 200
    assert s_res.json()["match_status"] == "suspended"

    # Delivery during suspension is rejected
    ball_res = client.post(
        f"/api/matches/{match_id}/ball",
        headers=scorer_headers,
        json={
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "bowler_id": str(t2_p[0]),
            "runs_batter": 1,
        },
    )
    assert ball_res.status_code == 400

    # Resume
    r_res = client.post(f"/api/matches/{match_id}/resume", headers=scorer_headers)
    assert r_res.status_code == 200
    assert r_res.json()["match_status"] == "live"


# -------------------------------------------------------------
# 5. FULL 2-OVER MATCH INTEGRATION FLOW
# -------------------------------------------------------------

def test_play_full_two_over_match(
    client: TestClient, match_fixture: dict, scorer_headers: dict
) -> None:
    """Simulate playing an entire 2-over match from toss to completion through API."""
    match_id = str(match_fixture["match"].match_id)
    t1_p = match_fixture["t1_players"]
    t2_p = match_fixture["t2_players"]

    # 1. Start Match (Team 1 bats first)
    start_res = client.post(
        f"/api/matches/{match_id}/start",
        headers=scorer_headers,
        json={
            "toss_winner_id": str(match_fixture["team1"].team_id),
            "toss_decision": "bat",
            "team1_xi": [str(p) for p in t1_p],
            "team2_xi": [str(p) for p in t2_p],
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "opening_bowler_id": str(t2_p[0]),
        },
    )
    assert start_res.status_code == 200
    assert start_res.json()["match_status"] == "live"

    # --- INNINGS 1 ---
    # Over 1: Bowler t2_p[0]
    # Ball 1: 1 run (strike rotates to t1_p[1])
    b1 = client.post(f"/api/matches/{match_id}/ball", headers=scorer_headers, json={
        "striker_id": str(t1_p[0]), "non_striker_id": str(t1_p[1]), "bowler_id": str(t2_p[0]), "runs_batter": 1
    }).json()
    assert b1["total_runs"] == 1
    assert b1["striker_id"] == str(t1_p[1])

    # Ball 2: 4 runs (boundary, strike remains t1_p[1])
    b2 = client.post(f"/api/matches/{match_id}/ball", headers=scorer_headers, json={
        "striker_id": str(t1_p[1]), "non_striker_id": str(t1_p[0]), "bowler_id": str(t2_p[0]), "runs_batter": 4
    }).json()
    assert b2["total_runs"] == 5

    # Ball 3: 0 runs
    client.post(f"/api/matches/{match_id}/ball", headers=scorer_headers, json={
        "striker_id": str(t1_p[1]), "non_striker_id": str(t1_p[0]), "bowler_id": str(t2_p[0]), "runs_batter": 0
    })

    # Ball 4: wide (1 extra run, legal balls unchanged)
    b4_wd = client.post(f"/api/matches/{match_id}/ball", headers=scorer_headers, json={
        "striker_id": str(t1_p[1]), "non_striker_id": str(t1_p[0]), "bowler_id": str(t2_p[0]),
        "extras_type": "wide", "extras_runs": 1
    }).json()
    assert b4_wd["total_runs"] == 6
    assert b4_wd["legal_balls"] == 3

    # Ball 4 (re-bowled): wicket (bowled!), next batter t1_p[2]
    b4_w = client.post(f"/api/matches/{match_id}/ball", headers=scorer_headers, json={
        "striker_id": str(t1_p[1]), "non_striker_id": str(t1_p[0]), "bowler_id": str(t2_p[0]),
        "is_wicket": True, "wicket_type": "bowled", "next_batter_id": str(t1_p[2])
    }).json()
    assert b4_w["wickets"] == 1
    assert b4_w["striker_id"] == str(t1_p[2])

    # Ball 5: 2 runs
    client.post(f"/api/matches/{match_id}/ball", headers=scorer_headers, json={
        "striker_id": str(t1_p[2]), "non_striker_id": str(t1_p[0]), "bowler_id": str(t2_p[0]), "runs_batter": 2
    })

    # Ball 6: 1 run (end of over + 1 run cancel out -> t1_p[2] remains on strike)
    b6 = client.post(f"/api/matches/{match_id}/ball", headers=scorer_headers, json={
        "striker_id": str(t1_p[2]), "non_striker_id": str(t1_p[0]), "bowler_id": str(t2_p[0]), "runs_batter": 1
    }).json()
    assert b6["legal_balls"] == 6
    assert b6["overs_formatted"] == "1.0"
    assert b6["striker_id"] == str(t1_p[2])

    # Over 2: Bowler t2_p[1] (different bowler)
    # Balls 7-11: singles
    for _ in range(5):
        client.post(f"/api/matches/{match_id}/ball", headers=scorer_headers, json={
            "striker_id": b6["striker_id"], "non_striker_id": b6["non_striker_id"], "bowler_id": str(t2_p[1]), "runs_batter": 1
        })

    # Ball 12 (final ball of over 2, allocated quota completed!): 4 runs
    final_b = client.post(f"/api/matches/{match_id}/ball", headers=scorer_headers, json={
        "striker_id": str(t1_p[2]), "non_striker_id": str(t1_p[0]), "bowler_id": str(t2_p[1]), "runs_batter": 4
    }).json()

    assert final_b["legal_balls"] == 12
    assert final_b["is_completed"] is True
    assert final_b["match_status"] == "innings_break"
    t1_score = final_b["total_runs"]

    # 2. End Innings 1 and Set Target
    end_i1 = client.post(f"/api/matches/{match_id}/end-innings", headers=scorer_headers)
    assert end_i1.status_code == 200
    assert end_i1.json()["target_runs"] == t1_score + 1

    # 3. Resume Match for Innings 2
    res_i2 = client.post(f"/api/matches/{match_id}/resume", headers=scorer_headers)
    assert res_i2.status_code == 200
    assert res_i2.json()["match_status"] == "live"
    assert res_i2.json()["innings_no"] == 2

    # --- INNINGS 2 ---
    # Team 2 chases target. Bowler t1_p[0].
    # Hit 6 on ball 1, 6 on ball 2, 6 on ball 3, 6 on ball 4
    for _ in range(4):
        i2_ball = client.post(f"/api/matches/{match_id}/ball", headers=scorer_headers, json={
            "striker_id": str(t2_p[0]),
            "non_striker_id": str(t2_p[1]),
            "bowler_id": str(t1_p[0]),
            "runs_batter": 6,
        }).json()
        if i2_ball["is_completed"]:
            break

    assert i2_ball["total_runs"] >= t1_score + 1
    assert i2_ball["is_completed"] is True

    # 4. Conclude Match
    comp_res = client.post(f"/api/matches/{match_id}/complete", headers=scorer_headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["match_status"] == "completed"
    assert "won by" in comp_data["result_summary"].lower()
    assert "wickets" in comp_data["result_summary"].lower()

