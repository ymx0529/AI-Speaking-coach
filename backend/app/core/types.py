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


class TurnRecord(BaseModel):
    turn_id: str
    user_text: str
    ai_reply: str
    pron_score: PronScore
    corrections: list[CorrectionIssue] = Field(default_factory=list)


class SpeakerTurnEvent(BaseModel):
    session_id: str
    turn_id: str
    user_text: str
    pron_score: PronScore
    ai_reply: str
    scene_id: str


class SessionSummaryResponse(BaseModel):
    session_id: str
    scene_id: str
    total_turns: int
    pron_avg: float
    accuracy_avg: float
    fluency_avg: float
    completeness_avg: float
    corrections_count: int
    ai_feedback: str
    turns: list[TurnRecord] = Field(default_factory=list)

