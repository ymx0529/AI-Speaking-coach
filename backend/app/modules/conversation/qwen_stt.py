from __future__ import annotations

import base64

from openai import OpenAI

from app.core.config import settings
from app.modules.conversation.audio_utils import (
    convert_audio_bytes_to_wav_bytes,
    convert_audio_chunks_to_wav_bytes,
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

    try:
        wav_bytes = convert_audio_bytes_to_wav_bytes(merged, source_format=source_format)
    except ValueError:
        wav_bytes = convert_audio_chunks_to_wav_bytes(chunks, source_format=source_format)
        if not wav_bytes:
            raise
    text = _qwen_transcribe_wav_bytes(wav_bytes, language=language)
    duration_ms = max(800, len(wav_bytes) // 32)
    return text, duration_ms


def _get_client() -> OpenAI:
    if not settings.dashscope_api_key:
        raise RuntimeError("DashScope API key is missing.")

    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        timeout=settings.qwen_request_timeout_sec,
    )


def _qwen_transcribe_wav_bytes(wav_bytes: bytes, *, language: str | None = None) -> str:
    data_uri = _wav_bytes_to_data_uri(wav_bytes)
    client = _get_client()
    completion = client.chat.completions.create(
        model=settings.qwen_asr_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": data_uri,
                        },
                    }
                ],
            }
        ],
        stream=False,
        extra_body={
            "asr_options": {
                "language": language or settings.qwen_input_language,
                "enable_itn": False,
            }
        },
    )
    content = completion.choices[0].message.content
    if isinstance(content, str) and content.strip():
        return content.strip()
    raise RuntimeError("Qwen ASR returned no transcript.")


def _wav_bytes_to_data_uri(wav_bytes: bytes) -> str:
    encoded = base64.b64encode(wav_bytes).decode("utf-8")
    return f"data:audio/wav;base64,{encoded}"
