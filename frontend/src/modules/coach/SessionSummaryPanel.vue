<template>
  <section class="min-h-screen bg-[linear-gradient(180deg,#f8fbff_0%,#eef4ff_46%,#f8fafc_100%)] px-5 py-8 lg:px-8 lg:py-10">
    <div class="mx-auto max-w-7xl">
      <header class="flex flex-wrap items-start justify-between gap-4 border-b border-[color:var(--line-soft)] pb-6">
        <div>
          <button class="text-sm font-medium text-slate-400 transition hover:text-slate-700" aria-label="返回首页" @click="restart()">
            返回首页
          </button>
          <div class="mt-4 text-xs uppercase tracking-[0.18em] text-slate-400">Report</div>
          <h2 class="mt-2 text-3xl font-semibold tracking-tight text-slate-950 lg:text-4xl">本次练习报告</h2>
          <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-500">看清这次表现，再决定下一轮怎么练。</p>
        </div>
        <div class="rounded-full bg-white px-4 py-2 text-xs font-semibold text-sky-700 shadow-sm">Session {{ sessionId }}</div>
      </header>

      <div v-if="store.summaryLoading" class="mt-8 rounded-[24px] bg-white px-6 py-10 text-center text-slate-500 shadow-sm">
        正在生成报告...
      </div>

      <div v-else-if="errorMessage" class="mt-8 space-y-4">
        <div class="rounded-[24px] bg-rose-50 px-6 py-6 text-rose-700">
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
        <div class="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(20rem,0.85fr)]">
          <main class="space-y-6">
            <section class="rounded-[28px] bg-white px-6 py-6 shadow-[0_18px_50px_rgba(15,23,42,0.07)]">
              <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_13rem]">
                <div>
                  <div class="text-sm font-semibold text-slate-900">总体评价</div>
                  <p class="mt-3 text-sm leading-8 text-slate-600">
                    {{ summary.ai_feedback }}
                  </p>
                  <div class="mt-5 flex flex-wrap gap-3 text-xs font-medium text-slate-500">
                    <span class="rounded-full bg-slate-100 px-3 py-1">共 {{ summary.total_turns }} 轮</span>
                    <span class="rounded-full bg-slate-100 px-3 py-1">纠错 {{ summary.corrections_count }} 条</span>
                    <span v-if="summary.avg_response_latency_ms != null" class="rounded-full bg-slate-100 px-3 py-1">
                      平均 {{ Math.round(summary.avg_response_latency_ms) }} ms
                    </span>
                  </div>
                </div>

                <div class="rounded-[22px] bg-slate-950 px-5 py-5 text-white">
                  <div class="text-xs uppercase tracking-[0.16em] text-sky-200">Overall</div>
                  <div class="mt-4 text-5xl font-semibold">{{ Math.round(summary.pron_avg) }}</div>
                  <div class="mt-2 text-sm text-sky-50/80">{{ overallLevel }}</div>
                </div>
              </div>
            </section>

            <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div v-for="card in scoreCards" :key="card.label" class="rounded-[22px] bg-white px-5 py-5 shadow-sm">
                <div class="text-xs uppercase tracking-[0.14em] text-slate-400">{{ card.label }}</div>
                <div class="mt-3 text-3xl font-semibold text-slate-950">{{ card.value }}</div>
                <div class="mt-1 text-xs text-slate-400">{{ card.unit }}</div>
                <div class="mt-4 h-2 rounded-full bg-slate-100">
                  <div class="h-2 rounded-full" :class="card.barClass" :style="{ width: `${card.percent}%` }" />
                </div>
              </div>
            </section>

            <section class="rounded-[28px] bg-white px-6 py-6 shadow-sm">
              <div class="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <div class="text-sm font-semibold text-slate-900">能力拆解</div>
                  <p class="mt-2 text-sm leading-7 text-slate-500">按维度看分数。</p>
                </div>
                <div class="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
                  {{ abilityRows.length }} 项
                </div>
              </div>

              <div class="mt-5 space-y-4">
                <div v-for="item in abilityRows" :key="item.label">
                  <div class="flex items-center justify-between gap-4 text-sm">
                    <div>
                      <span class="font-semibold text-slate-800">{{ item.label }}</span>
                      <span class="ml-2 text-xs text-slate-400">{{ item.hint }}</span>
                    </div>
                    <span class="font-semibold text-slate-900">{{ item.display }}</span>
                  </div>
                  <div class="mt-2 h-2 rounded-full bg-slate-100">
                    <div class="h-2 rounded-full" :class="item.barClass" :style="{ width: `${item.percent}%` }" />
                  </div>
                </div>
              </div>
            </section>

            <ShadowingPracticePanel :session-id="sessionId" :summary="summary" />

            <section class="grid gap-5 xl:grid-cols-2">
              <div class="rounded-[28px] bg-white px-6 py-6 shadow-sm">
                <div class="text-sm font-semibold text-slate-900">重点发音</div>
                <p class="mt-2 text-sm leading-7 text-slate-500">优先复练这些词。</p>
                <div v-if="weakWords.length" class="mt-5 flex flex-wrap gap-2">
                  <span
                    v-for="word in weakWords"
                    :key="word.word"
                    class="rounded-full px-3 py-1 text-xs font-semibold"
                    :class="word.score < 70 ? 'bg-rose-50 text-rose-600' : 'bg-amber-50 text-amber-700'"
                  >
                    {{ word.word }} · {{ word.score }} · {{ word.count }}次
                  </span>
                </div>
                <div v-else class="mt-5 rounded-[18px] bg-emerald-50 px-4 py-4 text-sm leading-7 text-emerald-700">
                  本次没有明显低分词。
                </div>
              </div>

              <div class="rounded-[28px] bg-white px-6 py-6 shadow-sm">
                <div class="text-sm font-semibold text-slate-900">问题分布</div>
                <p class="mt-2 text-sm leading-7 text-slate-500">看看问题主要在哪一类。</p>
                <div class="mt-5 space-y-3">
                  <div v-for="item in correctionBreakdown" :key="item.key">
                    <div class="flex items-center justify-between text-sm">
                      <span class="font-medium text-slate-700">{{ item.label }}</span>
                      <span class="text-slate-400">{{ item.count }} 条</span>
                    </div>
                    <div class="mt-2 h-2 rounded-full bg-slate-100">
                      <div class="h-2 rounded-full bg-sky-500" :style="{ width: `${item.percent}%` }" />
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section class="rounded-[28px] bg-white px-6 py-6 shadow-sm">
              <div class="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <div class="text-sm font-semibold text-slate-900">逐轮回看</div>
                  <p class="mt-2 text-sm leading-7 text-slate-500">保留原句、推荐表达和 AI 回复。</p>
                </div>
                <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-500">
                  {{ turnRows.length }} 轮
                </div>
              </div>

              <div class="mt-5 space-y-4">
                <article
                  v-for="row in turnRows"
                  :key="row.turn.turn_id"
                  class="rounded-[22px] border border-slate-100 bg-slate-50/80 px-5 py-5"
                >
                  <div class="flex flex-wrap items-center justify-between gap-3">
                    <div class="text-sm font-semibold text-slate-900">第 {{ row.index + 1 }} 轮</div>
                    <div class="flex flex-wrap gap-2 text-xs font-medium">
                      <span class="rounded-full bg-white px-3 py-1 text-slate-500">发音 {{ Math.round(row.turn.pron_score.overall) }}</span>
                      <span class="rounded-full bg-white px-3 py-1 text-slate-500">纠错 {{ row.turn.corrections.length }}</span>
                    </div>
                  </div>

                  <div class="mt-4 grid gap-4 lg:grid-cols-2">
                    <div>
                      <div class="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">原句</div>
                      <p class="mt-2 text-sm leading-7 text-slate-700">{{ row.turn.user_text || '暂无文本' }}</p>
                    </div>
                    <div>
                      <div class="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-600">推荐表达</div>
                      <p class="mt-2 text-sm leading-7 text-slate-700">{{ row.sampleAnswer }}</p>
                    </div>
                  </div>

                  <div v-if="row.turn.ai_reply" class="mt-4 rounded-[18px] bg-white px-4 py-3">
                    <div class="text-xs font-semibold uppercase tracking-[0.12em] text-sky-600">AI 回复</div>
                    <p class="mt-2 text-sm leading-7 text-slate-600">{{ row.turn.ai_reply }}</p>
                  </div>
                </article>
              </div>
            </section>
          </main>

          <aside class="space-y-5">
            <section class="rounded-[28px] bg-slate-950 px-6 py-6 text-white shadow-[0_24px_60px_rgba(15,23,42,0.2)]">
              <div class="text-xs uppercase tracking-[0.18em] text-sky-200/90">Next</div>
              <div class="mt-3 text-2xl font-semibold leading-snug">下一轮重点</div>
              <div class="mt-5 space-y-3">
                <div
                  v-for="(recommendation, index) in nextPracticeItems"
                  :key="`${index}-${recommendation}`"
                  class="rounded-[18px] bg-white/10 px-4 py-3 text-sm leading-6 text-sky-50/88"
                >
                  {{ recommendation }}
                </div>
              </div>
              <button
                class="mt-6 w-full rounded-full bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-sky-50"
                aria-label="返回首页并开始新一轮练习"
                @click="restart()"
              >
                再练一次
              </button>
            </section>

            <section class="rounded-[28px] bg-white px-6 py-6 shadow-sm">
              <div class="text-sm font-semibold text-slate-900">升级表达</div>
              <p class="mt-2 text-sm leading-7 text-slate-500">下次可直接复用。</p>
              <div class="mt-5 space-y-4">
                <div
                  v-for="example in upgradedExamples"
                  :key="example.id"
                  class="rounded-[18px] bg-slate-50 px-4 py-4"
                >
                  <div class="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">原句</div>
                  <p class="mt-2 text-sm leading-6 text-slate-600">{{ example.original }}</p>
                  <div class="mt-3 text-xs font-semibold uppercase tracking-[0.12em] text-emerald-600">更自然的说法</div>
                  <p class="mt-2 text-sm leading-6 text-slate-800">{{ example.improved }}</p>
                </div>
              </div>
            </section>

            <section class="rounded-[28px] bg-white px-6 py-6 shadow-sm">
              <div class="text-sm font-semibold text-slate-900">本次数据</div>
              <div class="mt-4 space-y-3 text-sm text-slate-500">
                <div class="flex justify-between gap-4">
                  <span>场景</span>
                  <span class="font-medium text-slate-800">{{ summary.scene_id }}</span>
                </div>
                <div class="flex justify-between gap-4">
                  <span>状态</span>
                  <span class="font-medium text-slate-800">{{ store.summaryReady ? '已生成' : '未生成' }}</span>
                </div>
                <div class="flex justify-between gap-4">
                  <span>会话 ID</span>
                  <span class="max-w-[12rem] truncate font-medium text-slate-800">{{ sessionId }}</span>
                </div>
              </div>
            </section>
          </aside>
        </div>
      </template>

      <div v-else class="mt-8 rounded-[24px] bg-white px-6 py-10 text-center text-slate-400 shadow-sm">
        暂无总结数据，请先完成一轮对话。
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { useAppStore } from '@/core/store'
import type { CorrectionIssue, TurnRecord, WordScore } from '@/core/types'
import { ws } from '@/core/ws'
import ShadowingPracticePanel from './ShadowingPracticePanel.vue'
import { useCoach } from './useCoach'

const props = defineProps<{ sessionId: string }>()

const store = useAppStore()
const { fetchSummary } = useCoach()
const errorMessage = ref('')

const summary = computed(() => store.summary)

const overallLevel = computed(() => scoreLevel(summary.value?.pron_avg ?? 0))

const scoreCards = computed(() => {
  if (!summary.value) return []
  return [
    scoreCard('综合评分', summary.value.pron_avg, '/100', 'bg-sky-500'),
    scoreCard('准确度', summary.value.accuracy_avg, '%', 'bg-emerald-500'),
    scoreCard('流利度', summary.value.fluency_avg, '%', 'bg-indigo-500'),
    scoreCard('完整度', summary.value.completeness_avg, '%', 'bg-amber-500'),
  ]
})

const abilityRows = computed(() => {
  if (!summary.value) return []
  return [
    abilityRow('发音准确度', summary.value.accuracy_avg, '单词是否清楚', 'bg-emerald-500'),
    abilityRow('口语流利度', summary.value.fluency_avg, '停顿和连贯性', 'bg-indigo-500'),
    abilityRow('表达完整度', summary.value.completeness_avg, '是否说完整', 'bg-amber-500'),
    abilityRow('语法正确性', summary.value.grammar_score, '句型和时态', 'bg-rose-500'),
    abilityRow('表达自然度', summary.value.expression_score, '是否自然得体', 'bg-sky-500'),
    abilityRow('词汇选择', summary.value.vocabulary_score, '词汇和搭配', 'bg-violet-500'),
  ]
})

const allCorrections = computed(() => {
  const rows: Array<CorrectionIssue & { turnIndex: number }> = []
  summary.value?.turns.forEach((turn, turnIndex) => {
    turn.corrections.forEach((issue) => rows.push({ ...issue, turnIndex }))
  })
  return rows
})

const correctionBreakdown = computed(() => {
  const total = Math.max(allCorrections.value.length, 1)
  return ([
    ['grammar', '语法'],
    ['expression', '表达'],
    ['vocabulary', '词汇'],
  ] as const).map(([key, label]) => {
    const count = allCorrections.value.filter((issue) => issue.category === key).length
    return {
      key,
      label,
      count,
      percent: Math.max(8, Math.round((count / total) * 100)),
    }
  })
})

const weakWords = computed(() => {
  const grouped = new Map<string, { word: string; total: number; count: number }>()
  summary.value?.turns.forEach((turn) => {
    turn.pron_score.words
      .filter((word) => isReportableWeakWord(word))
      .forEach((word) => {
        const key = word.word.toLowerCase()
        const existing = grouped.get(key) ?? { word: word.word, total: 0, count: 0 }
        existing.total += word.accuracy_score
        existing.count += 1
        grouped.set(key, existing)
      })
  })

  return Array.from(grouped.values())
    .map((item) => ({
      word: item.word,
      score: Math.round(item.total / item.count),
      count: item.count,
    }))
    .sort((a, b) => a.score - b.score || b.count - a.count)
    .slice(0, 8)
})

const turnRows = computed(() => {
  return (summary.value?.turns ?? []).map((turn, index) => ({
    turn,
    index,
    sampleAnswer: getSampleAnswer(turn),
  }))
})

const upgradedExamples = computed(() => {
  const examples = turnRows.value
    .filter((row) => row.turn.user_text && row.sampleAnswer && row.sampleAnswer !== row.turn.user_text)
    .map((row) => ({
      id: row.turn.turn_id,
      original: row.turn.user_text,
      improved: row.sampleAnswer,
    }))
    .slice(0, 4)

  if (examples.length) return examples

  return turnRows.value.slice(0, 2).map((row) => ({
    id: row.turn.turn_id,
    original: row.turn.user_text || '暂无用户文本',
    improved: row.sampleAnswer,
  }))
})

const nextPracticeItems = computed(() => {
  const base = summary.value?.focus_recommendations ?? []
  if (base.length) return base
  if (weakWords.value.length) {
    return [`优先复练 ${weakWords.value.slice(0, 3).map((item) => item.word).join('、')}。`]
  }
  return ['下一轮试着用更完整的句子回答。']
})

function scoreCard(label: string, value: number, unit: string, barClass: string) {
  const percent = scorePercent(value)
  return {
    label,
    value: Math.round(value),
    unit,
    percent,
    barClass,
  }
}

function abilityRow(label: string, value: number | undefined, hint: string, barClass: string) {
  const numeric = value ?? 0
  return {
    label,
    hint,
    display: value == null ? '暂无' : `${Math.round(numeric)}%`,
    percent: value == null ? 0 : scorePercent(numeric),
    barClass,
  }
}

function scorePercent(value: number) {
  return Math.max(0, Math.min(100, Math.round(value)))
}

function scoreLevel(score: number) {
  if (score >= 85) return '表现优秀'
  if (score >= 70) return '整体稳定'
  if (score >= 60) return '基础可用'
  return '建议先做短句练习'
}

function isReportableWeakWord(word: WordScore) {
  const normalized = word.word.trim().toLowerCase()
  if (!normalized || ['sil', 'sp', 'silence'].includes(normalized)) return false
  return word.error_type !== 'None' || word.accuracy_score < 80
}

function getSampleAnswer(turn: TurnRecord) {
  return turn.sample_answer || buildSampleAnswer(turn)
}

function buildSampleAnswer(turn: TurnRecord) {
  let sample = turn.user_text || '本轮暂无推荐表达'
  turn.corrections.forEach((issue) => {
    if (issue.original && issue.corrected) {
      sample = sample.replace(issue.original, issue.corrected)
    }
  })
  return sample
}

async function loadSummary() {
  errorMessage.value = ''
  store.resetSummaryState()
  const result = await fetchSummary(props.sessionId)
  if (!result) {
    errorMessage.value = '获取总结失败，请确认后端已启动。'
  }
}

async function retry() {
  await loadSummary()
}

function restart() {
  ws.disconnect()
  store.clearConversationState()
}

onMounted(() => {
  void loadSummary()
})
</script>
