export type Difficulty = 1 | 2 | 3
export type AudioEncoding = 'webm_opus' | 'wav_pcm16'
export type AudioFormat = 'mp3' | 'wav_pcm16'
export type ErrorCode =
  | 'BAD_REQUEST'
  | 'SESSION_NOT_FOUND'
  | 'AUDIO_DECODE_FAILED'
  | 'ASR_FAILED'
  | 'LLM_REPLY_FAILED'
  | 'TTS_FAILED'
  | 'PRON_ANALYSIS_FAILED'
  | 'CORRECTION_FAILED'
  | 'SUMMARY_NOT_READY'

export interface WordScore {
  word: string
  accuracy_score: number
  error_type: 'None' | 'Omission' | 'Insertion' | 'Mispronunciation'
}

export interface PronScore {
  overall: number
  accuracy: number
  fluency: number
  completeness: number
  words: WordScore[]
}

export interface CorrectionIssue {
  original: string
  corrected: string
  explanation: string
  category: 'grammar' | 'expression' | 'vocabulary'
  severity: 'high' | 'medium' | 'low'
}

/** Dev A → Dev B via backend EventBus (see PROTOCOL.md) */
export interface TurnTranscriptReadyEvent {
  session_id: string
  turn_id: string
  scene_id: string
  difficulty: number
  persona_id: string
  transcript: string
  wav_audio_b64: string | null
  assistant_reply_text: string
  turn_duration_ms: number
}

/** Dev B internal aggregated turn analysis (not sent over WS directly) */
export interface TurnAnalysisReadyEvent {
  session_id: string
  turn_id: string
  pronunciation: PronScore | null
  corrections: CorrectionIssue[]
  grammar_score: number | null
  expression_score: number | null
  vocabulary_score: number | null
}

export interface TurnRecord {
  turn_id: string
  user_text: string
  ai_reply: string
  pron_score: PronScore
  corrections: CorrectionIssue[]
}

export interface SessionSummaryResponse {
  session_id: string
  scene_id: string
  total_turns: number
  pron_avg: number
  accuracy_avg: number
  fluency_avg: number
  completeness_avg: number
  grammar_score?: number
  expression_score?: number
  vocabulary_score?: number
  corrections_count: number
  avg_response_latency_ms?: number
  ai_feedback: string
  focus_recommendations?: string[]
  turns: TurnRecord[]
}

export interface SessionStatusResponse {
  session_id: string
  state: 'active' | 'finished'
  summary_ready: boolean
  last_turn_id: string | null
  last_error: string | null
}

// ── Client → Server ──────────────────────────────────────────

export interface SessionStartMessage {
  type: 'session.start'
  session_id: string
  scene_id: string
  difficulty: Difficulty
  persona_id: string
  client_ts: number
}

export interface AudioAppendMessage {
  type: 'audio.append'
  session_id: string
  turn_id?: string | null
  seq: number
  encoding: AudioEncoding
  chunk: string
  is_last: boolean
  client_ts: number
}

export interface SessionFinishMessage {
  type: 'session.finish'
  session_id: string
}

export interface SessionReadyMessage {
  type: 'session.ready'
  session_id: string
  server_ts: number
}

export interface TurnStartedMessage {
  type: 'turn.started'
  session_id: string
  turn_id: string
  server_ts: number
}

export interface AsrPartialMessage {
  type: 'asr.partial'
  session_id: string
  turn_id: string
  text: string
  server_ts: number
}

export interface UserTurnFinalMessage {
  type: 'user_turn.final'
  session_id: string
  turn_id: string
  text: string
  duration_ms: number
  server_ts: number
}

export interface AssistantReplyTextMessage {
  type: 'assistant.reply_text'
  session_id: string
  turn_id: string
  text: string
}

export interface AssistantReplyAudioMessage {
  type: 'assistant.reply_audio'
  session_id: string
  turn_id: string
  audio_format: AudioFormat
  data: string
}

export interface AnalysisPronunciationMessage {
  type: 'analysis.pronunciation'
  session_id: string
  turn_id: string
  overall: number
  accuracy: number
  fluency: number
  completeness: number
  words: WordScore[]
}

export interface AnalysisCorrectionMessage {
  type: 'analysis.correction'
  session_id: string
  turn_id: string
  issues: CorrectionIssue[]
}

export interface TurnCompletedMessage {
  type: 'turn.completed'
  session_id: string
  turn_id: string
  server_ts: number
}

export interface ErrorMessage {
  type: 'error'
  session_id?: string | null
  turn_id?: string | null
  code: ErrorCode | string
  message: string
  retryable?: boolean
}

export type CanonicalClientMsg = SessionStartMessage | AudioAppendMessage | SessionFinishMessage

export type LegacyClientMsg =
  | { type: 'session_start'; scene_id: string; difficulty: Difficulty; persona_id: string }
  | { type: 'audio_chunk'; data: string; seq: number }
  | { type: 'audio_end'; seq_count: number }
  | { type: 'session_end' }
  // v2
  | { type: 'session.start'; session_id: string; scene_id: string; difficulty: Difficulty; persona_id: string; client_ts: number }
  | { type: 'audio.append'; session_id: string; turn_id: string | null; seq: number; encoding: string; chunk: string; is_last: boolean; client_ts: number }
  | { type: 'session.finish'; session_id: string }

// ── Server → Client ──────────────────────────────────────────

export type ClientMsg = CanonicalClientMsg | LegacyClientMsg

export type CanonicalServerMsg =
  | SessionReadyMessage
  | TurnStartedMessage
  | AsrPartialMessage
  | UserTurnFinalMessage
  | AssistantReplyTextMessage
  | AssistantReplyAudioMessage
  | AnalysisPronunciationMessage
  | AnalysisCorrectionMessage
  | TurnCompletedMessage
  | ErrorMessage

export type LegacyServerMsg =
  | { type: 'asr_partial'; text: string }
  | { type: 'asr_final'; turn_id: string; text: string; duration_ms: number }
  | { type: 'pron_score'; turn_id: string; overall: number; accuracy: number; fluency: number; completeness: number; words: WordScore[] }
  | { type: 'reply_text'; turn_id: string; text: string }
  | { type: 'reply_audio'; turn_id: string; data: string }
  | { type: 'correction'; turn_id: string; issues: CorrectionIssue[] }
  | { type: 'turn_end'; turn_id: string }
  | { type: 'error'; code: string; message: string; retryable?: boolean }

export type ServerMsg = CanonicalServerMsg | LegacyServerMsg

