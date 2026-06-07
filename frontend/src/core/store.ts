import axios from 'axios'
import { defineStore } from 'pinia'

import type {
  AuthResponse,
  AuthUser,
  ConversationMessage,
  CorrectionIssue,
  ErrorCode,
  PronScore,
  SessionSummaryResponse,
} from './types'
import { ws } from './ws'

const AUTH_TOKEN_KEY = 'speakcoach.auth_token'
const AUTH_RESTORE_TIMEOUT_MS = 4000

function getStoredToken() {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(AUTH_TOKEN_KEY)
}

function storeToken(token: string | null) {
  if (typeof window === 'undefined') return
  if (token) {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token)
  } else {
    window.localStorage.removeItem(AUTH_TOKEN_KEY)
  }
}

function setAuthHeader(token: string | null) {
  if (token) {
    axios.defaults.headers.common.Authorization = `Bearer ${token}`
  } else {
    delete axios.defaults.headers.common.Authorization
  }
}

function getAuthErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}

function withTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => {
      reject(new Error('Request timed out.'))
    }, timeoutMs)

    promise
      .then((value) => resolve(value))
      .catch((error) => reject(error))
      .finally(() => window.clearTimeout(timer))
  })
}

export const useAppStore = defineStore('app', {
  state: () => ({
    currentUser: null as AuthUser | null,
    authToken: null as string | null,
    authReady: false,
    authLoading: false,
    authError: '',

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
    currentSampleAnswer: '',
    summary: null as SessionSummaryResponse | null,
    lastError: null as { code: ErrorCode | string; message: string; retryable?: boolean } | null,

    pronunciationByTurn: {} as Record<string, PronScore>,
    correctionsByTurn: {} as Record<string, CorrectionIssue[]>,
    sampleAnswerByTurn: {} as Record<string, string>,
    coachAnalysisStatus: {} as Record<string, 'pending' | 'analyzed' | 'failed'>,
    latestAnalyzedTurnId: null as string | null,
    summaryReady: false,
    summaryLoading: false,
  }),

  actions: {
    async restoreAuth() {
      const token = getStoredToken()
      if (!token) {
        this.clearAuthSession()
        this.authReady = true
        return
      }

      this.authLoading = true
      setAuthHeader(token)
      try {
        const response = await withTimeout(
          axios.get<AuthUser>('/api/auth/me', { timeout: AUTH_RESTORE_TIMEOUT_MS }),
          AUTH_RESTORE_TIMEOUT_MS + 500,
        )
        this.authToken = token
        this.currentUser = response.data
        this.authError = ''
      } catch {
        this.clearAuthSession()
        this.authError = '登录状态已过期，请重新登录。'
      } finally {
        this.authLoading = false
        this.authReady = true
      }
    },

    async login(payload: { email: string; password: string }) {
      this.authLoading = true
      this.authError = ''
      try {
        const response = await axios.post<AuthResponse>('/api/auth/login', payload)
        this.applyAuthSession(response.data)
      } catch (error) {
        const message = getAuthErrorMessage(error, '登录失败，请检查邮箱和密码。')
        this.authError = message
        throw new Error(message)
      } finally {
        this.authLoading = false
        this.authReady = true
      }
    },

    async register(payload: { name: string; email: string; password: string }) {
      this.authLoading = true
      this.authError = ''
      try {
        const response = await axios.post<AuthResponse>('/api/auth/register', payload)
        this.applyAuthSession(response.data)
      } catch (error) {
        const message = getAuthErrorMessage(error, '注册失败，请稍后重试。')
        this.authError = message
        throw new Error(message)
      } finally {
        this.authLoading = false
        this.authReady = true
      }
    },

    async logout() {
      const token = this.authToken
      if (token) {
        try {
          await axios.post('/api/auth/logout', null, {
            headers: { Authorization: `Bearer ${token}` },
          })
        } catch {
          // Server-side session may already be gone, local logout should still succeed.
        }
      }
      ws.disconnect()
      this.clearAuthSession()
      this.clearConversationState()
      this.authReady = true
    },

    applyAuthSession(response: AuthResponse) {
      this.authToken = response.token
      this.currentUser = response.user
      this.authError = ''
      storeToken(response.token)
      setAuthHeader(response.token)
      this.clearConversationState()
    },

    clearAuthSession() {
      this.authToken = null
      this.currentUser = null
      this.authError = ''
      storeToken(null)
      setAuthHeader(null)
    },

    clearConversationState() {
      this.sessionId = null
      this.sceneId = null
      this.difficulty = 1
      this.personaId = null
      this.customBackground = ''
      this.phase = 'scene_select'
      this.sessionReady = false
      this.currentTurnId = null
      this.isRecording = false
      this.isSpeaking = false
      this.isReplyAudioPending = false
      this.asrText = ''
      this.aiReplyText = ''
      this.messages = []
      this.currentPronScore = null
      this.currentCorrections = []
      this.currentSampleAnswer = ''
      this.summary = null
      this.lastError = null
      this.pronunciationByTurn = {}
      this.correctionsByTurn = {}
      this.sampleAnswerByTurn = {}
      this.coachAnalysisStatus = {}
      this.latestAnalyzedTurnId = null
      this.summaryReady = false
      this.summaryLoading = false
    },

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
      this.sampleAnswerByTurn = {}
      this.coachAnalysisStatus = {}
      this.summary = null
      this.summaryReady = false
      this.summaryLoading = false
      this.currentTurnId = null
      this.asrText = ''
      this.aiReplyText = ''
      this.currentPronScore = null
      this.currentCorrections = []
      this.currentSampleAnswer = ''
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
      this.isSpeaking = false
      this.isReplyAudioPending = false
      this.currentPronScore = null
      this.currentCorrections = []
      this.currentSampleAnswer = ''
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

    setCorrectionsResult(turnId: string, issues: CorrectionIssue[], sampleAnswer = '') {
      this.correctionsByTurn[turnId] = issues
      this.sampleAnswerByTurn[turnId] = sampleAnswer
      this.coachAnalysisStatus[turnId] = 'analyzed'
      this.latestAnalyzedTurnId = turnId
      if (this.currentTurnId === turnId) {
        this.currentCorrections = issues
        this.currentSampleAnswer = sampleAnswer
      }
    },

    resetSummaryState() {
      this.summary = null
      this.summaryReady = false
      this.summaryLoading = false
    },
  },
})
