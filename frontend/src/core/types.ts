export type Difficulty = 1 | 2 | 3

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
  severity?: 'high' | 'medium' | 'low'
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

// ── Client → Server ──────────────────────────────────────────

export type ClientMsg =
  // v1 (kept for backward compat, Dev A will migrate)
  | { type: 'session_start'; scene_id: string; difficulty: Difficulty; persona_id: string }
  | { type: 'audio_chunk'; data: string; seq: number }
  | { type: 'audio_end'; seq_count: number }
  | { type: 'session_end' }
  // v2
  | { type: 'session.start'; session_id: string; scene_id: string; difficulty: Difficulty; persona_id: string; client_ts: number }
  | { type: 'audio.append'; session_id: string; turn_id: string | null; seq: number; encoding: string; chunk: string; is_last: boolean; client_ts: number }
  | { type: 'session.finish'; session_id: string }

// ── Server → Client ──────────────────────────────────────────

export type ServerMsg =
  // v1 (kept for backward compat, Dev A will migrate)
  | { type: 'asr_partial'; text: string }
  | { type: 'asr_final'; turn_id: string; text: string; duration_ms: number }
  | { type: 'pron_score'; turn_id: string; overall: number; accuracy: number; fluency: number; completeness: number; words: WordScore[] }
  | { type: 'reply_text'; turn_id: string; text: string }
  | { type: 'reply_audio'; turn_id: string; data: string }
  | { type: 'correction'; turn_id: string; issues: CorrectionIssue[] }
  | { type: 'turn_end'; turn_id: string }
  // v2 conversation events (Dev A)
  | { type: 'session.ready'; session_id: string }
  | { type: 'turn.started'; session_id: string; turn_id: string; server_ts: number }
  | { type: 'asr.partial'; session_id: string; turn_id: string; text: string; server_ts: number }
  | { type: 'user_turn.final'; session_id: string; turn_id: string; text: string; duration_ms: number; server_ts: number }
  | { type: 'assistant.reply_text'; session_id: string; turn_id: string; text: string }
  | { type: 'assistant.reply_audio'; session_id: string; turn_id: string; audio_format: string; data: string }
  | { type: 'turn.completed'; session_id: string; turn_id: string; server_ts: number }
  // v2 coach events (Dev B)
  | { type: 'analysis.pronunciation'; session_id: string; turn_id: string; overall: number; accuracy: number; fluency: number; completeness: number; words: WordScore[] }
  | { type: 'analysis.correction'; session_id: string; turn_id: string; issues: CorrectionIssue[] }
  // error: merged v1+v2 (session_id and retryable optional for backward compat)
  | { type: 'error'; code: string; message: string; session_id?: string; turn_id?: string; retryable?: boolean }
