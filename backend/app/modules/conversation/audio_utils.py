from __future__ import annotations

import base64
import binascii


def decode_base64_chunk(data: str) -> bytes:
    try:
        return base64.b64decode(data.encode("utf-8"), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 audio chunk") from exc


def merge_sorted_chunks(chunks: list[tuple[int, str]]) -> bytes:
    ordered = sorted(chunks, key=lambda item: item[0])
    return b"".join(decode_base64_chunk(chunk) for _, chunk in ordered)


def mock_bytes_to_text(audio_bytes: bytes) -> str:
    text = audio_bytes.decode("utf-8", errors="ignore").strip()
    return " ".join(text.split())
