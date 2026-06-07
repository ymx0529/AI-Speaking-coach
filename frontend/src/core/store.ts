import axios from 'axios'
import { defineStore } from 'pinia'

import type { AuthResponse, AuthUser, CorrectionIssue, ErrorCode, PronScore, SessionSummaryResponse } from './types'
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

    // ── Conversation State (Dev A) ────────────────────────────
    sessionId: null as string | null,
    sceneId: null as string | null,
    difficulty: 1 as 1 | 2 | 3,
    personaId: null as string | null,
    phase: 'scene_select' as 'scene_select' | 'in_session' | 'summary',
    sessionReady: false,
    currentTurnId: null as string | null,
    isRecording: false,
    isSpeaking: false,
    isReplyAudioPending: false,
    asrText: '',
    aiReplyText: '',
    currentPronScore: null as PronScore | null,
    currentCorrections: [] as CorrectionIssue[],
    summary: null as SessionSummaryResponse | null,
    lastError: null as { code: ErrorCode | string; message: string; retryable?: boolean } | null,
    // ── Coach Analysis State (Dev B) ─────────────────────────
    pronunciationByTurn: {} as Record<string, PronScore>,
    correctionsByTurn: {} as Record<string, CorrectionIssue[]>,
    coachAnalysisStatus: {} as Record<string, 'pending' | 'analyzed' | 'failed'>,
    summaryReady: false,
    summaryLoading: false,
    // ─────────────────────────────────────────────────────────
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
          // Local logout should still succeed if the server session already expired.
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
      this.phase = 'scene_select'
      this.sessionReady = false
      this.currentTurnId = null
      this.isRecording = false
      this.isSpeaking = false
      this.isReplyAudioPending = false
      this.asrText = ''
      this.aiReplyText = ''
      this.currentPronScore = null
      this.currentCorrections = []
      this.summary = null
      this.lastError = null
      this.pronunciationByTurn = {}
      this.correctionsByTurn = {}
      this.coachAnalysisStatus = {}
      this.summaryReady = false
      this.summaryLoading = false
    },

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
      this.isReplyAudioPending = false
      this.currentPronScore = null
      this.currentCorrections = []
      this.lastError = null
    },

    // ── Coach actions (Dev B) ─────────────────────────────────
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
    // ─────────────────────────────────────────────────────────
  },
})
