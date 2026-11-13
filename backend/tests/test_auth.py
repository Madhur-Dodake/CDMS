from datetime import timedelta
import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_access_token, get_password_hash, verify_password
from app.models.user import UserRole


# 1. Password hashing & verification
def test_password_hashing_unit() -> None:
    """Case 1: Verify password hashing and verification logic."""
    plain = "secret123"
    hashed = get_password_hash(plain)
    assert verify_password(plain, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
    assert verify_password("", hashed) is False


# 2. Valid admin login
def test_valid_admin_login(client: TestClient) -> None:
    """Case 2: Test successful login with admin credentials and role."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@cdms.com",
            "password": "admin123",
            "role": "admin",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    assert data["email"] == "admin@cdms.com"


# 3. Valid scorer login
def test_valid_scorer_login(client: TestClient) -> None:
    """Case 3: Test successful login with scorer credentials and role."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "scorer1@cdms.com",
            "password": "scorer123",
            "role": "scorer",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "scorer"


# 4. Valid viewer login
def test_valid_viewer_login(client: TestClient) -> None:
    """Case 4: Test successful login with viewer credentials and role."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "viewer@cdms.com",
            "password": "viewer123",
            "role": "viewer",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "viewer"


# 5. Wrong password
def test_login_wrong_password(client: TestClient) -> None:
    """Case 5: Test login failure with incorrect password returns 401."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@cdms.com",
            "password": "incorrect_password",
            "role": "admin",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


# 6. Unknown email
def test_login_unknown_email(client: TestClient) -> None:
    """Case 6: Test login failure with non-existent email returns 401."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@cdms.com",
            "password": "admin123",
            "role": "admin",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


# 7. Wrong role selection
def test_login_wrong_role_selection(client: TestClient) -> None:
    """Case 7: Test login failure when selected role does not match account returns 403."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@cdms.com",
            "password": "admin123",
            "role": "scorer",  # User is an admin
        },
    )
    assert response.status_code == 403
    assert "Invalid role" in response.json()["detail"]


# 8. Malformed email validation
def test_login_invalid_email_format(client: TestClient) -> None:
    """Case 8: Test login with malformed email string fails validation (422)."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "not-a-valid-email",
            "password": "admin123",
            "role": "admin",
        },
    )
    assert response.status_code == 422


# 9. No token provided
def test_no_token_returns_401(client: TestClient) -> None:
    """Case 9: Test accessing protected route without Authorization header returns 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


# 10. Expired token
def test_expired_token_returns_401(client: TestClient) -> None:
    """Case 10: Test accessing protected route with expired token returns 401."""
    expired_token = create_access_token(
        data={"user_id": str(uuid.uuid4()), "role": "admin"},
        expires_delta=timedelta(seconds=-10),
    )
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"


# 11. Tampered token
def test_tampered_token_returns_401(client: TestClient) -> None:
    """Case 11: Test accessing protected route with tampered token returns 401."""
    valid_token = create_access_token(
        data={"user_id": str(uuid.uuid4()), "role": "admin"},
    )
    tampered_token = valid_token[:-6] + "xxxxxx"
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


# 12. Malformed Authorization header
def test_malformed_token_header_format(client: TestClient) -> None:
    """Case 12: Test accessing protected route with invalid auth scheme returns 401."""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert response.status_code == 401


# 13. Current user profile endpoint
def test_get_current_user_profile(client: TestClient) -> None:
    """Case 13: Test GET /api/auth/me returns authenticated user details."""
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "admin@cdms.com",
            "password": "admin123",
            "role": "admin",
        },
    )
    token = login_res.json()["access_token"]
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@cdms.com"
    assert data["role"] == "admin"
    assert "user_id" in data


# 14. Admin accessing admin-only route
def test_admin_hitting_admin_only_route_succeeds(client: TestClient) -> None:
    """Case 14: Test admin user successfully accesses admin-only route."""
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "admin@cdms.com",
            "password": "admin123",
            "role": "admin",
        },
    )
    token = login_res.json()["access_token"]
    response = client.get(
        "/api/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# 15. Scorer accessing admin-only route
def test_scorer_hitting_admin_only_route_returns_403(client: TestClient) -> None:
    """Case 15: Test scorer user accessing admin-only endpoint is rejected (403)."""
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "scorer1@cdms.com",
            "password": "scorer123",
            "role": "scorer",
        },
    )
    token = login_res.json()["access_token"]
    response = client.get(
        "/api/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


# 16. Viewer accessing admin-only route
def test_viewer_hitting_admin_only_route_returns_403(client: TestClient) -> None:
    """Case 16: Test viewer user accessing admin-only endpoint is rejected (403)."""
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "viewer@cdms.com",
            "password": "viewer123",
            "role": "viewer",
        },
    )
    token = login_res.json()["access_token"]
    response = client.get(
        "/api/auth/admin-only",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


# 17. Scorer accessing scorer-or-admin route
def test_scorer_hitting_scorer_or_admin_route_succeeds(client: TestClient) -> None:
    """Case 17: Test scorer user successfully accesses scorer-or-admin route."""
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "scorer1@cdms.com",
            "password": "scorer123",
            "role": "scorer",
        },
    )
    token = login_res.json()["access_token"]
    response = client.get(
        "/api/auth/scorer-or-admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# 18. Viewer accessing scorer-or-admin route
def test_viewer_hitting_scorer_or_admin_route_returns_403(client: TestClient) -> None:
    """Case 18: Test viewer user accessing scorer-or-admin route is rejected (403)."""
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "viewer@cdms.com",
            "password": "viewer123",
            "role": "viewer",
        },
    )
    token = login_res.json()["access_token"]
    response = client.get(
        "/api/auth/scorer-or-admin",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Scorer or Admin access required"


# 19. Security headers test
def test_security_headers_present(client: TestClient) -> None:
    """Case 19: Verify OWASP-recommended security headers are set on responses."""
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


# 20. Rate limiting enforcement test
def test_login_rate_limiting_enforcement() -> None:
    """Case 20: Verify rate limiter throws HTTP 429 when threshold exceeded."""
    from unittest.mock import MagicMock
    from fastapi import HTTPException, Request
    from app.core.rate_limit import InMemoryRateLimiter

    limiter = InMemoryRateLimiter(requests_per_minute=2, window_seconds=60)
    mock_request = MagicMock(spec=Request)
    mock_request.headers.get.return_value = "192.168.1.100"
    limiter.check_rate_limit(mock_request)
    limiter.check_rate_limit(mock_request)
    with pytest.raises(HTTPException) as exc_info:
        limiter.check_rate_limit(mock_request)
    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail
