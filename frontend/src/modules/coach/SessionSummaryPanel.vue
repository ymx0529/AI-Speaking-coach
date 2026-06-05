<template>
  <section class="mx-auto max-w-3xl p-6">
    <div class="rounded-3xl bg-white p-8 shadow-sm">
      <div class="text-sm text-slate-500">Summary Scaffold</div>
      <h2 class="mt-2 text-2xl font-semibold text-slate-900">Session {{ sessionId }}</h2>
      <div v-if="loading" class="mt-4 text-slate-500">正在加载总结...</div>
      <div v-else-if="errorMessage" class="mt-4 rounded-2xl bg-rose-50 p-4 text-rose-700">
        {{ errorMessage }}
      </div>
      <div v-else-if="summary" class="mt-4 space-y-4">
        <p class="text-slate-700">{{ summary.ai_feedback }}</p>
        <div class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-2xl bg-slate-50 p-4">综合评分：{{ summary.pron_avg }}</div>
          <div class="rounded-2xl bg-slate-50 p-4">准确度：{{ summary.accuracy_avg }}</div>
          <div class="rounded-2xl bg-slate-50 p-4">流利度：{{ summary.fluency_avg }}</div>
          <div class="rounded-2xl bg-slate-50 p-4">完整度：{{ summary.completeness_avg }}</div>
        </div>
        <div class="rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
          共 {{ summary.total_turns }} 轮，累计纠错 {{ summary.corrections_count }} 条。
        </div>
      </div>
      <button
        class="mt-6 rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white"
        @click="restart()"
      >
        再练一次
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { onMounted, ref } from 'vue'

import { useAppStore } from '@/core/store'
import type { SessionSummaryResponse } from '@/core/types'
import { ws } from '@/core/ws'

const props = defineProps<{
  sessionId: string
}>()

const store = useAppStore()
const summary = ref<SessionSummaryResponse | null>(null)
const loading = ref(true)
const errorMessage = ref('')

async function loadSummary() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await axios.post<SessionSummaryResponse>(
      `http://localhost:8000/api/sessions/${props.sessionId}/summary`
    )
    summary.value = response.data
    store.summary = response.data
  } catch (error) {
    console.error(error)
    errorMessage.value = '总结获取失败，请确认后端已经启动并至少完成一轮对话。'
  } finally {
    loading.value = false
  }
}

function restart() {
  ws.disconnect()
  store.$reset()
}

onMounted(() => {
  void loadSummary()
})
</script>
