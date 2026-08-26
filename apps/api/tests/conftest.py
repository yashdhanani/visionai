from __future__ import annotations

import os
import tempfile

# Set env BEFORE any app imports
_test_db = tempfile.mktemp(suffix=".db")
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db}"
os.environ["JWT_SECRET"] = "test-secret-0123456789abcdef0123456789abcdef"
os.environ["MODEL_NAME"] = "yolov8n.pt"

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base, get_db, engine as _prod_engine
from app.main import app

# Create tables on the actual engine that settings resolved to
Base.metadata.create_all(bind=_prod_engine)

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def db_session():
    with Session(_prod_engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    import uuid
    email = f"test{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/api/v1/auth/register", json={"name": "Test", "email": email, "password": "Test1234!"})
    assert resp.status_code == 201, resp.json()
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project(client, auth_headers):
    resp = client.post("/api/v1/projects", json={"name": "Test Project"}, headers=auth_headers)
    assert resp.status_code == 201, resp.json()
    return resp.json()["data"]