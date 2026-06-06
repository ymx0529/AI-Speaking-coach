from __future__ import annotations

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
