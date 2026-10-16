import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client backed by a fresh, empty database for every test."""
    monkeypatch.setenv("BOOKINGS_DB", str(tmp_path / "test.db"))
    with TestClient(app) as test_client:  # "with" runs the startup migrations
        yield test_client


@pytest.fixture
def alice():
    return {"X-User-Token": "demo-token-alice"}


@pytest.fixture
def bob():
    return {"X-User-Token": "demo-token-bob"}
