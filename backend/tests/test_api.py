import os
import sys
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / f"test_{uuid.uuid4().hex}.db"
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-unit-tests-32chars")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("API_PUBLIC_URL", "http://testserver")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:8000")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:8000")
    monkeypatch.setenv("SEED_ON_STARTUP", "false")
    monkeypatch.setenv("ENABLE_DOCS", "false")
    monkeypatch.setenv("ADMIN_USERNAMES", "admin_user")

    # Drop cached src modules so settings/engine/routers bind to this test DB.
    for name in list(sys.modules):
        if name == "src" or name.startswith("src."):
            del sys.modules[name]

    from src.main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_ready(client):
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json()["database"] == "ok"


def test_live(client):
    assert client.get("/live").json()["status"] == "alive"


def test_security_headers(client):
    res = client.get("/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert "X-Request-ID" in res.headers


def test_register_login_create_meme(client):
    username = f"user_{uuid.uuid4().hex[:8]}"
    reg = client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "secret12"},
    )
    assert reg.status_code == 201, reg.text

    login = client.post(
        "/auth/login",
        data={"username": username, "password": "secret12"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    denied = client.post("/memes", json={"caption": "nope", "url": "https://example.com/a.jpg"})
    assert denied.status_code == 401

    created = client.post(
        "/memes",
        headers=headers,
        json={"caption": "hello prod", "url": "https://example.com/meme.jpg", "tags": ["test"]},
    )
    assert created.status_code == 201, created.text
    meme_id = created.json()["id"]
    assert created.json()["status"] == "published"

    listed = client.get("/memes")
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    detail = client.get(f"/memes/{meme_id}?track_view=true")
    assert detail.status_code == 200
    assert detail.json()["view_count"] >= 1

    following = client.get("/memes?following=true")
    assert following.status_code == 401


def test_admin_reports_gated(client):
    username = f"user_{uuid.uuid4().hex[:8]}"
    client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": "secret12"},
    )
    login = client.post(
        "/auth/login",
        data={"username": username, "password": "secret12"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    res = client.get("/admin/reports", headers=headers)
    assert res.status_code == 403
