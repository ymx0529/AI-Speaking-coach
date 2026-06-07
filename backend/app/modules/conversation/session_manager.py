from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

from app.core.types import CorrectionIssue, PronScore, TurnRecord

TurnState = Literal["idle", "streaming", "processing", "completed", "failed"]
SessionStatus = Literal["active", "finished"]


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class FinalizedTurn:
    turn_id: str
    audio_chunks: list[str]
    finalized_at_ms: int


@dataclass
class SessionState:
    session_id: str
    user_id: str
    scene_id: str
    difficulty: int
    persona_id: str
    history: list[dict[str, str]] = field(default_factory=list)
    turns: list[TurnRecord] = field(default_factory=list)
    turn_count: int = 0
    current_turn_id: str | None = None
    current_turn_state: TurnState = "idle"
    current_turn_audio_chunks: list[tuple[int, str]] = field(default_factory=list)
    current_turn_started_at_ms: int | None = None
    current_turn_finalized_at_ms: int | None = None
    session_status: SessionStatus = "active"
    finished_at_ms: int | None = None
    retain_until_ms: int | None = None


_sessions: dict[str, SessionState] = {}


def start_session(session_id: str, scene_id: str, difficulty: int, persona_id: str, user_id: str = "") -> None:
    _sessions[session_id] = SessionState(
        session_id=session_id,
        user_id=user_id,
        scene_id=scene_id,
        difficulty=difficulty,
        persona_id=persona_id,
    )


def start_turn(session_id: str, now_ms: int | None = None) -> str | None:
    session = _sessions.get(session_id)
    if session is None:
        return None

    if session.current_turn_id and session.current_turn_state in {"streaming", "processing"}:
        return session.current_turn_id

    timestamp = _now_ms() if now_ms is None else now_ms
    session.current_turn_id = str(uuid4())
    session.current_turn_state = "streaming"
    session.current_turn_audio_chunks = []
    session.current_turn_started_at_ms = timestamp
    session.current_turn_finalized_at_ms = None
    return session.current_turn_id


def append_audio_chunk(session_id: str, seq: int, data: str, now_ms: int | None = None) -> str | None:
    session = _sessions.get(session_id)
    if session is None:
        return None

    turn_id = start_turn(session_id, now_ms=now_ms)
    session.current_turn_audio_chunks.append((seq, data))
    session.current_turn_state = "streaming"
    return turn_id


def finalize_turn(session_id: str, now_ms: int | None = None) -> FinalizedTurn | None:
    session = _sessions.get(session_id)
    if session is None or session.current_turn_id is None:
        return None

    timestamp = _now_ms() if now_ms is None else now_ms
    ordered_chunks = [chunk for _, chunk in sorted(session.current_turn_audio_chunks, key=lambda item: item[0])]
    finalized = FinalizedTurn(
        turn_id=session.current_turn_id,
        audio_chunks=ordered_chunks,
        finalized_at_ms=timestamp,
    )
    session.current_turn_audio_chunks = []
    session.current_turn_state = "processing"
    session.current_turn_finalized_at_ms = timestamp
    return finalized


def get_session(session_id: str) -> SessionState | None:
    return _sessions.get(session_id)


def get_session_for_user(session_id: str, user_id: str) -> SessionState | None:
    session = get_session(session_id)
    if session is None or session.user_id != user_id:
        return None
    return session


def append_turn(
    session_id: str,
    turn_id: str,
    user_text: str,
    ai_reply: str,
    pron_score: PronScore,
    corrections: list[CorrectionIssue],
) -> SessionState | None:
    session = _sessions.get(session_id)
    if session is None:
        return None

    session.turn_count += 1
    session.history.append({"role": "user", "content": user_text})
    session.history.append({"role": "assistant", "content": ai_reply})
    session.turns.append(
        TurnRecord(
            turn_id=turn_id,
            user_text=user_text,
            ai_reply=ai_reply,
            pron_score=pron_score,
            corrections=corrections,
        )
    )
    session.current_turn_id = turn_id
    session.current_turn_state = "completed"
    return session


def append_dialogue_turn(
    session_id: str,
    turn_id: str,
    user_text: str,
    ai_reply: str,
) -> SessionState | None:
    session = _sessions.get(session_id)
    if session is None:
        return None

    session.turn_count += 1
    session.history.append({"role": "user", "content": user_text})
    session.history.append({"role": "assistant", "content": ai_reply})
    session.current_turn_id = turn_id
    session.current_turn_state = "completed"
    return session


def finish_session(
    session_id: str,
    *,
    now_ms: int | None = None,
    retain_for_ms: int = 10 * 60 * 1000,
) -> SessionState | None:
    session = _sessions.get(session_id)
    if session is None:
        return None

    timestamp = _now_ms() if now_ms is None else now_ms
    session.session_status = "finished"
    session.finished_at_ms = timestamp
    session.retain_until_ms = timestamp + retain_for_ms
    return session


def cleanup_expired_sessions(now_ms: int | None = None) -> list[str]:
    timestamp = _now_ms() if now_ms is None else now_ms
    expired_ids = [
        session_id
        for session_id, session in _sessions.items()
        if session.session_status == "finished"
        and session.retain_until_ms is not None
        and session.retain_until_ms <= timestamp
    ]
    for session_id in expired_ids:
        _sessions.pop(session_id, None)
    return expired_ids


def end_session(session_id: str) -> None:
    finish_session(session_id)
