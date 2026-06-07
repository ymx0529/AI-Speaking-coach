import base64
from io import BytesIO
from unittest.mock import AsyncMock, patch
import wave

import pytest

pytestmark = pytest.mark.anyio

from app.core.types import PronScore, WordScore
from app.modules.coach import pronunciation_service


def _wav_b64(pcm: bytes = b"\x00\x00" * 1600, *, sample_rate: int = 16000) -> str:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm)
    return base64.b64encode(buffer.getvalue()).decode()


async def test_empty_transcript_returns_none():
    result = await pronunciation_service.assess("", "somebase64")
    assert result is None


async def test_whitespace_transcript_returns_none():
    result = await pronunciation_service.assess("   ", "somebase64")
    assert result is None


async def test_no_audio_returns_none():
    result = await pronunciation_service.assess("Hello world", None)
    assert result is None


async def test_missing_xfyun_credentials_returns_none_when_provider_xfyun(monkeypatch):
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.pronunciation_provider", "xfyun")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_app_id", "")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_api_key", "")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_api_secret", "")

    result = await pronunciation_service.assess("Hello", _wav_b64())

    assert result is None


async def test_missing_azure_key_returns_none(monkeypatch):
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.pronunciation_provider", "azure")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.azure_speech_key", "")
    result = await pronunciation_service.assess("Hello", _wav_b64())
    assert result is None


async def test_azure_sdk_not_installed_returns_none(monkeypatch):
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.pronunciation_provider", "azure")
    monkeypatch.setattr(
        "app.modules.coach.pronunciation_service.settings.azure_speech_key", "fake-key"
    )
    with patch("builtins.__import__", side_effect=ImportError("No module named 'azure'")):
        result = await pronunciation_service.assess("Hello", _wav_b64())
    assert result is None


async def test_azure_exception_returns_none(monkeypatch):
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.pronunciation_provider", "azure")
    monkeypatch.setattr(
        "app.modules.coach.pronunciation_service.settings.azure_speech_key", "fake-key"
    )
    with patch(
        "app.modules.coach.pronunciation_service.asyncio.to_thread",
        new=AsyncMock(side_effect=RuntimeError("Azure connection failed")),
    ):
        result = await pronunciation_service.assess("Hello", _wav_b64())
    assert result is None


async def test_assess_prefers_xfyun_when_configured(monkeypatch):
    expected = PronScore(overall=86, accuracy=82, fluency=90, completeness=88)

    async def fake_to_thread(func, *args):
        return func(*args)

    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.pronunciation_provider", "auto")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_app_id", "app")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_api_key", "key")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_api_secret", "secret")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr("app.modules.coach.pronunciation_service._run_xfyun_ise", lambda *_: expected)

    result = await pronunciation_service.assess("Hello", _wav_b64())

    assert result == expected


async def test_assess_auto_falls_back_to_azure_when_xfyun_returns_none(monkeypatch):
    expected = PronScore(overall=76, accuracy=74, fluency=80, completeness=82)

    async def fake_to_thread(func, *args):
        return func(*args)

    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.pronunciation_provider", "auto")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_app_id", "app")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_api_key", "key")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_api_secret", "secret")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.azure_speech_key", "fake-key")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr("app.modules.coach.pronunciation_service._run_xfyun_ise", lambda *_: None)
    monkeypatch.setattr("app.modules.coach.pronunciation_service._run_azure", lambda *_: expected)

    result = await pronunciation_service.assess("Hello", _wav_b64())

    assert result == expected


def test_xfyun_ise_stream_result_maps_to_pron_score(monkeypatch):
    pcm = b"\x01\x00" * 1600
    xml = """
    <xml_result>
      <read_sentence>
        <sentence accuracy_score="78.6" fluency_score="88.2" integrity_score="92.0">
          <total_score value="83.4" />
          <word content="hello" accuracy_score="68.2" perr_msg="1" />
          <word content="world" accuracy_score="90.1" perr_msg="0" />
        </sentence>
      </read_sentence>
    </xml_result>
    """

    class FakeIseClient:
        last_kwargs = None
        last_text = ""
        last_audio = b""

        def __init__(self, **kwargs):
            FakeIseClient.last_kwargs = kwargs

        def stream(self, text, audio_file):
            FakeIseClient.last_text = text
            FakeIseClient.last_audio = audio_file.read()
            yield {"data": base64.b64encode(xml.encode("utf-8")).decode("utf-8")}

    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_app_id", "app")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_api_key", "key")
    monkeypatch.setattr("app.modules.coach.pronunciation_service.settings.xfyun_api_secret", "secret")
    monkeypatch.setattr("app.modules.coach.pronunciation_service._get_ise_client_class", lambda: FakeIseClient)

    result = pronunciation_service._run_xfyun_ise("Hello world", _wav_b64(pcm))

    assert result == PronScore(
        overall=83.4,
        accuracy=78.6,
        fluency=88.2,
        completeness=92.0,
        words=[
            WordScore(word="hello", accuracy_score=68.2, error_type="Mispronunciation"),
            WordScore(word="world", accuracy_score=90.1, error_type="None"),
        ],
    )
    assert FakeIseClient.last_text == "\ufeffHello world"
    assert FakeIseClient.last_audio == pcm
    assert FakeIseClient.last_kwargs["ent"] == "en_vip"
    assert FakeIseClient.last_kwargs["category"] == "read_sentence"
    assert FakeIseClient.last_kwargs["extra_ability"] == "multi_dimension"


def test_extract_ise_chunk_data_accepts_dict_and_string():
    encoded = base64.b64encode(b"<xml_result />").decode("utf-8")

    assert pronunciation_service._extract_ise_chunk_data({"data": encoded}) == encoded
    assert pronunciation_service._extract_ise_chunk_data(encoded) == encoded
    assert pronunciation_service._extract_ise_chunk_data({"code": 101, "data": encoded}) is None
    assert pronunciation_service._extract_ise_chunk_data({"data": {"nested": encoded}}) is None


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
