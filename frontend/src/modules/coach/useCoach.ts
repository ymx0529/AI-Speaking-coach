import axios from 'axios'

import type { PronScore, ServerMsg, SessionSummaryResponse } from '@/core/types'
import { useAppStore } from '@/core/store'
import { ws } from '@/core/ws'

const MOCK_SESSION_ID = 'mock-session'

let wsCleanup: (() => void) | null = null

function handleCoachMessage(msg: ServerMsg, store: ReturnType<typeof useAppStore>) {
  switch (msg.type) {
    // v2: mark analysis pending when a turn begins or user text is final
    case 'turn.started':
      store.currentTurnId = msg.turn_id
      store.setCoachAnalysisStatus(msg.turn_id, 'pending')
      break
    case 'asr_final':
    case 'user_turn.final':
      store.currentTurnId = msg.turn_id
      store.setCoachAnalysisStatus(msg.turn_id, 'pending')
      break

    // v2 Coach events
    case 'analysis.pronunciation':
      store.setPronunciationResult(msg.turn_id, toPronScore(msg))
      break
    case 'analysis.correction':
      store.setCorrectionsResult(msg.turn_id, msg.issues, msg.sample_answer ?? '')
      store.setCoachAnalysisStatus(msg.turn_id, 'analyzed')
      break

    // v1 transition bridge (remove after Dev A migrates)
    case 'pron_score':
      store.setPronunciationResult(msg.turn_id, {
        overall: msg.overall,
        accuracy: msg.accuracy,
        fluency: msg.fluency,
        completeness: msg.completeness,
        words: msg.words,
      })
      break
    case 'correction':
      store.setCorrectionsResult(msg.turn_id, msg.issues, msg.sample_answer ?? '')
      store.setCoachAnalysisStatus(msg.turn_id, 'analyzed')
      break
  }
}

function toPronScore(msg: Extract<ServerMsg, { type: 'analysis.pronunciation' }>): PronScore {
  return {
    overall: msg.overall,
    accuracy: msg.accuracy,
    fluency: msg.fluency,
    completeness: msg.completeness,
    words: msg.words,
  }
}

function ensureCoachSubscription(store: ReturnType<typeof useAppStore>) {
  if (wsCleanup) return
  wsCleanup = ws.onMessage((msg) => handleCoachMessage(msg, store))
}

export function useCoach() {
  const store = useAppStore()
  ensureCoachSubscription(store)

  async function fetchSummary(sessionId?: string): Promise<SessionSummaryResponse | null> {
    const id = sessionId ?? store.sessionId
    if (!id) return null

    store.summaryLoading = true
    store.summaryReady = false

    try {
      if (id === MOCK_SESSION_ID) {
        const { MOCK_SUMMARY_RESPONSE } = await import('@/mock/events')
        store.summary = MOCK_SUMMARY_RESPONSE
        store.summaryReady = true
        return MOCK_SUMMARY_RESPONSE
      }

      const res = await axios.post<SessionSummaryResponse>(
        `/api/sessions/${id}/summary`,
      )
      store.summary = res.data
      store.summaryReady = true
      return res.data
    } catch {
      store.summary = null
      store.summaryReady = false
      return null
    } finally {
      store.summaryLoading = false
    }
  }

  return { fetchSummary }
}

/** Tear down WS subscription (mainly for tests). */
export function resetCoachSubscription() {
  wsCleanup?.()
  wsCleanup = null
}
