import { defineStore } from 'pinia'

import type { CorrectionIssue, PronScore, SessionSummaryResponse } from './types'

export const useAppStore = defineStore('app', {
  state: () => ({
    // ── Conversation State (Dev A) ────────────────────────────
    sessionId: null as string | null,
    sceneId: null as string | null,
    difficulty: 1 as 1 | 2 | 3,
    personaId: null as string | null,
    phase: 'scene_select' as 'scene_select' | 'in_session' | 'summary',
    currentTurnId: null as string | null,
    isRecording: false,
    isSpeaking: false,
    asrText: '',
    aiReplyText: '',
    currentPronScore: null as PronScore | null,
    currentCorrections: [] as CorrectionIssue[],
    summary: null as SessionSummaryResponse | null,
    // ── Coach Analysis State (Dev B) ─────────────────────────
    pronunciationByTurn: {} as Record<string, PronScore>,
    correctionsByTurn: {} as Record<string, CorrectionIssue[]>,
    coachAnalysisStatus: {} as Record<string, 'pending' | 'analyzed' | 'failed'>,
    summaryReady: false,
    summaryLoading: false,
    // ─────────────────────────────────────────────────────────
  }),

  actions: {
    startSession(params: {
      sessionId: string
      sceneId: string
      difficulty: 1 | 2 | 3
      personaId: string
    }) {
      this.sessionId = params.sessionId
      this.sceneId = params.sceneId
      this.difficulty = params.difficulty
      this.personaId = params.personaId
      this.phase = 'in_session'
    },

    endSession() {
      this.phase = 'summary'
    },

    resetTurn() {
      this.currentTurnId = null
      this.asrText = ''
      this.aiReplyText = ''
      this.currentPronScore = null
      this.currentCorrections = []
    },

    // ── Coach actions (Dev B) ─────────────────────────────────
    setCoachAnalysisStatus(turnId: string, status: 'pending' | 'analyzed' | 'failed') {
      this.coachAnalysisStatus[turnId] = status
    },

    setPronunciationResult(turnId: string, score: PronScore) {
      this.pronunciationByTurn[turnId] = score
    },

    setCorrectionsResult(turnId: string, issues: CorrectionIssue[]) {
      this.correctionsByTurn[turnId] = issues
    },
    // ─────────────────────────────────────────────────────────
  },
})

