import pytest
from fastapi.testclient import TestClient

from app.core.types import PronScore, TurnTranscriptReadyEvent
from app.main import app
from app.modules.coach import store as coach_store

client = TestClient(app)


def _event(session_id="sess-x", turn_id="turn-x"):
    return TurnTranscriptReadyEvent(
        session_id=session_id,
        turn_id=turn_id,
        scene_id="restaurant",
        difficulty=1,
        persona_id="waiter",
        transcript="I want pasta.",
        wav_audio_b64=None,
        assistant_reply_text="Sure!",
        turn_duration_ms=800,
    )


@pytest.fixture(autouse=True)
def clear_store():
    coach_store._store.clear()
    yield
    coach_store._store.clear()


def test_summary_404_for_unknown_session():
    response = client.post("/api/sessions/no-such-session/summary")
    assert response.status_code == 404


def test_summary_returns_200_with_analyzed_turns():
    record = coach_store.init_turn(_event())
    record.pronunciation = PronScore(overall=75, accuracy=70, fluency=78, completeness=85)
    record.grammar_score = 80.0
    coach_store.set_status("sess-x", "turn-x", "analyzed")

    response = client.post("/api/sessions/sess-x/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "sess-x"
    assert data["total_turns"] == 1
    assert data["pron_avg"] == 75.0
    assert data["grammar_score"] == 80.0
    assert "focus_recommendations" in data
    assert "ai_feedback" in data


def test_summary_stable_with_no_pronunciation():
    record = coach_store.init_turn(_event())
    coach_store.set_status("sess-x", "turn-x", "analyzed")

    response = client.post("/api/sessions/sess-x/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["pron_avg"] == 0.0
    assert data["total_turns"] == 1
