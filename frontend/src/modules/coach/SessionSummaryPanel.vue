<template>
  <section class="mx-auto max-w-7xl px-6 py-8 lg:px-10">
    <div class="overflow-hidden rounded-[32px] border border-white/80 bg-white/90 shadow-[0_24px_70px_rgba(15,23,42,0.08)]">
      <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-6 py-5">
        <div>
          <button class="text-sm font-medium text-slate-400 transition hover:text-slate-600" @click="restart()">
            ← 返回首页
          </button>
          <div class="mt-3 text-xs uppercase tracking-[0.15em] text-slate-400">Summary Scaffold</div>
          <h2 class="mt-2 text-3xl font-semibold text-slate-900">Session {{ sessionId }}</h2>
        </div>
        <div class="rounded-full bg-indigo-50 px-4 py-2 text-xs font-semibold text-indigo-600">
          查看详细报告
        </div>
      </div>

      <div class="grid gap-8 px-6 py-6 lg:grid-cols-[1.35fr_0.8fr]">
        <div class="space-y-5">
          <div v-if="store.summaryLoading" class="rounded-[28px] bg-slate-50 px-6 py-10 text-center text-slate-500">
            正在加载总结...
          </div>

          <div v-else-if="errorMessage" class="space-y-4">
            <div class="rounded-[28px] bg-rose-50 px-6 py-6 text-rose-700">
              {{ errorMessage }}
            </div>
            <button
              class="rounded-full bg-rose-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-rose-500"
              @click="retry()"
            >
              重新获取
            </button>
          </div>

          <template v-else-if="summary">
            <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div
                v-for="card in scoreCards"
                :key="card.label"
                class="rounded-[24px] bg-slate-50 px-5 py-5 shadow-inner"
              >
                <div class="text-xs text-slate-400">{{ card.label }}</div>
                <div class="mt-3 text-3xl font-semibold text-slate-900">{{ card.value }}</div>
                <div class="mt-1 text-xs text-slate-400">{{ card.unit }}</div>
              </div>
            </div>

            <div class="rounded-[28px] bg-gradient-to-r from-indigo-50 via-white to-sky-50 px-6 py-6">
              <div class="text-sm font-semibold text-slate-900">教练总结</div>
              <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
                {{ summary.ai_feedback }}
              </p>
            </div>

            <div class="rounded-[28px] bg-slate-50 px-6 py-5 text-sm text-slate-600">
              共 {{ summary.total_turns }} 轮，累计纠错 {{ summary.corrections_count }} 条
              <span v-if="summary.avg_response_latency_ms != null">
                ，平均响应 {{ Math.round(summary.avg_response_latency_ms) }} ms
              </span>
            </div>

            <div v-if="summary.focus_recommendations?.length" class="space-y-3">
              <div class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">建议重点</div>
              <div class="space-y-3">
                <div
                  v-for="(rec, index) in summary.focus_recommendations"
                  :key="`${index}-${rec}`"
                  class="rounded-[24px] border border-indigo-100 bg-indigo-50/60 px-5 py-4 text-sm leading-6 text-slate-700"
                >
                  {{ rec }}
                </div>
              </div>
            </div>
          </template>

          <div v-else class="rounded-[28px] bg-slate-50 px-6 py-10 text-center text-slate-400">
            暂无总结数据，请先完成至少一轮对话。
          </div>
        </div>

        <div class="rounded-[30px] bg-gradient-to-br from-indigo-50 via-white to-sky-50 p-6">
          <div class="space-y-4">
            <div class="inline-flex items-center rounded-full bg-white px-3 py-1 text-xs font-semibold text-indigo-500 shadow-sm">
              学习反馈
            </div>
            <div class="text-2xl font-semibold text-slate-900">完成练习后，AI 教练将为你提供更详细的反馈</div>
            <p class="text-sm leading-7 text-slate-500">
              当前总结页会优先展示评分卡片、基础统计和反馈文案，后续还能继续接 Dev B 的细化评分与纠错建议。
            </p>
          </div>

          <div class="mt-8 flex justify-center">
            <div class="flex h-48 w-48 items-center justify-center rounded-full bg-white/90 shadow-[0_20px_50px_rgba(84,108,255,0.12)]">
              <div class="flex h-28 w-28 items-center justify-center rounded-[28px] bg-gradient-to-br from-indigo-500 to-blue-500 text-4xl text-white shadow-lg">
                ✓
              </div>
            </div>
          </div>

          <button
            class="mt-8 w-full rounded-full bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
            @click="restart()"
          >
            再练一次
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { useAppStore } from '@/core/store'
import { ws } from '@/core/ws'
import { useCoach } from './useCoach'

const props = defineProps<{ sessionId: string }>()

const store = useAppStore()
const { fetchSummary } = useCoach()
const errorMessage = ref('')

const summary = computed(() => store.summary)

const scoreCards = computed(() => {
  if (!summary.value) return []
  return [
    { label: '综合评分', value: Math.round(summary.value.pron_avg), unit: '/100' },
    { label: '准确度', value: Math.round(summary.value.accuracy_avg), unit: '%' },
    { label: '流利度', value: Math.round(summary.value.fluency_avg), unit: '%' },
    { label: '完整度', value: Math.round(summary.value.completeness_avg), unit: '%' },
  ]
})

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
</script>
