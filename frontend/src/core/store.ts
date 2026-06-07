import { defineStore } from 'pinia'

import type { ConversationMessage, CorrectionIssue, ErrorCode, PronScore, SessionSummaryResponse } from './types'

export const useAppStore = defineStore('app', {
  state: () => ({
    sessionId: null as string | null,
    sceneId: null as string | null,
    difficulty: 1 as 1 | 2 | 3,
    personaId: null as string | null,
    customBackground: '',
    phase: 'scene_select' as 'scene_select' | 'in_session' | 'summary',
    sessionReady: false,
    currentTurnId: null as string | null,
    isRecording: false,
    isSpeaking: false,
    isReplyAudioPending: false,
    asrText: '',
    aiReplyText: '',
    messages: [] as ConversationMessage[],
    currentPronScore: null as PronScore | null,
    currentCorrections: [] as CorrectionIssue[],
    summary: null as SessionSummaryResponse | null,
    lastError: null as { code: ErrorCode | string; message: string; retryable?: boolean } | null,
    pronunciationByTurn: {} as Record<string, PronScore>,
    correctionsByTurn: {} as Record<string, CorrectionIssue[]>,
    coachAnalysisStatus: {} as Record<string, 'pending' | 'analyzed' | 'failed'>,
    summaryReady: false,
    summaryLoading: false,
  }),

  actions: {
    startSession(params: {
      sessionId: string
      sceneId: string
      difficulty: 1 | 2 | 3
      personaId: string
      customBackground?: string
    }) {
      this.sessionId = params.sessionId
      this.sceneId = params.sceneId
      this.difficulty = params.difficulty
      this.personaId = params.personaId
      this.customBackground = params.customBackground ?? ''
      this.phase = 'in_session'
      this.sessionReady = false
      this.pronunciationByTurn = {}
      this.correctionsByTurn = {}
      this.coachAnalysisStatus = {}
      this.summary = null
      this.summaryReady = false
      this.summaryLoading = false
      this.currentTurnId = null
      this.asrText = ''
      this.aiReplyText = ''
      this.currentPronScore = null
      this.currentCorrections = []
      this.isRecording = false
      this.isSpeaking = false
      this.isReplyAudioPending = false
      this.messages = [
        {
          id: 'system-welcome',
          turnId: null,
          role: 'system',
          text: params.customBackground
            ? '自定义场景已经准备好。开始录音后，AI 会根据你提供的背景进入角色并继续追问。'
            : '会话已创建。开始录音后，系统会识别你的英文，并把整轮对话记录在聊天区。',
          state: 'final',
        },
      ]
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
      this.isReplyAudioPending = false
      this.currentPronScore = null
      this.currentCorrections = []
      this.lastError = null
    },

    upsertConversationMessage(message: ConversationMessage) {
      const existingIndex = this.messages.findIndex((item) => item.id === message.id)
      if (existingIndex >= 0) {
        this.messages[existingIndex] = message
        return
      }
      this.messages.push(message)
    },

    setUserMessage(turnId: string, text: string, state: 'streaming' | 'final') {
      this.upsertConversationMessage({
        id: `user-${turnId}`,
        turnId,
        role: 'user',
        text,
        state,
      })
    },

    setAssistantMessage(turnId: string, text: string, state: 'streaming' | 'final' = 'final') {
      this.upsertConversationMessage({
        id: `assistant-${turnId}`,
        turnId,
        role: 'assistant',
        text,
        state,
      })
    },

    setCoachAnalysisStatus(turnId: string, status: 'pending' | 'analyzed' | 'failed') {
      this.coachAnalysisStatus[turnId] = status
    },

    setPronunciationResult(turnId: string, score: PronScore) {
      this.pronunciationByTurn[turnId] = score
      if (this.currentTurnId === turnId) {
        this.currentPronScore = score
      }
    },

    setCorrectionsResult(turnId: string, issues: CorrectionIssue[]) {
      this.correctionsByTurn[turnId] = issues
      if (this.currentTurnId === turnId) {
        this.currentCorrections = issues
      }
    },

    resetSummaryState() {
      this.summary = null
      this.summaryReady = false
      this.summaryLoading = false
    },
  },
})
