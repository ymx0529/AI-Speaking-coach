from __future__ import annotations

from base64 import b64encode
from pathlib import Path
import sys
import wave
from io import BytesIO

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.conversation.audio_utils import (
    convert_audio_bytes_to_pcm16_bytes,
    convert_audio_chunks_to_pcm16_bytes,
    convert_audio_bytes_to_wav_bytes,
    decode_base64_chunk,
    merge_sorted_chunks,
    mock_bytes_to_text,
)


def test_merge_sorted_chunks_keeps_sequence_order():
    chunks = [
        (2, "Yw=="),
        (0, "YQ=="),
        (1, "Yg=="),
    ]

    merged = merge_sorted_chunks(chunks)

    assert merged == b"abc"


def test_decode_base64_chunk_rejects_invalid_data():
    try:
        decode_base64_chunk("%%%")
    except ValueError as exc:
        assert "Invalid base64 audio chunk" in str(exc)
    else:
        raise AssertionError("Expected invalid base64 chunk to raise ValueError")


def test_convert_audio_bytes_to_wav_bytes_normalizes_to_pcm_wav():
    source = BytesIO()
    with wave.open(source, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 400)

    converted = convert_audio_bytes_to_wav_bytes(source.getvalue(), source_format="wav")

    assert converted[:4] == b"RIFF"
    assert b"WAVE" in converted[:16]


def test_convert_audio_bytes_to_pcm16_bytes_returns_raw_pcm_frames():
    source = BytesIO()
    with wave.open(source, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x01\x00" * 400)

    converted = convert_audio_bytes_to_pcm16_bytes(source.getvalue(), source_format="wav")

    assert isinstance(converted, bytes)
    assert converted[:4] != b"RIFF"
    assert len(converted) > 0


def test_convert_audio_chunks_to_pcm16_bytes_combines_multiple_segments():
    first = BytesIO()
    with wave.open(first, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x01\x00" * 200)

    second = BytesIO()
    with wave.open(second, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x02\x00" * 200)

    chunks = [
        (1, b64encode(second.getvalue()).decode("utf-8")),
        (0, b64encode(first.getvalue()).decode("utf-8")),
    ]

    converted = convert_audio_chunks_to_pcm16_bytes(chunks, source_format="wav")

    assert len(converted) == 800


def test_mock_bytes_to_text_returns_empty_for_binary_like_data():
    assert mock_bytes_to_text(b"\x00\x01\x02\x03\x04\x05") == ""
