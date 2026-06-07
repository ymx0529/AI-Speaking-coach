<template>
  <div class="overflow-hidden rounded-[28px] border border-white/80 bg-white shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
    <div class="border-b border-slate-100 px-5 py-4">
      <div class="text-sm font-semibold text-slate-900">Coach Panel</div>
      <div class="mt-1 text-xs text-slate-400">每轮发音、语法、表达与用词反馈</div>
    </div>

    <div class="space-y-4 p-5">
      <div v-if="isAnalysingNextTurn" class="rounded-[24px] bg-indigo-50 px-5 py-4 text-sm text-indigo-700">
        新一轮正在分析中，下面先保留上一轮纠错结果。
      </div>

      <div v-if="isAnalysing" class="rounded-[24px] bg-indigo-50 px-5 py-4 text-sm text-indigo-700">
        正在分析本轮发音和表达...
      </div>

      <div v-else-if="!hasResult" class="rounded-[24px] bg-gradient-to-br from-amber-50 via-white to-slate-50 px-5 py-6">
        <div class="flex items-center justify-between gap-4">
          <div class="space-y-2">
            <div class="text-sm font-semibold text-slate-900">当前还没有纠错结果</div>
            <p class="max-w-sm text-sm leading-6 text-slate-500">
              完成一轮对话后，这里会展示发音、语法、表达、用词和示例回答。
            </p>
          </div>
          <div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-2xl shadow-sm">
            📋
          </div>
        </div>
      </div>

      <template v-else>
        <section class="rounded-2xl border border-emerald-100 bg-emerald-50/70 p-4">
          <div class="text-xs font-semibold uppercase tracking-[0.12em] text-emerald-600">Pronunciation</div>
          <div v-if="pronunciationIssues.length" class="mt-3 flex flex-wrap gap-2">
            <span
              v-for="word in pronunciationIssues"
              :key="word.word"
              class="rounded-full bg-white px-3 py-1 text-xs font-semibold text-emerald-700 shadow-sm"
            >
              {{ word.word }} · {{ Math.round(word.accuracy_score) }}
            </span>
          </div>
          <p v-else class="mt-3 text-sm leading-6 text-slate-600">
            本轮暂无明显发音问题。
          </p>
        </section>

        <section
          v-for="group in issueGroups"
          :key="group.category"
          class="rounded-2xl border border-slate-100 bg-slate-50/80 p-4"
        >
          <div class="flex items-center justify-between gap-3">
            <div>
              <div class="text-xs font-semibold uppercase tracking-[0.12em]" :class="group.titleClass">
                {{ group.title }}
              </div>
              <div class="mt-1 text-xs text-slate-400">{{ group.subtitle }}</div>
            </div>
            <div class="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-500">
              {{ group.issues.length }}
            </div>
          </div>

          <div v-if="group.issues.length" class="mt-3 space-y-3">
            <div
              v-for="(issue, index) in group.issues"
              :key="`${group.category}-${index}`"
              class="rounded-2xl border border-white bg-white p-3 text-sm text-slate-700 shadow-sm"
            >
              <div class="font-medium text-slate-900">{{ issue.original }} → {{ issue.corrected }}</div>
              <div class="mt-2 text-xs leading-5 text-slate-500">{{ issue.explanation }}</div>
              <div class="mt-3 inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold" :class="severityClass(issue.severity)">
                {{ severityLabel(issue.severity) }}
              </div>
            </div>
          </div>

          <p v-else class="mt-3 text-sm leading-6 text-slate-500">
            {{ group.emptyText }}
          </p>
        </section>

        <section class="rounded-2xl border border-indigo-100 bg-indigo-50/70 p-4">
          <div class="text-xs font-semibold uppercase tracking-[0.12em] text-indigo-600">Sample Answer</div>
          <p class="mt-3 text-sm leading-7 text-slate-800">
            {{ sampleAnswer || '本轮表达整体清晰，可以继续保持。' }}
          </p>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { useAppStore } from '@/core/store'
import type { CorrectionIssue } from '@/core/types'

const store = useAppStore()

const currentTurnStatus = computed(() => {
  if (!store.currentTurnId) return null
  return store.coachAnalysisStatus[store.currentTurnId] ?? null
})

const analyzedTurnId = computed(() => {
  if (store.currentTurnId && currentTurnStatus.value === 'analyzed') {
    return store.currentTurnId
  }
  return store.latestAnalyzedTurnId
})

const turnId = computed(() => analyzedTurnId.value ?? store.currentTurnId)
const isAnalysing = computed(() => currentTurnStatus.value === 'pending' && !analyzedTurnId.value)
const isAnalysingNextTurn = computed(
  () => currentTurnStatus.value === 'pending' && !!analyzedTurnId.value && analyzedTurnId.value !== store.currentTurnId,
)
const hasResult = computed(() => (turnId.value ? store.coachAnalysisStatus[turnId.value] === 'analyzed' : false))

const corrections = computed<CorrectionIssue[]>(() => {
  if (!turnId.value) return []
  return store.correctionsByTurn[turnId.value] ?? []
})

const sampleAnswer = computed(() => {
  if (!turnId.value) return ''
  return store.sampleAnswerByTurn[turnId.value] ?? store.currentSampleAnswer
})

const pronunciationIssues = computed(() => {
  if (!turnId.value) return []
  const score = store.pronunciationByTurn[turnId.value] ?? store.currentPronScore
  return (score?.words ?? []).filter((word) => word.error_type !== 'None' || word.accuracy_score < 80)
})

const issueGroups = computed(() => [
  {
    category: 'grammar',
    title: 'Grammar',
    subtitle: '语法结构与句子正确性',
    titleClass: 'text-rose-600',
    emptyText: '本轮暂无明显语法问题。',
    issues: filterIssues('grammar'),
  },
  {
    category: 'expression',
    title: 'Expression',
    subtitle: '自然度、礼貌度和表达方式',
    titleClass: 'text-amber-600',
    emptyText: '本轮表达方式基本自然。',
    issues: filterIssues('expression'),
  },
  {
    category: 'vocabulary',
    title: 'Vocabulary',
    subtitle: '词汇选择与搭配',
    titleClass: 'text-sky-600',
    emptyText: '本轮暂无明显用词问题。',
    issues: filterIssues('vocabulary'),
  },
])

function filterIssues(category: CorrectionIssue['category']) {
  return corrections.value
    .filter((issue) => issue.category === category)
    .sort((a, b) => severityRank(b.severity) - severityRank(a.severity))
}

function severityRank(s?: string): number {
  return s === 'high' ? 2 : s === 'medium' ? 1 : 0
}

function severityLabel(s?: string): string {
  return s === 'high' ? '重点修改' : s === 'medium' ? '建议优化' : '轻微提示'
}

function severityClass(s?: string): string {
  if (s === 'high') return 'bg-rose-100 text-rose-700'
  if (s === 'medium') return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-500'
}
</script>
