from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth import service as auth_service
from app.modules.conversation import session_manager


def setup_function() -> None:
    session_manager._sessions.clear()
    auth_service._sessions.clear()


def _auth(monkeypatch, tmp_path, email: str = "status@example.com") -> tuple[dict[str, str], dict]:
    monkeypatch.setattr(auth_service, "USERS_FILE", tmp_path / "users.json")
    monkeypatch.setattr(auth_service, "SESSIONS_FILE", tmp_path / "sessions.json")
    token, user = auth_service.register_user(name="Status User", email=email, password="secret1")
    return {"Authorization": f"Bearer {token}"}, user


def test_get_session_status_returns_active_session_state(monkeypatch, tmp_path):
    headers, user = _auth(monkeypatch, tmp_path)
    session_manager.start_session("status-1", "interview", 1, "strict_interviewer", user_id=user["id"])
    client = TestClient(app)

    response = client.get("/api/sessions/status-1/status", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "status-1"
    assert data["state"] == "active"
    assert data["summary_ready"] is False
    assert data["last_turn_id"] is None
    assert data["last_error"] is None


def test_session_finish_keeps_status_queryable(monkeypatch, tmp_path):
    headers, _user = _auth(monkeypatch, tmp_path)
    token = headers["Authorization"].replace("Bearer ", "")
    client = TestClient(app)

    with client.websocket_connect(f"/ws/session/status-2?token={token}") as websocket:
        websocket.send_json(
            {
                "type": "session.start",
                "session_id": "status-2",
                "scene_id": "meeting",
                "difficulty": 2,
                "persona_id": "colleague",
                "client_ts": 100,
            }
        )
        websocket.receive_json()
        websocket.send_json(
            {
                "type": "session.finish",
                "session_id": "status-2",
            }
        )

    response = client.get("/api/sessions/status-2/status", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "status-2"
    assert data["state"] == "finished"
    assert data["summary_ready"] is False


def test_get_session_status_returns_404_for_missing_session(monkeypatch, tmp_path):
    headers, _user = _auth(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/api/sessions/missing/status", headers=headers)

    assert response.status_code == 404


def test_get_session_status_requires_auth():
    client = TestClient(app)

    response = client.get("/api/sessions/missing/status")

    assert response.status_code == 401


def test_get_session_status_hides_other_users_session(monkeypatch, tmp_path):
    headers, user = _auth(monkeypatch, tmp_path, email="owner@example.com")
    other_headers, _other_user = _auth(monkeypatch, tmp_path, email="other@example.com")
    session_manager.start_session("status-owned", "interview", 1, "strict_interviewer", user_id=user["id"])
    client = TestClient(app)

    owner_response = client.get("/api/sessions/status-owned/status", headers=headers)
    other_response = client.get("/api/sessions/status-owned/status", headers=other_headers)

    assert owner_response.status_code == 200
    assert other_response.status_code == 404
