import uuid
from datetime import date, datetime, time, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.models.match import Match, MatchStatus
from app.models.team import Team, TournamentTeam
from app.models.tournament import MatchFormat, Tournament, TournamentLevel
from app.models.venue import Venue


# -------------------------------------------------------------
# 1. MANUAL MATCH SCHEDULING & CONFLICT DETECTION
# -------------------------------------------------------------

def test_reject_same_team_match(client: TestClient, admin_headers: dict, db_session) -> None:
    """POST /api/matches rejects if team1 == team2 (422 Unprocessable Entity)."""
    tournament = db_session.query(Tournament).first()
    team = db_session.query(Team).first()

    now = datetime.now(timezone.utc) + timedelta(days=2)
    response = client.post(
        "/api/matches",
        headers=admin_headers,
        json={
            "tournament_id": str(tournament.tournament_id),
            "team1_id": str(team.team_id),
            "team2_id": str(team.team_id),
            "match_date": now.isoformat(),
            "overs": 20,
        },
    )
    assert response.status_code == 422
    assert "different teams" in str(response.json()).lower()


def test_reject_unregistered_team_in_tournament(
    client: TestClient, admin_headers: dict, db_session
) -> None:
    """POST /api/matches rejects if either team is not registered in the tournament (409 Conflict)."""
    tournament = db_session.query(Tournament).first()
    teams = db_session.query(Team).all()
    registered_ids = {
        tt.team_id
        for tt in db_session.query(TournamentTeam)
        .filter(TournamentTeam.tournament_id == tournament.tournament_id)
        .all()
    }

    # Find or create a team not registered in this tournament
    unregistered_team = next((t for t in teams if t.team_id not in registered_ids), None)
    if not unregistered_team:
        unreg_res = client.post(
            "/api/teams",
            headers=admin_headers,
            json={"team_name": "Outsider Team", "city": "Goa"},
        )
        unregistered_team_id = unreg_res.json()["team_id"]
    else:
        unregistered_team_id = str(unregistered_team.team_id)

    # Use a registered team for team 1
    registered_team_id = str(list(registered_ids)[0])

    now = datetime.now(timezone.utc) + timedelta(days=3)
    response = client.post(
        "/api/matches",
        headers=admin_headers,
        json={
            "tournament_id": str(tournament.tournament_id),
            "team1_id": registered_team_id,
            "team2_id": unregistered_team_id,
            "match_date": now.isoformat(),
            "overs": 20,
        },
    )
    assert response.status_code == 409
    assert "not registered" in response.json()["detail"].lower()


def test_venue_double_booking_conflict_t20(
    client: TestClient, admin_headers: dict, db_session
) -> None:
    """Venue double-booked at the same time (+/- 4 hours for T20) is rejected with 409 Conflict."""
    tournament = db_session.query(Tournament).filter(Tournament.format == MatchFormat.T20).first()
    if not tournament:
        tournament = db_session.query(Tournament).first()

    # Get two registered teams
    reg_teams = (
        db_session.query(TournamentTeam)
        .filter(TournamentTeam.tournament_id == tournament.tournament_id)
        .all()
    )
    team1_id = str(reg_teams[0].team_id)
    team2_id = str(reg_teams[1].team_id)
    venue = db_session.query(Venue).first()
    venue_id = str(venue.venue_id)

    base_time = datetime(2027, 5, 1, 14, 0, tzinfo=timezone.utc)

    # 1. Schedule initial match at 14:00
    res1 = client.post(
        "/api/matches",
        headers=admin_headers,
        json={
            "tournament_id": str(tournament.tournament_id),
            "team1_id": team1_id,
            "team2_id": team2_id,
            "venue_id": venue_id,
            "match_date": base_time.isoformat(),
            "overs": 20,
        },
    )
    assert res1.status_code == 201
    match1_id = res1.json()["match_id"]

    try:
        # 2. Attempt second match at 16:00 (+2 hours: within +/- 4h conflict window) -> 409 Conflict
        conflict_time = base_time + timedelta(hours=2)
        res_conflict = client.post(
            "/api/matches",
            headers=admin_headers,
            json={
                "tournament_id": str(tournament.tournament_id),
                "team1_id": team1_id,
                "team2_id": team2_id,
                "venue_id": venue_id,
                "match_date": conflict_time.isoformat(),
                "overs": 20,
            },
        )
        assert res_conflict.status_code == 409
        assert "venue is already booked" in res_conflict.json()["detail"].lower()

        # 3. Attempt match at 19:00 (+5 hours: outside +/- 4h window) -> 201 Success
        free_time = base_time + timedelta(hours=5)
        res_free = client.post(
            "/api/matches",
            headers=admin_headers,
            json={
                "tournament_id": str(tournament.tournament_id),
                "team1_id": team1_id,
                "team2_id": team2_id,
                "venue_id": venue_id,
                "match_date": free_time.isoformat(),
                "overs": 20,
            },
        )
        assert res_free.status_code == 201
        match2_id = res_free.json()["match_id"]

        # Clean up match 2
        db_session.query(Match).filter(Match.match_id == match2_id).delete()
        db_session.commit()

    finally:
        # Clean up match 1
        db_session.query(Match).filter(Match.match_id == match1_id).delete()
        db_session.commit()


def test_venue_double_booking_conflict_odi(
    client: TestClient, admin_headers: dict, db_session
) -> None:
    """Venue double-booked at the same time (+/- 9 hours for ODI) is rejected with 409 Conflict."""
    # Create or find an ODI tournament
    odi_t = db_session.query(Tournament).filter(Tournament.format == MatchFormat.ODI).first()
    if not odi_t:
        odi_res = client.post(
            "/api/tournaments",
            headers=admin_headers,
            json={
                "name": "ODI Cup Conflict Test",
                "level": "domestic",
                "format": "ODI",
                "start_date": "2027-06-01",
                "end_date": "2027-06-30",
            },
        )
        assert odi_res.status_code == 201
        odi_t_id = odi_res.json()["tournament_id"]
    else:
        odi_t_id = str(odi_t.tournament_id)

    # Register two teams into ODI tournament
    teams = db_session.query(Team).limit(2).all()
    t1_id = str(teams[0].team_id)
    t2_id = str(teams[1].team_id)

    client.post(f"/api/tournaments/{odi_t_id}/teams", headers=admin_headers, json={"team_id": t1_id})
    client.post(f"/api/tournaments/{odi_t_id}/teams", headers=admin_headers, json={"team_id": t2_id})

    venue = db_session.query(Venue).first()
    venue_id = str(venue.venue_id)

    base_time = datetime(2027, 6, 10, 9, 0, tzinfo=timezone.utc)

    # 1. Initial ODI match at 09:00
    res1 = client.post(
        "/api/matches",
        headers=admin_headers,
        json={
            "tournament_id": odi_t_id,
            "team1_id": t1_id,
            "team2_id": t2_id,
            "venue_id": venue_id,
            "match_date": base_time.isoformat(),
            "overs": 50,
        },
    )
    assert res1.status_code == 201
    m1_id = res1.json()["match_id"]

    try:
        # 2. Attempt match at 15:00 (+6 hours: within +/- 9h ODI conflict window) -> 409 Conflict
        conflict_time = base_time + timedelta(hours=6)
        res_conflict = client.post(
            "/api/matches",
            headers=admin_headers,
            json={
                "tournament_id": odi_t_id,
                "team1_id": t1_id,
                "team2_id": t2_id,
                "venue_id": venue_id,
                "match_date": conflict_time.isoformat(),
                "overs": 50,
            },
        )
        assert res_conflict.status_code == 409
        assert "venue is already booked" in res_conflict.json()["detail"].lower()

        # 3. Attempt match at next day 09:00 (+24 hours: outside +/- 9h window) -> 201 Success
        next_day = base_time + timedelta(hours=24)
        res_ok = client.post(
            "/api/matches",
            headers=admin_headers,
            json={
                "tournament_id": odi_t_id,
                "team1_id": t1_id,
                "team2_id": t2_id,
                "venue_id": venue_id,
                "match_date": next_day.isoformat(),
                "overs": 50,
            },
        )
        assert res_ok.status_code == 201
        m2_id = res_ok.json()["match_id"]

        # Clean up match 2
        db_session.query(Match).filter(Match.match_id == m2_id).delete()
        db_session.commit()

    finally:
        db_session.query(Match).filter(Match.match_id == m1_id).delete()
        db_session.commit()


# -------------------------------------------------------------
# 2. ROUND-ROBIN FIXTURE GENERATION & CONFLICT SHIFTING
# -------------------------------------------------------------

def test_generate_schedule_round_robin_count_and_status(
    client: TestClient, admin_headers: dict
) -> None:
    """Generate round-robin fixtures n*(n-1)/2, status 'scheduled', assigning dates/venues."""
    today = date.today() + timedelta(days=100)

    # 1. Create tournament
    t_res = client.post(
        "/api/tournaments",
        headers=admin_headers,
        json={
            "name": "Round Robin League",
            "level": "club",
            "format": "T20",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
        },
    )
    assert t_res.status_code == 201
    t_id = t_res.json()["tournament_id"]

    # 2. Register 4 fresh teams -> n = 4, expected fixtures = 4*3/2 = 6
    created_team_ids = []
    for i in range(1, 5):
        team_res = client.post(
            "/api/teams",
            headers=admin_headers,
            json={"team_name": f"RR Team {i} ({uuid.uuid4().hex[:4]})", "city": f"City {i}"},
        )
        assert team_res.status_code == 201
        tm_id = team_res.json()["team_id"]
        created_team_ids.append(tm_id)

        # Register to tournament
        reg_res = client.post(
            f"/api/tournaments/{t_id}/teams",
            headers=admin_headers,
            json={"team_id": tm_id},
        )
        assert reg_res.status_code == 201

    try:
        # 3. Generate schedule
        gen_res = client.post(
            f"/api/tournaments/{t_id}/generate-schedule",
            headers=admin_headers,
        )
        assert gen_res.status_code == 201
        data = gen_res.json()
        assert data["fixtures_count"] == 6  # 4*(4-1)/2 = 6
        assert len(data["matches"]) == 6

        # 4. Check all matches have status 'scheduled' and venues assigned
        venues_and_times = []
        for m in data["matches"]:
            assert m["status"] == "scheduled"
            assert m["venue_id"] is not None
            assert m["match_date"] is not None
            venues_and_times.append((m["venue_id"], datetime.fromisoformat(m["match_date"])))

        # 5. Verify NO double-booking conflicts among the generated fixtures (min 4h spacing per venue)
        for i in range(len(venues_and_times)):
            for j in range(i + 1, len(venues_and_times)):
                v1, dt1 = venues_and_times[i]
                v2, dt2 = venues_and_times[j]
                if v1 == v2:
                    diff_hours = abs((dt1 - dt2).total_seconds()) / 3600
                    assert diff_hours >= 4.0, f"Venue double booked with only {diff_hours} hours diff"

    finally:
        # Cleanup tournament and teams
        client.delete(f"/api/tournaments/{t_id}", headers=admin_headers)
        for tm_id in created_team_ids:
            client.delete(f"/api/teams/{tm_id}", headers=admin_headers)


def test_generate_schedule_insufficient_teams_fails(
    client: TestClient, admin_headers: dict
) -> None:
    """Generating schedule with < 2 teams returns 400 Bad Request."""
    today = date.today() + timedelta(days=50)
    t_res = client.post(
        "/api/tournaments",
        headers=admin_headers,
        json={
            "name": "Solo Tournament",
            "level": "local",
            "format": "T20",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=10)).isoformat(),
        },
    )
    t_id = t_res.json()["tournament_id"]

    try:
        # Attempt schedule with 0 teams
        res = client.post(f"/api/tournaments/{t_id}/generate-schedule", headers=admin_headers)
        assert res.status_code == 400
        assert "at least 2 registered teams" in res.json()["detail"].lower()
    finally:
        client.delete(f"/api/tournaments/{t_id}", headers=admin_headers)


def test_generate_schedule_shifts_on_preexisting_conflict(
    client: TestClient, admin_headers: dict, db_session
) -> None:
    """When a venue is already booked, generate-schedule shifts fixtures to avoid conflicts."""
    today = date.today() + timedelta(days=150)
    conflict_slot = datetime.combine(today, time(10, 0), tzinfo=timezone.utc)

    # 1. Create a tournament
    t_res = client.post(
        "/api/tournaments",
        headers=admin_headers,
        json={
            "name": "Conflict Shift League",
            "level": "club",
            "format": "T20",
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=20)).isoformat(),
        },
    )
    t_id = t_res.json()["tournament_id"]

    # 2. Register 3 teams (expected 3*(2)/2 = 3 fixtures)
    created_teams = []
    for i in range(1, 4):
        tm = client.post(
            "/api/teams",
            headers=admin_headers,
            json={"team_name": f"Shift Team {i} ({uuid.uuid4().hex[:4]})", "city": "Pune"},
        ).json()
        created_teams.append(tm["team_id"])
        client.post(f"/api/tournaments/{t_id}/teams", headers=admin_headers, json={"team_id": tm["team_id"]})

    # 3. Create an unrelated match at the first venue at exactly day 1 10:00 AM
    venues = db_session.query(Venue).all()
    first_venue_id = str(venues[0].venue_id)

    pre_match_res = client.post(
        "/api/matches",
        headers=admin_headers,
        json={
            "tournament_id": t_id,
            "team1_id": created_teams[0],
            "team2_id": created_teams[1],
            "venue_id": first_venue_id,
            "match_date": conflict_slot.isoformat(),
            "overs": 20,
        },
    )
    pre_match_id = pre_match_res.json()["match_id"]

    try:
        # 4. Generate schedule for tournament
        gen_res = client.post(f"/api/tournaments/{t_id}/generate-schedule", headers=admin_headers)
        assert gen_res.status_code == 201
        data = gen_res.json()
        assert data["fixtures_count"] == 3

        # 5. Verify NONE of the generated matches booked first_venue_id at conflict_slot
        for m in data["matches"]:
            m_dt = datetime.fromisoformat(m["match_date"])
            if m["venue_id"] == first_venue_id:
                diff = abs((m_dt - conflict_slot).total_seconds()) / 3600
                assert diff >= 4.0, "Scheduler failed to shift away from pre-booked slot!"

    finally:
        client.delete(f"/api/tournaments/{t_id}", headers=admin_headers)
        for tm_id in created_teams:
            client.delete(f"/api/teams/{tm_id}", headers=admin_headers)


def test_public_matches_listing_and_filtering(client: TestClient) -> None:
    """Public can list matches with pagination and retrieve single match details."""
    list_res = client.get("/api/matches?page=1&page_size=5")
    assert list_res.status_code == 200
    data = list_res.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1

    first_match = data["items"][0]
    single_res = client.get(f"/api/matches/{first_match['match_id']}")
    assert single_res.status_code == 200
    m = single_res.json()
    assert m["match_id"] == first_match["match_id"]
    assert "team1_name" in m
    assert "team2_name" in m
    assert "status" in m


# -------------------------------------------------------------
# 3. MATCH STATE TRANSITION ENDPOINT
# -------------------------------------------------------------

def test_match_state_transition_endpoint(
    client: TestClient, admin_headers: dict, db_session
) -> None:
    """POST /api/matches/{id}/transition executes state machine and rejects invalid transitions."""
    match = db_session.query(Match).filter(Match.status == MatchStatus.SCHEDULED).first()
    assert match is not None, "Seeded scheduled match required"
    match_id = str(match.match_id)

    # 1. Invalid transition from SCHEDULED: innings_end -> 400 Bad Request
    inv_res = client.post(
        f"/api/matches/{match_id}/transition",
        headers=admin_headers,
        json={"event": "innings_end"},
    )
    assert inv_res.status_code == 400
    assert "invalid transition" in inv_res.json()["detail"].lower()

    # 2. Valid transition from SCHEDULED: start_toss -> LIVE (200)
    res_live = client.post(
        f"/api/matches/{match_id}/transition",
        headers=admin_headers,
        json={"event": "start_toss"},
    )
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "live"

    # 3. Valid transition from LIVE: innings_end -> INNINGS_BREAK (200)
    res_break = client.post(
        f"/api/matches/{match_id}/transition",
        headers=admin_headers,
        json={"event": "innings_end"},
    )
    assert res_break.status_code == 200
    assert res_break.json()["status"] == "innings_break"

    # 4. Valid transition from INNINGS_BREAK: resume -> LIVE (200)
    res_resume = client.post(
        f"/api/matches/{match_id}/transition",
        headers=admin_headers,
        json={"event": "resume"},
    )
    assert res_resume.status_code == 200
    assert res_resume.json()["status"] == "live"

    # 5. Valid transition from LIVE: complete -> COMPLETED (200)
    res_comp = client.post(
        f"/api/matches/{match_id}/transition",
        headers=admin_headers,
        json={"event": "complete"},
    )
    assert res_comp.status_code == 200
    assert res_comp.json()["status"] == "completed"

    # 6. Invalid transition from COMPLETED: start_toss -> 400
    res_terminal = client.post(
        f"/api/matches/{match_id}/transition",
        headers=admin_headers,
        json={"event": "start_toss"},
    )
    assert res_terminal.status_code == 400
