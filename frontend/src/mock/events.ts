import type { ServerMsg, SessionSummaryResponse } from '@/core/types'

export const MOCK_TURN_EVENTS: ServerMsg[] = [
  { type: 'asr_partial', text: 'I am inter...' },
  {
    type: 'asr_final',
    turn_id: 'mock-turn-1',
    text: 'I am interested in the position.',
    duration_ms: 2200,
  },
  {
    type: 'pron_score',
    turn_id: 'mock-turn-1',
    overall: 72,
    accuracy: 68,
    fluency: 78,
    completeness: 90,
    words: [{ word: 'interested', accuracy_score: 58, error_type: 'Mispronunciation' }],
  },
  {
    type: 'reply_text',
    turn_id: 'mock-turn-1',
    text: 'That sounds good. Could you tell me more about your experience?',
  },
  {
    type: 'correction',
    turn_id: 'mock-turn-1',
    issues: [
      {
        original: 'I am interest in',
        corrected: 'I am interested in',
        explanation: 'Use the adjective form here.',
        category: 'grammar',
      },
    ],
  },
  { type: 'turn_end', turn_id: 'mock-turn-1' },
]

export const MOCK_SUMMARY_RESPONSE: SessionSummaryResponse = {
  session_id: 'mock-session',
  scene_id: 'interview',
  total_turns: 3,
  pron_avg: 72,
  accuracy_avg: 68,
  fluency_avg: 78,
  completeness_avg: 90,
  corrections_count: 2,
  ai_feedback: '整体表现不错，继续强化多音节单词重音和表达准确性。',
  turns: [],
}

