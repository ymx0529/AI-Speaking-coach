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
  corrections_count: number
  ai_feedback: string
  turns: TurnRecord[]
}

export type ClientMsg =
  | { type: 'session_start'; scene_id: string; difficulty: Difficulty; persona_id: string }
  | { type: 'audio_chunk'; data: string; seq: number }
  | { type: 'audio_end'; seq_count: number }
  | { type: 'session_end' }

export type ServerMsg =
  | { type: 'asr_partial'; text: string }
  | { type: 'asr_final'; turn_id: string; text: string; duration_ms: number }
  | {
      type: 'pron_score'
      turn_id: string
      overall: number
      accuracy: number
      fluency: number
      completeness: number
      words: WordScore[]
    }
  | { type: 'reply_text'; turn_id: string; text: string }
  | { type: 'reply_audio'; turn_id: string; data: string }
  | { type: 'correction'; turn_id: string; issues: CorrectionIssue[] }
  | { type: 'turn_end'; turn_id: string }
  | { type: 'error'; code: string; message: string }

