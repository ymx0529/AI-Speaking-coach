from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.types import (
    AnalysisCorrectionMessage,
    AnalysisPronunciationMessage,
    AudioAppendMessage,
    ErrorMessage,
    SessionReadyMessage,
    SessionStartMessage,
    TurnCompletedMessage,
    TurnStartedMessage,
    TurnTranscriptReadyEvent,
    UserTurnFinalMessage,
)


def test_turn_transcript_ready_event_contains_required_handoff_fields():
    event = TurnTranscriptReadyEvent(
        session_id="session-1",
        turn_id="turn-1",
        scene_id="interview",
        difficulty=2,
        persona_id="strict_interviewer",
        custom_background="The learner is introducing a delayed launch plan.",
        transcript="I would like to introduce myself.",
        audio_format="wav_pcm16",
        audio_b64="ZmFrZV9hdWRpbw==",
        assistant_reply_text="Please tell me about your experience.",
        turn_duration_ms=2100,
    )

    assert event.session_id == "session-1"
    assert event.turn_id == "turn-1"
    assert event.audio_format == "wav_pcm16"
    assert event.turn_duration_ms == 2100


def test_canonical_ws_message_models_match_v2_contract():
    session_start = SessionStartMessage(
        session_id="session-1",
        scene_id="meeting",
        difficulty=1,
        persona_id="colleague",
        custom_background="The learner wants to propose a new marketing plan.",
        client_ts=1717651200000,
    )
    audio_append = AudioAppendMessage(
        session_id="session-1",
        turn_id="turn-1",
        seq=0,
        encoding="webm_opus",
        chunk="ZmFrZQ==",
        is_last=False,
        client_ts=1717651200300,
    )
    session_ready = SessionReadyMessage(
        session_id="session-1",
        server_ts=1717651200100,
    )
    turn_started = TurnStartedMessage(
        session_id="session-1",
        turn_id="turn-1",
        server_ts=1717651200400,
    )
    user_turn_final = UserTurnFinalMessage(
        session_id="session-1",
        turn_id="turn-1",
        text="I would like to order a pasta, please.",
        duration_ms=2800,
        server_ts=1717651202000,
    )
    pronunciation = AnalysisPronunciationMessage(
        session_id="session-1",
        turn_id="turn-1",
        overall=81.0,
        accuracy=79.0,
        fluency=84.0,
        completeness=90.0,
        words=[],
    )
    correction = AnalysisCorrectionMessage(
        session_id="session-1",
        turn_id="turn-1",
        issues=[],
    )
    completed = TurnCompletedMessage(
        session_id="session-1",
        turn_id="turn-1",
        server_ts=1717651202600,
    )
    error = ErrorMessage(
        session_id="session-1",
        turn_id="turn-1",
        code="ASR_FAILED",
        message="Speech recognition returned empty result.",
        retryable=True,
    )

    assert session_start.type == "session.start"
    assert session_start.custom_background == "The learner wants to propose a new marketing plan."
    assert audio_append.encoding == "webm_opus"
    assert session_ready.type == "session.ready"
    assert turn_started.type == "turn.started"
    assert user_turn_final.type == "user_turn.final"
    assert pronunciation.type == "analysis.pronunciation"
    assert correction.type == "analysis.correction"
    assert completed.type == "turn.completed"
    assert error.retryable is True
