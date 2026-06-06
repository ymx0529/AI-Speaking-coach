import { defineStore } from 'pinia'

import type { CorrectionIssue, ErrorCode, PronScore, SessionSummaryResponse } from './types'

export const useAppStore = defineStore('app', {
  state: () => ({
    sessionId: null as string | null,
    sceneId: null as string | null,
    difficulty: 1 as 1 | 2 | 3,
    personaId: null as string | null,
    phase: 'scene_select' as 'scene_select' | 'in_session' | 'summary',
    sessionReady: false,
    currentTurnId: null as string | null,
    isRecording: false,
    isSpeaking: false,
    asrText: '',
    aiReplyText: '',
    currentPronScore: null as PronScore | null,
    currentCorrections: [] as CorrectionIssue[],
    summary: null as SessionSummaryResponse | null,
    lastError: null as { code: ErrorCode | string; message: string; retryable?: boolean } | null,
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
      this.sessionReady = false
      this.lastError = null
    },

    endSession() {
      this.phase = 'summary'
    },

    markSessionReady() {
      this.sessionReady = true
    },

    setError(error: { code: ErrorCode | string; message: string; retryable?: boolean }) {
      this.lastError = error
    },

    resetTurn() {
      this.currentTurnId = null
      this.asrText = ''
      this.aiReplyText = ''
      this.currentPronScore = null
      this.currentCorrections = []
      this.lastError = null
    },
  },
})

