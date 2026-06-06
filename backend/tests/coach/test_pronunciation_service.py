import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.anyio

from app.core.types import PronScore, WordScore
from app.modules.coach import pronunciation_service


async def test_empty_transcript_returns_none():
    result = await pronunciation_service.assess("", "somebase64")
    assert result is None


async def test_whitespace_transcript_returns_none():
    result = await pronunciation_service.assess("   ", "somebase64")
    assert result is None


async def test_no_audio_returns_none():
    result = await pronunciation_service.assess("Hello world", None)
    assert result is None


async def test_missing_azure_key_returns_none(monkeypatch):
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.azure_speech_key", "")
    result = await pronunciation_service.assess("Hello", base64.b64encode(b"audio").decode())
    assert result is None


async def test_azure_sdk_not_installed_returns_none(monkeypatch):
    monkeypatch.setattr(
        "app.modules.coach.pronunciation_service.settings.azure_speech_key", "fake-key"
    )
    with patch("builtins.__import__", side_effect=ImportError("No module named 'azure'")):
        result = await pronunciation_service.assess(
            "Hello", base64.b64encode(b"audio").decode()
        )
    assert result is None


async def test_azure_exception_returns_none(monkeypatch):
    monkeypatch.setattr(
        "app.modules.coach.pronunciation_service.settings.azure_speech_key", "fake-key"
    )
    with patch(
        "app.modules.coach.pronunciation_service.asyncio.to_thread",
        new=AsyncMock(side_effect=RuntimeError("Azure connection failed")),
    ):
        result = await pronunciation_service.assess(
            "Hello", base64.b64encode(b"audio").decode()
        )
    assert result is None


def test_build_ws_payload_structure():
    score = PronScore(
        overall=80.0,
        accuracy=75.0,
        fluency=85.0,
        completeness=90.0,
        words=[WordScore(word="hello", accuracy_score=78.0, error_type="None")],
    )
    payload = pronunciation_service.build_ws_payload("sess-1", "turn-1", score)
    assert payload["type"] == "analysis.pronunciation"
    assert payload["session_id"] == "sess-1"
    assert payload["turn_id"] == "turn-1"
    assert payload["overall"] == 80.0
    assert len(payload["words"]) == 1


def test_normalise_error_type_unknown_falls_back_to_none():
    result = pronunciation_service._normalise_error_type("WeirdValue")
    assert result == "None"


def test_normalise_error_type_valid_passes_through():
    result = pronunciation_service._normalise_error_type(
        type("E", (), {"name": "Mispronunciation"})()
    )
    assert result == "Mispronunciation"
