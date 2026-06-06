from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class WordScore(BaseModel):
    word: str
    accuracy_score: float
    error_type: Literal["None", "Omission", "Insertion", "Mispronunciation"] = "None"


class PronScore(BaseModel):
    overall: float
    accuracy: float
    fluency: float
    completeness: float
    words: list[WordScore] = Field(default_factory=list)


class CorrectionIssue(BaseModel):
    original: str
    corrected: str
    explanation: str
    category: Literal["grammar", "expression", "vocabulary"]
    severity: Literal["high", "medium", "low"] = "medium"


class TurnRecord(BaseModel):
    turn_id: str
    user_text: str
    ai_reply: str
    pron_score: PronScore
    corrections: list[CorrectionIssue] = Field(default_factory=list)


# Dev A → Dev B via event bus. Replaces SpeakerTurnEvent.
class TurnTranscriptReadyEvent(BaseModel):
    session_id: str
    turn_id: str
    scene_id: str
    difficulty: int
    persona_id: str
    transcript: str
    wav_audio_b64: str | None = None  # required for pronunciation assessment
    assistant_reply_text: str
    turn_duration_ms: int


# Kept for backward compatibility until Dev A migrates conversation/router.py
SpeakerTurnEvent = TurnTranscriptReadyEvent


# Dev B internal: aggregated analysis result for one turn
class TurnAnalysisReadyEvent(BaseModel):
    session_id: str
    turn_id: str
    pronunciation: PronScore | None = None
    corrections: list[CorrectionIssue] = Field(default_factory=list)
    grammar_score: float | None = None
    expression_score: float | None = None
    vocabulary_score: float | None = None


class SessionSummaryResponse(BaseModel):
    session_id: str
    scene_id: str
    total_turns: int
    pron_avg: float
    accuracy_avg: float
    fluency_avg: float
    completeness_avg: float
    grammar_score: float | None = None
    expression_score: float | None = None
    vocabulary_score: float | None = None
    corrections_count: int
    avg_response_latency_ms: int | None = None
    ai_feedback: str
    focus_recommendations: list[str] = Field(default_factory=list)
    turns: list[TurnRecord] = Field(default_factory=list)

