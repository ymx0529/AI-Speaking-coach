from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.types import PronScore
from app.modules.conversation import session_manager


def setup_function() -> None:
    session_manager._sessions.clear()


def test_start_session_creates_clean_state():
    session_manager.start_session(
        session_id="session-1",
        scene_id="interview",
        difficulty=2,
        persona_id="strict_interviewer",
    )

    session = session_manager.get_session("session-1")

    assert session is not None
    assert session.session_id == "session-1"
    assert session.scene_id == "interview"
    assert session.difficulty == 2
    assert session.persona_id == "strict_interviewer"
    assert session.current_turn_id is None
    assert session.current_turn_state == "idle"
    assert session.current_turn_audio_chunks == []
    assert session.history == []
    assert session.session_status == "active"
    assert session.retain_until_ms is None


def test_first_audio_chunk_auto_starts_turn():
    session_manager.start_session("session-1", "meeting", 1, "colleague")

    turn_id = session_manager.append_audio_chunk("session-1", 0, "chunk-0", now_ms=1000)
    session = session_manager.get_session("session-1")

    assert turn_id is not None
    assert session is not None
    assert session.current_turn_id == turn_id
    assert session.current_turn_state == "streaming"
    assert session.current_turn_started_at_ms == 1000


def test_audio_chunks_are_finalized_in_sequence_order():
    session_manager.start_session("session-1", "restaurant", 1, "friendly_waiter")

    turn_id = session_manager.append_audio_chunk("session-1", 2, "chunk-2")
    session_manager.append_audio_chunk("session-1", 0, "chunk-0")
    session_manager.append_audio_chunk("session-1", 1, "chunk-1")

    finalized = session_manager.finalize_turn("session-1", now_ms=2200)

    assert finalized is not None
    assert finalized.turn_id == turn_id
    assert finalized.audio_chunks == ["chunk-0", "chunk-1", "chunk-2"]


def test_finalize_turn_only_clears_turn_buffer():
    session_manager.start_session("session-1", "interview", 3, "strict_interviewer")
    session_manager.append_audio_chunk("session-1", 0, "chunk-0")
    turn_id = session_manager.get_session("session-1").current_turn_id

    finalized = session_manager.finalize_turn("session-1", now_ms=2500)
    session = session_manager.get_session("session-1")

    assert finalized is not None
    assert finalized.turn_id == turn_id
    assert session is not None
    assert session.current_turn_audio_chunks == []
    assert session.current_turn_state == "processing"
    assert session.current_turn_id == turn_id
    assert session.scene_id == "interview"
    assert session.history == []


def test_finish_session_keeps_session_queryable():
    session_manager.start_session("session-1", "meeting", 2, "colleague")
    session_manager.finish_session("session-1", now_ms=3000, retain_for_ms=60000)

    session = session_manager.get_session("session-1")

    assert session is not None
    assert session.session_status == "finished"
    assert session.finished_at_ms == 3000
    assert session.retain_until_ms == 63000


def test_cleanup_only_removes_expired_sessions():
    session_manager.start_session("keep-me", "meeting", 1, "colleague")
    session_manager.start_session("remove-me", "interview", 1, "strict_interviewer")
    session_manager.finish_session("keep-me", now_ms=1000, retain_for_ms=5000)
    session_manager.finish_session("remove-me", now_ms=1000, retain_for_ms=1000)

    removed = session_manager.cleanup_expired_sessions(now_ms=2500)

    assert removed == ["remove-me"]
    assert session_manager.get_session("remove-me") is None
    assert session_manager.get_session("keep-me") is not None


def test_append_turn_preserves_history_without_mixing_coach_state():
    session_manager.start_session("session-1", "interview", 1, "strict_interviewer")
    session_manager.append_audio_chunk("session-1", 0, "chunk-0")
    turn_id = session_manager.get_session("session-1").current_turn_id
    session_manager.finalize_turn("session-1", now_ms=2000)

    session = session_manager.append_turn(
        "session-1",
        turn_id=turn_id,
        user_text="Hello, I am interested in the role.",
        ai_reply="Nice to meet you. Please introduce yourself.",
        pron_score=PronScore(overall=80, accuracy=79, fluency=82, completeness=90, words=[]),
        corrections=[],
    )

    assert session is not None
    assert session.turn_count == 1
    assert session.history == [
        {"role": "user", "content": "Hello, I am interested in the role."},
        {"role": "assistant", "content": "Nice to meet you. Please introduce yourself."},
    ]
    assert session.current_turn_state == "completed"
