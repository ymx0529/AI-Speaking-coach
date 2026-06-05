<template>
  <section class="mx-auto max-w-6xl p-6">
    <div class="grid gap-6 lg:grid-cols-[2fr_1fr]">
      <div class="rounded-3xl bg-white p-6 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm text-slate-500">Conversation Scaffold</div>
            <h2 class="text-2xl font-semibold text-slate-900">{{ store.sceneId }}</h2>
          </div>
          <button
            class="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white"
            @click="finishSession()"
          >
            结束
          </button>
        </div>

        <div class="mt-6 rounded-2xl border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          最小验证版：点击下方按钮，模拟一次“发送语音后拿到识别、评分、回复、纠错”的完整回合。
        </div>

        <div class="mt-4 flex flex-wrap gap-3">
          <button
            class="rounded-full bg-emerald-600 px-4 py-2 text-sm font-medium text-white"
            @click="runMockTurn()"
          >
            模拟一轮对话
          </button>
          <div v-if="errorMessage" class="rounded-full bg-rose-50 px-4 py-2 text-sm text-rose-700">
            {{ errorMessage }}
          </div>
        </div>

        <div class="mt-6 space-y-4">
          <div class="rounded-2xl bg-slate-50 p-4">
            <div class="text-xs uppercase tracking-wide text-slate-400">ASR Text</div>
            <div class="mt-2 text-slate-800">{{ store.asrText || 'Waiting for speech input...' }}</div>
          </div>

          <div class="rounded-2xl bg-slate-50 p-4">
            <div class="text-xs uppercase tracking-wide text-slate-400">AI Reply</div>
            <div class="mt-2 text-slate-800">{{ store.aiReplyText || 'Reply placeholder.' }}</div>
          </div>

          <PronScoreBar :score="store.currentPronScore" />
        </div>
      </div>

      <aside class="space-y-4">
        <div class="rounded-3xl bg-white p-6 shadow-sm">
          <div class="text-sm font-medium text-slate-900">Coach Panel</div>
          <div class="mt-3">
            <slot name="correction" />
          </div>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

import { useAppStore } from '@/core/store'
import type { ServerMsg } from '@/core/types'
import { ws } from '@/core/ws'

import PronScoreBar from './PronScoreBar.vue'

const store = useAppStore()
const errorMessage = ref('')
let unsubscribe: (() => void) | null = null

function handleServerMessage(msg: ServerMsg) {
  if (msg.type === 'asr_partial') {
    store.asrText = msg.text
  } else if (msg.type === 'asr_final') {
    store.currentTurnId = msg.turn_id
    store.asrText = msg.text
  } else if (msg.type === 'pron_score') {
    store.currentPronScore = {
      overall: msg.overall,
      accuracy: msg.accuracy,
      fluency: msg.fluency,
      completeness: msg.completeness,
      words: msg.words,
    }
  } else if (msg.type === 'reply_text') {
    store.aiReplyText = msg.text
  } else if (msg.type === 'correction') {
    store.currentCorrections = msg.issues
  } else if (msg.type === 'error') {
    errorMessage.value = msg.message
  }
}

function runMockTurn() {
  errorMessage.value = ''
  store.resetTurn()
  ws.send({ type: 'audio_end', seq_count: 0 })
}

function finishSession() {
  store.endSession()
}

onMounted(() => {
  unsubscribe = ws.onMessage(handleServerMessage)
})

onUnmounted(() => {
  unsubscribe?.()
})
</script>
