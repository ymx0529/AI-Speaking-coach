from __future__ import annotations

import base64
import json
from uuid import uuid4

import websocket

from app.core.config import settings
from app.modules.conversation.audio_utils import (
    convert_audio_chunks_to_pcm16_bytes,
    merge_sorted_chunks,
    mock_bytes_to_text,
)


def build_partial_transcript(chunks: list[tuple[int, str]]) -> str:
    if not chunks:
        return ""
    merged = merge_sorted_chunks(chunks)
    mock_text = mock_bytes_to_text(merged)
    return mock_text or "Listening..."


def transcribe_chunks(
    chunks: list[tuple[int, str]],
    *,
    source_format: str = "webm",
    language: str | None = None,
) -> tuple[str, int]:
    merged = merge_sorted_chunks(chunks)
    mock_text = mock_bytes_to_text(merged)
    if mock_text:
        duration_ms = max(800, len(merged) * 40)
        return mock_text, duration_ms

    pcm16_bytes = convert_audio_chunks_to_pcm16_bytes(chunks, source_format=source_format)
    text = _qwen_transcribe_pcm16(pcm16_bytes, language=language)
    duration_ms = max(800, len(pcm16_bytes) // 32)
    return text, duration_ms


def _qwen_transcribe_pcm16(pcm16_bytes: bytes, *, language: str | None = None) -> str:
    if not settings.dashscope_api_key:
        raise RuntimeError("DashScope API key is missing.")

    ws = websocket.create_connection(
        settings.qwen_realtime_url,
        header=[f"Authorization: Bearer {settings.dashscope_api_key}"],
        timeout=settings.qwen_ws_timeout_sec,
    )

    try:
        ws.send(
            json.dumps(
                _make_event(
                    "session.update",
                    session={
                        "modalities": ["text"],
                        "input_audio_format": "pcm",
                        "sample_rate": 16000,
                        "input_audio_transcription": {
                            "language": language or settings.qwen_input_language,
                        },
                        "turn_detection": None,
                    },
                )
            )
        )

        for audio_chunk in _chunk_bytes(pcm16_bytes):
            ws.send(
                json.dumps(
                    _make_event(
                        "input_audio_buffer.append",
                        audio=base64.b64encode(audio_chunk).decode("utf-8"),
                    )
                )
            )

        ws.send(json.dumps(_make_event("input_audio_buffer.commit")))
        ws.send(json.dumps(_make_event("session.finish")))

        final_transcript = ""
        latest_partial = ""

        while True:
            event = json.loads(ws.recv())
            event_type = event.get("type", "")

            if event_type in {
                "conversation.item.input_audio_transcription.delta",
                "conversation.item.input_audio_transcription.text",
            }:
                latest_partial = _extract_transcript(event) or latest_partial
            elif event_type == "conversation.item.input_audio_transcription.completed":
                final_transcript = _extract_transcript(event) or final_transcript
            elif event_type == "conversation.item.input_audio_transcription.failed":
                raise RuntimeError(_extract_error_message(event, default="Qwen ASR transcription failed."))
            elif event_type == "error":
                raise RuntimeError(_extract_error_message(event, default="Qwen realtime websocket returned an error."))
            elif event_type == "session.finished":
                if final_transcript:
                    return final_transcript.strip()
                if latest_partial:
                    return latest_partial.strip()
                raise RuntimeError("Qwen ASR returned no transcript.")
    finally:
        ws.close()


def _chunk_bytes(data: bytes, *, chunk_size: int = 3200) -> list[bytes]:
    return [data[index : index + chunk_size] for index in range(0, len(data), chunk_size)] or [b""]


def _make_event(event_type: str, **payload: object) -> dict[str, object]:
    message: dict[str, object] = {
        "event_id": f"event_{uuid4().hex}",
        "type": event_type,
    }
    message.update(payload)
    return message


def _extract_transcript(event: dict[str, object]) -> str:
    for field in ("transcript", "text", "delta", "stash"):
        value = event.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _extract_error_message(event: dict[str, object], *, default: str) -> str:
    error = event.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message
    return default
