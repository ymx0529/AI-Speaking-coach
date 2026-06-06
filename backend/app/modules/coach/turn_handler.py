from __future__ import annotations

import asyncio

from app.core import ws_hub
from app.core.types import SpeakerTurnEvent, TurnTranscriptReadyEvent
from app.modules.coach import correction_service, pronunciation_service
from app.modules.coach import store as coach_store


def _to_transcript_event(event: object) -> TurnTranscriptReadyEvent | None:
    """Normalize incoming event to TurnTranscriptReadyEvent.

    Handles both the v2 target format and the v1 SpeakerTurnEvent still
    published by conversation/router.py until Dev A migrates.
    """
    if isinstance(event, TurnTranscriptReadyEvent):
        return event
    if isinstance(event, SpeakerTurnEvent):
        return TurnTranscriptReadyEvent(
            session_id=event.session_id,
            turn_id=event.turn_id,
            scene_id=event.scene_id,
            difficulty=1,
            persona_id="",
            transcript=event.user_text,
            wav_audio_b64=None,
            assistant_reply_text=event.ai_reply,
            turn_duration_ms=0,
        )
    return None


async def on_turn_event(event: object) -> None:
    transcript_event = _to_transcript_event(event)
    if transcript_event is None:
        return

    record = coach_store.init_turn(transcript_event)

    # Run pronunciation and correction in parallel
    pron_score, (issues, grammar_score, expr_score, vocab_score) = await asyncio.gather(
        pronunciation_service.assess(
            transcript=transcript_event.transcript,
            wav_audio_b64=transcript_event.wav_audio_b64,
        ),
        correction_service.analyse(
            transcript=transcript_event.transcript,
            assistant_reply=transcript_event.assistant_reply_text,
        ),
    )

    # Write results to store
    if pron_score is not None:
        record.pronunciation = pron_score
    record.corrections = issues
    record.grammar_score = grammar_score
    record.expression_score = expr_score
    record.vocabulary_score = vocab_score
    coach_store.set_status(transcript_event.session_id, transcript_event.turn_id, "analyzed")

    # Push pronunciation result
    if pron_score is not None:
        await ws_hub.send(
            transcript_event.session_id,
            pronunciation_service.build_ws_payload(
                transcript_event.session_id,
                transcript_event.turn_id,
                pron_score,
            ),
        )

    # Push correction result (always push, even if issues list is empty)
    await ws_hub.send(
        transcript_event.session_id,
        correction_service.build_ws_payload(
            transcript_event.session_id,
            transcript_event.turn_id,
            issues,
        ),
    )
