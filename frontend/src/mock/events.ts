import type { ServerMsg, SessionSummaryResponse } from '@/core/types'

export const MOCK_SESSION_ID = 'mock-session'
export const MOCK_TURN_ID = 'mock-turn-1'

/** Single-turn WS sequence for Dev B UI dev without backend */
export const MOCK_TURN_EVENTS: ServerMsg[] = [
  { type: 'turn.started', session_id: MOCK_SESSION_ID, turn_id: MOCK_TURN_ID, server_ts: Date.now() },
  { type: 'asr.partial', session_id: MOCK_SESSION_ID, turn_id: MOCK_TURN_ID, text: 'I am inter...', server_ts: Date.now() },
  {
    type: 'user_turn.final',
    session_id: MOCK_SESSION_ID,
    turn_id: MOCK_TURN_ID,
    text: 'I am interested in the position.',
    duration_ms: 2200,
    server_ts: Date.now(),
  },
  {
    type: 'assistant.reply_text',
    session_id: MOCK_SESSION_ID,
    turn_id: MOCK_TURN_ID,
    text: 'That sounds good. Could you tell me more about your experience?',
  },
  {
    type: 'analysis.pronunciation',
    session_id: MOCK_SESSION_ID,
    turn_id: MOCK_TURN_ID,
    overall: 72,
    accuracy: 68,
    fluency: 78,
    completeness: 90,
    words: [{ word: 'interested', accuracy_score: 58, error_type: 'Mispronunciation' }],
  },
  {
    type: 'analysis.correction',
    session_id: MOCK_SESSION_ID,
    turn_id: MOCK_TURN_ID,
    issues: [
      {
        original: 'I am interest in',
        corrected: 'I am interested in',
        explanation: '形容词形式，需要用 interested 而非名词 interest。',
        category: 'grammar',
        severity: 'high',
      },
    ],
  },
  { type: 'turn.completed', session_id: MOCK_SESSION_ID, turn_id: MOCK_TURN_ID, server_ts: Date.now() },
]

/** v1 mock sequence still used by backend conversation/router.py mock path */
export const MOCK_TURN_EVENTS_V1: ServerMsg[] = [
  { type: 'asr_partial', text: 'I am inter...' },
  {
    type: 'asr_final',
    turn_id: MOCK_TURN_ID,
    text: 'I am interested in the position.',
    duration_ms: 2200,
  },
  {
    type: 'pron_score',
    turn_id: MOCK_TURN_ID,
    overall: 72,
    accuracy: 68,
    fluency: 78,
    completeness: 90,
    words: [{ word: 'interested', accuracy_score: 58, error_type: 'Mispronunciation' }],
  },
  {
    type: 'correction',
    turn_id: MOCK_TURN_ID,
    issues: [
      {
        original: 'I am interest in',
        corrected: 'I am interested in',
        explanation: '形容词形式，需要用 interested 而非名词 interest。',
        category: 'grammar',
        severity: 'high',
      },
    ],
  },
  {
    type: 'reply_text',
    turn_id: MOCK_TURN_ID,
    text: 'That sounds good. Could you tell me more about your experience?',
  },
  { type: 'turn_end', turn_id: MOCK_TURN_ID },
]

export const MOCK_SUMMARY_RESPONSE: SessionSummaryResponse = {
  session_id: MOCK_SESSION_ID,
  scene_id: 'interview',
  total_turns: 3,
  pron_avg: 72,
  accuracy_avg: 68,
  fluency_avg: 78,
  completeness_avg: 90,
  grammar_score: 75,
  expression_score: 80,
  vocabulary_score: 85,
  corrections_count: 2,
  avg_response_latency_ms: 1260,
  ai_feedback: '整体表现不错，继续强化多音节单词重音和表达准确性。',
  focus_recommendations: [
    '重点练习单词发音准确度，可通过跟读练习提升',
    '注意语法结构，尤其是形容词与名词的区分',
  ],
  turns: [
    {
      turn_id: 'mock-turn-1',
      user_text: 'I am interested in the position.',
      ai_reply: 'Tell me more about your experience.',
      pron_score: {
        overall: 72,
        accuracy: 68,
        fluency: 78,
        completeness: 90,
        words: [],
      },
      corrections: [
        {
          original: 'I am interest in',
          corrected: 'I am interested in',
          explanation: 'Use adjective form.',
          category: 'grammar',
          severity: 'high',
        },
      ],
    },
  ],
}
