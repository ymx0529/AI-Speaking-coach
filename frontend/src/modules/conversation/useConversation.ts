import { ref } from 'vue'
import axios from 'axios'

import { useAppStore } from '@/core/store'
import type { ServerMsg, SessionStatusResponse } from '@/core/types'
import { ws } from '@/core/ws'

const SCENE_SAMPLES: Record<string, [string, string]> = {
  interview: ['Hello, I would like', ' to introduce myself.'],
  restaurant: ['I would like to order', ' a pasta and water.'],
  meeting: ['I think we should', ' increase the budget.'],
}

function encodeChunk(text: string) {
  return btoa(text)
}

function getAudioMimeType(format?: string) {
  if (format === 'wav_pcm16') return 'audio/wav'
  return 'audio/mpeg'
}

async function blobToBase64(blob: Blob): Promise<string> {
  const buffer = await blob.arrayBuffer()
  const bytes = new Uint8Array(buffer)
  let binary = ''
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte)
  })
  return btoa(binary)
}

export function useConversation() {
  const store = useAppStore()
  const errorMessage = ref('')
  const recordingSupported = typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && typeof MediaRecorder !== 'undefined'
  let mediaRecorder: MediaRecorder | null = null
  let mediaStream: MediaStream | null = null
  let chunkSeq = 0
  let stopRequested = false

  function cleanupMediaStream() {
    mediaRecorder = null
    mediaStream?.getTracks().forEach((track) => track.stop())
    mediaStream = null
    store.isRecording = false
  }

  function playAssistantAudio(data: string, format?: string) {
    try {
      store.isSpeaking = true
      const audio = new Audio(`data:${getAudioMimeType(format)};base64,${data}`)
      audio.onended = () => {
        store.isSpeaking = false
      }
      audio.onerror = () => {
        store.isSpeaking = false
      }
      const playPromise = audio.play()
      if (playPromise) {
        void playPromise.catch(() => {
          store.isSpeaking = false
        })
      }
    } catch {
      store.isSpeaking = false
    }
  }

  function handleServerMessage(msg: ServerMsg) {
    if (msg.type === 'session.ready') {
      store.markSessionReady()
    } else if (msg.type === 'turn.started') {
      store.currentTurnId = msg.turn_id
    } else if (msg.type === 'asr.partial' || msg.type === 'asr_partial') {
      store.asrText = msg.text
    } else if (msg.type === 'user_turn.final' || msg.type === 'asr_final') {
      store.currentTurnId = msg.turn_id
      store.asrText = msg.text
    } else if (msg.type === 'assistant.reply_text' || msg.type === 'reply_text') {
      store.aiReplyText = msg.text
    } else if (msg.type === 'assistant.reply_audio') {
      playAssistantAudio(msg.data, msg.audio_format)
    } else if (msg.type === 'reply_audio') {
      playAssistantAudio(msg.data, 'mp3')
    } else if (msg.type === 'error') {
      errorMessage.value = msg.message
      store.setError({
        code: msg.code,
        message: msg.message,
        retryable: msg.retryable,
      })
    }
  }

  function runMockTurn() {
    if (!store.sessionId) {
      errorMessage.value = '当前没有可用会话，请先选择场景。'
      return
    }

    errorMessage.value = ''
    store.resetTurn()

    const [firstChunk, secondChunk] = SCENE_SAMPLES[store.sceneId ?? 'interview'] ?? SCENE_SAMPLES.interview

    ws.send({
      type: 'audio.append',
      session_id: store.sessionId,
      turn_id: null,
      seq: 0,
      encoding: 'webm_opus',
      chunk: encodeChunk(firstChunk),
      is_last: false,
      client_ts: Date.now(),
    })

    window.setTimeout(() => {
      ws.send({
        type: 'audio.append',
        session_id: store.sessionId!,
        turn_id: store.currentTurnId,
        seq: 1,
        encoding: 'webm_opus',
        chunk: encodeChunk(secondChunk),
        is_last: true,
        client_ts: Date.now(),
      })
    }, 250)
  }

  async function startRecording() {
    if (!store.sessionId) {
      errorMessage.value = '当前没有可用会话，请先选择场景。'
      return
    }

    if (!recordingSupported) {
      errorMessage.value = '当前浏览器不支持录音，请先使用模拟模式。'
      return
    }

    errorMessage.value = ''
    store.resetTurn()
    chunkSeq = 0
    stopRequested = false

    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'
      mediaRecorder = new MediaRecorder(mediaStream, { mimeType })
      store.isRecording = true

      mediaRecorder.ondataavailable = async (event: BlobEvent) => {
        if (!event.data || event.data.size === 0 || !store.sessionId) return
        const chunk = await blobToBase64(event.data)
        const isLast = stopRequested
        ws.send({
          type: 'audio.append',
          session_id: store.sessionId,
          turn_id: store.currentTurnId,
          seq: chunkSeq++,
          encoding: 'webm_opus',
          chunk,
          is_last: isLast,
          client_ts: Date.now(),
        })
        if (isLast) {
          stopRequested = false
          cleanupMediaStream()
        }
      }

      mediaRecorder.onerror = () => {
        errorMessage.value = '录音过程中发生错误，请重试。'
        cleanupMediaStream()
      }

      mediaRecorder.start(400)
    } catch {
      errorMessage.value = '无法访问麦克风，请检查浏览器权限设置。'
      cleanupMediaStream()
    }
  }

  function stopRecording() {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
      return
    }
    stopRequested = true
    mediaRecorder.stop()
  }

  async function finishCurrentSession() {
    if (!store.sessionId) {
      errorMessage.value = '当前没有可结束的会话。'
      return
    }

    if (ws.isConnected()) {
      ws.send({
        type: 'session.finish',
        session_id: store.sessionId,
      })
    }

    try {
      const response = await axios.get<SessionStatusResponse>(
        `http://localhost:8000/api/sessions/${store.sessionId}/status`
      )
      if (response.data.state !== 'finished') {
        errorMessage.value = '会话结束状态未同步完成，请稍后再试。'
        return
      }
    } catch {
      errorMessage.value = '结束会话失败，无法确认当前状态。'
      return
    }

    store.endSession()
  }

  return {
    errorMessage,
    recordingSupported,
    handleServerMessage,
    finishCurrentSession,
    startRecording,
    stopRecording,
    runMockTurn,
  }
}
