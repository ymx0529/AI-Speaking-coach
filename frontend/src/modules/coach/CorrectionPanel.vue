<template>
  <div>
    <div>
      <div class="text-lg font-semibold text-[var(--ink-2)]">Coach</div>
      <div class="mt-1 text-sm text-[var(--ink-3)]">纠错、优化和本轮建议</div>
    </div>

    <div class="mt-4 space-y-4">
      <div v-if="isAnalysingNextTurn" class="rounded-[16px] bg-indigo-50 px-4 py-4 text-sm text-indigo-700">
        新一轮分析中，先保留上一轮结果。
      </div>

      <div v-if="isAnalysing" class="rounded-[16px] bg-indigo-50 px-4 py-4 text-sm text-indigo-700">
        正在分析本轮表达。
      </div>

      <div v-else-if="!hasResult" class="rounded-[16px] bg-[linear-gradient(135deg,#eff6ff_0%,#ffffff_55%,#f8fafc_100%)] p-4">
        <div class="flex items-center justify-between gap-4">
          <div>
            <div class="text-sm font-semibold text-[var(--ink-1)]">还没有结果</div>
            <p class="mt-2 text-sm leading-6 text-[var(--ink-3)]">
              完成一轮对话后，这里会显示纠错和示例回答。
            </p>
          </div>
          <div class="flex h-14 w-14 items-center justify-center rounded-[16px] bg-white text-2xl">📋</div>
        </div>
      </div>

      <template v-else>
        <section class="rounded-[14px] bg-[var(--surface-2)] px-4 py-4">
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
          <p v-else class="mt-3 text-sm leading-6 text-[var(--ink-3)]">
            本轮发音整体正常。
          </p>
        </section>

        <section
          v-for="group in issueGroups"
          :key="group.category"
          class="rounded-[14px] bg-[var(--surface-2)] px-4 py-4"
        >
          <div class="flex items-center justify-between gap-3">
            <div>
              <div class="text-xs font-semibold uppercase tracking-[0.12em]" :class="group.titleClass">
                {{ group.title }}
              </div>
              <div class="mt-1 text-xs text-[var(--ink-4)]">{{ group.subtitle }}</div>
            </div>
            <div class="rounded-full bg-white px-3 py-1 text-xs font-semibold text-[var(--ink-3)]">
              {{ group.issues.length }}
            </div>
          </div>

          <div v-if="group.issues.length" class="mt-3 space-y-3">
            <div
              v-for="(issue, index) in group.issues"
              :key="`${group.category}-${index}`"
              class="rounded-[14px] border border-white bg-white p-3 text-sm text-[var(--ink-3)] shadow-sm"
            >
              <div class="font-medium text-[var(--ink-1)]">{{ issue.original }} → {{ issue.corrected }}</div>
              <div class="mt-2 text-xs leading-5 text-[var(--ink-3)]">{{ issue.explanation }}</div>
              <div class="mt-3 inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold" :class="severityClass(issue.severity)">
                {{ severityLabel(issue.severity) }}
              </div>
            </div>
          </div>

          <p v-else class="mt-3 text-sm leading-6 text-[var(--ink-3)]">
            {{ group.emptyText }}
          </p>
        </section>

        <section class="rounded-[14px] bg-[var(--surface-2)] px-4 py-4">
          <div class="text-xs font-semibold uppercase tracking-[0.12em] text-indigo-600">Sample Answer</div>
          <p class="mt-3 text-sm leading-7 text-[var(--ink-2)]">
            {{ sampleAnswer || '本轮表达整体清晰。' }}
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
import { useCoach } from './useCoach'

const store = useAppStore()
useCoach()

const currentTurnStatus = computed(() => {
  if (!store.currentTurnId) return null
  return store.coachAnalysisStatus[store.currentTurnId] ?? null
})

const analyzedTurnId = computed(() => {
  if (store.currentTurnId && currentTurnStatus.value === 'analyzed') return store.currentTurnId
  return store.latestAnalyzedTurnId
})

const turnId = computed(() => analyzedTurnId.value ?? store.currentTurnId)
const isAnalysing = computed(() => currentTurnStatus.value === 'pending' && !analyzedTurnId.value)
const isAnalysingNextTurn = computed(() => currentTurnStatus.value === 'pending' && !!analyzedTurnId.value && analyzedTurnId.value !== store.currentTurnId)
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
  { category: 'grammar', title: 'Grammar', subtitle: '语法和句型', titleClass: 'text-rose-600', emptyText: '本轮没有明显语法问题。', issues: filterIssues('grammar') },
  { category: 'expression', title: 'Expression', subtitle: '自然度和表达方式', titleClass: 'text-amber-600', emptyText: '本轮表达基本自然。', issues: filterIssues('expression') },
  { category: 'vocabulary', title: 'Vocabulary', subtitle: '词汇和搭配', titleClass: 'text-sky-600', emptyText: '本轮没有明显用词问题。', issues: filterIssues('vocabulary') },
])

function filterIssues(category: CorrectionIssue['category']) {
  return corrections.value.filter((issue) => issue.category === category).sort((a, b) => severityRank(b.severity) - severityRank(a.severity))
}

function severityRank(severity?: string): number {
  return severity === 'high' ? 2 : severity === 'medium' ? 1 : 0
}

function severityLabel(severity?: string): string {
  return severity === 'high' ? '重点' : severity === 'medium' ? '建议' : '提示'
}

function severityClass(severity?: string): string {
  if (severity === 'high') return 'bg-rose-100 text-rose-700'
  if (severity === 'medium') return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-500'
}
</script>
