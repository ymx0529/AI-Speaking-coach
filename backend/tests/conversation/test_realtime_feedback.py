from pathlib import Path
import sys
from base64 import b64encode
import threading
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core import event_bus
from app.main import app
from app.modules.auth import service as auth_service
from app.modules.conversation import session_manager


def _b64(text: str) -> str:
    return b64encode(text.encode("utf-8")).decode("utf-8")


def setup_function() -> None:
    session_manager._sessions.clear()
    auth_service.clear_sessions()


def _receive_until(websocket, msg_type: str, *, max_messages: int = 8) -> dict:
    for _ in range(max_messages):
        message = websocket.receive_json()
        if message.get("type") == msg_type:
            return message
    raise AssertionError(f"Did not receive message type {msg_type}")


def _auth_query(monkeypatch, tmp_path, email: str = "realtime@example.com") -> str:
    monkeypatch.setattr(auth_service, "USERS_FILE", tmp_path / "users.json")
    token, _user = auth_service.register_user(name="Realtime User", email=email, password="secret1")
    return f"?token={token}"


def test_websocket_rejects_missing_token():
    client = TestClient(app)

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/session/realtime-auth"):
            pass


def test_audio_append_emits_partial_then_final_transcript(monkeypatch, tmp_path):
    auth_query = _auth_query(monkeypatch, tmp_path)
    client = TestClient(app)

    with client.websocket_connect(f"/ws/session/realtime-1{auth_query}") as websocket:
        websocket.send_json(
            {
                "type": "session.start",
                "session_id": "realtime-1",
                "scene_id": "interview",
                "difficulty": 1,
                "persona_id": "strict_interviewer",
                "client_ts": 100,
            }
        )
        ready = websocket.receive_json()

        websocket.send_json(
            {
                "type": "audio.append",
                "session_id": "realtime-1",
                "turn_id": None,
                "seq": 0,
                "encoding": "webm_opus",
                "chunk": _b64("Hello, I would like"),
                "is_last": False,
                "client_ts": 200,
            }
        )
        turn_started = websocket.receive_json()
        partial = websocket.receive_json()

        websocket.send_json(
            {
                "type": "audio.append",
                "session_id": "realtime-1",
                "turn_id": turn_started["turn_id"],
                "seq": 1,
                "encoding": "webm_opus",
                "chunk": _b64(" to introduce myself."),
                "is_last": True,
                "client_ts": 300,
            }
        )
        final_msg = _receive_until(websocket, "user_turn.final")
        reply_msg = _receive_until(websocket, "assistant.reply_text")
        reply_audio_start_msg = _receive_until(websocket, "assistant.reply_audio_start")
        reply_audio_chunk_msg = _receive_until(websocket, "assistant.reply_audio_chunk")

    assert ready["type"] == "session.ready"
    assert turn_started["type"] == "turn.started"
    assert partial["type"] == "asr.partial"
    assert partial["text"] == "Hello, I would like"
    assert final_msg["type"] == "user_turn.final"
    assert final_msg["text"] == "Hello, I would like to introduce myself."
    assert final_msg["duration_ms"] > 0
    assert reply_msg["type"] == "assistant.reply_text"
    assert isinstance(reply_msg["text"], str)
    assert reply_msg["text"]
    assert reply_audio_start_msg["type"] == "assistant.reply_audio_start"
    assert reply_audio_start_msg["total_chunks"] >= 1
    assert reply_audio_chunk_msg["type"] == "assistant.reply_audio_chunk"
    assert reply_audio_chunk_msg["sequence"] == 0
    assert reply_audio_chunk_msg["audio_format"] == "wav_pcm16"
    assert isinstance(reply_audio_chunk_msg["data"], str)
    assert reply_audio_chunk_msg["data"]


def test_audio_append_publishes_turn_transcript_ready_event_once(monkeypatch, tmp_path):
    auth_query = _auth_query(monkeypatch, tmp_path)
    publish_mock = AsyncMock()
    monkeypatch.setattr(event_bus, "publish", publish_mock)
    client = TestClient(app)

    with client.websocket_connect(f"/ws/session/realtime-2{auth_query}") as websocket:
        websocket.send_json(
            {
                "type": "session.start",
                "session_id": "realtime-2",
                "scene_id": "meeting",
                "difficulty": 2,
                "persona_id": "colleague",
                "client_ts": 100,
            }
        )
        websocket.receive_json()

        websocket.send_json(
            {
                "type": "audio.append",
                "session_id": "realtime-2",
                "turn_id": None,
                "seq": 0,
                "encoding": "webm_opus",
                "chunk": _b64("I think we should"),
                "is_last": False,
                "client_ts": 200,
            }
        )
        turn_started = websocket.receive_json()
        websocket.receive_json()

        websocket.send_json(
            {
                "type": "audio.append",
                "session_id": "realtime-2",
                "turn_id": turn_started["turn_id"],
                "seq": 1,
                "encoding": "webm_opus",
                "chunk": _b64(" launch next month."),
                "is_last": True,
                "client_ts": 300,
            }
        )
        websocket.receive_json()
        websocket.receive_json()
        websocket.receive_json()

    assert publish_mock.await_count == 1
    event = publish_mock.await_args.args[0]
    assert event.session_id == "realtime-2"
    assert event.turn_id == turn_started["turn_id"]
    assert event.scene_id == "meeting"
    assert event.difficulty == 2
    assert event.persona_id == "colleague"
    assert event.transcript == "I think we should launch next month."
    assert event.assistant_reply_text
    assert event.audio_b64
    assert event.turn_duration_ms > 0


def test_audio_append_publishes_analysis_before_tts(monkeypatch, tmp_path):
    auth_query = _auth_query(monkeypatch, tmp_path)
    order: list[str] = []

    async def fake_publish(event):
        order.append("publish")

    def fake_synthesize(text: str):
        order.append("tts")
        return _b64("audio"), "wav_pcm16"

    monkeypatch.setattr(event_bus, "publish", fake_publish)
    monkeypatch.setattr("app.modules.conversation.router.generate_reply", lambda **_kwargs: "One reply.")
    monkeypatch.setattr("app.modules.conversation.router.synthesize_reply_audio", fake_synthesize)
    client = TestClient(app)

    with client.websocket_connect(f"/ws/session/realtime-3{auth_query}") as websocket:
        websocket.send_json(
            {
                "type": "session.start",
                "session_id": "realtime-3",
                "scene_id": "interview",
                "difficulty": 1,
                "persona_id": "strict_interviewer",
                "client_ts": 100,
            }
        )
        websocket.receive_json()

        websocket.send_json(
            {
                "type": "audio.append",
                "session_id": "realtime-3",
                "turn_id": None,
                "seq": 0,
                "encoding": "webm_opus",
                "chunk": _b64("Hello"),
                "is_last": True,
                "client_ts": 200,
            }
        )
        _receive_until(websocket, "assistant.reply_audio_chunk")

    assert order == ["publish", "tts"]


def test_audio_append_does_not_wait_for_slow_tts(monkeypatch, tmp_path):
    auth_query = _auth_query(monkeypatch, tmp_path)
    tts_started = threading.Event()
    tts_release = threading.Event()
    order: list[str] = []

    def slow_synthesize(text: str):
        order.append("tts_started")
        tts_started.set()
        tts_release.wait(timeout=2)
        order.append("tts_done")
        return _b64("audio"), "wav_pcm16"

    monkeypatch.setattr(event_bus, "publish", AsyncMock())
    monkeypatch.setattr("app.modules.conversation.router.generate_reply", lambda **_kwargs: "One reply.")
    monkeypatch.setattr("app.modules.conversation.router.synthesize_reply_audio", slow_synthesize)
    client = TestClient(app)

    with client.websocket_connect(f"/ws/session/realtime-4{auth_query}") as websocket:
        websocket.send_json(
            {
                "type": "session.start",
                "session_id": "realtime-4",
                "scene_id": "interview",
                "difficulty": 1,
                "persona_id": "strict_interviewer",
                "client_ts": 100,
            }
        )
        websocket.receive_json()

        websocket.send_json(
            {
                "type": "audio.append",
                "session_id": "realtime-4",
                "turn_id": None,
                "seq": 0,
                "encoding": "webm_opus",
                "chunk": _b64("Hello"),
                "is_last": True,
                "client_ts": 200,
            }
        )

        _receive_until(websocket, "assistant.reply_text")
        _receive_until(websocket, "assistant.reply_audio_start")
        assert tts_started.wait(timeout=1)
        tts_release.set()
        _receive_until(websocket, "assistant.reply_audio_chunk")
        websocket.send_json({"type": "session.finish", "session_id": "realtime-4"})

    assert order == ["tts_started", "tts_done"]


def test_audio_append_uses_previous_turn_history(monkeypatch, tmp_path):
    auth_query = _auth_query(monkeypatch, tmp_path)
    generate_calls: list[dict] = []

    def fake_generate_reply(**kwargs):
        generate_calls.append(
            {
                "history": list(kwargs["history"]),
                "user_text": kwargs["user_text"],
            }
        )
        return f"reply-{len(generate_calls)}"

    monkeypatch.setattr(event_bus, "publish", AsyncMock())
    monkeypatch.setattr("app.modules.conversation.router.generate_reply", fake_generate_reply)
    monkeypatch.setattr(
        "app.modules.conversation.router.synthesize_reply_audio",
        lambda text: (_b64("audio"), "wav_pcm16"),
    )
    client = TestClient(app)

    with client.websocket_connect(f"/ws/session/realtime-5{auth_query}") as websocket:
        websocket.send_json(
            {
                "type": "session.start",
                "session_id": "realtime-5",
                "scene_id": "interview",
                "difficulty": 1,
                "persona_id": "strict_interviewer",
                "client_ts": 100,
            }
        )
        websocket.receive_json()

        websocket.send_json(
            {
                "type": "audio.append",
                "session_id": "realtime-5",
                "turn_id": None,
                "seq": 0,
                "encoding": "webm_opus",
                "chunk": _b64("First answer"),
                "is_last": True,
                "client_ts": 200,
            }
        )
        _receive_until(websocket, "assistant.reply_text")

        websocket.send_json(
            {
                "type": "audio.append",
                "session_id": "realtime-5",
                "turn_id": None,
                "seq": 0,
                "encoding": "webm_opus",
                "chunk": _b64("Second answer"),
                "is_last": True,
                "client_ts": 300,
            }
        )
        _receive_until(websocket, "assistant.reply_text")

    assert generate_calls[0]["history"] == []
    assert generate_calls[0]["user_text"] == "First answer"
    assert generate_calls[1]["history"] == [
        {"role": "user", "content": "First answer"},
        {"role": "assistant", "content": "reply-1"},
    ]
    assert generate_calls[1]["user_text"] == "Second answer"


def test_audio_append_streams_reply_audio_by_segments(monkeypatch, tmp_path):
    auth_query = _auth_query(monkeypatch, tmp_path)
    synthesized_segments: list[str] = []

    def fake_generate_reply(**_kwargs):
        return "First short answer. Second follow-up question?"

    def fake_synthesize(text: str):
        synthesized_segments.append(text)
        return _b64(f"audio:{text}"), "wav_pcm16"

    monkeypatch.setattr(event_bus, "publish", AsyncMock())
    monkeypatch.setattr("app.modules.conversation.router.generate_reply", fake_generate_reply)
    monkeypatch.setattr("app.modules.conversation.router.synthesize_reply_audio", fake_synthesize)
    client = TestClient(app)

    with client.websocket_connect(f"/ws/session/realtime-6{auth_query}") as websocket:
        websocket.send_json(
            {
                "type": "session.start",
                "session_id": "realtime-6",
                "scene_id": "interview",
                "difficulty": 1,
                "persona_id": "strict_interviewer",
                "client_ts": 100,
            }
        )
        websocket.receive_json()

        websocket.send_json(
            {
                "type": "audio.append",
                "session_id": "realtime-6",
                "turn_id": None,
                "seq": 0,
                "encoding": "webm_opus",
                "chunk": _b64("Hello"),
                "is_last": True,
                "client_ts": 200,
            }
        )
        start_msg = _receive_until(websocket, "assistant.reply_audio_start")
        first_chunk = _receive_until(websocket, "assistant.reply_audio_chunk")
        second_chunk = _receive_until(websocket, "assistant.reply_audio_chunk")
        end_msg = _receive_until(websocket, "assistant.reply_audio_end")

    assert start_msg["total_chunks"] == 2
    assert first_chunk["sequence"] == 0
    assert first_chunk["text"] == "First short answer."
    assert second_chunk["sequence"] == 1
    assert second_chunk["text"] == "Second follow-up question?"
    assert end_msg["total_chunks"] == 2
    assert synthesized_segments == ["First short answer.", "Second follow-up question?"]
