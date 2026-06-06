from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from app.main import app
from app.modules.conversation import session_manager


def setup_function() -> None:
    session_manager._sessions.clear()


def test_get_session_status_returns_active_session_state():
    session_manager.start_session("status-1", "interview", 1, "strict_interviewer")
    client = TestClient(app)

    response = client.get("/api/sessions/status-1/status")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "status-1"
    assert data["state"] == "active"
    assert data["summary_ready"] is False
    assert data["last_turn_id"] is None
    assert data["last_error"] is None


def test_session_finish_keeps_status_queryable():
    client = TestClient(app)

    with client.websocket_connect("/ws/session/status-2") as websocket:
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

    response = client.get("/api/sessions/status-2/status")

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "status-2"
    assert data["state"] == "finished"
    assert data["summary_ready"] is False


def test_get_session_status_returns_404_for_missing_session():
    client = TestClient(app)

    response = client.get("/api/sessions/missing/status")

    assert response.status_code == 404
