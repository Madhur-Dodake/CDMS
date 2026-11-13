from typing import Generator
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Test client fixture for FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client

