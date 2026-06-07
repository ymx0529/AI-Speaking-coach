import pytest
from fastapi.testclient import TestClient

from app.core.types import PronScore, TurnTranscriptReadyEvent
from app.main import app
from app.modules.auth import service as auth_service
from app.modules.coach import store as coach_store

client = TestClient(app)


def _event(session_id="sess-x", turn_id="turn-x", user_id="user-1"):
    return TurnTranscriptReadyEvent(
        session_id=session_id,
        user_id=user_id,
        turn_id=turn_id,
        scene_id="restaurant",
        difficulty=1,
        persona_id="waiter",
        transcript="I want pasta.",
        audio_b64=None,
        assistant_reply_text="Sure!",
        turn_duration_ms=800,
    )


@pytest.fixture(autouse=True)
def clear_store():
    coach_store._store.clear()
    auth_service.clear_sessions()
    yield
    coach_store._store.clear()
    auth_service.clear_sessions()


def _auth(monkeypatch, tmp_path, email: str = "summary@example.com") -> tuple[dict[str, str], dict]:
    monkeypatch.setattr(auth_service, "USERS_FILE", tmp_path / "users.json")
    token, user = auth_service.register_user(name="Summary User", email=email, password="secret1")
    return {"Authorization": f"Bearer {token}"}, user


def test_summary_404_for_unknown_session(monkeypatch, tmp_path):
    headers, _user = _auth(monkeypatch, tmp_path)
    response = client.post("/api/sessions/no-such-session/summary", headers=headers)
    assert response.status_code == 404


def test_summary_returns_200_with_analyzed_turns(monkeypatch, tmp_path):
    headers, user = _auth(monkeypatch, tmp_path)
    record = coach_store.init_turn(_event(user_id=user["id"]))
    record.pronunciation = PronScore(overall=75, accuracy=70, fluency=78, completeness=85)
    record.grammar_score = 80.0
    coach_store.set_status("sess-x", "turn-x", "analyzed")

    response = client.post("/api/sessions/sess-x/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "sess-x"
    assert data["total_turns"] == 1
    assert data["pron_avg"] == 75.0
    assert data["grammar_score"] == 80.0
    assert "focus_recommendations" in data
    assert "ai_feedback" in data


def test_summary_stable_with_no_pronunciation(monkeypatch, tmp_path):
    headers, user = _auth(monkeypatch, tmp_path)
    record = coach_store.init_turn(_event(user_id=user["id"]))
    coach_store.set_status("sess-x", "turn-x", "analyzed")

    response = client.post("/api/sessions/sess-x/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pron_avg"] == 0.0
    assert data["total_turns"] == 1


def test_summary_requires_auth():
    response = client.post("/api/sessions/sess-x/summary")
    assert response.status_code == 401


def test_summary_hides_other_users_session(monkeypatch, tmp_path):
    owner_headers, owner = _auth(monkeypatch, tmp_path, email="summary-owner@example.com")
    other_headers, _other = _auth(monkeypatch, tmp_path, email="summary-other@example.com")
    record = coach_store.init_turn(_event(user_id=owner["id"]))
    record.pronunciation = PronScore(overall=75, accuracy=70, fluency=78, completeness=85)
    coach_store.set_status("sess-x", "turn-x", "analyzed")

    owner_response = client.post("/api/sessions/sess-x/summary", headers=owner_headers)
    other_response = client.post("/api/sessions/sess-x/summary", headers=other_headers)

    assert owner_response.status_code == 200
    assert other_response.status_code == 404
