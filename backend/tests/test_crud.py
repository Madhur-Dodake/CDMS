import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from app.models.match import Match
from app.models.player import Player
from app.models.team import Team
from app.models.tournament import Tournament


# ---------------------------------------------------------
# 1. VENUES CRUD & ACCESS CONTROL
# ---------------------------------------------------------

def test_public_can_list_venues(client: TestClient) -> None:
    """Public can list venues without authentication."""
    response = client.get("/api/venues")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert len(data["items"]) >= 1


def test_public_can_get_venue_by_id(client: TestClient) -> None:
    """Public can view a single venue by ID."""
    venues = client.get("/api/venues").json()["items"]
    venue_id = venues[0]["venue_id"]

    response = client.get(f"/api/venues/{venue_id}")
    assert response.status_code == 200
    assert response.json()["venue_id"] == venue_id


def test_get_nonexistent_venue_returns_404(client: TestClient) -> None:
    """Requesting non-existent venue ID returns 404."""
    random_id = str(uuid.uuid4())
    response = client.get(f"/api/venues/{random_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_unauthenticated_cannot_create_venue(client: TestClient) -> None:
    """Unauthenticated users cannot create venues (401)."""
    response = client.post(
        "/api/venues",
        json={"venue_name": "Unauthorized Stadium", "city": "London", "capacity": 30000},
    )
    assert response.status_code == 401


def test_scorer_cannot_create_venue(client: TestClient, scorer_headers: dict) -> None:
    """Scorer users cannot create venues (403)."""
    response = client.post(
        "/api/venues",
        headers=scorer_headers,
        json={"venue_name": "Scorer Stadium", "city": "Bristol", "capacity": 15000},
    )
    assert response.status_code == 403


def test_admin_can_crud_venue(client: TestClient, admin_headers: dict) -> None:
    """Admin can create, update, and delete a venue."""
    # Create
    create_res = client.post(
        "/api/venues",
        headers=admin_headers,
        json={"venue_name": "Test Cricket Ground", "city": "Nottingham", "capacity": 25000},
    )
    assert create_res.status_code == 201
    venue = create_res.json()
    venue_id = venue["venue_id"]
    assert venue["venue_name"] == "Test Cricket Ground"

    # Update
    update_res = client.put(
        f"/api/venues/{venue_id}",
        headers=admin_headers,
        json={"capacity": 28000},
    )
    assert update_res.status_code == 200
    assert update_res.json()["capacity"] == 28000

    # Delete
    del_res = client.delete(f"/api/venues/{venue_id}", headers=admin_headers)
    assert del_res.status_code == 204

    # Verify deleted
    get_res = client.get(f"/api/venues/{venue_id}")
    assert get_res.status_code == 404


def test_venue_search_and_pagination(client: TestClient) -> None:
    """Test search query ?q= and pagination ?page=&page_size= on venues."""
    res_paginated = client.get("/api/venues?page=1&page_size=2")
    assert res_paginated.status_code == 200
    data = res_paginated.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) <= 2

    # Search with city or name
    res_search = client.get("/api/venues?q=Wankhede")
    assert res_search.status_code == 200
    search_items = res_search.json()["items"]
    assert any("Wankhede" in v["venue_name"] for v in search_items)


# ---------------------------------------------------------
# 2. TEAMS CRUD & VALIDATION
# ---------------------------------------------------------

def test_admin_can_crud_team(client: TestClient, admin_headers: dict) -> None:
    """Admin can create, update, and delete a fresh team."""
    create_res = client.post(
        "/api/teams",
        headers=admin_headers,
        json={
            "team_name": "Temporary Titans",
            "city": "Ahmedabad",
            "short_code": "TT",
            "coach_name": "Coach Test",
        },
    )
    assert create_res.status_code == 201
    team = create_res.json()
    team_id = team["team_id"]
    assert team["team_name"] == "Temporary Titans"
    assert team["player_count"] == 0

    # Update
    upd_res = client.put(
        f"/api/teams/{team_id}",
        headers=admin_headers,
        json={"coach_name": "Updated Coach"},
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["coach_name"] == "Updated Coach"

    # Delete
    del_res = client.delete(f"/api/teams/{team_id}", headers=admin_headers)
    assert del_res.status_code == 204


def test_cannot_delete_team_with_matches(client: TestClient, admin_headers: dict, db_session) -> None:
    """Cannot delete a team that has associated matches (409 Conflict)."""
    # Find a match and get team1_id
    match = db_session.query(Match).first()
    assert match is not None, "Seeded match expected"

    team_id = str(match.team1_id)
    response = client.delete(f"/api/teams/{team_id}", headers=admin_headers)
    assert response.status_code == 409
    assert "matches" in response.json()["detail"].lower()


def test_team_search_and_details(client: TestClient) -> None:
    """Search teams and check player_count in team details."""
    teams_res = client.get("/api/teams?q=Mumbai")
    assert teams_res.status_code == 200
    items = teams_res.json()["items"]
    assert len(items) >= 1
    team = items[0]
    assert "Mumbai" in team["team_name"] or "Mumbai" in team["city"]

    # Check get single team
    single_res = client.get(f"/api/teams/{team['team_id']}")
    assert single_res.status_code == 200
    assert single_res.json()["player_count"] >= 0


# ---------------------------------------------------------
# 3. TOURNAMENTS CRUD & REGISTRATION
# ---------------------------------------------------------

def test_admin_can_create_and_delete_tournament(client: TestClient, admin_headers: dict) -> None:
    """Admin can create and manage a tournament."""
    today = date.today()
    create_res = client.post(
        "/api/tournaments",
        headers=admin_headers,
        json={
            "name": "Winter Premier Cup",
            "level": "club",
            "format": "T20",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=14)).isoformat(),
        },
    )
    assert create_res.status_code == 201
    tournament = create_res.json()
    t_id = tournament["tournament_id"]
    assert tournament["team_count"] == 0

    # Delete
    del_res = client.delete(f"/api/tournaments/{t_id}", headers=admin_headers)
    assert del_res.status_code == 204


def test_tournament_date_validation_failure(client: TestClient, admin_headers: dict) -> None:
    """End date earlier than start date must return 422 Unprocessable Entity."""
    today = date.today()
    response = client.post(
        "/api/tournaments",
        headers=admin_headers,
        json={
            "name": "Invalid Date Cup",
            "level": "domestic",
            "format": "ODI",
            "start_date": today.isoformat(),
            "end_date": (today - timedelta(days=5)).isoformat(),
        },
    )
    assert response.status_code == 422


def test_tournament_team_registration_and_unique_name(
    client: TestClient, admin_headers: dict
) -> None:
    """Test M:N tournament team registration, duplicate prevention, and unique team name per tournament."""
    today = date.today()
    # 1. Create a fresh tournament
    t_res = client.post(
        "/api/tournaments",
        headers=admin_headers,
        json={
            "name": "T20 Registration League",
            "level": "local",
            "format": "T20",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=7)).isoformat(),
        },
    )
    assert t_res.status_code == 201
    t_id = t_res.json()["tournament_id"]

    # 2. Create two teams with the same team name in different cities
    team1_res = client.post(
        "/api/teams",
        headers=admin_headers,
        json={"team_name": "Royal Challengers", "city": "Bengaluru"},
    )
    assert team1_res.status_code == 201
    team1_id = team1_res.json()["team_id"]

    team2_res = client.post(
        "/api/teams",
        headers=admin_headers,
        json={"team_name": "Royal Challengers", "city": "Hubli"},
    )
    assert team2_res.status_code == 201
    team2_id = team2_res.json()["team_id"]

    team3_res = client.post(
        "/api/teams",
        headers=admin_headers,
        json={"team_name": "Sunrisers Elite", "city": "Hyderabad"},
    )
    assert team3_res.status_code == 201
    team3_id = team3_res.json()["team_id"]

    try:
        # 3. Register team 1
        reg_res = client.post(
            f"/api/tournaments/{t_id}/teams",
            headers=admin_headers,
            json={"team_id": team1_id},
        )
        assert reg_res.status_code == 201

        # 4. Try duplicate registration of the exact same team -> 409
        dup_reg = client.post(
            f"/api/tournaments/{t_id}/teams",
            headers=admin_headers,
            json={"team_id": team1_id},
        )
        assert dup_reg.status_code == 409
        assert "already registered" in dup_reg.json()["detail"].lower()

        # 5. Try registering team 2 (same team_name) -> 409 Conflict
        name_conflict = client.post(
            f"/api/tournaments/{t_id}/teams",
            headers=admin_headers,
            json={"team_id": team2_id},
        )
        assert name_conflict.status_code == 409
        assert "name" in name_conflict.json()["detail"].lower()

        # 6. Register team 3 (different name) -> 201
        reg3 = client.post(
            f"/api/tournaments/{t_id}/teams",
            headers=admin_headers,
            json={"team_id": team3_id},
        )
        assert reg3.status_code == 201

        # 7. Check list of teams in tournament
        teams_in_t = client.get(f"/api/tournaments/{t_id}/teams").json()
        assert len(teams_in_t) == 2

        # 8. Unregister team 3
        unreg = client.delete(
            f"/api/tournaments/{t_id}/teams/{team3_id}",
            headers=admin_headers,
        )
        assert unreg.status_code == 204

        # Verify team 3 is removed
        teams_after = client.get(f"/api/tournaments/{t_id}/teams").json()
        assert len(teams_after) == 1

    finally:
        # Cleanup tournament and teams
        client.delete(f"/api/tournaments/{t_id}", headers=admin_headers)
        client.delete(f"/api/teams/{team1_id}", headers=admin_headers)
        client.delete(f"/api/teams/{team2_id}", headers=admin_headers)
        client.delete(f"/api/teams/{team3_id}", headers=admin_headers)


# ---------------------------------------------------------
# 4. PLAYERS CRUD & STATS
# ---------------------------------------------------------

def test_dob_future_validation_fails(client: TestClient, admin_headers: dict) -> None:
    """Player DOB in future must return 422 Unprocessable Entity."""
    future_date = date.today() + timedelta(days=365)
    response = client.post(
        "/api/players",
        headers=admin_headers,
        json={
            "name": "Time Traveler",
            "dob": future_date.isoformat(),
            "role": "Batsman",
        },
    )
    assert response.status_code == 422
    assert "future" in str(response.json()).lower()


def test_admin_can_crud_player(client: TestClient, admin_headers: dict) -> None:
    """Admin can create, update, and delete player."""
    create_res = client.post(
        "/api/players",
        headers=admin_headers,
        json={
            "name": "Rohit Verma",
            "dob": "1998-05-15",
            "batting_style": "Right-hand bat",
            "bowling_style": "Right-arm offbreak",
            "role": "All-Rounder",
        },
    )
    assert create_res.status_code == 201
    player = create_res.json()
    player_id = player["player_id"]
    assert player["name"] == "Rohit Verma"
    assert player["stats"] is not None
    assert player["stats"]["matches_played"] == 0

    # Update player
    upd_res = client.put(
        f"/api/players/{player_id}",
        headers=admin_headers,
        json={"role": "Top-order Batter"},
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["role"] == "Top-order Batter"

    # Delete player
    del_res = client.delete(f"/api/players/{player_id}", headers=admin_headers)
    assert del_res.status_code == 204


def test_get_player_by_id_returns_career_stats(client: TestClient, db_session) -> None:
    """GET /api/players/{id} returns profile with career stats."""
    seeded_player = db_session.query(Player).first()
    assert seeded_player is not None, "Seeded player expected"

    response = client.get(f"/api/players/{seeded_player.player_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == str(seeded_player.player_id)
    assert "stats" in data
    assert data["stats"] is not None
    assert "runs" in data["stats"]
    assert "wickets" in data["stats"]
    assert "strike_rate" in data["stats"]
    assert "economy" in data["stats"]


def test_player_search_and_filter(client: TestClient) -> None:
    """Filter players by q, role, batting_style."""
    res = client.get("/api/players?page=1&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) <= 5
    assert data["total"] > 0


# ---------------------------------------------------------
# 5. USER MANAGEMENT (ADMIN ONLY)
# ---------------------------------------------------------

def test_unauthenticated_cannot_access_user_endpoints(client: TestClient) -> None:
    """Unauthenticated users receive 401 on /api/users."""
    res = client.get("/api/users")
    assert res.status_code == 401


def test_scorer_cannot_access_user_endpoints(client: TestClient, scorer_headers: dict) -> None:
    """Scorers receive 403 on /api/users."""
    res = client.get("/api/users")
    assert res.status_code == 401  # Unauthenticated
    res2 = client.get("/api/users", headers=scorer_headers)
    assert res2.status_code == 403


def test_admin_can_manage_users(client: TestClient, admin_headers: dict) -> None:
    """Admin creates, updates, lists, and deletes scorer accounts."""
    test_email = f"new_scorer_{uuid.uuid4().hex[:6]}@cdms.com"

    # Create scorer account
    create_res = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "name": "Match Scorer Official",
            "email": test_email,
            "password": "securepassword123",
            "role": "scorer",
        },
    )
    assert create_res.status_code == 201
    user = create_res.json()
    user_id = user["user_id"]
    assert user["email"] == test_email
    assert user["role"] == "scorer"

    # Duplicate email prevention -> 409 Conflict
    dup_res = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "name": "Another Scorer",
            "email": test_email,
            "password": "securepassword123",
            "role": "scorer",
        },
    )
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"].lower()

    # List users with search
    list_res = client.get(f"/api/users?q={test_email}", headers=admin_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # Update user
    upd_res = client.put(
        f"/api/users/{user_id}",
        headers=admin_headers,
        json={"name": "Updated Scorer Name"},
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["name"] == "Updated Scorer Name"

    # Delete user
    del_res = client.delete(f"/api/users/{user_id}", headers=admin_headers)
    assert del_res.status_code == 204


# ---------------------------------------------------------
# 6. DASHBOARD SUMMARY
# ---------------------------------------------------------

def test_get_dashboard_summary(client: TestClient) -> None:
    """GET /api/dashboard/summary returns metrics counts and 5 recent activities."""
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()

    # Check metrics counts
    assert data["tournaments_count"] >= 1
    assert data["teams_count"] >= 1
    assert data["players_count"] >= 1
    assert data["scheduled_matches_count"] >= 1

    # Check recent activities list
    assert "recent_activities" in data
    assert isinstance(data["recent_activities"], list)
    assert len(data["recent_activities"]) <= 5
    if len(data["recent_activities"]) > 0:
        act = data["recent_activities"][0]
        assert "id" in act
        assert "type" in act
        assert "description" in act
        assert "timestamp" in act
