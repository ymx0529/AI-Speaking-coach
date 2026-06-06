from __future__ import annotations

import asyncio
import base64
import logging

from app.core.config import settings
from app.core.types import PronScore, WordScore

logger = logging.getLogger(__name__)

_VALID_ERROR_TYPES = {"None", "Omission", "Insertion", "Mispronunciation"}


async def assess(transcript: str, wav_audio_b64: str | None) -> PronScore | None:
    """Run Azure pronunciation assessment against the given transcript.

    Returns None when:
    - transcript is empty
    - wav_audio_b64 is None (audio not yet provided by Dev A)
    - Azure credentials are not configured
    - Azure SDK is not installed
    - The recognition call fails for any reason
    """
    if not transcript.strip():
        return None
    if wav_audio_b64 is None:
        return None
    if not settings.azure_speech_key:
        logger.warning("AZURE_SPEECH_KEY not set — skipping pronunciation assessment")
        return None

    try:
        return await asyncio.to_thread(_run_azure, transcript, wav_audio_b64)
    except Exception as exc:
        logger.error("Pronunciation assessment failed: %s", exc)
        return None


def _run_azure(transcript: str, wav_audio_b64: str) -> PronScore | None:
    """Blocking Azure SDK call — must be run in a thread via asyncio.to_thread."""
    try:
        import azure.cognitiveservices.speech as speechsdk  # noqa: PLC0415
    except ImportError:
        logger.warning("azure-cognitiveservices-speech not installed — skipping")
        return None

    audio_bytes = base64.b64decode(wav_audio_b64)

    speech_config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region,
    )
    pron_config = speechsdk.PronunciationAssessmentConfig(
        reference_text=transcript,
        grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
        granularity=speechsdk.PronunciationAssessmentGranularity.Word,
    )

    stream = speechsdk.audio.PushAudioInputStream()
    audio_config = speechsdk.audio.AudioConfig(stream=stream)
    stream.write(audio_bytes)
    stream.close()

    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
    )
    pron_config.apply_to(recognizer)

    result = recognizer.recognize_once()
    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        logger.warning("ASR result reason: %s", result.reason)
        return None

    pron_result = speechsdk.PronunciationAssessmentResult(result)

    words = [
        WordScore(
            word=w.word,
            accuracy_score=round(w.accuracy_score, 1),
            error_type=_normalise_error_type(w.error_type),
        )
        for w in pron_result.words
    ]

    return PronScore(
        overall=round(pron_result.pronunciation_score, 1),
        accuracy=round(pron_result.accuracy_score, 1),
        fluency=round(pron_result.fluency_score, 1),
        completeness=round(pron_result.completeness_score, 1),
        words=words,
    )


def _normalise_error_type(raw) -> str:
    name = raw.name if hasattr(raw, "name") else str(raw)
    return name if name in _VALID_ERROR_TYPES else "None"


def build_ws_payload(session_id: str, turn_id: str, score: PronScore) -> dict:
    """Build the analysis.pronunciation WebSocket message."""
    return {
        "type": "analysis.pronunciation",
        "session_id": session_id,
        "turn_id": turn_id,
        **score.model_dump(),
    }
