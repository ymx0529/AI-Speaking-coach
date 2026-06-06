from __future__ import annotations

from app.core import ws_hub
from app.core.types import SpeakerTurnEvent, TurnTranscriptReadyEvent
from app.modules.coach import pronunciation_service, store as coach_store


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

    coach_store.init_turn(transcript_event)

    pron_score = await pronunciation_service.assess(
        transcript=transcript_event.transcript,
        wav_audio_b64=transcript_event.wav_audio_b64,
    )

    if pron_score is not None:
        record = coach_store.get_turn(transcript_event.session_id, transcript_event.turn_id)
        if record is not None:
            record.pronunciation = pron_score
        await ws_hub.send(
            transcript_event.session_id,
            pronunciation_service.build_ws_payload(
                transcript_event.session_id,
                transcript_event.turn_id,
                pron_score,
            ),
        )
    # Correction analysis added in PR 3 — status set to "analyzed" there
