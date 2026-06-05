import { defineStore } from 'pinia'

import type { CorrectionIssue, PronScore, SessionSummaryResponse } from './types'

export const useAppStore = defineStore('app', {
  state: () => ({
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
  },
})

