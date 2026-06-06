import { ref } from 'vue'

import { useAppStore } from '@/core/store'
import type { ServerMsg } from '@/core/types'
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

export function useConversation() {
  const store = useAppStore()
  const errorMessage = ref('')

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

  return {
    errorMessage,
    handleServerMessage,
    runMockTurn,
  }
}
