from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.core.types import CorrectionIssue, PronScore, TurnTranscriptReadyEvent

TurnStatus = Literal["pending", "analyzed", "failed"]


@dataclass
class TurnAnalysisRecord:
    session_id: str
    user_id: str
    turn_id: str
    transcript: str
    assistant_reply_text: str
    scene_id: str
    difficulty: int
    persona_id: str
    turn_duration_ms: int
    status: TurnStatus = "pending"
    pronunciation: PronScore | None = None
    corrections: list[CorrectionIssue] = field(default_factory=list)
    grammar_score: float | None = None
    expression_score: float | None = None
    vocabulary_score: float | None = None
    sample_answer: str = ""


# {session_id: {turn_id: TurnAnalysisRecord}}
_store: dict[str, dict[str, TurnAnalysisRecord]] = {}


def init_turn(event: TurnTranscriptReadyEvent) -> TurnAnalysisRecord:
    """Create a pending record for a turn. Idempotent: returns existing record if already present."""
    session = _store.setdefault(event.session_id, {})
    if event.turn_id in session:
        return session[event.turn_id]
    record = TurnAnalysisRecord(
        session_id=event.session_id,
        user_id=event.user_id,
        turn_id=event.turn_id,
        transcript=event.transcript,
        assistant_reply_text=event.assistant_reply_text,
        scene_id=event.scene_id,
        difficulty=event.difficulty,
        persona_id=event.persona_id,
        turn_duration_ms=event.turn_duration_ms,
    )
    session[event.turn_id] = record
    return record


def get_turn(session_id: str, turn_id: str) -> TurnAnalysisRecord | None:
    return _store.get(session_id, {}).get(turn_id)


def get_session_turns(session_id: str) -> list[TurnAnalysisRecord]:
    return list(_store.get(session_id, {}).values())


def set_status(session_id: str, turn_id: str, status: TurnStatus) -> None:
    record = get_turn(session_id, turn_id)
    if record is not None:
        record.status = status


def set_assistant_reply(session_id: str, turn_id: str, assistant_reply_text: str) -> None:
    record = get_turn(session_id, turn_id)
    if record is not None:
        record.assistant_reply_text = assistant_reply_text
