import pytest

from app.core.types import CorrectionIssue, PronScore, TurnTranscriptReadyEvent
from app.modules.coach import store as coach_store
from app.modules.coach import summary_service


def _event(session_id="s1", turn_id="t1", scene_id="interview", **kwargs):
    return TurnTranscriptReadyEvent(
        session_id=session_id,
        user_id="user-1",
        turn_id=turn_id,
        scene_id=scene_id,
        difficulty=1,
        persona_id="p",
        transcript="I want pasta.",
        audio_b64=None,
        assistant_reply_text="Sure!",
        turn_duration_ms=1000,
        **kwargs,
    )


def _pron(overall=80.0, accuracy=75.0, fluency=82.0, completeness=90.0):
    return PronScore(overall=overall, accuracy=accuracy, fluency=fluency, completeness=completeness)


@pytest.fixture(autouse=True)
def clear_store():
    coach_store._store.clear()
    yield
    coach_store._store.clear()


def test_returns_none_for_unknown_session():
    result = summary_service.build_summary("no-such-session")
    assert result is None


def test_empty_turns_returns_none():
    # Store has the session bucket but it's empty (edge case)
    coach_store._store["s1"] = {}
    result = summary_service.build_summary("s1")
    assert result is None


def test_single_analyzed_turn():
    record = coach_store.init_turn(_event())
    record.pronunciation = _pron(overall=78.0, accuracy=74.0, fluency=80.0, completeness=88.0)
    record.grammar_score = 72.0
    record.corrections = [
        CorrectionIssue(original="x", corrected="y", explanation="e", category="grammar", severity="high")
    ]
    coach_store.set_status("s1", "t1", "analyzed")

    summary = summary_service.build_summary("s1")
    assert summary is not None
    assert summary.session_id == "s1"
    assert summary.total_turns == 1
    assert summary.pron_avg == 78.0
    assert summary.grammar_score == 72.0
    assert summary.corrections_count == 1


def test_returns_none_for_other_users_session():
    record = coach_store.init_turn(_event())
    record.pronunciation = _pron(overall=78.0)
    coach_store.set_status("s1", "t1", "analyzed")

    assert summary_service.build_summary("s1", user_id="user-2") is None


def test_multi_turn_averages_correct():
    for i, (overall, grammar) in enumerate([(60.0, 65.0), (80.0, 85.0)], start=1):
        record = coach_store.init_turn(_event(turn_id=f"t{i}"))
        record.pronunciation = _pron(overall=overall)
        record.grammar_score = grammar
        coach_store.set_status("s1", f"t{i}", "analyzed")

    summary = summary_service.build_summary("s1")
    assert summary is not None
    assert summary.pron_avg == 70.0
    assert summary.grammar_score == 75.0


def test_partial_failure_still_returns_summary():
    # Turn 1: analyzed with data
    r1 = coach_store.init_turn(_event(turn_id="t1"))
    r1.pronunciation = _pron()
    coach_store.set_status("s1", "t1", "analyzed")
    # Turn 2: failed (no pronunciation)
    coach_store.init_turn(_event(turn_id="t2"))
    coach_store.set_status("s1", "t2", "failed")

    summary = summary_service.build_summary("s1")
    assert summary is not None
    assert summary.total_turns == 2
    assert summary.pron_avg == 80.0  # only from turn 1


def test_no_pronunciation_data_zeros_pron_fields():
    record = coach_store.init_turn(_event())
    record.grammar_score = 70.0
    coach_store.set_status("s1", "t1", "analyzed")

    summary = summary_service.build_summary("s1")
    assert summary is not None
    assert summary.pron_avg == 0.0
    assert summary.grammar_score == 70.0


def test_focus_recommendations_generated():
    record = coach_store.init_turn(_event())
    record.pronunciation = _pron(overall=55.0)  # low → triggers recommendation
    coach_store.set_status("s1", "t1", "analyzed")

    summary = summary_service.build_summary("s1")
    assert summary is not None
    assert len(summary.focus_recommendations) >= 1
    assert any("发音" in r for r in summary.focus_recommendations)
