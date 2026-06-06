from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Difficulty = Literal[1, 2, 3]
AudioEncoding = Literal["webm_opus", "wav_pcm16"]
AudioFormat = Literal["mp3", "wav_pcm16"]
ErrorCode = Literal[
    "BAD_REQUEST",
    "SESSION_NOT_FOUND",
    "AUDIO_DECODE_FAILED",
    "ASR_FAILED",
    "LLM_REPLY_FAILED",
    "TTS_FAILED",
    "PRON_ANALYSIS_FAILED",
    "CORRECTION_FAILED",
    "SUMMARY_NOT_READY",
]


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


class SpeakerTurnEvent(BaseModel):
    session_id: str
    turn_id: str
    user_text: str
    pron_score: PronScore
    ai_reply: str
    scene_id: str


class TurnTranscriptReadyEvent(BaseModel):
    session_id: str
    turn_id: str
    scene_id: str
    difficulty: Difficulty
    persona_id: str
    transcript: str
    audio_format: Literal["wav_pcm16"] = "wav_pcm16"
    audio_b64: str
    assistant_reply_text: str
    turn_duration_ms: int


class SessionSummaryResponse(BaseModel):
    session_id: str
    scene_id: str
    total_turns: int
    pron_avg: float
    accuracy_avg: float
    fluency_avg: float
    completeness_avg: float
    grammar_score: float = 0.0
    expression_score: float = 0.0
    vocabulary_score: float = 0.0
    corrections_count: int
    avg_response_latency_ms: float = 0.0
    ai_feedback: str
    focus_recommendations: list[str] = Field(default_factory=list)
    turns: list[TurnRecord] = Field(default_factory=list)


class SessionStartMessage(BaseModel):
    type: Literal["session.start"] = "session.start"
    session_id: str
    scene_id: str
    difficulty: Difficulty
    persona_id: str
    client_ts: int


class AudioAppendMessage(BaseModel):
    type: Literal["audio.append"] = "audio.append"
    session_id: str
    turn_id: str | None = None
    seq: int
    encoding: AudioEncoding
    chunk: str
    is_last: bool = False
    client_ts: int


class SessionFinishMessage(BaseModel):
    type: Literal["session.finish"] = "session.finish"
    session_id: str


class SessionReadyMessage(BaseModel):
    type: Literal["session.ready"] = "session.ready"
    session_id: str
    server_ts: int


class TurnStartedMessage(BaseModel):
    type: Literal["turn.started"] = "turn.started"
    session_id: str
    turn_id: str
    server_ts: int


class AsrPartialMessage(BaseModel):
    type: Literal["asr.partial"] = "asr.partial"
    session_id: str
    turn_id: str
    text: str
    server_ts: int


class UserTurnFinalMessage(BaseModel):
    type: Literal["user_turn.final"] = "user_turn.final"
    session_id: str
    turn_id: str
    text: str
    duration_ms: int
    server_ts: int


class AssistantReplyTextMessage(BaseModel):
    type: Literal["assistant.reply_text"] = "assistant.reply_text"
    session_id: str
    turn_id: str
    text: str


class AssistantReplyAudioMessage(BaseModel):
    type: Literal["assistant.reply_audio"] = "assistant.reply_audio"
    session_id: str
    turn_id: str
    audio_format: AudioFormat = "mp3"
    data: str


class AnalysisPronunciationMessage(BaseModel):
    type: Literal["analysis.pronunciation"] = "analysis.pronunciation"
    session_id: str
    turn_id: str
    overall: float
    accuracy: float
    fluency: float
    completeness: float
    words: list[WordScore] = Field(default_factory=list)


class AnalysisCorrectionMessage(BaseModel):
    type: Literal["analysis.correction"] = "analysis.correction"
    session_id: str
    turn_id: str
    issues: list[CorrectionIssue] = Field(default_factory=list)


class TurnCompletedMessage(BaseModel):
    type: Literal["turn.completed"] = "turn.completed"
    session_id: str
    turn_id: str
    server_ts: int


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    session_id: str | None = None
    turn_id: str | None = None
    code: ErrorCode
    message: str
    retryable: bool = False

