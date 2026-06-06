<template>
  <section class="mx-auto max-w-3xl p-6">
    <div class="rounded-3xl bg-white p-8 shadow-sm">
      <div class="text-sm text-slate-500">Session {{ sessionId }}</div>
      <h2 class="mt-1 text-2xl font-semibold text-slate-900">练习总结</h2>

      <!-- Loading -->
      <div v-if="store.summaryLoading" class="mt-6 flex items-center gap-2 text-slate-500">
        <span class="animate-spin">⟳</span>
        <span>正在加载总结...</span>
      </div>

      <!-- Error + retry -->
      <div v-else-if="errorMessage" class="mt-6 space-y-3">
        <div class="rounded-2xl bg-rose-50 p-4 text-rose-700">{{ errorMessage }}</div>
        <button
          class="rounded-full bg-rose-600 px-4 py-2 text-sm font-medium text-white"
          @click="retry()"
        >
          重试
        </button>
      </div>

      <!-- Summary content -->
      <div v-else-if="store.summary" class="mt-6 space-y-5">
        <p class="text-slate-700 leading-relaxed">{{ store.summary.ai_feedback }}</p>

        <!-- Pronunciation metrics -->
        <div>
          <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">发音评分</div>
          <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="综合" :score="store.summary.pron_avg" />
            <MetricCard label="准确度" :score="store.summary.accuracy_avg" />
            <MetricCard label="流利度" :score="store.summary.fluency_avg" />
            <MetricCard label="完整度" :score="store.summary.completeness_avg" />
          </div>
        </div>

        <!-- Language metrics -->
        <div
          v-if="
            store.summary.grammar_score != null ||
            store.summary.expression_score != null ||
            store.summary.vocabulary_score != null
          "
        >
          <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">语言维度</div>
          <div class="grid gap-3 sm:grid-cols-3">
            <MetricCard
              v-if="store.summary.grammar_score != null"
              label="语法"
              :score="store.summary.grammar_score"
            />
            <MetricCard
              v-if="store.summary.expression_score != null"
              label="表达"
              :score="store.summary.expression_score"
            />
            <MetricCard
              v-if="store.summary.vocabulary_score != null"
              label="词汇"
              :score="store.summary.vocabulary_score"
            />
          </div>
        </div>

        <!-- Stats -->
        <div class="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
          共 <span class="font-semibold">{{ store.summary.total_turns }}</span> 轮对话，
          累计纠错 <span class="font-semibold">{{ store.summary.corrections_count }}</span> 条
          <span v-if="store.summary.avg_response_latency_ms != null">
            ，平均响应 {{ store.summary.avg_response_latency_ms }} ms
          </span>
        </div>

        <!-- Focus recommendations -->
        <div v-if="store.summary.focus_recommendations?.length">
          <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">建议重点</div>
          <ul class="space-y-2">
            <li
              v-for="(rec, i) in store.summary.focus_recommendations"
              :key="i"
              class="flex items-start gap-2 rounded-2xl bg-blue-50 px-4 py-3 text-sm text-blue-800"
            >
              <span class="mt-0.5 shrink-0 text-blue-400">•</span>
              <span>{{ rec }}</span>
            </li>
          </ul>
        </div>

        <!-- Turn review -->
        <div v-if="store.summary.turns.length">
          <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">逐轮回顾</div>
          <div class="space-y-2">
            <div
              v-for="(turn, i) in store.summary.turns"
              :key="turn.turn_id"
              class="rounded-2xl bg-slate-50 p-4 text-sm text-slate-700"
            >
              <div class="mb-1 flex items-center justify-between">
                <span class="font-medium">第 {{ i + 1 }} 轮</span>
                <span class="text-xs font-mono">{{ Math.round(turn.pron_score.overall) }} 分</span>
              </div>
              <div class="text-slate-600">你说：{{ turn.user_text }}</div>
              <div v-if="turn.corrections.length" class="mt-1 text-xs text-amber-700">
                纠错：{{ turn.corrections.map((c) => `${c.original} → ${c.corrected}`).join(' / ') }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty (no data yet) -->
      <p v-else class="mt-6 text-sm text-slate-500">暂无总结数据。</p>

      <button
        class="mt-8 rounded-full bg-slate-900 px-5 py-2 text-sm font-medium text-white"
        @click="restart()"
      >
        再练一次
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { defineComponent, h, onMounted, ref } from 'vue'

import { useAppStore } from '@/core/store'
import { ws } from '@/core/ws'
import { useCoach } from './useCoach'

const props = defineProps<{ sessionId: string }>()

const store = useAppStore()
const { fetchSummary } = useCoach()
const errorMessage = ref('')

async function loadSummary() {
  errorMessage.value = ''
  store.resetSummaryState()
  const result = await fetchSummary(props.sessionId)
  if (!result) {
    errorMessage.value = '总结获取失败，请确认后端已启动并至少完成一轮对话。'
  }
}

async function retry() {
  await loadSummary()
}

function restart() {
  ws.disconnect()
  store.$reset()
}

onMounted(() => {
  void loadSummary()
})

const MetricCard = defineComponent({
  props: {
    label: { type: String, required: true },
    score: { type: Number, required: true },
  },
  setup(cardProps) {
    const color =
      cardProps.score >= 80
        ? 'text-emerald-600'
        : cardProps.score >= 60
          ? 'text-amber-600'
          : 'text-rose-600'
    return () =>
      h('div', { class: 'rounded-2xl bg-slate-50 p-4 text-center' }, [
        h('div', { class: `text-2xl font-bold ${color}` }, cardProps.score.toFixed(0)),
        h('div', { class: 'mt-1 text-xs text-slate-500' }, cardProps.label),
      ])
  },
})
</script>
