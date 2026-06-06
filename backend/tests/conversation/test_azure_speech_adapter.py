from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.conversation.azure_speech import synthesize_reply_audio


@patch("app.modules.conversation.azure_speech._dashscope_synthesize_wav_bytes", return_value=b"RIFFmockWAVE")
def test_synthesize_reply_audio_returns_base64_wav(mock_synthesize):
    audio_data, audio_format = synthesize_reply_audio("Hello there.")

    assert audio_format == "wav_pcm16"
    assert isinstance(audio_data, str)
    assert audio_data
    mock_synthesize.assert_called_once()


@patch(
    "app.modules.conversation.azure_speech._dashscope_synthesize_wav_bytes",
    side_effect=RuntimeError("tts failed"),
)
def test_synthesize_reply_audio_falls_back_to_mock_beep(_mock_synthesize):
    audio_data, audio_format = synthesize_reply_audio("Hello there.")

    assert audio_format == "wav_pcm16"
    assert isinstance(audio_data, str)
    assert audio_data
