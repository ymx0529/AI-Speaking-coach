from pathlib import Path
from datetime import datetime, timedelta, timezone
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth import service as auth_service


def _client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setattr(auth_service, "USERS_FILE", tmp_path / "users.json")
    auth_service.clear_sessions()
    return TestClient(app)


def _register(client: TestClient, email: str = "xin@example.com") -> dict:
    response = client.post(
        "/api/auth/register",
        json={"name": "Xin", "email": email, "password": "secret1"},
    )
    assert response.status_code == 200
    return response.json()


def test_register_persists_user_without_plain_password(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)

    data = _register(client)

    assert data["token"]
    assert data["user"]["name"] == "Xin"
    assert data["user"]["email"] == "xin@example.com"

    users = json.loads((tmp_path / "users.json").read_text(encoding="utf-8"))
    assert len(users) == 1
    assert users[0]["email"] == "xin@example.com"
    assert users[0]["password_hash"] != "secret1"
    assert "password" not in users[0]


def test_register_rejects_duplicate_email(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    _register(client)

    response = client.post(
        "/api/auth/register",
        json={"name": "Xin Again", "email": "XIN@example.com", "password": "secret1"},
    )

    assert response.status_code == 409


def test_register_rejects_weak_password(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)

    response = client.post(
        "/api/auth/register",
        json={"name": "Xin", "email": "xin@example.com", "password": "123"},
    )

    assert response.status_code == 400


def test_login_accepts_valid_credentials(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    _register(client)

    response = client.post(
        "/api/auth/login",
        json={"email": "xin@example.com", "password": "secret1"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token"]
    assert data["user"]["email"] == "xin@example.com"


def test_login_rejects_invalid_password(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    _register(client)

    response = client.post(
        "/api/auth/login",
        json={"email": "xin@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_me_returns_current_user(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    token = _register(client)["token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "xin@example.com"


def test_token_expires_after_one_day(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    data = _register(client)
    token = data["token"]
    user_id = data["user"]["id"]
    _session_user_id, expires_at = auth_service._sessions[token]

    assert _session_user_id == user_id
    assert timedelta(hours=23, minutes=59) < expires_at - datetime.now(timezone.utc) <= timedelta(days=1)

    auth_service._sessions[token] = (user_id, datetime.now(timezone.utc) - timedelta(seconds=1))
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert token not in auth_service._sessions


def test_logout_invalidates_token(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    token = _register(client)["token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout_response = client.post("/api/auth/logout", headers=headers)
    me_response = client.get("/api/auth/me", headers=headers)

    assert logout_response.status_code == 200
    assert logout_response.json() == {"ok": True}
    assert me_response.status_code == 401
