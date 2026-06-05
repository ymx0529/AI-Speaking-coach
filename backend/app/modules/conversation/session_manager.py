from __future__ import annotations

from dataclasses import dataclass, field

from app.core.types import CorrectionIssue, PronScore, TurnRecord


@dataclass
class SessionState:
    session_id: str
    scene_id: str
    difficulty: int
    persona_id: str
    audio_chunks: list[tuple[int, str]] = field(default_factory=list)
    history: list[dict[str, str]] = field(default_factory=list)
    turns: list[TurnRecord] = field(default_factory=list)
    turn_count: int = 0


_sessions: dict[str, SessionState] = {}


def start_session(session_id: str, scene_id: str, difficulty: int, persona_id: str) -> None:
    _sessions[session_id] = SessionState(
        session_id=session_id,
        scene_id=scene_id,
        difficulty=difficulty,
        persona_id=persona_id,
    )


def append_audio_chunk(session_id: str, seq: int, data: str) -> None:
    session = _sessions.get(session_id)
    if session is None:
        return
    session.audio_chunks.append((seq, data))


def get_session(session_id: str) -> SessionState | None:
    return _sessions.get(session_id)


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
    return session


def end_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
