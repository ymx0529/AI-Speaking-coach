import pytest
from fastapi.testclient import TestClient

from app.core.types import PronScore, TurnTranscriptReadyEvent, WordScore
from app.main import app
from app.modules.auth import service as auth_service
from app.modules.coach import store as coach_store

client = TestClient(app)


def _event(session_id="sess-shadow", turn_id="turn-shadow", user_id="user-1"):
    return TurnTranscriptReadyEvent(
        session_id=session_id,
        user_id=user_id,
        turn_id=turn_id,
        scene_id="restaurant",
        difficulty=1,
        persona_id="waiter",
        transcript="I want pasta.",
        audio_b64=None,
        assistant_reply_text="Sure, I can help you order pasta.",
        turn_duration_ms=800,
    )


@pytest.fixture(autouse=True)
def clear_store():
    coach_store._store.clear()
    auth_service._sessions.clear()
    yield
    coach_store._store.clear()
    auth_service._sessions.clear()


def _auth(monkeypatch, tmp_path, email: str = "shadow@example.com") -> tuple[dict[str, str], dict]:
    monkeypatch.setattr(auth_service, "USERS_FILE", tmp_path / "users.json")
    monkeypatch.setattr(auth_service, "SESSIONS_FILE", tmp_path / "sessions.json")
    token, user = auth_service.register_user(name="Shadow User", email=email, password="secret1")
    return {"Authorization": f"Bearer {token}"}, user


def _init_analyzed_turn(user_id: str):
    record = coach_store.init_turn(_event(user_id=user_id))
    record.sample_answer = "I would like to order pasta, please."
    record.pronunciation = PronScore(
        overall=76,
        accuracy=72,
        fluency=80,
        completeness=92,
        words=[
            WordScore(word="would", accuracy_score=62, error_type="Mispronunciation"),
            WordScore(word="pasta", accuracy_score=86, error_type="None"),
        ],
    )
    coach_store.set_status("sess-shadow", "turn-shadow", "analyzed")
    return record


def test_shadowing_items_requires_auth():
    response = client.get("/api/sessions/sess-shadow/shadowing/items")

    assert response.status_code == 401


def test_shadowing_items_returns_key_sentences(monkeypatch, tmp_path):
    headers, user = _auth(monkeypatch, tmp_path)
    _init_analyzed_turn(user["id"])

    response = client.get("/api/sessions/sess-shadow/shadowing/items", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "sess-shadow"
    assert data["items"][0]["text"] == "I would like to order pasta, please."
    assert data["items"][0]["source"] == "sample_answer"
    assert data["items"][0]["focus_words"] == ["would"]
    texts = [item["text"] for item in data["items"]]
    assert "Sure, I can help you order pasta." not in texts


def test_shadowing_items_hides_other_users_session(monkeypatch, tmp_path):
    _owner_headers, owner = _auth(monkeypatch, tmp_path, email="shadow-owner@example.com")
    other_headers, _other = _auth(monkeypatch, tmp_path, email="shadow-other@example.com")
    _init_analyzed_turn(owner["id"])

    response = client.get("/api/sessions/sess-shadow/shadowing/items", headers=other_headers)

    assert response.status_code == 404


def test_shadowing_tts_returns_audio(monkeypatch, tmp_path):
    headers, _user = _auth(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "app.modules.coach.router.synthesize_reply_audio",
        lambda text: ("ZmFrZS13YXY=", "wav_pcm16"),
    )

    response = client.post("/api/shadowing/tts", json={"text": "Hello there."}, headers=headers)

    assert response.status_code == 200
    assert response.json() == {"audio_format": "wav_pcm16", "data": "ZmFrZS13YXY="}


def test_shadowing_assess_returns_shadowing_metrics(monkeypatch, tmp_path):
    headers, user = _auth(monkeypatch, tmp_path)
    _init_analyzed_turn(user["id"])

    async def fake_assess(text, audio_b64):
        assert text == "I would like to order pasta, please."
        assert audio_b64 == "ZmFrZS13YXY="
        return PronScore(
            overall=82,
            accuracy=78,
            fluency=74,
            completeness=94,
            words=[WordScore(word="would", accuracy_score=65, error_type="Mispronunciation")],
        )

    monkeypatch.setattr("app.modules.coach.router.pronunciation_service.assess", fake_assess)

    response = client.post(
        "/api/sessions/sess-shadow/shadowing/assess",
        json={
            "item_id": "turn-shadow-sample",
            "text": "I would like to order pasta, please.",
            "audio_b64": "ZmFrZS13YXY=",
            "audio_format": "wav_pcm16",
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == "turn-shadow-sample"
    assert data["similarity_score"] == 82
    assert data["weak_words"][0]["word"] == "would"
    assert data["stress_score"] > 0
    assert data["intonation_score"] > 0
    assert data["liaison_score"] > 0
    assert data["pause_score"] > 0
