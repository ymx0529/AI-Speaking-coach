import pytest

pytestmark = pytest.mark.anyio

from app.core.types import SpeakerTurnEvent, TurnTranscriptReadyEvent
from app.core.types import PronScore
from app.modules.coach import store as coach_store
from app.modules.coach.turn_handler import on_turn_event


@pytest.fixture(autouse=True)
def clear_store():
    coach_store._store.clear()
    yield
    coach_store._store.clear()


def _transcript_event(**kwargs) -> TurnTranscriptReadyEvent:
    defaults = dict(
        session_id="sess-a",
        turn_id="turn-a",
        scene_id="restaurant",
        difficulty=1,
        persona_id="waiter",
        transcript="I want pasta.",
        wav_audio_b64=None,
        assistant_reply_text="Sure!",
        turn_duration_ms=800,
    )
    return TurnTranscriptReadyEvent(**{**defaults, **kwargs})


def _speaker_event(**kwargs):
    pron = PronScore(overall=75, accuracy=70, fluency=78, completeness=90)
    defaults = dict(
        session_id="sess-b",
        turn_id="turn-b",
        scene_id="interview",
        user_text="I am a developer.",
        pron_score=pron,
        ai_reply="Interesting.",
    )
    return SpeakerTurnEvent(**{**defaults, **kwargs})


async def test_v2_event_creates_record():
    await on_turn_event(_transcript_event())
    assert coach_store.get_turn("sess-a", "turn-a") is not None


async def test_v1_speaker_event_creates_record():
    await on_turn_event(_speaker_event())
    record = coach_store.get_turn("sess-b", "turn-b")
    assert record is not None
    assert record.transcript == "I am a developer."


async def test_replay_same_turn_id_is_idempotent():
    await on_turn_event(_transcript_event())
    await on_turn_event(_transcript_event())
    assert len(coach_store.get_session_turns("sess-a")) == 1


async def test_unknown_event_type_is_ignored():
    await on_turn_event({"type": "garbage"})
    assert coach_store.get_session_turns("unknown") == []
