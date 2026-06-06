from __future__ import annotations

import io
import math
import wave
from base64 import b64encode

from app.modules.conversation.audio_utils import decode_base64_chunk, merge_sorted_chunks, mock_bytes_to_text


def build_partial_transcript(chunks: list[tuple[int, str]]) -> str:
    if not chunks:
        return ""
    merged = merge_sorted_chunks(chunks)
    return mock_bytes_to_text(merged)


def build_partial_from_chunk(chunk_b64: str) -> str:
    return mock_bytes_to_text(decode_base64_chunk(chunk_b64))


def transcribe_chunks(chunks: list[tuple[int, str]]) -> tuple[str, int]:
    merged = merge_sorted_chunks(chunks)
    text = mock_bytes_to_text(merged)
    duration_ms = max(800, len(merged) * 40)
    return text, duration_ms


def synthesize_reply_audio(text: str) -> tuple[str, str]:
    duration_ms = min(max(len(text) * 20, 400), 1200)
    sample_rate = 16000
    frame_count = int(sample_rate * (duration_ms / 1000))
    amplitude = 8000
    frequency = 523.25
    frames = bytearray()
    for index in range(frame_count):
        sample = int(amplitude * math.sin(2 * math.pi * frequency * (index / sample_rate)))
        frames.extend(sample.to_bytes(2, byteorder="little", signed=True))

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(bytes(frames))

    return b64encode(buffer.getvalue()).decode("utf-8"), "wav_pcm16"
