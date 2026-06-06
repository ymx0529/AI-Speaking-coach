from __future__ import annotations

from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.conversation.qwen_stt import _qwen_transcribe_pcm16, transcribe_chunks


class FakeWebSocket:
    def __init__(self, responses: list[dict]):
        self._responses = [json.dumps(item) for item in responses]
        self.sent_messages: list[dict] = []
        self.closed = False

    def send(self, payload: str) -> None:
        self.sent_messages.append(json.loads(payload))

    def recv(self) -> str:
        if not self._responses:
            raise AssertionError("No more fake websocket responses configured.")
        return self._responses.pop(0)

    def close(self) -> None:
        self.closed = True


def test_qwen_transcribe_pcm16_sends_manual_mode_events(monkeypatch):
    fake_socket = FakeWebSocket(
        [
            {"type": "session.created"},
            {"type": "session.updated"},
            {"type": "input_audio_buffer.committed"},
            {
                "type": "conversation.item.input_audio_transcription.text",
                "text": "hello wor",
            },
            {
                "type": "conversation.item.input_audio_transcription.completed",
                "transcript": "hello world",
            },
            {"type": "session.finished"},
        ]
    )
    monkeypatch.setattr("app.modules.conversation.qwen_stt.settings.dashscope_api_key", "fake-key")
    monkeypatch.setattr("app.modules.conversation.qwen_stt.websocket.create_connection", lambda *args, **kwargs: fake_socket)

    transcript = _qwen_transcribe_pcm16(b"\x01\x02" * 1600, language="en")

    assert transcript == "hello world"
    assert fake_socket.closed is True
    assert [item["type"] for item in fake_socket.sent_messages] == [
        "session.update",
        "input_audio_buffer.append",
        "input_audio_buffer.commit",
        "session.finish",
    ]
    assert fake_socket.sent_messages[0]["session"]["turn_detection"] is None
    assert fake_socket.sent_messages[0]["session"]["input_audio_transcription"]["language"] == "en"


def test_transcribe_chunks_uses_qwen_for_binary_audio(monkeypatch):
    monkeypatch.setattr("app.modules.conversation.qwen_stt.convert_audio_chunks_to_pcm16_bytes", lambda chunks, source_format="webm": b"\x00\x01" * 800)
    monkeypatch.setattr("app.modules.conversation.qwen_stt._qwen_transcribe_pcm16", lambda pcm_bytes, language=None: "recognized by qwen")

    text, duration_ms = transcribe_chunks([(0, "AAECAwQF")], source_format="webm")

    assert text == "recognized by qwen"
    assert duration_ms > 0


def test_transcribe_chunks_keeps_mock_text_shortcut():
    text, duration_ms = transcribe_chunks(
        [
            (0, "SGVsbG8s"),
            (1, "IHdvcmxkIQ=="),
        ]
    )

    assert text == "Hello, world!"
    assert duration_ms > 0


def test_qwen_transcribe_pcm16_raises_on_transcription_failure(monkeypatch):
    fake_socket = FakeWebSocket(
        [
            {"type": "session.created"},
            {"type": "session.updated"},
            {
                "type": "conversation.item.input_audio_transcription.failed",
                "error": {"message": "bad audio"},
            },
        ]
    )
    monkeypatch.setattr("app.modules.conversation.qwen_stt.settings.dashscope_api_key", "fake-key")
    monkeypatch.setattr("app.modules.conversation.qwen_stt.websocket.create_connection", lambda *args, **kwargs: fake_socket)

    with pytest.raises(RuntimeError, match="bad audio"):
        _qwen_transcribe_pcm16(b"\x01\x02" * 1600, language="en")
