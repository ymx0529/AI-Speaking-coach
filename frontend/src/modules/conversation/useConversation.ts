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

function getAudioContextCtor(): typeof AudioContext | null {
  if (typeof window === 'undefined') return null
  return window.AudioContext ?? (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext ?? null
}

function mergeFloat32Chunks(chunks: Float32Array[]): Float32Array {
  const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0)
  const merged = new Float32Array(totalLength)
  let offset = 0
  chunks.forEach((chunk) => {
    merged.set(chunk, offset)
    offset += chunk.length
  })
  return merged
}

function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2)
  const view = new DataView(buffer)

  function writeString(offset: number, value: string) {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index))
    }
  }

  writeString(0, 'RIFF')
  view.setUint32(4, 36 + samples.length * 2, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, samples.length * 2, true)

  let offset = 44
  for (let index = 0; index < samples.length; index += 1) {
    const clamped = Math.max(-1, Math.min(1, samples[index]))
    view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true)
    offset += 2
  }

  return new Blob([buffer], { type: 'audio/wav' })
}

export function useConversation() {
  const store = useAppStore()
  const errorMessage = ref('')
  const debugInfo = ref({
    audioContextState: 'idle',
    chunkCount: 0,
    sampleRate: 0,
    capturedSamples: 0,
    peakLevel: 0,
    sentBytes: 0,
    lastEncoding: '',
  })
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

  function playAssistantAudio(data: string, format?: string) {
    try {
      store.isReplyAudioPending = false
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
      store.isReplyAudioPending = false
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
      store.isReplyAudioPending = true
    } else if (msg.type === 'assistant.reply_audio') {
      playAssistantAudio(msg.data, msg.audio_format)
    } else if (msg.type === 'reply_audio') {
      playAssistantAudio(msg.data, 'mp3')
    } else if (msg.type === 'error') {
      store.isReplyAudioPending = false
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
    debugInfo.value = {
      audioContextState: 'initializing',
      chunkCount: 0,
      sampleRate: 0,
      capturedSamples: 0,
      peakLevel: 0,
      sentBytes: 0,
      lastEncoding: '',
    }
    store.resetTurn()
    recordedChunks = []

    try {
      const AudioContextCtor = getAudioContextCtor()
      if (!AudioContextCtor) {
        errorMessage.value = '当前浏览器不支持 PCM 录音，请使用模拟模式。'
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
      debugInfo.value.audioContextState = audioContext.state
      debugInfo.value.sampleRate = recordedSampleRate

      processorNode.onaudioprocess = (event: AudioProcessingEvent) => {
        const inputData = event.inputBuffer.getChannelData(0)
        recordedChunks.push(new Float32Array(inputData))
        let peak = 0
        for (let index = 0; index < inputData.length; index += 1) {
          const value = Math.abs(inputData[index])
          if (value > peak) peak = value
        }
        debugInfo.value.chunkCount += 1
        debugInfo.value.capturedSamples += inputData.length
        debugInfo.value.peakLevel = Math.max(debugInfo.value.peakLevel, peak)
      }

      sourceNode.connect(processorNode)
      processorNode.connect(muteNode)
      muteNode.connect(audioContext.destination)
    } catch {
      errorMessage.value = '无法访问麦克风，请检查浏览器权限设置。'
      debugInfo.value.audioContextState = 'failed'
      cleanupMediaStream()
    }
  }

  async function stopRecording() {
    if (!store.isRecording) {
      return
    }

    if (!store.sessionId || recordedChunks.length === 0) {
      errorMessage.value = '前端没有采集到音频数据，请检查麦克风权限、系统默认输入设备，或确认页面是否成功开始录音。'
      cleanupMediaStream()
      return
    }

    store.isRecording = false

    try {
      const wavBlob = encodeWav(mergeFloat32Chunks(recordedChunks), recordedSampleRate)
      const chunk = await blobToBase64(wavBlob)
      debugInfo.value.sentBytes = wavBlob.size
      debugInfo.value.lastEncoding = 'wav_pcm16'
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
      errorMessage.value = '录音数据处理失败，请重试。'
    } finally {
      cleanupMediaStream()
    }
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
    debugInfo,
    recordingSupported,
    handleServerMessage,
    finishCurrentSession,
    startRecording,
    stopRecording,
    runMockTurn,
  }
}
