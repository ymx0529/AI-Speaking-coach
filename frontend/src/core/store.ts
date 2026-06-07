import axios from 'axios'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import type {
  AuthResponse,
  AuthUser,
  ConversationMessage,
  CorrectionIssue,
  Difficulty,
  PronScore,
  SessionSummaryResponse,
} from './types'

type AppPhase = 'home' | 'auth' | 'scene_select' | 'in_session' | 'summary'
type CoachAnalysisStatus = 'idle' | 'pending' | 'analyzed'

const TOKEN_KEY = 'speakcoach_token'
const USER_KEY = 'speakcoach_user'

function createEmptyPronScore(): PronScore {
  return {
    overall: 0,
    accuracy: 0,
    fluency: 0,
    completeness: 0,
    words: [],
  }
}

function createId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`
}

export const useAppStore = defineStore('app', () => {
  const phase = ref<AppPhase>('home')
  const authReady = ref(true)
  const authLoading = ref(false)
  const currentUser = ref<AuthUser | null>(readCachedUser())
  const authToken = ref<string | null>(localStorage.getItem(TOKEN_KEY))

  const sessionId = ref<string | null>(null)
  const sessionReady = ref(false)
  const sceneId = ref<string | null>(null)
  const personaId = ref('strict_interviewer')
  const difficulty = ref<Difficulty>(1)
  const customBackground = ref('')

  const currentTurnId = ref<string | null>(null)
  const latestAnalyzedTurnId = ref<string | null>(null)
  const messages = ref<ConversationMessage[]>([])
  const asrText = ref('')
  const aiReplyText = ref('')
  const isRecording = ref(false)
  const isSpeaking = ref(false)
  const isReplyAudioPending = ref(false)

  const currentPronScore = ref<PronScore>(createEmptyPronScore())
  const currentCorrections = ref<CorrectionIssue[]>([])
  const currentSampleAnswer = ref('')

  const pronunciationByTurn = ref<Record<string, PronScore>>({})
  const correctionsByTurn = ref<Record<string, CorrectionIssue[]>>({})
  const sampleAnswerByTurn = ref<Record<string, string>>({})
  const coachAnalysisStatus = ref<Record<string, CoachAnalysisStatus>>({})

  const summary = ref<SessionSummaryResponse | null>(null)
  const summaryReady = ref(false)
  const summaryLoading = ref(false)

  const lastError = ref<{ code: string; message: string; retryable?: boolean } | null>(null)

  const isAuthenticated = computed(() => !!currentUser.value && !!authToken.value)

  function persistToken(token: string | null) {
    authToken.value = token
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  function persistUser(user: AuthUser | null) {
    currentUser.value = user
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    } else {
      localStorage.removeItem(USER_KEY)
    }
  }

  function applyAuthSession(payload: AuthResponse) {
    persistToken(payload.token)
    persistUser(payload.user)
    authReady.value = true
  }

  async function register(payload: { name: string; email: string; password: string }) {
    authLoading.value = true
    try {
      const { data } = await axios.post<AuthResponse>('/api/auth/register', payload)
      applyAuthSession(data)
      phase.value = 'scene_select'
      return true
    } finally {
      authLoading.value = false
    }
  }

  async function login(payload: { email: string; password: string }) {
    authLoading.value = true
    try {
      const { data } = await axios.post<AuthResponse>('/api/auth/login', payload)
      applyAuthSession(data)
      phase.value = 'scene_select'
      return true
    } finally {
      authLoading.value = false
    }
  }

  async function restoreAuth() {
    if (!authToken.value) {
      authReady.value = true
      persistUser(null)
      return null
    }

    authLoading.value = true
    authReady.value = false
    try {
      const { data } = await axios.get<AuthUser>('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${authToken.value}`,
        },
      })
      persistUser(data)
      authReady.value = true
      return data
    } catch {
      persistToken(null)
      persistUser(null)
      authReady.value = true
      return null
    } finally {
      authLoading.value = false
    }
  }

  async function logout() {
    try {
      if (authToken.value) {
        await axios.post(
          '/api/auth/logout',
          {},
          {
            headers: {
              Authorization: `Bearer ${authToken.value}`,
            },
          },
        )
      }
    } catch {
      // Ignore logout failures and clear local session anyway.
    } finally {
      persistToken(null)
      persistUser(null)
      clearConversationState()
      phase.value = 'home'
    }
  }

  function ensureSystemWelcome() {
    if (messages.value.length > 0) return
    messages.value = [
      {
        id: createId('msg'),
        turnId: null,
        role: 'system',
        text: '会话已开始。完成一轮录音后，系统会把你的英文和 AI 回复保存在这里。',
        state: 'final',
      },
    ]
  }

  function startSession(payload: {
    sessionId: string
    sceneId: string
    difficulty: Difficulty
    personaId: string
    customBackground?: string
  }) {
    sessionId.value = payload.sessionId
    sceneId.value = payload.sceneId
    difficulty.value = payload.difficulty
    personaId.value = payload.personaId
    customBackground.value = payload.customBackground ?? ''
    sessionReady.value = false
    currentTurnId.value = null
    asrText.value = ''
    aiReplyText.value = ''
    isRecording.value = false
    isSpeaking.value = false
    isReplyAudioPending.value = false
    currentPronScore.value = createEmptyPronScore()
    currentCorrections.value = []
    currentSampleAnswer.value = ''
    pronunciationByTurn.value = {}
    correctionsByTurn.value = {}
    sampleAnswerByTurn.value = {}
    coachAnalysisStatus.value = {}
    latestAnalyzedTurnId.value = null
    lastError.value = null
    summary.value = null
    summaryReady.value = false
    summaryLoading.value = false
    messages.value = []
    ensureSystemWelcome()
    phase.value = 'in_session'
  }

  function markSessionReady() {
    sessionReady.value = true
  }

  function resetTurn() {
    asrText.value = ''
    aiReplyText.value = ''
    currentPronScore.value = createEmptyPronScore()
    currentCorrections.value = []
    currentSampleAnswer.value = ''
    lastError.value = null
  }

  function upsertMessage(role: ConversationMessage['role'], turnId: string | null, text: string, state: ConversationMessage['state']) {
    const target = messages.value.find((message) => message.role === role && message.turnId === turnId)
    if (target) {
      target.text = text
      target.state = state
      return
    }

    messages.value.push({
      id: createId('msg'),
      turnId,
      role,
      text,
      state,
    })
  }

  function setUserMessage(turnId: string, text: string, state: ConversationMessage['state']) {
    upsertMessage('user', turnId, text, state)
  }

  function setAssistantMessage(turnId: string, text: string) {
    upsertMessage('assistant', turnId, text, 'final')
  }

  function setPronunciationResult(turnId: string, score: PronScore) {
    pronunciationByTurn.value[turnId] = score
    currentPronScore.value = score
  }

  function setCorrectionsResult(turnId: string, issues: CorrectionIssue[], sampleAnswer: string) {
    correctionsByTurn.value[turnId] = issues
    sampleAnswerByTurn.value[turnId] = sampleAnswer
    currentCorrections.value = issues
    currentSampleAnswer.value = sampleAnswer
  }

  function setCoachAnalysisStatus(turnId: string, status: CoachAnalysisStatus) {
    coachAnalysisStatus.value[turnId] = status
    if (status === 'analyzed') {
      latestAnalyzedTurnId.value = turnId
    }
  }

  function setError(error: { code: string; message: string; retryable?: boolean }) {
    lastError.value = error
  }

  function endSession() {
    phase.value = 'summary'
  }

  function resetSummaryState() {
    summary.value = null
    summaryReady.value = false
    summaryLoading.value = false
  }

  function clearConversationState() {
    sessionId.value = null
    sessionReady.value = false
    sceneId.value = null
    personaId.value = 'strict_interviewer'
    difficulty.value = 1
    customBackground.value = ''
    currentTurnId.value = null
    latestAnalyzedTurnId.value = null
    messages.value = []
    asrText.value = ''
    aiReplyText.value = ''
    isRecording.value = false
    isSpeaking.value = false
    isReplyAudioPending.value = false
    currentPronScore.value = createEmptyPronScore()
    currentCorrections.value = []
    currentSampleAnswer.value = ''
    pronunciationByTurn.value = {}
    correctionsByTurn.value = {}
    sampleAnswerByTurn.value = {}
    coachAnalysisStatus.value = {}
    resetSummaryState()
    lastError.value = null
    phase.value = 'home'
  }

  return {
    phase,
    authReady,
    authLoading,
    currentUser,
    authToken,
    isAuthenticated,
    sessionId,
    sessionReady,
    sceneId,
    personaId,
    difficulty,
    customBackground,
    currentTurnId,
    latestAnalyzedTurnId,
    messages,
    asrText,
    aiReplyText,
    isRecording,
    isSpeaking,
    isReplyAudioPending,
    currentPronScore,
    currentCorrections,
    currentSampleAnswer,
    pronunciationByTurn,
    correctionsByTurn,
    sampleAnswerByTurn,
    coachAnalysisStatus,
    summary,
    summaryReady,
    summaryLoading,
    lastError,
    register,
    login,
    restoreAuth,
    logout,
    startSession,
    markSessionReady,
    resetTurn,
    setUserMessage,
    setAssistantMessage,
    setPronunciationResult,
    setCorrectionsResult,
    setCoachAnalysisStatus,
    setError,
    endSession,
    resetSummaryState,
    clearConversationState,
  }
})

function readCachedUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}
