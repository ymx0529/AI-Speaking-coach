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
          当前版本会模拟两段音频分片上传：第一段返回实时识别中间结果，第二段返回本轮最终识别文本。
        </div>

        <div class="mt-4 flex flex-wrap gap-3">
          <button
            class="rounded-full bg-emerald-600 px-4 py-2 text-sm font-medium text-white"
            @click="runMockTurn()"
          >
            模拟实时识别
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
import { onMounted, onUnmounted } from 'vue'

import { useAppStore } from '@/core/store'
import { ws } from '@/core/ws'

import PronScoreBar from './PronScoreBar.vue'
import { useConversation } from './useConversation'

const store = useAppStore()
const { errorMessage, handleServerMessage, runMockTurn } = useConversation()
let unsubscribe: (() => void) | null = null

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
