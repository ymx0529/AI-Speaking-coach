from __future__ import annotations

import base64
import binascii
from io import BytesIO
import os

from pydub import AudioSegment

from app.core.config import settings

if settings.ffmpeg_binary:
    AudioSegment.converter = settings.ffmpeg_binary
    ffprobe_candidate = settings.ffmpeg_binary.replace("ffmpeg.exe", "ffprobe.exe")
    if os.path.exists(ffprobe_candidate):
        AudioSegment.ffprobe = ffprobe_candidate


def decode_base64_chunk(data: str) -> bytes:
    try:
        return base64.b64decode(data.encode("utf-8"), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 audio chunk") from exc


def merge_sorted_chunks(chunks: list[tuple[int, str]]) -> bytes:
    ordered = sorted(chunks, key=lambda item: item[0])
    return b"".join(decode_base64_chunk(chunk) for _, chunk in ordered)


def mock_bytes_to_text(audio_bytes: bytes) -> str:
    decoded = audio_bytes.decode("utf-8", errors="ignore").strip()
    normalized = " ".join(decoded.split())
    if not normalized:
        return ""

    printable_count = sum(char.isprintable() for char in normalized)
    printable_ratio = printable_count / max(len(normalized), 1)
    if printable_ratio < 0.85:
        return ""
    return normalized


def _normalize_audio_segment(audio_bytes: bytes, *, source_format: str) -> AudioSegment:
    try:
        segment = AudioSegment.from_file(BytesIO(audio_bytes), format=source_format)
    except Exception as exc:
        raise ValueError(f"Failed to decode {source_format} audio bytes") from exc
    return segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)


def convert_audio_bytes_to_wav_bytes(audio_bytes: bytes, *, source_format: str = "webm") -> bytes:
    normalized = _normalize_audio_segment(audio_bytes, source_format=source_format)
    output = BytesIO()
    normalized.export(output, format="wav")
    return output.getvalue()


def convert_audio_bytes_to_pcm16_bytes(audio_bytes: bytes, *, source_format: str = "webm") -> bytes:
    normalized = _normalize_audio_segment(audio_bytes, source_format=source_format)
    return normalized.raw_data


def convert_audio_chunks_to_wav_bytes(chunks: list[tuple[int, str]], *, source_format: str = "webm") -> bytes:
    combined: AudioSegment | None = None
    for _, chunk in sorted(chunks, key=lambda item: item[0]):
        segment = _normalize_audio_segment(decode_base64_chunk(chunk), source_format=source_format)
        combined = segment if combined is None else combined + segment

    if combined is None:
        return b""

    output = BytesIO()
    combined.export(output, format="wav")
    return output.getvalue()


def convert_audio_chunks_to_pcm16_bytes(chunks: list[tuple[int, str]], *, source_format: str = "webm") -> bytes:
    combined: AudioSegment | None = None
    for _, chunk in sorted(chunks, key=lambda item: item[0]):
        segment = _normalize_audio_segment(decode_base64_chunk(chunk), source_format=source_format)
        combined = segment if combined is None else combined + segment

    if combined is None:
        return b""
    return combined.raw_data
