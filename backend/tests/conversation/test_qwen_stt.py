from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.conversation.qwen_stt import (
    _qwen_transcribe_wav_bytes,
    _wav_bytes_to_data_uri,
    transcribe_chunks,
)


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeCompletion:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeChatCompletions:
    def __init__(self, content: str):
        self._content = content
        self.last_kwargs: dict | None = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return _FakeCompletion(self._content)


class _FakeClient:
    def __init__(self, content: str):
        self.chat = type("ChatNamespace", (), {"completions": _FakeChatCompletions(content)})()


def test_wav_bytes_to_data_uri_prefix():
    data_uri = _wav_bytes_to_data_uri(b"RIFFmock")

    assert data_uri.startswith("data:audio/wav;base64,")


def test_qwen_transcribe_wav_bytes_uses_openai_compatible_payload(monkeypatch):
    fake_client = _FakeClient("hello world")
    monkeypatch.setattr("app.modules.conversation.qwen_stt._get_client", lambda: fake_client)

    transcript = _qwen_transcribe_wav_bytes(b"RIFFmock", language="en")

    assert transcript == "hello world"
    payload = fake_client.chat.completions.last_kwargs
    assert payload is not None
    assert payload["model"] == "qwen3-asr-flash"
    assert payload["messages"][0]["content"][0]["type"] == "input_audio"
    assert payload["extra_body"]["asr_options"]["language"] == "en"


def test_transcribe_chunks_uses_qwen_for_binary_audio(monkeypatch):
    monkeypatch.setattr(
        "app.modules.conversation.qwen_stt.convert_audio_bytes_to_wav_bytes",
        lambda audio_bytes, source_format="webm": b"RIFFmock",
    )
    monkeypatch.setattr(
        "app.modules.conversation.qwen_stt._qwen_transcribe_wav_bytes",
        lambda wav_bytes, language=None: "recognized by qwen",
    )

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


def test_qwen_transcribe_wav_bytes_raises_on_empty_transcript(monkeypatch):
    fake_client = _FakeClient("")
    monkeypatch.setattr("app.modules.conversation.qwen_stt._get_client", lambda: fake_client)

    with pytest.raises(RuntimeError, match="Qwen ASR returned no transcript"):
        _qwen_transcribe_wav_bytes(b"RIFFmock", language="en")
