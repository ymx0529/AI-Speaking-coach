<template>
  <section class="mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">
    <div class="overflow-hidden rounded-[34px] border border-[color:var(--line-soft)] bg-[var(--surface-1)] shadow-[var(--shadow-strong)]">
      <div class="border-b border-[color:var(--line-soft)] px-6 py-5">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <button class="text-sm font-medium text-slate-400 transition hover:text-slate-700" aria-label="返回首页" @click="restart()">
              ← 返回首页
            </button>
            <div class="mt-3 text-xs uppercase tracking-[0.18em] text-slate-400">Session Summary</div>
            <h2 class="mt-2 text-3xl font-semibold tracking-tight text-slate-950">练习完成，来看这轮总结</h2>
            <p class="mt-2 text-sm leading-7 text-slate-500">
              系统会汇总你的发音分数、对话轮次和教练反馈，帮助你继续下一轮针对性练习。
            </p>
          </div>
          <div class="rounded-full bg-sky-50 px-4 py-2 text-xs font-semibold text-sky-700">Session {{ sessionId }}</div>
        </div>
      </div>

      <div class="grid gap-6 px-6 py-6 lg:grid-cols-[1.35fr_0.85fr]">
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
              aria-label="重新获取总结"
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
                class="rounded-[24px] bg-[linear-gradient(180deg,#f8fbff_0%,#f8fafc_100%)] px-5 py-5 shadow-inner"
              >
                <div class="text-xs uppercase tracking-[0.14em] text-slate-400">{{ card.label }}</div>
                <div class="mt-3 text-3xl font-semibold text-slate-950">{{ card.value }}</div>
                <div class="mt-1 text-xs text-slate-400">{{ card.unit }}</div>
              </div>
            </div>

            <div class="rounded-[28px] bg-[linear-gradient(135deg,#eef6ff_0%,#ffffff_58%,#f8fafc_100%)] px-6 py-6">
              <div class="text-sm font-semibold text-slate-900">教练总结</div>
              <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
                {{ summary.ai_feedback }}
              </p>
            </div>

            <div class="rounded-[28px] bg-slate-50 px-6 py-5 text-sm leading-7 text-slate-600">
              共 {{ summary.total_turns }} 轮对话，累计纠错 {{ summary.corrections_count }} 条。
              <span v-if="summary.avg_response_latency_ms != null">
                平均响应 {{ Math.round(summary.avg_response_latency_ms) }} ms。
              </span>
            </div>

            <div v-if="summary.focus_recommendations?.length" class="space-y-3">
              <div class="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">下一轮建议重点</div>
              <div class="space-y-3">
                <div
                  v-for="(recommendation, index) in summary.focus_recommendations"
                  :key="`${index}-${recommendation}`"
                  class="rounded-[24px] border border-sky-100 bg-sky-50/80 px-5 py-4 text-sm leading-6 text-slate-700"
                >
                  {{ recommendation }}
                </div>
              </div>
            </div>
          </template>

          <div v-else class="rounded-[28px] bg-slate-50 px-6 py-10 text-center text-slate-400">
            暂无总结数据，请先完成至少一轮对话。
          </div>
        </div>

        <div class="rounded-[30px] bg-[linear-gradient(160deg,#0f172a_0%,#2563eb_55%,#38bdf8_100%)] p-6 text-white shadow-[0_24px_60px_rgba(15,23,42,0.2)]">
          <div class="text-xs uppercase tracking-[0.18em] text-sky-200/90">Next Practice</div>
          <div class="mt-3 text-2xl font-semibold leading-snug">带着本轮反馈继续练，提升会更明显</div>
          <p class="mt-4 text-sm leading-7 text-sky-50/82">
            现在这页会优先显示综合得分、练习统计和 AI 教练反馈。你可以回到首页重新选场景或难度，继续下一轮更有针对性的训练。
          </p>

          <div class="mt-7 rounded-[24px] bg-white/10 p-4">
            <div class="text-sm font-semibold">本轮数据概览</div>
            <div class="mt-3 space-y-2 text-sm text-sky-50/84">
              <div>会话 ID：{{ sessionId }}</div>
              <div>总结状态：{{ store.summaryReady ? '已生成' : '未生成' }}</div>
              <div>当前可以继续回到首页发起新会话。</div>
            </div>
          </div>

          <button
            class="mt-8 w-full rounded-full bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-sky-50"
            aria-label="返回首页并开始新一轮练习"
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
