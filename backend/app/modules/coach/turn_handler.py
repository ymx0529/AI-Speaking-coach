from __future__ import annotations

from app.core.types import SpeakerTurnEvent, TurnTranscriptReadyEvent
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
    coach_store.init_turn(transcript_event)
    # Pronunciation and correction analysis added in PR 2 and PR 3
