from pathlib import Path
import sys
from base64 import b64encode

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from app.main import app
from app.modules.conversation import session_manager


def _b64(text: str) -> str:
    return b64encode(text.encode("utf-8")).decode("utf-8")


def setup_function() -> None:
    session_manager._sessions.clear()


def test_audio_append_emits_partial_then_final_transcript():
    client = TestClient(app)

    with client.websocket_connect("/ws/session/realtime-1") as websocket:
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
        final_msg = websocket.receive_json()
        reply_msg = websocket.receive_json()

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
