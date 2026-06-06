from __future__ import annotations

import io
import math
import wave
from base64 import b64encode
from tempfile import NamedTemporaryFile

import azure.cognitiveservices.speech as speechsdk

from app.core.config import settings
from app.modules.conversation.audio_utils import (
    decode_base64_chunk,
    merge_sorted_chunks,
    mock_bytes_to_text,
    convert_audio_bytes_to_wav_bytes,
)


def build_partial_transcript(chunks: list[tuple[int, str]]) -> str:
    if not chunks:
        return ""
    merged = merge_sorted_chunks(chunks)
    mock_text = mock_bytes_to_text(merged)
    return mock_text or "Listening..."


def build_partial_from_chunk(chunk_b64: str) -> str:
    return mock_bytes_to_text(decode_base64_chunk(chunk_b64))


def transcribe_chunks(chunks: list[tuple[int, str]]) -> tuple[str, int]:
    merged = merge_sorted_chunks(chunks)
    mock_text = mock_bytes_to_text(merged)
    if mock_text:
        duration_ms = max(800, len(merged) * 40)
        return mock_text, duration_ms

    wav_bytes = convert_audio_bytes_to_wav_bytes(merged, source_format="webm")
    text = _azure_transcribe_wav_bytes(wav_bytes)
    duration_ms = max(800, len(wav_bytes) // 32)
    return text, duration_ms


def synthesize_reply_audio(text: str) -> tuple[str, str]:
    try:
        wav_bytes = _azure_synthesize_wav_bytes(text)
    except RuntimeError:
        wav_bytes = _mock_beep_wav_bytes(text)
    return b64encode(wav_bytes).decode("utf-8"), "wav_pcm16"


def _ensure_azure_config() -> None:
    if not settings.azure_speech_key or not settings.azure_speech_region:
        raise RuntimeError("Azure Speech configuration is missing.")


def _azure_transcribe_wav_bytes(wav_bytes: bytes) -> str:
    _ensure_azure_config()
    speech_config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region,
    )

    with NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_file.write(wav_bytes)
        temp_path = tmp_file.name

    try:
        audio_config = speechsdk.audio.AudioConfig(filename=temp_path)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )
        result = recognizer.recognize_once_async().get()
    finally:
        try:
            import os

            os.remove(temp_path)
        except OSError:
            pass

    if result.reason == speechsdk.ResultReason.RecognizedSpeech and result.text:
        return result.text.strip()
    raise RuntimeError("Azure Speech recognition returned no text.")


def _azure_synthesize_wav_bytes(text: str) -> bytes:
    _ensure_azure_config()
    speech_config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region,
    )
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    )
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()
    if not result.audio_data:
        raise RuntimeError("Azure Speech synthesis returned no audio.")
    return result.audio_data


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
