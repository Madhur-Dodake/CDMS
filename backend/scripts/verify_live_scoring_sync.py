import asyncio
import json
import uuid
import httpx
import websockets

BASE_HTTP = "http://127.0.0.1:8000"
BASE_WS = "ws://127.0.0.1:8000"

async def test_scoring_and_live_sync():
    client = httpx.AsyncClient(base_url=BASE_HTTP, timeout=10.0)

    print("--- 1. Authenticating as Scorer ---")
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "scorer1@cdms.com", "password": "scorer123", "role": "scorer"},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("  Authenticated successfully!")

    print("--- 2. Finding or Scheduling 2-Over Match ---")
    scheduled_res = await client.get("/api/matches?status=scheduled&page_size=20", headers=headers)
    scheduled_matches = scheduled_res.json().get("items", [])
    
    two_over_matches = [m for m in scheduled_matches if m.get("overs") == 2]
    if not two_over_matches:
        raise RuntimeError("No 2-over scheduled match found")
    
    match = two_over_matches[0]
    match_id = match["match_id"]
    t1_id = match["team1_id"]
    t2_id = match["team2_id"]
    print(f"  Target Match ID: {match_id}")
    print(f"  {match['team1_name']} vs {match['team2_name']} (Overs: {match['overs']})")

    # Fetch team rosters
    t1_res = await client.get(f"/api/players?team_id={t1_id}&page_size=50")
    t2_res = await client.get(f"/api/players?team_id={t2_id}&page_size=50")
    t1_roster = t1_res.json()["items"]
    t2_roster = t2_res.json()["items"]
    assert len(t1_roster) >= 2, "Team 1 has insufficient players"
    assert len(t2_roster) >= 2, "Team 2 has insufficient players"

    t1_xi = [p["player_id"] for p in t1_roster[:11]]
    t2_xi = [p["player_id"] for p in t2_roster[:11]]
    striker_id = t1_xi[0]
    non_striker_id = t1_xi[1]
    bowler_1_id = t2_xi[0]
    bowler_2_id = t2_xi[1]

    print("--- 3. Setup Wizard: Recording Toss & Starting Match ---")
    setup_payload = {
        "toss_winner_id": t1_id,
        "toss_decision": "bat",
        "team1_xi": t1_xi,
        "team2_xi": t2_xi,
        "striker_id": striker_id,
        "non_striker_id": non_striker_id,
        "opening_bowler_id": bowler_1_id,
    }
    start_res = await client.post(
        f"/api/matches/{match_id}/start",
        json=setup_payload,
        headers=headers,
    )
    assert start_res.status_code == 200, f"Start failed: {start_res.text}"
    start_data = start_res.json()
    print(f"  Match status transitioned to: {start_data['match_status']}")
    print(f"  Initial Score: {start_data['total_runs']}/{start_data['wickets']} ({start_data['overs_formatted']} Ov)")

    print("--- 4. Connecting Viewer Tab via WebSocket Stream ---")
    ws_uri = f"{BASE_WS}/ws/matches/{match_id}"
    async with websockets.connect(ws_uri) as ws:
        # Initial snapshot on connect
        initial_snap = json.loads(await ws.recv())
        print(f"  [Viewer WS Snapshot Received] Status: {initial_snap['status']}, Score: {initial_snap['score']}/{initial_snap['wickets']}")
        assert initial_snap["score"] == 0
        assert initial_snap["overs"] == "0.0"

        print("\n--- 5. Scoring Over 1 (Deliveries 1 to 6) ---")
        over_1_runs = [1, 2, 4, 0, 1, 4]
        current_striker = striker_id
        current_non_striker = non_striker_id

        for i, r in enumerate(over_1_runs):
            ball_payload = {
                "striker_id": current_striker,
                "non_striker_id": current_non_striker,
                "bowler_id": bowler_1_id,
                "runs_batter": r,
                "extras_type": None,
                "extras_runs": 0,
                "is_wicket": False,
            }
            res = await client.post(f"/api/matches/{match_id}/ball", json=ball_payload, headers=headers)
            assert res.status_code == 200, f"Ball failed: {res.text}"
            res_data = res.json()

            # Verify WebSocket broadcast arrives in Viewer tab
            broadcast = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.0))
            print(f"  Ball 1.{i+1} (+{r} runs) -> Scorer: {res_data['total_runs']}/{res_data['wickets']} ({res_data['overs_formatted']} Ov) | Viewer WS: {broadcast['score']}/{broadcast['wickets']} ({broadcast['overs']} Ov) [Recent: {broadcast['recent_balls']}]")
            assert broadcast["score"] == res_data["total_runs"]
            assert broadcast["overs"] == res_data["overs_formatted"]

            # Update active strike for next delivery
            current_striker = res_data["striker_id"]
            current_non_striker = res_data["non_striker_id"]

        print(f"  Over 1 Complete! Total: {res_data['total_runs']}/{res_data['wickets']} ({res_data['overs_formatted']} Ov)")
        assert res_data["total_runs"] == 12
        assert res_data["overs_formatted"] == "1.0"

        print("\n--- 6. Scoring Over 2 with Wicket & Boundaries ---")
        # Ball 2.1: Wicket! (Bowled, next batter in)
        next_batter = t1_xi[2]
        wicket_payload = {
            "striker_id": current_striker,
            "non_striker_id": current_non_striker,
            "bowler_id": bowler_2_id,
            "runs_batter": 0,
            "extras_type": None,
            "extras_runs": 0,
            "is_wicket": True,
            "wicket_type": "bowled",
            "dismissed_player_id": current_striker,
            "next_batter_id": next_batter,
        }
        res = await client.post(f"/api/matches/{match_id}/ball", json=wicket_payload, headers=headers)
        assert res.status_code == 200, f"Wicket ball failed: {res.text}"
        res_data = res.json()

        broadcast = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.0))
        print(f"  Ball 2.1 (WICKET) -> Scorer: {res_data['total_runs']}/{res_data['wickets']} ({res_data['overs_formatted']} Ov) | Viewer WS: {broadcast['score']}/{broadcast['wickets']} ({broadcast['overs']} Ov) [Recent: {broadcast['recent_balls']}]")
        assert broadcast["wickets"] == 1
        assert "W" in broadcast["recent_balls"]

        current_striker = res_data["striker_id"]
        current_non_striker = res_data["non_striker_id"]

        # Balls 2.2 to 2.6: [1, 2, 1, 0, 6]
        over_2_remaining = [1, 2, 1, 0, 6]
        for i, r in enumerate(over_2_remaining):
            ball_payload = {
                "striker_id": current_striker,
                "non_striker_id": current_non_striker,
                "bowler_id": bowler_2_id,
                "runs_batter": r,
                "extras_type": None,
                "extras_runs": 0,
                "is_wicket": False,
            }
            res = await client.post(f"/api/matches/{match_id}/ball", json=ball_payload, headers=headers)
            assert res.status_code == 200, f"Ball failed: {res.text}"
            res_data = res.json()

            broadcast = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.0))
            print(f"  Ball 2.{i+2} (+{r} runs) -> Scorer: {res_data['total_runs']}/{res_data['wickets']} ({res_data['overs_formatted']} Ov) | Viewer WS: {broadcast['score']}/{broadcast['wickets']} ({broadcast['overs']} Ov)")
            assert broadcast["score"] == res_data["total_runs"]
            assert broadcast["overs"] == res_data["overs_formatted"]

            current_striker = res_data["striker_id"]
            current_non_striker = res_data["non_striker_id"]

        print(f"\n  Innings 1 Completed at 2.0 Overs! Final Score: {res_data['total_runs']}/{res_data['wickets']} ({res_data['overs_formatted']} Ov)")
        assert res_data["total_runs"] == 22
        assert res_data["wickets"] == 1
        assert res_data["overs_formatted"] == "2.0"
        assert res_data["is_completed"] == True

        print("\n--- 7. Testing Undo Delivery Feature ---")
        undo_res = await client.post(f"/api/matches/{match_id}/undo", headers=headers)
        assert undo_res.status_code == 200, f"Undo failed: {undo_res.text}"
        undo_data = undo_res.json()
        undo_broadcast = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.0))
        print(f"  [Undone 2.6 SIX] -> Score reverted to: {undo_data['total_runs']}/{undo_data['wickets']} ({undo_data['overs_formatted']} Ov) | Viewer WS: {undo_broadcast['score']}/{undo_broadcast['wickets']}")
        assert undo_data["total_runs"] == 16
        assert undo_data["overs_formatted"] == "1.5"
        assert undo_broadcast["score"] == 16

        print("\n--- 8. Re-playing delivery 2.6 (SIX!) to finish Innings 1 ---")
        final_ball = {
            "striker_id": undo_data["striker_id"],
            "non_striker_id": undo_data["non_striker_id"],
            "bowler_id": bowler_2_id,
            "runs_batter": 6,
            "extras_type": None,
            "extras_runs": 0,
            "is_wicket": False,
        }
        res = await client.post(f"/api/matches/{match_id}/ball", json=final_ball, headers=headers)
        assert res.status_code == 200
        res_data = res.json()
        broadcast = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.0))
        print(f"  Re-scored 2.6 -> Final: {broadcast['score']}/{broadcast['wickets']} ({broadcast['overs']} Ov)")
        assert broadcast["score"] == 22

        print("\n--- 9. Ending Innings 1 & Transitioning to Innings Break ---")
        end_inn_res = await client.post(f"/api/matches/{match_id}/end-innings", headers=headers)
        assert end_inn_res.status_code == 200
        end_inn_data = end_inn_res.json()
        print(f"  Innings 1 Ended! Target for Innings 2: {end_inn_data['target_runs']} runs")
        assert end_inn_data["target_runs"] == 23

        print("\n=======================================================")
        print("ALL SCORING CONSOLE & REAL-TIME VIEWER WS CHECKS PASSED!")
        print("=======================================================")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_scoring_and_live_sync())
