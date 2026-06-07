from __future__ import annotations

import asyncio
import audioop
import base64
import binascii
from io import BytesIO
import logging
from typing import Any
import wave
from xml.etree import ElementTree

from app.core.config import settings
from app.core.types import PronScore, WordScore

logger = logging.getLogger(__name__)

_VALID_ERROR_TYPES = {"None", "Omission", "Insertion", "Mispronunciation"}
_XFYUN_TEXT_PREFIX = "\ufeff"


async def assess(transcript: str, wav_audio_b64: str | None) -> PronScore | None:
    """Run pronunciation assessment against the given transcript and audio."""
    if not transcript.strip():
        return None
    if wav_audio_b64 is None:
        return None

    provider = settings.pronunciation_provider.lower().strip()
    if provider not in {"auto", "xfyun", "azure"}:
        logger.warning("Unknown pronunciation provider %s", settings.pronunciation_provider)
        return None

    if provider in {"auto", "xfyun"} and _has_xfyun_credentials():
        try:
            result = await asyncio.to_thread(_run_xfyun_ise, transcript, wav_audio_b64)
            if result is not None:
                return result
            logger.warning("Xfyun ISE returned no pronunciation result")
            if provider == "xfyun":
                return None
        except Exception as exc:
            logger.error("Xfyun ISE pronunciation assessment failed: %s", exc)
            if provider == "xfyun":
                return None

    if provider in {"auto", "azure"}:
        if not settings.azure_speech_key:
            logger.warning("AZURE_SPEECH_KEY not set - skipping Azure pronunciation assessment")
            return None
        try:
            return await asyncio.to_thread(_run_azure, transcript, wav_audio_b64)
        except Exception as exc:
            logger.error("Azure pronunciation assessment failed: %s", exc)
            return None

    if provider == "xfyun":
        logger.warning("XFYUN_APP_ID/API_KEY/API_SECRET not set - skipping pronunciation assessment")
    return None


def _has_xfyun_credentials() -> bool:
    return bool(settings.xfyun_app_id and settings.xfyun_api_key and settings.xfyun_api_secret)


def _get_ise_client_class():
    try:
        from xfyunsdkspeech.ise_client import IseClient  # noqa: PLC0415
    except ImportError:
        logger.warning("xfyunsdkspeech not installed - skipping Xfyun ISE assessment")
        return None
    return IseClient


def _run_xfyun_ise(transcript: str, wav_audio_b64: str) -> PronScore | None:
    """Blocking Xfyun ISE SDK call. Must be run in a worker thread."""
    client_class = _get_ise_client_class()
    if client_class is None:
        return None

    audio_bytes = _audio_b64_to_pcm16_mono(wav_audio_b64)
    if not audio_bytes:
        return None

    client = _build_ise_client(client_class)
    decoded_results: list[str] = []
    text = _XFYUN_TEXT_PREFIX + transcript.strip()

    for chunk in client.stream(text, BytesIO(audio_bytes)):
        data = _extract_ise_chunk_data(chunk)
        if data:
            decoded_results.append(base64.b64decode(data).decode("utf-8", errors="ignore"))

    for result_xml in reversed(decoded_results):
        score = _parse_ise_xml_result(result_xml)
        if score is not None:
            return score
    return None


def _extract_ise_chunk_data(chunk: Any) -> str | None:
    if isinstance(chunk, str):
        return chunk
    if not isinstance(chunk, dict):
        return None
    code = chunk.get("code")
    if code not in (None, 0, "0"):
        logger.warning("Xfyun ISE returned non-zero code: %s", chunk)
        return None
    data = chunk.get("data")
    return data if isinstance(data, str) else None


def _build_ise_client(client_class):
    base_kwargs = {
        "app_id": settings.xfyun_app_id,
        "api_key": settings.xfyun_api_key,
        "api_secret": settings.xfyun_api_secret,
        "aue": settings.xfyun_ise_aue,
        "auf": settings.xfyun_ise_auf,
        "group": settings.xfyun_ise_group,
        "ent": settings.xfyun_ise_ent,
        "category": settings.xfyun_ise_category,
        "request_timeout": settings.xfyun_ise_timeout_sec,
    }
    optional_kwargs = {
        "rst": settings.xfyun_ise_rst,
        "ise_unite": settings.xfyun_ise_unite,
        "extra_ability": settings.xfyun_ise_extra_ability,
    }
    optional_kwargs = {key: value for key, value in optional_kwargs.items() if value}

    try:
        return client_class(**base_kwargs, **optional_kwargs)
    except TypeError:
        logger.warning("xfyunsdkspeech IseClient rejected optional ISE parameters; retrying minimal config")
        return client_class(**base_kwargs)


def _audio_b64_to_pcm16_mono(wav_audio_b64: str) -> bytes:
    try:
        audio_bytes = base64.b64decode(wav_audio_b64.encode("utf-8"), validate=True)
    except (binascii.Error, ValueError):
        logger.warning("Invalid base64 audio payload for pronunciation assessment")
        return b""

    if audio_bytes.startswith(b"RIFF"):
        return _wav_bytes_to_pcm16_mono(audio_bytes)
    return audio_bytes


def _wav_bytes_to_pcm16_mono(wav_bytes: bytes) -> bytes:
    with wave.open(BytesIO(wav_bytes), "rb") as wav_file:
        sample_width = wav_file.getsampwidth()
        channels = wav_file.getnchannels()
        frame_rate = wav_file.getframerate()
        pcm = wav_file.readframes(wav_file.getnframes())

    if sample_width != 2:
        pcm = audioop.lin2lin(pcm, sample_width, 2)
        sample_width = 2
    if channels == 2:
        pcm = audioop.tomono(pcm, sample_width, 0.5, 0.5)
        channels = 1
    elif channels > 2:
        pcm = audioop.tomono(pcm, sample_width, 1.0, 0.0)
        channels = 1
    if frame_rate != 16000:
        pcm, _ = audioop.ratecv(pcm, sample_width, channels, frame_rate, 16000, None)
    return pcm


def _parse_ise_xml_result(result_xml: str) -> PronScore | None:
    try:
        root = ElementTree.fromstring(result_xml.lstrip("\ufeff").strip())
    except ElementTree.ParseError as exc:
        logger.warning("Failed to parse Xfyun ISE XML result: %s", exc)
        return None

    overall = _find_total_score(root) or _find_score_attr(root, ["total_score", "standard_score"])
    if overall is None:
        return None

    accuracy = _find_score_attr(root, ["accuracy_score", "phone_score"]) or overall
    fluency = _find_score_attr(root, ["fluency_score"]) or overall
    completeness = (
        _find_score_attr(root, ["integrity_score", "completeness_score", "complete_score"])
        or overall
    )

    return PronScore(
        overall=overall,
        accuracy=accuracy,
        fluency=fluency,
        completeness=completeness,
        words=_parse_word_scores(root),
    )


def _find_total_score(root: ElementTree.Element) -> float | None:
    for element in root.iter():
        if _tag_name(element) == "total_score":
            return _safe_score(element.attrib.get("value"))
    return None


def _find_score_attr(root: ElementTree.Element, names: list[str]) -> float | None:
    for element in root.iter():
        for name in names:
            score = _safe_score(element.attrib.get(name))
            if score is not None:
                return score
    return None


def _parse_word_scores(root: ElementTree.Element) -> list[WordScore]:
    words: list[WordScore] = []
    for element in root.iter():
        if _tag_name(element) != "word":
            continue
        word = (
            element.attrib.get("content")
            or element.attrib.get("word")
            or element.attrib.get("text")
            or ""
        ).strip()
        if not word:
            continue
        score = (
            _safe_score(element.attrib.get("accuracy_score"))
            or _safe_score(element.attrib.get("total_score"))
            or 0.0
        )
        words.append(
            WordScore(
                word=word,
                accuracy_score=score,
                error_type=_normalise_ise_error_type(element),
            )
        )
    return words


def _tag_name(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _safe_score(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return round(max(0.0, min(100.0, score)), 1)


def _normalise_ise_error_type(element: ElementTree.Element) -> str:
    raw = (
        element.attrib.get("error_type")
        or element.attrib.get("perr_msg")
        or element.attrib.get("serr_msg")
        or element.attrib.get("dp_message")
        or ""
    )
    text = str(raw).strip().lower()
    if text in {"", "0", "none", "normal", "correct"}:
        return "None"
    if "omit" in text or "missing" in text:
        return "Omission"
    if "insert" in text:
        return "Insertion"
    return "Mispronunciation"


def _run_azure(transcript: str, wav_audio_b64: str) -> PronScore | None:
    """Blocking Azure SDK call. Must be run in a worker thread."""
    try:
        import azure.cognitiveservices.speech as speechsdk  # noqa: PLC0415
    except ImportError:
        logger.warning("azure-cognitiveservices-speech not installed - skipping")
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
