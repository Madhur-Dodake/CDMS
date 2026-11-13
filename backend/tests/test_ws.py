import json
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.match import Match, MatchStatus
from app.models.player import Player
from app.models.stats import PlayerStats
from app.models.team import Team, TournamentTeam
from app.models.tournament import MatchFormat, Tournament
from app.models.user import User
from app.ws.connection_manager import manager


@pytest.fixture
def ws_match_fixture(db_session: Session, scorer_user: User):
    """Create a 2-over match with registered teams and players for WebSocket testing."""
    now = datetime.now(timezone.utc)
    t = Tournament(
        name=f"WS Scoring League {uuid.uuid4().hex[:4]}",
        level="local",
        format=MatchFormat.T20,
        start_date=now.date(),
        end_date=(now + timedelta(days=5)).date(),
    )
    db_session.add(t)
    db_session.flush()

    team1 = Team(team_name=f"Eagles WS {uuid.uuid4().hex[:4]}", city="Mumbai")
    team2 = Team(team_name=f"Hawks WS {uuid.uuid4().hex[:4]}", city="Delhi")
    db_session.add_all([team1, team2])
    db_session.flush()

    db_session.add(TournamentTeam(tournament_id=t.tournament_id, team_id=team1.team_id))
    db_session.add(TournamentTeam(tournament_id=t.tournament_id, team_id=team2.team_id))
    db_session.flush()

    t1_players = []
    for i in range(1, 6):
        p = Player(name=f"Eagles WS P{i}", team_id=team1.team_id)
        db_session.add(p)
        db_session.flush()
        db_session.add(PlayerStats(player_id=p.player_id))
        t1_players.append(p.player_id)

    t2_players = []
    for i in range(1, 6):
        p = Player(name=f"Hawks WS P{i}", team_id=team2.team_id)
        db_session.add(p)
        db_session.flush()
        db_session.add(PlayerStats(player_id=p.player_id))
        t2_players.append(p.player_id)

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
    }


@pytest.fixture
def live_match_fixture(client: TestClient, ws_match_fixture, scorer_headers: dict):
    """Fixture with the match already started into LIVE status."""
    match = ws_match_fixture["match"]
    match_id = str(match.match_id)
    t1_p = ws_match_fixture["t1_players"]
    t2_p = ws_match_fixture["t2_players"]

    start_payload = {
        "toss_winner_id": str(ws_match_fixture["team1"].team_id),
        "toss_decision": "bat",
        "team1_xi": [str(p) for p in t1_p],
        "team2_xi": [str(p) for p in t2_p],
        "striker_id": str(t1_p[0]),
        "non_striker_id": str(t1_p[1]),
        "opening_bowler_id": str(t2_p[0]),
    }
    res = client.post(
        f"/api/matches/{match_id}/start",
        headers=scorer_headers,
        json=start_payload,
    )
    assert res.status_code == 200
    return ws_match_fixture


def test_ws_connect_receives_snapshot_immediately(client: TestClient, ws_match_fixture):
    """On WebSocket connect, client immediately receives current snapshot JSON."""
    match = ws_match_fixture["match"]
    match_id = str(match.match_id)

    with client.websocket_connect(f"/ws/matches/{match_id}") as ws:
        snapshot = ws.receive_json()

        assert snapshot["match_id"] == match_id
        assert snapshot["status"] == "scheduled"
        assert snapshot["score"] == 0
        assert snapshot["wickets"] == 0
        assert snapshot["overs"] == "0.0"
        assert snapshot["run_rate"] == 0.0
        assert snapshot["required_rate"] is None
        assert snapshot["target"] is None
        assert snapshot["striker"] is None
        assert snapshot["non_striker"] is None
        assert snapshot["bowler"] is None
        assert snapshot["last_ball"] is None
        assert snapshot["recent_balls"] == []


def test_ws_receives_live_update_after_ball(
    client: TestClient, live_match_fixture, scorer_headers: dict
):
    """Client connected to WebSocket receives real-time broadcast after a ball is recorded."""
    match = live_match_fixture["match"]
    match_id = str(match.match_id)
    t1_p = live_match_fixture["t1_players"]
    t2_p = live_match_fixture["t2_players"]

    with client.websocket_connect(f"/ws/matches/{match_id}") as ws:
        # 1. First message is immediate snapshot of live match
        snapshot = ws.receive_json()
        assert snapshot["match_id"] == match_id
        assert snapshot["status"] == "live"
        assert snapshot["score"] == 0
        assert snapshot["striker"] == str(t1_p[0])
        assert snapshot["non_striker"] == str(t1_p[1])
        assert snapshot["bowler"] == str(t2_p[0])

        # 2. Score a boundary four via POST /ball
        ball_payload = {
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "bowler_id": str(t2_p[0]),
            "runs_batter": 4,
            "extras_type": None,
            "extras_runs": 0,
            "is_wicket": False,
        }
        res_ball = client.post(
            f"/api/matches/{match_id}/ball",
            headers=scorer_headers,
            json=ball_payload,
        )
        assert res_ball.status_code == 200

        # 3. WebSocket receives broadcast update
        update = ws.receive_json()
        assert update["match_id"] == match_id
        assert update["status"] == "live"
        assert update["score"] == 4
        assert update["wickets"] == 0
        assert update["overs"] == "0.1"
        assert update["run_rate"] == 24.0
        assert update["last_ball"] == "4"
        assert update["recent_balls"] == ["4"]


def test_ws_receives_update_after_undo(
    client: TestClient, live_match_fixture, scorer_headers: dict
):
    """Client connected to WebSocket receives broadcast update when a ball is undone."""
    match = live_match_fixture["match"]
    match_id = str(match.match_id)
    t1_p = live_match_fixture["t1_players"]
    t2_p = live_match_fixture["t2_players"]

    with client.websocket_connect(f"/ws/matches/{match_id}") as ws:
        # Initial snapshot
        ws.receive_json()

        # Score a 1-run delivery
        ball_payload = {
            "striker_id": str(t1_p[0]),
            "non_striker_id": str(t1_p[1]),
            "bowler_id": str(t2_p[0]),
            "runs_batter": 1,
            "extras_type": None,
            "extras_runs": 0,
            "is_wicket": False,
        }
        res_ball = client.post(
            f"/api/matches/{match_id}/ball",
            headers=scorer_headers,
            json=ball_payload,
        )
        assert res_ball.status_code == 200

        # Receive ball update
        ball_msg = ws.receive_json()
        assert ball_msg["score"] == 1
        assert ball_msg["overs"] == "0.1"
        assert ball_msg["last_ball"] == "1"

        # Undo delivery
        res_undo = client.post(
            f"/api/matches/{match_id}/undo",
            headers=scorer_headers,
        )
        assert res_undo.status_code == 200

        # Receive undo update
        undo_msg = ws.receive_json()
        assert undo_msg["score"] == 0
        assert undo_msg["overs"] == "0.0"
        assert undo_msg["last_ball"] is None
        assert undo_msg["recent_balls"] == []


def test_ws_receives_state_change_update(
    client: TestClient, live_match_fixture, scorer_headers: dict
):
    """Client receives broadcast update when match is suspended and resumed."""
    match = live_match_fixture["match"]
    match_id = str(match.match_id)

    with client.websocket_connect(f"/ws/matches/{match_id}") as ws:
        # Initial snapshot
        ws.receive_json()

        # Suspend match
        sus_res = client.post(
            f"/api/matches/{match_id}/suspend",
            headers=scorer_headers,
        )
        assert sus_res.status_code == 200

        sus_msg = ws.receive_json()
        assert sus_msg["status"] == "suspended"

        # Resume match
        res_res = client.post(
            f"/api/matches/{match_id}/resume",
            headers=scorer_headers,
        )
        assert res_res.status_code == 200

        res_msg = ws.receive_json()
        assert res_msg["status"] == "live"


def test_ws_ping_pong_heartbeat(client: TestClient, ws_match_fixture):
    """Test ping and pong heartbeats via both plain text and JSON."""
    match = ws_match_fixture["match"]
    match_id = str(match.match_id)

    with client.websocket_connect(f"/ws/matches/{match_id}") as ws:
        # Snapshot
        ws.receive_json()

        # Plain text ping
        ws.send_text("ping")
        text_resp = ws.receive_text()
        assert text_resp == "pong"

        # JSON ping
        ws.send_text(json.dumps({"type": "ping"}))
        json_resp = ws.receive_json()
        assert json_resp == {"type": "pong"}


def test_ws_disconnect_and_dead_connection_clean(client: TestClient, ws_match_fixture):
    """Test clean disconnection and room cleanup."""
    match = ws_match_fixture["match"]
    match_id = str(match.match_id)

    # Connect and then exit context manager (disconnect)
    with client.websocket_connect(f"/ws/matches/{match_id}") as ws:
        ws.receive_json()

    # Connection should be removed from active connections
    assert match_id not in manager.active_connections or len(manager.active_connections[match_id]) == 0

    # Broadcasting to an empty/disconnected room should not fail
    manager.broadcast_sync(match_id, {"test": "noop"})
