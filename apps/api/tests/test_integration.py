import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_diagnostics():
    # Requires auth, but we can test the endpoint exists
    response = client.get("/api/v1/diagnostics/health")
    # Should return 401 if not authenticated
    assert response.status_code in (200, 401)


def test_categories():
    response = client.get("/api/v1/categories")
    assert response.status_code in (200, 401)


def test_events():
    response = client.get("/api/v1/events")
    assert response.status_code in (200, 401)


def test_rules():
    response = client.get("/api/v1/rules")
    assert response.status_code in (200, 401)