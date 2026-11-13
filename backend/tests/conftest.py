import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_access_token
from app.core.database import SessionLocal
from app.main import app
from app.models.user import User, UserRole


@pytest.fixture(scope="session")
def db_session() -> Generator[Session, None, None]:
    """Database session fixture for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Test client fixture for FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def admin_user(db_session: Session) -> User:
    """Fixture to obtain the seeded admin user or create a test admin."""
    admin = db_session.query(User).filter(User.role == UserRole.ADMIN).first()
    if not admin:
        admin = User(
            user_id=uuid.uuid4(),
            name="Test Admin",
            email="test_admin@cdms.com",
            password="hashedpassword",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
    return admin


@pytest.fixture(scope="module")
def scorer_user(db_session: Session) -> User:
    """Fixture to obtain the seeded scorer user."""
    scorer = db_session.query(User).filter(User.role == UserRole.SCORER).first()
    if not scorer:
        scorer = User(
            user_id=uuid.uuid4(),
            name="Test Scorer",
            email="test_scorer@cdms.com",
            password="hashedpassword",
            role=UserRole.SCORER,
        )
        db_session.add(scorer)
        db_session.commit()
        db_session.refresh(scorer)
    return scorer


@pytest.fixture(scope="module")
def admin_headers(admin_user: User) -> dict:
    """Authorization header fixture for admin requests."""
    token = create_access_token(
        data={
            "user_id": str(admin_user.user_id),
            "role": admin_user.role.value,
            "sub": admin_user.email,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def scorer_headers(scorer_user: User) -> dict:
    """Authorization header fixture for scorer requests."""
    token = create_access_token(
        data={
            "user_id": str(scorer_user.user_id),
            "role": scorer_user.role.value,
            "sub": scorer_user.email,
        }
    )
    return {"Authorization": f"Bearer {token}"}
