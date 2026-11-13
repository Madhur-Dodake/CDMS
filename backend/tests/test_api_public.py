import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.match import MatchStatus


@pytest.fixture
def client():
    return TestClient(app)


def test_public_matches_live_and_scorecard(client):
    """Verify public live matches listing and full scorecard endpoint."""
    res = client.get("/api/matches")
    assert res.status_code == 200
    items = res.json().get("items", [])
    assert len(items) > 0

    # Pick the first match
    m = items[0]
    match_id = m["match_id"]

    # Test scorecard endpoint
    sc_res = client.get(f"/api/matches/{match_id}/scorecard")
    assert sc_res.status_code == 200
    scorecard = sc_res.json()
    assert "team1" in scorecard
    assert "team2" in scorecard
    assert "innings" in scorecard

    # Test live snapshot endpoint
    live_res = client.get(f"/api/matches/{match_id}/live")
    assert live_res.status_code == 200
    live_data = live_res.json()
    assert "score" in live_data
    assert "wickets" in live_data
    assert "overs" in live_data


def test_public_tournaments_and_standings(client):
    """Verify tournament listing and points table."""
    res = client.get("/api/tournaments")
    assert res.status_code == 200
    tourneys = res.json().get("items", [])
    assert len(tourneys) > 0

    t_id = tourneys[0]["tournament_id"]
    pt_res = client.get(f"/api/tournaments/{t_id}/points-table")
    assert pt_res.status_code == 200
    assert isinstance(pt_res.json(), list)


def test_public_teams_and_players(client):
    """Verify teams, player listing, and career stats with chart data."""
    teams_res = client.get("/api/teams")
    assert teams_res.status_code == 200
    teams = teams_res.json().get("items", [])
    assert len(teams) > 0

    players_res = client.get("/api/players")
    assert players_res.status_code == 200
    players = players_res.json().get("items", [])
    assert len(players) > 0

    p_id = players[0]["player_id"]
    stats_res = client.get(f"/api/players/{p_id}/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "runs" in stats
    assert "recent_innings" in stats
    assert isinstance(stats["recent_innings"], list)
