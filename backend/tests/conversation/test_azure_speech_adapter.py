from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.conversation.azure_speech import split_reply_for_tts, synthesize_reply_audio


def test_split_reply_for_tts_uses_sentence_boundaries():
    segments = split_reply_for_tts("Sure, I can help. What kind of role are you applying for?")

    assert segments == [
        "Sure, I can help.",
        "What kind of role are you applying for?",
    ]


def test_split_reply_for_tts_splits_long_sentence():
    segments = split_reply_for_tts(
        "Please describe a project where you improved performance, reduced latency, "
        "and explained the result clearly to your team.",
        max_chars=70,
    )

    assert segments == [
        "Please describe a project where you improved performance,",
        "reduced latency, and explained the result clearly to your team.",
    ]


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
