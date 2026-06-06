import pytest

from app.core.types import TurnTranscriptReadyEvent
from app.modules.coach import store as coach_store


def _event(**kwargs) -> TurnTranscriptReadyEvent:
    defaults = dict(
        session_id="sess-1",
        turn_id="turn-1",
        scene_id="interview",
        difficulty=2,
        persona_id="interviewer",
        transcript="I enjoy solving problems.",
        audio_b64=None,
        assistant_reply_text="Tell me more.",
        turn_duration_ms=1500,
    )
    return TurnTranscriptReadyEvent(**{**defaults, **kwargs})


@pytest.fixture(autouse=True)
def clear_store():
    coach_store._store.clear()
    yield
    coach_store._store.clear()


def test_init_creates_pending_record():
    record = coach_store.init_turn(_event())
    assert record.session_id == "sess-1"
    assert record.turn_id == "turn-1"
    assert record.status == "pending"


def test_init_is_idempotent():
    r1 = coach_store.init_turn(_event())
    r2 = coach_store.init_turn(_event())
    assert r1 is r2
    assert len(coach_store.get_session_turns("sess-1")) == 1


def test_different_turns_stored_separately():
    coach_store.init_turn(_event(turn_id="turn-1"))
    coach_store.init_turn(_event(turn_id="turn-2"))
    assert len(coach_store.get_session_turns("sess-1")) == 2


def test_failed_turn_retains_transcript():
    coach_store.init_turn(_event())
    coach_store.set_status("sess-1", "turn-1", "failed")
    record = coach_store.get_turn("sess-1", "turn-1")
    assert record is not None
    assert record.status == "failed"
    assert record.transcript == "I enjoy solving problems."
