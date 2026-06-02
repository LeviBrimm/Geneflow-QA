import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTH_SECRET"] = "test-secret"
os.environ["ANALYSIS_QUEUE_MODE"] = "inline"

from app.db.database import Base, SessionLocal, engine, get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.reference_data import seed_reference_data  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_reference_data(db)
    db.close()

    def override_get_db():
        test_db = SessionLocal()
        try:
            yield test_db
        finally:
            test_db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture()
def auth_headers(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "qa@example.com", "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
