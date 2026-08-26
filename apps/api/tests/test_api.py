from __future__ import annotations

import json

from tests.helpers import generate_test_image


class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/api/v1/health/live")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_readiness(self, client):
        resp = client.get("/api/v1/health/ready")
        assert resp.status_code == 200
        assert "ready" in resp.json()

    def test_api_root(self, client):
        resp = client.get("/api/v1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "VisionAI"


class TestAuth:
    def test_register(self, client):
        resp = client.post("/api/v1/auth/register", json={"name": "Alice", "email": "alice@test.com", "password": "Test1234!"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"]
        assert "access_token" in data["data"]

    def test_login(self, client, auth_headers):
        me = client.get("/api/v1/auth/me", headers=auth_headers)
        assert me.status_code == 200
        email = me.json()["data"]["email"]
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Test1234!"})
        assert resp.status_code == 200
        assert resp.json()["success"]

    def test_login_wrong_password(self, client, auth_headers):
        me = client.get("/api/v1/auth/me", headers=auth_headers)
        email = me.json()["data"]["email"]
        resp = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
        assert resp.status_code == 401

    def test_me_requires_auth(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_register_duplicate(self, client):
        client.post("/api/v1/auth/register", json={"name": "Bob", "email": "bob@test.com", "password": "Test1234!"})
        resp = client.post("/api/v1/auth/register", json={"name": "Bob2", "email": "bob@test.com", "password": "Test1234!"})
        assert resp.status_code == 409

    def test_create_api_key(self, client, auth_headers):
        resp = client.post("/api/v1/auth/api-keys", json={"name": "Test Key"}, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert "prefix_display" in data

    def test_list_api_keys(self, client, auth_headers):
        client.post("/api/v1/auth/api-keys", json={"name": "Key A"}, headers=auth_headers)
        resp = client.get("/api/v1/auth/api-keys", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1


class TestProjects:
    def test_create_project(self, client, auth_headers):
        resp = client.post("/api/v1/projects", json={"name": "Traffic Monitor", "description": "Road analysis"}, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["data"]["name"] == "Traffic Monitor"

    def test_list_projects(self, client, auth_headers):
        client.post("/api/v1/projects", json={"name": "P1"}, headers=auth_headers)
        resp = client.get("/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] >= 1

    def test_get_project(self, client, auth_headers):
        create = client.post("/api/v1/projects", json={"name": "GetTest"}, headers=auth_headers)
        pid = create.json()["data"]["id"]
        resp = client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "GetTest"

    def test_update_project(self, client, auth_headers):
        create = client.post("/api/v1/projects", json={"name": "Old Name"}, headers=auth_headers)
        pid = create.json()["data"]["id"]
        resp = client.patch(f"/api/v1/projects/{pid}", json={"name": "New Name"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "New Name"

    def test_delete_project(self, client, auth_headers):
        create = client.post("/api/v1/projects", json={"name": "ToDelete"}, headers=auth_headers)
        pid = create.json()["data"]["id"]
        resp = client.delete(f"/api/v1/projects/{pid}", headers=auth_headers)
        assert resp.status_code == 200
        resp2 = client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
        assert resp2.status_code == 404

    def test_project_isolation(self, client):
        """Two users cannot see each other's projects."""
        import uuid
        from tests.helpers import generate_test_image

        h1 = _make_user(client, "iso1@test.com")
        h2 = _make_user(client, "iso2@test.com")
        p1 = client.post("/api/v1/projects", json={"name": "P1"}, headers=h1).json()["data"]["id"]
        p2 = client.post("/api/v1/projects", json={"name": "P2"}, headers=h2).json()["data"]["id"]
        resp1 = client.get(f"/api/v1/projects/{p1}", headers=h1)
        assert resp1.status_code == 200
        resp2 = client.get(f"/api/v1/projects/{p1}", headers=h2)
        assert resp2.status_code == 404


def _make_user(client, email: str) -> dict:
    resp = client.post("/api/v1/auth/register", json={"name": "U", "email": email, "password": "Test1234!"})
    return {"Authorization": f"Bearer {resp.json()['data']['access_token']}"}


class TestDetections:
    def test_image_detection(self, client, auth_headers, project):
        img_bytes = generate_test_image()
        resp = client.post(
            "/api/v1/detections/image",
            data={"project_id": project["id"]},
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data
        assert data["status"] == "completed"
        assert data["source_type"] == "image"

    def test_list_detections(self, client, auth_headers, project):
        img_bytes = generate_test_image()
        client.post(
            "/api/v1/detections/image",
            data={"project_id": project["id"]},
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        resp = client.get("/api/v1/detections", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] >= 1

    def test_get_detection_detail(self, client, auth_headers, project):
        img_bytes = generate_test_image()
        create = client.post(
            "/api/v1/detections/image",
            data={"project_id": project["id"]},
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        det_id = create.json()["data"]["id"]
        resp = client.get(f"/api/v1/detections/{det_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == det_id

    def test_detection_with_confidence(self, client, auth_headers, project):
        img_bytes = generate_test_image()
        resp = client.post(
            "/api/v1/detections/image",
            data={"project_id": project["id"], "confidence": 0.5},
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "completed"

    def test_video_detection(self, client, auth_headers, project):
        from tests.helpers import generate_test_video
        vid = generate_test_video(frames=5)
        resp = client.post(
            "/api/v1/detections/video",
            data={"project_id": project["id"], "sample_fps": 10},
            files={"file": ("test.mp4", vid, "video/mp4")},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "processing"

    def test_invalid_file_type(self, client, auth_headers, project):
        resp = client.post(
            "/api/v1/detections/image",
            data={"project_id": project["id"]},
            files={"file": ("test.txt", b"not an image", "text/plain")},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestModels:
    def test_list_models(self, client, auth_headers):
        resp = client.get("/api/v1/models", headers=auth_headers)
        assert resp.status_code == 200

    def test_register_model_admin(self, client, db_session):
        """Admin-only model registration."""
        h = _make_admin(client, db_session)
        resp = client.post("/api/v1/models", json={"name": "YOLOv8x", "version": "8.0", "path": "yolov8x.pt"}, headers=h)
        assert resp.status_code == 201

    def test_register_model_non_admin(self, client, auth_headers):
        resp = client.post("/api/v1/models", json={"name": "YOLOv8x", "version": "8.0", "path": "yolov8x.pt"}, headers=auth_headers)
        assert resp.status_code == 403


def _make_admin(client, db_session) -> dict:
    import uuid
    h = _make_user(client, f"admin{uuid.uuid4().hex[:6]}@test.com")
    from app.models.db_models import User, UserRole
    user = db_session.query(User).order_by(User.created_at.desc()).first()
    if user:
        user.role = UserRole.ADMIN
        db_session.commit()
        db_session.expire_all()
    return h


class TestAnalytics:
    def test_summary(self, client, auth_headers):
        resp = client.get("/api/v1/analytics/summary", headers=auth_headers)
        assert resp.status_code == 200
        assert "total_detections" in resp.json()["data"]

    def test_timeseries(self, client, auth_headers):
        resp = client.get("/api/v1/analytics/timeseries", headers=auth_headers)
        assert resp.status_code == 200

    def test_class_distribution(self, client, auth_headers):
        resp = client.get("/api/v1/analytics/classes", headers=auth_headers)
        assert resp.status_code == 200