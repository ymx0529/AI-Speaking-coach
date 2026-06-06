from __future__ import annotations

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.conversation.azure_speech import build_partial_transcript, synthesize_reply_audio, transcribe_chunks


def test_build_partial_transcript_returns_listening_for_non_text_binary():
    chunks = [
        (0, "AAECAwQF"),
    ]

    partial = build_partial_transcript(chunks)

    assert partial == "Listening..."


def test_transcribe_chunks_supports_existing_mock_text_path():
    chunks = [
        (0, "SGVsbG8sIEkgd291bGQgbGlrZQ=="),
        (1, "IHRvIGludHJvZHVjZSBteXNlbGYu"),
    ]

    text, duration_ms = transcribe_chunks(chunks)

    assert text == "Hello, I would like to introduce myself."
    assert duration_ms > 0


@patch("app.modules.conversation.azure_speech._azure_synthesize_wav_bytes", return_value=b"RIFFmockWAVE")
def test_synthesize_reply_audio_returns_base64_wav(mock_synthesize):
    audio_data, audio_format = synthesize_reply_audio("Hello there.")

    assert audio_format == "wav_pcm16"
    assert isinstance(audio_data, str)
    assert audio_data
    mock_synthesize.assert_called_once()
