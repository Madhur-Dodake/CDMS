"""Basis Path Testing Suite (Report Section 9).

This test module verifies the 5 core computational components:
  1. Module 1: auth (18 basis paths)
  2. Module 2: nrr_calculator (11 basis paths)
  3. Module 3: stats_engine (11 basis paths)
  4. Module 4: connection_manager (8 basis paths)
  5. Module 5: scoring logic (41 basis paths)

Total Test Cases: exactly 89 tests (18 + 11 + 11 + 8 + 41 = 89).
All tested functions have been analyzed and refactored to ensure Cyclomatic Complexity V(G) <= 5.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, WebSocket

# 1. Auth imports
from app.core.auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
    get_password_hash,
    require_admin,
    require_scorer_or_admin,
    verify_password,
)
from app.models.user import User, UserRole

# 2. NRR Calculator imports
from app.services.nrr_calculator import (
    MatchNRREntry,
    balls_to_decimal_overs,
    calculate_cumulative_nrr,
    calculate_nrr,
    decimal_to_overs,
    overs_to_decimal,
)

# 3. Stats Engine imports
from app.services.stats_engine import (
    PlayerCareerMetrics,
    batting_average,
    batting_strike_rate,
    bowling_average,
    bowling_economy,
    compute_career_metrics,
    count_milestones,
)

# 4. Connection Manager imports
from app.ws.connection_manager import ConnectionManager

# 5. Scoring Engine imports
from app.services.scoring_engine import (
    BallInput,
    BatterStats,
    BowlerStats,
    InningsState,
    apply_ball,
    current_run_rate,
    get_ball_display_token,
    overs_display,
    replay,
    required_run_rate,
)


# ============================================================================
# MODULE 1: AUTHENTICATION & ACCESS CONTROL (18 Tests)
# ============================================================================

class TestAuthBasisPaths:
    """Basis path test suite for `app.core.auth`.

    Flow Graphs & Cyclomatic Complexity:
    -------------------------------------------------------------------------
    verify_password(plain_password, hashed_password):
      Control Flow:
        (1) Entry
        (2) if not plain_password -> return False (4)
        (3) if not hashed_password -> return False (4)
        (5) try bcrypt.checkpw -> return bool (6)
        (7) except ValueError -> return plain == hashed (8)
      Nodes (N) = 8, Edges (E) = 10
      Cyclomatic Complexity V(G) = E - N + 2 = 10 - 8 + 2 = 4 (<= 5)

    get_password_hash(password):
      Control Flow: (1) Entry -> bcrypt.gensalt() -> bcrypt.hashpw() -> (2) Exit
      N = 2, E = 1 => V(G) = 1 (<= 5)

    create_access_token(data, expires_delta):
      Control Flow:
        (1) Entry -> copy data
        (2) if expires_delta is not None -> (3) delta branch else (4) default
        (5) jwt.encode -> Exit
      N = 5, E = 5 => V(G) = 5 - 5 + 2 = 2 (<= 5)

    decode_access_token(token):
      Control Flow:
        (1) Entry -> try jwt.decode -> (2) return payload
        (3) except ExpiredSignatureError -> raise 401
        (4) except PyJWTError -> raise 401
      N = 4, E = 5 => V(G) = 5 - 4 + 2 = 3 (<= 5)

    get_current_user(token, db):
      Control Flow:
        (1) Entry -> decode_access_token()
        (2) if not user_id_raw -> (3) raise 401
        (4) try uuid.UUID() -> except ValueError -> (5) raise 401
        (6) query DB -> if user is None -> (7) raise 401
        (8) return user
      N = 8, E = 10 => V(G) = 10 - 8 + 2 = 4 (<= 5)

    require_admin(current_user):
      Control Flow: (1) if role != ADMIN -> (2) raise 403 else (3) return user
      N = 4, E = 4 => V(G) = 2 (<= 5)

    require_scorer_or_admin(current_user):
      Control Flow: (1) if role not in (ADMIN, SCORER) -> (2) raise 403 else (3) return user
      N = 4, E = 4 => V(G) = 2 (<= 5)
    -------------------------------------------------------------------------
    """

    # 1. verify_password paths
    def test_verify_password_empty_plain(self):
        """Path 1: plain_password is empty -> return False."""
        hashed = get_password_hash("Secret123")
        assert verify_password("", hashed) is False

    def test_verify_password_empty_hashed(self):
        """Path 2: hashed_password is empty -> return False."""
        assert verify_password("Secret123", "") is False

    def test_verify_password_bcrypt_match(self):
        """Path 3: bcrypt match succeeds -> return True."""
        hashed = get_password_hash("Secret123")
        assert verify_password("Secret123", hashed) is True

    def test_verify_password_bcrypt_mismatch(self):
        """Path 4: bcrypt password mismatch -> return False."""
        hashed = get_password_hash("Secret123")
        assert verify_password("WrongPassword", hashed) is False

    def test_verify_password_fallback_match(self):
        """Path 5: non-bcrypt plain hash raises ValueError -> fallback match True."""
        assert verify_password("plain_text_pass", "plain_text_pass") is True

    def test_verify_password_fallback_mismatch(self):
        """Path 6: non-bcrypt plain hash raises ValueError -> fallback match False."""
        assert verify_password("plain_text_pass", "different_pass") is False

    # 2. get_password_hash path
    def test_get_password_hash_success(self):
        """Path 7: generates non-empty bcrypt hash string."""
        pw_hash = get_password_hash("Password123")
        assert isinstance(pw_hash, str)
        assert len(pw_hash) > 20
        assert verify_password("Password123", pw_hash) is True

    # 3. create_access_token paths
    def test_create_access_token_custom_expiry(self):
        """Path 8: create token with explicit custom expires_delta."""
        delta = timedelta(minutes=15)
        token = create_access_token({"sub": "admin@cdms.com", "user_id": str(uuid.uuid4())}, expires_delta=delta)
        payload = decode_access_token(token)
        assert payload["sub"] == "admin@cdms.com"
        assert "exp" in payload

    def test_create_access_token_default_expiry(self):
        """Path 9: create token with default expires_delta (None)."""
        token = create_access_token({"sub": "scorer@cdms.com", "user_id": str(uuid.uuid4())})
        payload = decode_access_token(token)
        assert payload["sub"] == "scorer@cdms.com"

    # 4. decode_access_token paths
    def test_decode_access_token_valid(self):
        """Path 10: decode valid non-expired access token."""
        test_uid = str(uuid.uuid4())
        token = create_access_token({"user_id": test_uid, "role": "scorer"})
        payload = decode_access_token(token)
        assert payload["user_id"] == test_uid
        assert payload["role"] == "scorer"

    def test_decode_access_token_expired(self):
        """Path 11: decode expired access token raises 401."""
        token = create_access_token({"user_id": str(uuid.uuid4())}, expires_delta=timedelta(seconds=-10))
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        assert exc_info.value.status_code == 401
        assert "Token expired" in exc_info.value.detail

    def test_decode_access_token_invalid_signature(self):
        """Path 12: decode tampered/invalid token raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("header.invalidpayload.invalidsignature")
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    # 5. get_current_user paths
    def test_get_current_user_missing_user_id(self):
        """Path 13: token payload missing user_id raises 401."""
        token = create_access_token({"role": "scorer"})  # user_id omitted
        mock_db = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, db=mock_db)
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_get_current_user_invalid_uuid(self):
        """Path 14: token payload contains non-UUID user_id raises 401."""
        token = create_access_token({"user_id": "not-a-valid-uuid-format"})
        mock_db = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, db=mock_db)
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_get_current_user_user_not_found(self):
        """Path 15: valid UUID not found in database raises 401."""
        u_id = uuid.uuid4()
        token = create_access_token({"user_id": str(u_id)})
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, db=mock_db)
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail

    def test_get_current_user_success(self):
        """Path 16: valid UUID found in DB returns User instance."""
        u_id = uuid.uuid4()
        token = create_access_token({"user_id": str(u_id)})
        dummy_user = User(user_id=u_id, email="user@cdms.com", name="User Test", password="pw", role=UserRole.SCORER)
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = dummy_user
        resolved = get_current_user(token=token, db=mock_db)
        assert resolved.user_id == u_id
        assert resolved.email == "user@cdms.com"

    # 6. require_admin path
    def test_require_admin_role_authorization(self):
        """Path 17: ADMIN succeeds, non-ADMIN raises 403."""
        admin_user = User(user_id=uuid.uuid4(), email="adm@cdms.com", name="Admin", password="pw", role=UserRole.ADMIN)
        scorer_user = User(user_id=uuid.uuid4(), email="sc@cdms.com", name="Scorer", password="pw", role=UserRole.SCORER)

        assert require_admin(admin_user) == admin_user
        with pytest.raises(HTTPException) as exc_info:
            require_admin(scorer_user)
        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail

    # 7. require_scorer_or_admin path
    def test_require_scorer_or_admin_role_authorization(self):
        """Path 18: ADMIN and SCORER succeed, VIEWER raises 403."""
        admin_user = User(user_id=uuid.uuid4(), email="adm@cdms.com", name="Admin", password="pw", role=UserRole.ADMIN)
        scorer_user = User(user_id=uuid.uuid4(), email="sc@cdms.com", name="Scorer", password="pw", role=UserRole.SCORER)
        viewer_user = User(user_id=uuid.uuid4(), email="vw@cdms.com", name="Viewer", password="pw", role=UserRole.VIEWER)

        assert require_scorer_or_admin(admin_user) == admin_user
        assert require_scorer_or_admin(scorer_user) == scorer_user
        with pytest.raises(HTTPException) as exc_info:
            require_scorer_or_admin(viewer_user)
        assert exc_info.value.status_code == 403
        assert "Scorer or Admin access required" in exc_info.value.detail


# ============================================================================
# MODULE 2: NET RUN RATE (NRR) CALCULATOR (11 Tests)
# ============================================================================

class TestNRRCalculatorBasisPaths:
    """Basis path test suite for `app.services.nrr_calculator`.

    Flow Graphs & Cyclomatic Complexity:
    -------------------------------------------------------------------------
    overs_to_decimal(overs_str):
      Control Flow:
        (1) Entry -> check isinstance
        (2) if not clean_str -> return 0.0 (3)
        (4) if "." in clean_str -> _parse_fractional_overs (5) else _parse_whole_overs (6)
      N = 6, E = 7 => V(G) = 7 - 6 + 2 = 3 (<= 5)

    _validate_fractional_parts(overs, balls, raw_str):
      Control Flow: (1) if overs < 0 -> raise else if not (0 <= balls <= 5) -> raise
      N = 4, E = 4 => V(G) = 2 (<= 5)

    decimal_to_overs(overs_decimal):
      Control Flow: (1) if overs_decimal <= 0 -> return "0.0" else convert and return
      N = 4, E = 4 => V(G) = 2 (<= 5)

    balls_to_decimal_overs(balls):
      Control Flow: (1) if balls <= 0 -> return 0.0 else round(balls / 6.0, 6)
      N = 4, E = 4 => V(G) = 2 (<= 5)

    calculate_nrr(runs_scored, overs_faced, runs_conceded, overs_bowled, is_all_out, max_overs):
      Control Flow:
        (1) _calculate_effective_overs
        (2) if effective_overs_faced <= 0 and overs_bowled <= 0 -> return 0.0
        (3) compute run_rate_for and run_rate_against
        (4) return round(diff, 3)
      N = 6, E = 8 => V(G) = 8 - 6 + 2 = 4 (<= 5)

    calculate_cumulative_nrr(match_entries):
      Control Flow:
        (1) if not match_entries -> return 0.0
        (2) aggregate entries -> _compute_run_rates -> return
      N = 4, E = 4 => V(G) = 2 (<= 5)
    -------------------------------------------------------------------------
    """

    def test_overs_to_decimal_valid_fractional(self):
        """Path 1: valid fractional notation '45.3' -> 45.5."""
        assert overs_to_decimal("45.3") == 45.5
        assert overs_to_decimal("19.4") == round(19 + 4 / 6.0, 6)

    def test_overs_to_decimal_valid_integer(self):
        """Path 2: valid integer string '20' -> 20.0."""
        assert overs_to_decimal("20") == 20.0
        assert overs_to_decimal("0") == 0.0

    def test_overs_to_decimal_empty_or_whitespace(self):
        """Path 3: empty or whitespace overs string returns 0.0."""
        assert overs_to_decimal("") == 0.0
        assert overs_to_decimal("   ") == 0.0

    def test_overs_to_decimal_non_string_input(self):
        """Path 4: non-string input (int/float) successfully coerced."""
        assert overs_to_decimal(20) == 20.0
        assert overs_to_decimal(19.3) == 19.5

    def test_overs_to_decimal_invalid_balls_exceeds_five(self):
        """Path 5: balls >= 6 in fractional notation raises ValueError."""
        with pytest.raises(ValueError) as exc:
            overs_to_decimal("19.6")
        assert "Balls component must be between 0 and 5" in str(exc.value)

    def test_overs_to_decimal_negative_or_malformed(self):
        """Path 6: negative overs or malformed components raise ValueError."""
        with pytest.raises(ValueError):
            overs_to_decimal("-1.2")
        with pytest.raises(ValueError):
            overs_to_decimal("-10")
        with pytest.raises(ValueError):
            overs_to_decimal("20.1.2")
        with pytest.raises(ValueError):
            overs_to_decimal("twenty.two")

    def test_decimal_to_overs_conversion(self):
        """Path 7: decimal overs back to cricket notation string."""
        assert decimal_to_overs(45.5) == "45.3"
        assert decimal_to_overs(0.0) == "0.0"
        assert decimal_to_overs(-2.5) == "0.0"

    def test_balls_to_decimal_overs_conversion(self):
        """Path 8: integer legal balls to decimal overs float."""
        assert balls_to_decimal_overs(118) == round(118 / 6.0, 6)
        assert balls_to_decimal_overs(0) == 0.0
        assert balls_to_decimal_overs(-10) == 0.0

    def test_calculate_nrr_standard_positive_and_negative(self):
        """Path 9: calculate standard match NRR with both positive and negative results."""
        # 180 runs in 20 overs vs 160 in 20 overs: (180/20) - (160/20) = 9.0 - 8.0 = +1.0
        nrr_win = calculate_nrr(runs_scored=180, overs_faced=20.0, runs_conceded=160, overs_bowled=20.0)
        assert nrr_win == 1.0

        # 140 in 20 overs vs 160 in 20 overs: 7.0 - 8.0 = -1.0
        nrr_loss = calculate_nrr(runs_scored=140, overs_faced=20.0, runs_conceded=160, overs_bowled=20.0)
        assert nrr_loss == -1.0

    def test_calculate_nrr_all_out_quota_cap_and_zero_division(self):
        """Path 10: all-out capped at max_overs, and zero division guard."""
        # Team scored 100 in 15.0 overs but bowled all out (max_overs=20): effective overs = 20.0
        nrr_all_out = calculate_nrr(
            runs_scored=100,
            overs_faced=15.0,
            runs_conceded=101,
            overs_bowled=12.0,
            is_all_out=True,
            max_overs=20.0,
        )
        # (100 / 20.0) - (101 / 12.0) = 5.0 - 8.416667 = -3.417
        assert nrr_all_out == -3.417

        # Zero division guard when no play has occurred
        nrr_zero = calculate_nrr(0, 0.0, 0, 0.0)
        assert nrr_zero == 0.0

    def test_calculate_cumulative_nrr_multi_match_and_empty(self):
        """Path 11: cumulative multi-match tournament NRR calculation & empty input."""
        assert calculate_cumulative_nrr([]) == 0.0

        matches = [
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
                runs_scored=120,
                overs_faced=18.0,
                is_all_out=True,  # bowled out in 18th over -> counted as full 20 overs
                max_overs=20.0,
                runs_conceded=121,
                overs_bowled=16.0,
                opponent_all_out=False,
            ),
        ]
        # Total Runs For: 160 + 120 = 280; Overs For: 20 + 20 = 40.0 -> RR For = 7.0
        # Total Runs Against: 140 + 121 = 261; Overs Against: 20 + 16 = 36.0 -> RR Against = 7.25
        # Cumulative NRR = 7.0 - 7.25 = -0.250
        cum_nrr = calculate_cumulative_nrr(matches)
        assert cum_nrr == -0.25


# ============================================================================
# MODULE 3: PLAYER STATISTICS ENGINE (11 Tests)
# ============================================================================

class TestStatsEngineBasisPaths:
    """Basis path test suite for `app.services.stats_engine`.

    Flow Graphs & Cyclomatic Complexity:
    -------------------------------------------------------------------------
    batting_average(runs, dismissals):
      Control Flow:
        (1) Entry -> if dismissals > 0 -> (2) return runs / dismissals
        (3) if runs > 0 -> (4) return float(runs) else (5) return 0.0
      N = 5, E = 6 => V(G) = 6 - 5 + 2 = 3 (<= 5)

    batting_strike_rate(runs, balls_faced):
      Control Flow: (1) if balls_faced > 0 -> (2) compute SR else (3) return 0.0
      N = 4, E = 4 => V(G) = 2 (<= 5)

    bowling_economy(runs_conceded, balls_bowled):
      Control Flow: (1) if balls_bowled > 0 -> (2) compute econ else (3) return 0.0
      N = 4, E = 4 => V(G) = 2 (<= 5)

    bowling_average(runs_conceded, wickets):
      Control Flow: (1) if wickets > 0 -> (2) compute avg else (3) return 0.0
      N = 4, E = 4 => V(G) = 2 (<= 5)

    count_milestones(scores):
      Control Flow: (1) count fifties in [50, 99] -> (2) count hundreds >= 100 -> (3) return
      N = 5, E = 6 => V(G) = 3 (<= 5)

    compute_career_metrics(...):
      Control Flow: (1) Entry -> assemble metric functions -> (2) return dataclass
      N = 2, E = 1 => V(G) = 1 (<= 5)
    -------------------------------------------------------------------------
    """

    def test_batting_average_with_dismissals(self):
        """Path 1: batting average with positive dismissals count."""
        assert batting_average(runs=450, dismissals=10) == 45.0
        assert batting_average(runs=100, dismissals=3) == 33.33

    def test_batting_average_not_out_with_runs(self):
        """Path 2: batting average undefeated (0 dismissals) with runs > 0."""
        assert batting_average(runs=85, dismissals=0) == 85.0

    def test_batting_average_not_out_zero_runs(self):
        """Path 3: batting average with 0 runs and 0 dismissals returns 0.0."""
        assert batting_average(runs=0, dismissals=0) == 0.0

    def test_batting_strike_rate_with_balls(self):
        """Path 4: batting strike rate calculation with balls_faced > 0."""
        assert batting_strike_rate(runs=50, balls_faced=40) == 125.0
        assert batting_strike_rate(runs=75, balls_faced=50) == 150.0

    def test_batting_strike_rate_zero_balls_guard(self):
        """Path 5: batting strike rate zero division protection (balls_faced == 0)."""
        assert batting_strike_rate(runs=0, balls_faced=0) == 0.0
        assert batting_strike_rate(runs=10, balls_faced=0) == 0.0

    def test_bowling_economy_with_balls(self):
        """Path 6: bowling economy rate with balls_bowled > 0."""
        # 30 runs in 36 balls (6.0 overs) = 5.0
        assert bowling_economy(runs_conceded=30, balls_bowled=36) == 5.0
        # 24 runs in 24 balls (4.0 overs) = 6.0
        assert bowling_economy(runs_conceded=24, balls_bowled=24) == 6.0

    def test_bowling_economy_zero_balls_guard(self):
        """Path 7: bowling economy zero division protection (balls_bowled == 0)."""
        assert bowling_economy(runs_conceded=0, balls_bowled=0) == 0.0
        assert bowling_economy(runs_conceded=15, balls_bowled=0) == 0.0

    def test_bowling_average_with_wickets(self):
        """Path 8: bowling average with wickets > 0."""
        assert bowling_average(runs_conceded=60, wickets=3) == 20.0
        assert bowling_average(runs_conceded=25, wickets=2) == 12.5

    def test_bowling_average_zero_wickets_guard(self):
        """Path 9: bowling average zero division protection (wickets == 0)."""
        assert bowling_average(runs_conceded=40, wickets=0) == 0.0
        assert bowling_average(runs_conceded=0, wickets=0) == 0.0

    def test_count_milestones_fifties_and_hundreds(self):
        """Path 10: count milestone fifties (50-99) and centuries (>=100)."""
        scores = [12, 49, 50, 78, 99, 100, 142]
        fifties, hundreds = count_milestones(scores)
        assert fifties == 3  # 50, 78, 99
        assert hundreds == 2  # 100, 142

    def test_compute_career_metrics_aggregation(self):
        """Path 11: comprehensive career metrics pure function integration."""
        metrics = compute_career_metrics(
            matches_played=10,
            runs=350,
            balls_faced=280,
            dismissals=7,
            wickets=12,
            runs_conceded=240,
            balls_bowled=180,
            innings_scores=[45, 60, 110, 35, 100],
        )
        assert isinstance(metrics, PlayerCareerMetrics)
        assert metrics.matches_played == 10
        assert metrics.runs == 350
        assert metrics.batting_average == 50.0  # 350 / 7
        assert metrics.strike_rate == 125.0  # (350 / 280) * 100
        assert metrics.wickets == 12
        assert metrics.bowling_average == 20.0  # 240 / 12
        assert metrics.economy == 8.0  # 240 / (180 / 6) = 240 / 30 = 8.0
        assert metrics.overs_display == "30.0"
        assert metrics.fifties == 1
        assert metrics.hundreds == 2


# ============================================================================
# MODULE 4: WEBSOCKET CONNECTION MANAGER (8 Tests)
# ============================================================================

class TestConnectionManagerBasisPaths:
    """Basis path test suite for `app.ws.connection_manager.ConnectionManager`.

    Flow Graphs & Cyclomatic Complexity:
    -------------------------------------------------------------------------
    connect(match_id, websocket):
      Control Flow:
        (1) try get_running_loop
        (2) await websocket.accept()
        (3) if match_id not in active_connections -> init list
        (4) if websocket not in active_connections[match_id] -> append
      N = 6, E = 8 => V(G) = 8 - 6 + 2 = 4 (<= 5)

    disconnect(match_id, websocket):
      Control Flow:
        (1) if match_id in active_connections:
        (2)   if websocket in list -> remove
        (3)   if not list -> delete room key
      N = 6, E = 8 => V(G) = 8 - 6 + 2 = 4 (<= 5)

    broadcast(match_id, message):
      Control Flow:
        (1) if match_id in active_connections:
        (2)   for connection in list:
        (3)     try send_json except dead_connections.append
        (4)   for dead in dead_connections -> disconnect
      N = 7, E = 10 => V(G) = 10 - 7 + 2 = 5 (<= 5)

    broadcast_match(match_id, message):
      Control Flow: (1) Entry -> await broadcast() -> (2) Exit
      N = 2, E = 1 => V(G) = 1 (<= 5)

    _ping_room(room_id):
      Control Flow: (1) for conn in room: try send_text except dead -> (2) purge dead
      N = 6, E = 8 => V(G) = 4 (<= 5)

    ping_all(match_id):
      Control Flow: (1) if match_id in dict -> _ping_room else for all rooms _ping_room
      N = 5, E = 6 => V(G) = 3 (<= 5)
    -------------------------------------------------------------------------
    """

    @pytest.mark.anyio
    async def test_connect_new_room_registers_websocket(self):
        """Path 1: connect socket to new match room."""
        cm = ConnectionManager()
        mock_ws = AsyncMock(spec=WebSocket)
        match_id = "match-101"

        await cm.connect(match_id, mock_ws)
        mock_ws.accept.assert_awaited_once()
        assert match_id in cm.active_connections
        assert mock_ws in cm.active_connections[match_id]

    @pytest.mark.anyio
    async def test_connect_existing_room_appends_socket(self):
        """Path 2: connect multiple sockets to the same match room without duplication."""
        cm = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        match_id = "match-102"

        await cm.connect(match_id, ws1)
        await cm.connect(match_id, ws2)
        await cm.connect(match_id, ws1)  # redundant add guard

        assert len(cm.active_connections[match_id]) == 2
        assert ws1 in cm.active_connections[match_id]
        assert ws2 in cm.active_connections[match_id]

    def test_disconnect_removes_socket_preserves_room(self):
        """Path 3: disconnect one socket while other sockets remain in room."""
        cm = ConnectionManager()
        ws1 = MagicMock(spec=WebSocket)
        ws2 = MagicMock(spec=WebSocket)
        match_id = "match-103"
        cm.active_connections[match_id] = [ws1, ws2]

        cm.disconnect(match_id, ws1)
        assert match_id in cm.active_connections
        assert ws1 not in cm.active_connections[match_id]
        assert ws2 in cm.active_connections[match_id]

    def test_disconnect_last_socket_cleans_up_room(self):
        """Path 4: disconnecting final socket in room purges the room key."""
        cm = ConnectionManager()
        ws1 = MagicMock(spec=WebSocket)
        match_id = "match-104"
        cm.active_connections[match_id] = [ws1]

        cm.disconnect(match_id, ws1)
        assert match_id not in cm.active_connections

    @pytest.mark.anyio
    async def test_broadcast_sends_to_all_connected_sockets(self):
        """Path 5: broadcast message delivers to every active client in the room."""
        cm = ConnectionManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        match_id = "match-105"
        cm.active_connections[match_id] = [ws1, ws2]

        msg = {"type": "BALL_SCORED", "score": "15/0"}
        await cm.broadcast(match_id, msg)

        ws1.send_json.assert_awaited_once_with(msg)
        ws2.send_json.assert_awaited_once_with(msg)

    @pytest.mark.anyio
    async def test_broadcast_handles_dead_socket_exception(self):
        """Path 6: broadcast cleans up dead sockets when send_json fails."""
        cm = ConnectionManager()
        good_ws = AsyncMock(spec=WebSocket)
        dead_ws = AsyncMock(spec=WebSocket)
        dead_ws.send_json.side_effect = RuntimeError("Socket disconnected")

        match_id = "match-106"
        cm.active_connections[match_id] = [good_ws, dead_ws]

        await cm.broadcast(match_id, {"event": "delivery"})
        good_ws.send_json.assert_awaited_once()
        assert dead_ws not in cm.active_connections.get(match_id, [])
        assert good_ws in cm.active_connections[match_id]

    @pytest.mark.anyio
    async def test_broadcast_match_alias(self):
        """Path 7: broadcast_match alias delegates to broadcast."""
        cm = ConnectionManager()
        ws = AsyncMock(spec=WebSocket)
        match_id = "match-107"
        cm.active_connections[match_id] = [ws]

        await cm.broadcast_match(match_id, {"ping": "pong"})
        ws.send_json.assert_awaited_once_with({"ping": "pong"})

    @pytest.mark.anyio
    async def test_ping_all_active_rooms_and_specific_room(self):
        """Path 8: ping_all delivers heartbeats and prunes broken sockets."""
        cm = ConnectionManager()
        alive_ws = AsyncMock(spec=WebSocket)
        dead_ws = AsyncMock(spec=WebSocket)
        dead_ws.send_text.side_effect = Exception("Closed connection")

        cm.active_connections["match-108A"] = [alive_ws, dead_ws]
        cm.active_connections["match-108B"] = [alive_ws]

        # 1. Ping specific match
        await cm.ping_all("match-108A")
        assert dead_ws not in cm.active_connections["match-108A"]
        assert alive_ws in cm.active_connections["match-108A"]

        # 2. Ping all matches
        await cm.ping_all()
        alive_ws.send_text.assert_awaited()


# ============================================================================
# MODULE 5: PURE CRICKET SCORING LOGIC (41 Tests)
# ============================================================================

class TestScoringLogicBasisPaths:
    """Basis path test suite for `app.services.scoring_engine`.

    Flow Graphs & Cyclomatic Complexity:
    -------------------------------------------------------------------------
    overs_display(balls):
      Control Flow: (1) if balls < 0 -> return "0.0" else return f"{overs}.{remainder}"
      N = 4, E = 4 => V(G) = 2 (<= 5)

    current_run_rate(total_runs, legal_balls):
      Control Flow: (1) if legal_balls <= 0 -> return 0.0 else return round(runs / overs, 2)
      N = 4, E = 4 => V(G) = 2 (<= 5)

    required_run_rate(runs_needed, balls_remaining):
      Control Flow:
        (1) if runs_needed <= 0 -> return 0.0
        (2) if balls_remaining <= 0 -> return None
        (3) return round(runs / overs, 2)
      N = 5, E = 6 => V(G) = 3 (<= 5)

    get_ball_display_token(ball):
      Control Flow: Dispatches to sub-formatters for wicket, wide, no_ball, bye, leg_bye, runs
      All sub-formatters have V(G) <= 2, dispatcher V(G) = 5 (<= 5)

    _process_delivery_outcome(state, striker, bowler, ball):
      Control Flow: extras routing via modular helpers (_process_wide, _process_no_ball, etc.)
      All sub-helpers have V(G) <= 4, dispatcher V(G) <= 5 (<= 5)

    _process_wicket(state, bowler, ball, ...):
      Control Flow: (1) if not is_wicket -> return else record dismissal & replace batter
      Sub-helpers V(G) <= 4, dispatcher V(G) <= 4 (<= 5)

    _compute_strike_rotation(striker_id, non_striker_id, rotates_on_runs, over_ended):
      Control Flow: compute swaps -> if odd return swapped else original
      N = 5, E = 6 => V(G) = 3 (<= 5)

    _check_innings_completion(state, target_chased):
      Control Flow: check wickets >= 10, overs reached, or target chased
      N = 5, E = 6 => V(G) = 3 (<= 5)

    apply_ball(state, ball):
      Control Flow: checks is_completed -> processes pure transforms -> returns new state
      N = 6, E = 8 => V(G) = 4 (<= 5)

    replay(events, initial_state, ...):
      Control Flow: (1) initialize state -> (2) loop apply_ball -> (3) return
      N = 5, E = 6 => V(G) = 3 (<= 5)
    -------------------------------------------------------------------------
    """

    # Helper fixtures & creators
    def _create_fresh_innings(self, innings_no=1, target_runs=None, max_overs=20):
        return InningsState(
            innings_no=innings_no,
            max_overs=max_overs,
            target_runs=target_runs,
            striker_id="p_striker",
            non_striker_id="p_non_striker",
        )

    # 1. overs_display (Paths 1-4)
    def test_overs_display_zero_balls(self):
        """Path 1: balls == 0 -> '0.0'."""
        assert overs_display(0) == "0.0"

    def test_overs_display_negative_balls(self):
        """Path 2: balls < 0 -> '0.0'."""
        assert overs_display(-6) == "0.0"

    def test_overs_display_partial_over(self):
        """Path 3: mid-over fractional calculation (e.g. 15 balls -> '2.3')."""
        assert overs_display(15) == "2.3"
        assert overs_display(1) == "0.1"

    def test_overs_display_completed_overs(self):
        """Path 4: full over boundaries (e.g. 120 balls -> '20.0')."""
        assert overs_display(120) == "20.0"
        assert overs_display(6) == "1.0"

    # 2. current_run_rate (Paths 5-6)
    def test_current_run_rate_zero_balls_guard(self):
        """Path 5: CRR division guard when legal_balls == 0 returns 0.0."""
        assert current_run_rate(total_runs=0, legal_balls=0) == 0.0
        assert current_run_rate(total_runs=10, legal_balls=0) == 0.0

    def test_current_run_rate_normal(self):
        """Path 6: CRR standard calculation (75 runs in 60 balls = 7.50)."""
        assert current_run_rate(total_runs=75, legal_balls=60) == 7.5

    # 3. required_run_rate (Paths 7-9)
    def test_required_run_rate_target_reached(self):
        """Path 7: RRR when runs_needed <= 0 returns 0.0."""
        assert required_run_rate(runs_needed=0, balls_remaining=20) == 0.0
        assert required_run_rate(runs_needed=-5, balls_remaining=10) == 0.0

    def test_required_run_rate_no_balls_remaining(self):
        """Path 8: RRR when balls_remaining <= 0 and runs still needed returns None."""
        assert required_run_rate(runs_needed=10, balls_remaining=0) is None
        assert required_run_rate(runs_needed=5, balls_remaining=-2) is None

    def test_required_run_rate_normal(self):
        """Path 9: RRR standard calculation (36 runs needed in 24 balls = 9.00)."""
        assert required_run_rate(runs_needed=36, balls_remaining=24) == 9.0

    # 4. get_ball_display_token (Paths 10-19)
    def test_token_dot_ball(self):
        """Path 10: dot ball token is '0'."""
        ball = BallInput(striker_id="p1", non_striker_id="p2", bowler_id="b1", runs_batter=0)
        assert get_ball_display_token(ball) == "0"

    def test_token_runs_off_bat(self):
        """Path 11: runs off bat tokens ('1', '4', '6')."""
        assert get_ball_display_token(BallInput("p1", "p2", "b1", runs_batter=1)) == "1"
        assert get_ball_display_token(BallInput("p1", "p2", "b1", runs_batter=4)) == "4"
        assert get_ball_display_token(BallInput("p1", "p2", "b1", runs_batter=6)) == "6"

    def test_token_standard_wicket(self):
        """Path 12: wicket token is 'W'."""
        ball = BallInput("p1", "p2", "b1", is_wicket=True, wicket_type="bowled")
        assert get_ball_display_token(ball) == "W"

    def test_token_wicket_on_no_ball(self):
        """Path 13: wicket off a no-ball (run out) is 'W+Nb'."""
        ball = BallInput("p1", "p2", "b1", extras_type="no_ball", is_wicket=True, wicket_type="run_out")
        assert get_ball_display_token(ball) == "W+Nb"

    def test_token_single_wide(self):
        """Path 14: single wide token is 'Wd'."""
        ball = BallInput("p1", "p2", "b1", extras_type="wide", extras_runs=1)
        assert get_ball_display_token(ball) == "Wd"

    def test_token_multi_run_wide(self):
        """Path 15: multi-run wide token (e.g. 3 wides -> '3Wd')."""
        ball = BallInput("p1", "p2", "b1", extras_type="wide", extras_runs=3)
        assert get_ball_display_token(ball) == "3Wd"

    def test_token_single_no_ball(self):
        """Path 16: single no ball token is 'Nb'."""
        ball = BallInput("p1", "p2", "b1", extras_type="no_ball", extras_runs=1, runs_batter=0)
        assert get_ball_display_token(ball) == "Nb"

    def test_token_no_ball_with_bat_runs(self):
        """Path 17: no-ball with boundary (4 + 1 nb = '5Nb')."""
        ball = BallInput("p1", "p2", "b1", extras_type="no_ball", extras_runs=1, runs_batter=4)
        assert get_ball_display_token(ball) == "5Nb"

    def test_token_bye(self):
        """Path 18: bye tokens ('1B', '2B')."""
        ball1 = BallInput("p1", "p2", "b1", extras_type="bye", extras_runs=1)
        ball2 = BallInput("p1", "p2", "b1", extras_type="bye", extras_runs=2)
        assert get_ball_display_token(ball1) == "1B"
        assert get_ball_display_token(ball2) == "2B"

    def test_token_leg_bye(self):
        """Path 19: leg bye token ('1Lb', '4Lb')."""
        ball = BallInput("p1", "p2", "b1", extras_type="leg_bye", extras_runs=1)
        assert get_ball_display_token(ball) == "1Lb"

    # 5. apply_ball: deliveries, boundaries & extras (Paths 20-31)
    def test_apply_ball_completed_innings_guard(self):
        """Path 20: applying delivery to completed innings raises ValueError."""
        state = self._create_fresh_innings()
        state.is_completed = True
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", runs_batter=1)
        with pytest.raises(ValueError) as exc:
            apply_ball(state, ball)
        assert "Cannot apply delivery to an already completed innings" in str(exc.value)

    def test_apply_ball_dot_ball(self):
        """Path 21: dot ball updates legal ball, balls faced, and bowler dots."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", runs_batter=0)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 0
        assert new_state.legal_balls == 1
        assert new_state.batters["p_striker"].balls_faced == 1
        assert new_state.batters["p_striker"].runs == 0
        assert new_state.bowlers["p_bowler"].dots == 1
        assert new_state.striker_id == "p_striker"  # strike unchanged

    def test_apply_ball_single_rotates_strike(self):
        """Path 22: odd runs off bat rotates strike to non-striker."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", runs_batter=1)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 1
        assert new_state.legal_balls == 1
        assert new_state.striker_id == "p_non_striker"
        assert new_state.non_striker_id == "p_striker"

    def test_apply_ball_two_runs_keeps_strike(self):
        """Path 23: even runs off bat keeps strike with current striker."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", runs_batter=2)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 2
        assert new_state.striker_id == "p_striker"

    def test_apply_ball_boundary_four(self):
        """Path 24: boundary four increments striker fours and bowler runs conceded."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", runs_batter=4)
        new_state = apply_ball(state, ball)

        assert new_state.batters["p_striker"].fours == 1
        assert new_state.batters["p_striker"].runs == 4
        assert new_state.bowlers["p_bowler"].runs_conceded == 4
        assert new_state.striker_id == "p_striker"

    def test_apply_ball_boundary_six(self):
        """Path 25: boundary six increments striker sixes."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", runs_batter=6)
        new_state = apply_ball(state, ball)

        assert new_state.batters["p_striker"].sixes == 1
        assert new_state.batters["p_striker"].runs == 6
        assert new_state.striker_id == "p_striker"

    def test_apply_ball_wide_illegal_extra(self):
        """Path 26: wide is illegal (legal_balls not incremented) and counts in extras."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", extras_type="wide", extras_runs=1)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 1
        assert new_state.legal_balls == 0  # not legal
        assert new_state.total_deliveries == 1
        assert new_state.extras.wides == 1
        assert new_state.bowlers["p_bowler"].wides == 1
        assert new_state.batters["p_striker"].balls_faced == 0  # wide does not face delivery

    def test_apply_ball_multi_run_wide(self):
        """Path 27: multi-run wide adds extra runs to total."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", extras_type="wide", extras_runs=3)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 3
        assert new_state.extras.wides == 3
        assert new_state.bowlers["p_bowler"].runs_conceded == 3

    def test_apply_ball_no_ball_single(self):
        """Path 28: no-ball with 1 run off bat: total 2 runs, strike rotates."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", extras_type="no_ball", extras_runs=1, runs_batter=1)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 2
        assert new_state.legal_balls == 0
        assert new_state.batters["p_striker"].runs == 1
        assert new_state.batters["p_striker"].balls_faced == 1
        assert new_state.bowlers["p_bowler"].no_balls == 1
        assert new_state.bowlers["p_bowler"].runs_conceded == 2
        assert new_state.striker_id == "p_non_striker"

    def test_apply_ball_no_ball_boundary_four(self):
        """Path 29: no-ball with boundary four: 5 total runs, striker credited 4 runs & 1 four."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", extras_type="no_ball", extras_runs=1, runs_batter=4)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 5
        assert new_state.batters["p_striker"].runs == 4
        assert new_state.batters["p_striker"].fours == 1
        assert new_state.extras.no_balls == 1
        assert new_state.striker_id == "p_striker"

    def test_apply_ball_bye_delivery(self):
        """Path 30: byes are legal balls, bowler not charged with conceded runs."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", extras_type="bye", extras_runs=1)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 1
        assert new_state.legal_balls == 1
        assert new_state.extras.byes == 1
        assert new_state.bowlers["p_bowler"].runs_conceded == 0  # byes not against bowler
        assert new_state.striker_id == "p_non_striker"  # 1 bye rotates strike

    def test_apply_ball_leg_bye_delivery(self):
        """Path 31: leg-byes are legal balls, bowler not charged."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", extras_type="leg_bye", extras_runs=2)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 2
        assert new_state.legal_balls == 1
        assert new_state.extras.leg_byes == 2
        assert new_state.bowlers["p_bowler"].runs_conceded == 0
        assert new_state.striker_id == "p_striker"  # 2 leg byes keeps strike

    def test_apply_ball_penalty_runs(self):
        """Path 32: penalty delivery adds 5 runs directly to extras without legal ball."""
        state = self._create_fresh_innings()
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", extras_type="penalty", extras_runs=5)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 5
        assert new_state.legal_balls == 0
        assert new_state.extras.penalty == 5

    # 6. Strike Rotation Mechanics (Paths 33-34)
    def test_apply_ball_over_end_strike_rotation(self):
        """Path 33: 6th legal delivery switches striker at over conclusion."""
        state = self._create_fresh_innings()
        state.legal_balls = 5  # ball 5 of over
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", runs_batter=0)
        new_state = apply_ball(state, ball)

        assert new_state.legal_balls == 6
        assert new_state.striker_id == "p_non_striker"  # strike swapped at end of over

    def test_apply_ball_odd_run_on_over_end_cancellation(self):
        """Path 34: odd run on 6th legal delivery cancels swap -> strike remains with batter."""
        state = self._create_fresh_innings()
        state.legal_balls = 5
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", runs_batter=1)
        new_state = apply_ball(state, ball)

        assert new_state.legal_balls == 6
        # Run swap + Over end swap = 2 swaps -> cancels out!
        assert new_state.striker_id == "p_striker"

    # 7. Wicket Mechanics (Paths 35-38)
    def test_apply_ball_wicket_bowled(self):
        """Path 35: bowled dismissal credits bowler and substitutes striker with next_batter."""
        state = self._create_fresh_innings()
        ball = BallInput(
            "p_striker",
            "p_non_striker",
            "p_bowler",
            is_wicket=True,
            wicket_type="bowled",
            dismissed_player_id="p_striker",
            next_batter_id="p_batter_3",
        )
        new_state = apply_ball(state, ball)

        assert new_state.wickets == 1
        assert new_state.batters["p_striker"].is_out is True
        assert new_state.batters["p_striker"].dismissal_type == "bowled"
        assert new_state.bowlers["p_bowler"].wickets == 1
        assert new_state.striker_id == "p_batter_3"
        assert "p_batter_3" in new_state.batters

    def test_apply_ball_wicket_run_out_non_striker(self):
        """Path 36: run out of non-striker does not credit bowler and replaces non-striker."""
        state = self._create_fresh_innings()
        ball = BallInput(
            "p_striker",
            "p_non_striker",
            "p_bowler",
            is_wicket=True,
            wicket_type="run_out",
            dismissed_player_id="p_non_striker",
            next_batter_id="p_batter_3",
        )
        new_state = apply_ball(state, ball)

        assert new_state.wickets == 1
        assert new_state.bowlers["p_bowler"].wickets == 0  # run out not credited to bowler
        assert new_state.batters["p_non_striker"].is_out is True
        assert new_state.non_striker_id == "p_batter_3"
        assert new_state.striker_id == "p_striker"

    def test_apply_ball_wicket_missing_next_batter_raises(self):
        """Path 37: wicket falling without next_batter_id raises ValueError when match ongoing."""
        state = self._create_fresh_innings()
        ball = BallInput(
            "p_striker",
            "p_non_striker",
            "p_bowler",
            is_wicket=True,
            wicket_type="caught",
            dismissed_player_id="p_striker",
            next_batter_id=None,  # missing next batter
        )
        with pytest.raises(ValueError) as exc:
            apply_ball(state, ball)
        assert "next_batter_id is required" in str(exc.value)

    def test_apply_ball_tenth_wicket_all_out(self):
        """Path 38: 10th wicket triggers all-out completion without needing next_batter."""
        state = self._create_fresh_innings()
        state.wickets = 9  # 9 down
        ball = BallInput(
            "p_striker",
            "p_non_striker",
            "p_bowler",
            is_wicket=True,
            wicket_type="lbw",
            dismissed_player_id="p_striker",
            next_batter_id=None,  # 10th wicket needs no replacement
        )
        new_state = apply_ball(state, ball)

        assert new_state.wickets == 10
        assert new_state.is_completed is True

    # 8. Innings Completion (Paths 39-40)
    def test_apply_ball_max_overs_quota_reached(self):
        """Path 39: reaching max overs quota (e.g. 120 legal balls) completes innings."""
        state = self._create_fresh_innings(max_overs=20)
        state.legal_balls = 119
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", runs_batter=1)
        new_state = apply_ball(state, ball)

        assert new_state.legal_balls == 120
        assert new_state.is_completed is True

    def test_apply_ball_target_chased_in_second_innings(self):
        """Path 40: successfully chasing target in 2nd innings completes innings immediately."""
        state = self._create_fresh_innings(innings_no=2, target_runs=150)
        state.total_runs = 148
        # Boundary 4 brings score to 152 >= 150
        ball = BallInput("p_striker", "p_non_striker", "p_bowler", runs_batter=4)
        new_state = apply_ball(state, ball)

        assert new_state.total_runs == 152
        assert new_state.is_completed is True

    # 9. Replay Determinism (Path 41)
    def test_replay_deterministic_reconstruction(self):
        """Path 41: replay accurately and deterministically reconstructs entire innings."""
        events = [
            BallInput("p1", "p2", "b1", runs_batter=1),
            BallInput("p2", "p1", "b1", runs_batter=4),
            BallInput("p2", "p1", "b1", extras_type="wide", extras_runs=1),
            BallInput("p2", "p1", "b1", runs_batter=2),
            BallInput("p2", "p1", "b1", runs_batter=0),
            BallInput("p2", "p1", "b1", runs_batter=1),
        ]
        replayed_state = replay(events=events, max_overs=20, striker_id="p1", non_striker_id="p2")

        # 1 + 4 + 1 + 2 + 0 + 1 = 9 runs
        assert replayed_state.total_runs == 9
        assert replayed_state.legal_balls == 5
        assert replayed_state.total_deliveries == 6
        assert len(replayed_state.recent_balls) == 6
        assert replayed_state.recent_balls[-1] == "1"
