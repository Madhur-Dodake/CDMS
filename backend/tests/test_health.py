from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient) -> None:
    """Verify /health returns 200 and expected health status structure."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


def test_api_health_endpoint(client: TestClient) -> None:
    """Verify /api/health returns 200 and identical structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

