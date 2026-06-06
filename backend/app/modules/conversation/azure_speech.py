from __future__ import annotations

import io
import json
import math
import urllib.request
import wave
from base64 import b64encode

from app.core.config import settings


def synthesize_reply_audio(text: str) -> tuple[str, str]:
    try:
        wav_bytes = _dashscope_synthesize_wav_bytes(text)
    except Exception:
        wav_bytes = _mock_beep_wav_bytes(text)
    return b64encode(wav_bytes).decode("utf-8"), "wav_pcm16"


def _dashscope_synthesize_wav_bytes(text: str) -> bytes:
    if not settings.dashscope_api_key:
        raise RuntimeError("DashScope API key is missing.")

    payload = json.dumps(
        {
            "model": settings.cosyvoice_model,
            "input": {
                "text": text,
                "voice": settings.cosyvoice_voice,
                "format": settings.cosyvoice_format,
                "sample_rate": settings.cosyvoice_sample_rate,
            },
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        settings.cosyvoice_api_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.dashscope_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=settings.qwen_request_timeout_sec) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    audio = response_payload.get("output", {}).get("audio", {})
    audio_url = audio.get("url")
    if not isinstance(audio_url, str) or not audio_url:
        raise RuntimeError("CosyVoice did not return an audio URL.")

    with urllib.request.urlopen(audio_url, timeout=settings.qwen_request_timeout_sec) as audio_response:
        return audio_response.read()


def _mock_beep_wav_bytes(text: str) -> bytes:
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
    return buffer.getvalue()
