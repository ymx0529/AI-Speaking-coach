import { ref } from 'vue'
import axios from 'axios'

import { blobToBase64, encodeWav, getAudioContextCtor, getAudioMimeType, mergeFloat32Chunks } from '@/core/audio'
import { useAppStore } from '@/core/store'
import type { ServerMsg, SessionStatusResponse } from '@/core/types'
import { ws } from '@/core/ws'

interface QueuedAssistantAudio {
  turnId: string | null
  data: string
  format?: string
}

const ASSISTANT_AUDIO_MIN_BUFFER_CHUNKS = 2
const ASSISTANT_AUDIO_MAX_INITIAL_BUFFER_WAIT_MS = 300

export function useConversation() {
  const store = useAppStore()
  const errorMessage = ref('')

  const authHeaders = () =>
    store.authToken
      ? {
          Authorization: `Bearer ${store.authToken}`,
        }
      : undefined

  const recordingSupported =
    typeof navigator !== 'undefined' &&
    !!navigator.mediaDevices?.getUserMedia &&
    !!getAudioContextCtor()

  let mediaStream: MediaStream | null = null
  let audioContext: AudioContext | null = null
  let sourceNode: MediaStreamAudioSourceNode | null = null
  let processorNode: ScriptProcessorNode | null = null
  let muteNode: GainNode | null = null
  let recordedChunks: Float32Array[] = []
  let recordedSampleRate = 16000
  let assistantAudioQueue: QueuedAssistantAudio[] = []
  let activeAssistantAudio: HTMLAudioElement | null = null
  let activeAudioStreamTurnId: string | null = null
  let assistantAudioExpectedChunks: number | null = null
  let assistantAudioReceivedChunks = 0
  let assistantAudioBufferTimer: number | null = null
  let assistantAudioPlaybackStarted = false
  let audioStreamEnded = false

  function isCurrentAudioTurn(turnId?: string | null) {
    return !turnId || !store.currentTurnId || store.currentTurnId === turnId
  }

  function clearAssistantAudioBufferTimer() {
    if (assistantAudioBufferTimer !== null) {
      window.clearTimeout(assistantAudioBufferTimer)
      assistantAudioBufferTimer = null
    }
  }

  function stopAssistantAudioPlayback() {
    clearAssistantAudioBufferTimer()
    if (activeAssistantAudio) {
      activeAssistantAudio.pause()
      activeAssistantAudio.src = ''
    }
    activeAssistantAudio = null
    assistantAudioQueue = []
    activeAudioStreamTurnId = null
    assistantAudioExpectedChunks = null
    assistantAudioReceivedChunks = 0
    assistantAudioPlaybackStarted = false
    audioStreamEnded = false
    store.isSpeaking = false
    store.isReplyAudioPending = false
  }

  function startAssistantAudioStream(turnId: string, totalChunks?: number) {
    if (!isCurrentAudioTurn(turnId)) return

    if (activeAudioStreamTurnId !== turnId) {
      stopAssistantAudioPlayback()
      activeAudioStreamTurnId = turnId
      assistantAudioReceivedChunks = 0
      audioStreamEnded = false
    }
    if (typeof totalChunks === 'number' && totalChunks > 0) {
      assistantAudioExpectedChunks = totalChunks
    }
    store.isReplyAudioPending = true
  }

  function hasEnoughAssistantAudioBuffer() {
    if (assistantAudioQueue.length === 0) return false
    if (audioStreamEnded) return true
    if (assistantAudioExpectedChunks !== null && assistantAudioReceivedChunks >= assistantAudioExpectedChunks) {
      return true
    }

    const expectedBuffer = Math.min(
      ASSISTANT_AUDIO_MIN_BUFFER_CHUNKS,
      assistantAudioExpectedChunks ?? ASSISTANT_AUDIO_MIN_BUFFER_CHUNKS,
    )
    return assistantAudioQueue.length >= expectedBuffer
  }

  function finishAssistantAudioIfIdle() {
    if (assistantAudioQueue.length > 0) {
      playNextAssistantAudio(true)
      return
    }

    store.isSpeaking = false
    store.isReplyAudioPending = !!activeAudioStreamTurnId && !audioStreamEnded
  }

  function scheduleAssistantAudioPlayback() {
    if (activeAssistantAudio || assistantAudioQueue.length === 0) return
    if (assistantAudioPlaybackStarted || hasEnoughAssistantAudioBuffer()) {
      playNextAssistantAudio(true)
      return
    }
    if (assistantAudioBufferTimer !== null) return

    assistantAudioBufferTimer = window.setTimeout(() => {
      assistantAudioBufferTimer = null
      playNextAssistantAudio(true)
    }, ASSISTANT_AUDIO_MAX_INITIAL_BUFFER_WAIT_MS)
  }

  function cleanupMediaStream() {
    processorNode?.disconnect()
    sourceNode?.disconnect()
    muteNode?.disconnect()
    if (audioContext) {
      void audioContext.close()
    }
    processorNode = null
    sourceNode = null
    muteNode = null
    audioContext = null
    mediaStream?.getTracks().forEach((track) => track.stop())
    mediaStream = null
    store.isRecording = false
    recordedChunks = []
  }

  function playNextAssistantAudio(force = false) {
    if (activeAssistantAudio || assistantAudioQueue.length === 0) return
    if (!force && !assistantAudioPlaybackStarted && !hasEnoughAssistantAudioBuffer()) {
      store.isSpeaking = false
      store.isReplyAudioPending = true
      scheduleAssistantAudioPlayback()
      return
    }
    clearAssistantAudioBufferTimer()

    const nextAudio = assistantAudioQueue.shift()
    if (!nextAudio) return
    if (!isCurrentAudioTurn(nextAudio.turnId)) {
      playNextAssistantAudio()
      return
    }

    try {
      store.isReplyAudioPending = false
      store.isSpeaking = true
      assistantAudioPlaybackStarted = true
      const audio = new Audio(`data:${getAudioMimeType(nextAudio.format)};base64,${nextAudio.data}`)
      activeAssistantAudio = audio
      const finishAudio = () => {
        if (activeAssistantAudio === audio) {
          activeAssistantAudio = null
        }
        finishAssistantAudioIfIdle()
      }
      audio.onended = finishAudio
      audio.onerror = finishAudio
      const playPromise = audio.play()
      if (playPromise) {
        void playPromise.catch(finishAudio)
      }
    } catch {
      activeAssistantAudio = null
      finishAssistantAudioIfIdle()
    }
  }

  function queueAssistantAudio(data: string, format?: string, turnId?: string | null, endsStream = false) {
    if (!isCurrentAudioTurn(turnId)) return

    if (turnId && activeAudioStreamTurnId !== turnId) {
      startAssistantAudioStream(turnId)
    }
    if (turnId && endsStream && activeAudioStreamTurnId === turnId) {
      audioStreamEnded = true
    }
    assistantAudioReceivedChunks += 1
    assistantAudioQueue.push({ turnId: turnId ?? null, data, format })
    scheduleAssistantAudioPlayback()
  }

  function endAssistantAudioStream(turnId: string) {
    if (!isCurrentAudioTurn(turnId)) return
    if (activeAudioStreamTurnId === turnId) {
      audioStreamEnded = true
    }
    if (!activeAssistantAudio && assistantAudioQueue.length > 0) {
      playNextAssistantAudio(true)
    } else if (!activeAssistantAudio && assistantAudioQueue.length === 0) {
      store.isSpeaking = false
      store.isReplyAudioPending = false
    }
  }

  function handleServerMessage(msg: ServerMsg) {
    if (msg.type === 'session.ready') {
      store.markSessionReady()
    } else if (msg.type === 'turn.started') {
      stopAssistantAudioPlayback()
      store.currentTurnId = msg.turn_id
      store.setUserMessage(msg.turn_id, '', 'streaming')
    } else if (msg.type === 'asr.partial' || msg.type === 'asr_partial') {
      store.asrText = msg.text
      if ('turn_id' in msg) {
        store.setUserMessage(msg.turn_id, msg.text, 'streaming')
      }
    } else if (msg.type === 'user_turn.final' || msg.type === 'asr_final') {
      store.currentTurnId = msg.turn_id
      store.asrText = msg.text
      store.setUserMessage(msg.turn_id, msg.text, 'final')
    } else if (msg.type === 'assistant.reply_text' || msg.type === 'reply_text') {
      store.aiReplyText = msg.text
      store.isReplyAudioPending = true
      store.setAssistantMessage(msg.turn_id, msg.text)
    } else if (msg.type === 'assistant.reply_audio') {
      queueAssistantAudio(msg.data, msg.audio_format, msg.turn_id, true)
    } else if (msg.type === 'assistant.reply_audio_start') {
      startAssistantAudioStream(msg.turn_id, msg.total_chunks)
    } else if (msg.type === 'assistant.reply_audio_chunk') {
      queueAssistantAudio(msg.data, msg.audio_format, msg.turn_id)
    } else if (msg.type === 'assistant.reply_audio_end') {
      endAssistantAudioStream(msg.turn_id)
    } else if (msg.type === 'reply_audio') {
      queueAssistantAudio(msg.data, 'mp3', msg.turn_id, true)
    } else if (msg.type === 'error') {
      stopAssistantAudioPlayback()
      store.isReplyAudioPending = false
      errorMessage.value = msg.message
      store.setError({
        code: msg.code,
        message: msg.message,
        retryable: msg.retryable,
      })
    }
  }

  async function startRecording() {
    if (!store.sessionId) {
      errorMessage.value = '请先选择练习场景。'
      return
    }

    if (!recordingSupported) {
      errorMessage.value = '当前浏览器不支持录音，请更换浏览器后重试。'
      return
    }

    errorMessage.value = ''
    stopAssistantAudioPlayback()
    store.resetTurn()
    recordedChunks = []

    try {
      const AudioContextCtor = getAudioContextCtor()
      if (!AudioContextCtor) {
        errorMessage.value = '当前浏览器不支持录音编码，请更换浏览器后重试。'
        return
      }

      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioContext = new AudioContextCtor()
      await audioContext.resume()
      recordedSampleRate = audioContext.sampleRate
      sourceNode = audioContext.createMediaStreamSource(mediaStream)
      processorNode = audioContext.createScriptProcessor(4096, 1, 1)
      muteNode = audioContext.createGain()
      muteNode.gain.value = 0
      store.isRecording = true

      processorNode.onaudioprocess = (event: AudioProcessingEvent) => {
        const inputData = event.inputBuffer.getChannelData(0)
        recordedChunks.push(new Float32Array(inputData))
      }

      sourceNode.connect(processorNode)
      processorNode.connect(muteNode)
      muteNode.connect(audioContext.destination)
    } catch {
      errorMessage.value = '无法访问麦克风，请检查浏览器权限。'
      cleanupMediaStream()
    }
  }

  async function stopRecording() {
    if (!store.isRecording) return

    if (!store.sessionId || recordedChunks.length === 0) {
      errorMessage.value = '没有采集到语音，请确认麦克风正常后重试。'
      cleanupMediaStream()
      return
    }

    store.isRecording = false

    try {
      const wavBlob = encodeWav(mergeFloat32Chunks(recordedChunks), recordedSampleRate)
      const chunk = await blobToBase64(wavBlob)
      ws.send({
        type: 'audio.append',
        session_id: store.sessionId,
        turn_id: null,
        seq: 0,
        encoding: 'wav_pcm16',
        chunk,
        is_last: true,
        client_ts: Date.now(),
      })
    } catch {
      errorMessage.value = '录音处理失败，请重新开始说话。'
    } finally {
      cleanupMediaStream()
    }
  }

  async function finishCurrentSession() {
    if (!store.sessionId) {
      errorMessage.value = '当前没有可结束的对话。'
      return
    }

    if (ws.isConnected()) {
      ws.send({
        type: 'session.finish',
        session_id: store.sessionId,
      })
    }

    try {
      for (let attempt = 0; attempt < 6; attempt += 1) {
        const response = await axios.get<SessionStatusResponse>(`/api/sessions/${store.sessionId}/status`, {
          headers: authHeaders(),
        })
        if (response.data.state === 'finished') {
          store.endSession()
          return
        }
        await new Promise((resolve) => window.setTimeout(resolve, 250))
      }
    } catch {
      errorMessage.value = '结束对话失败，请稍后重试。'
      return
    }
    errorMessage.value = '对话还没有结束，请稍后再试。'
  }

  return {
    errorMessage,
    recordingSupported,
    handleServerMessage,
    finishCurrentSession,
    startRecording,
    stopRecording,
  }
}
