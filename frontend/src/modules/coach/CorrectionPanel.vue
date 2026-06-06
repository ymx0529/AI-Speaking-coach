<template>
  <div class="rounded-2xl border border-amber-200 bg-amber-50 p-4">
    <div class="text-sm font-medium text-amber-800">Correction Panel</div>

    <!-- Loading -->
    <div v-if="isAnalysing" class="mt-3 flex items-center gap-2 text-sm text-amber-600">
      <span class="animate-spin">⟳</span>
      <span>分析中...</span>
    </div>

    <!-- Corrections -->
    <div v-else-if="sortedCorrections.length" class="mt-3 space-y-3">
      <div
        v-for="(issue, index) in sortedCorrections"
        :key="index"
        class="rounded-xl bg-white/70 p-3 text-sm text-amber-900"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="font-medium">{{ issue.original }} → {{ issue.corrected }}</div>
          <span :class="severityClass(issue.severity)" class="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium">
            {{ severityLabel(issue.severity) }}
          </span>
        </div>
        <div class="mt-1 text-xs text-amber-700">{{ issue.explanation }}</div>
        <div class="mt-1 text-xs text-slate-400 uppercase tracking-wide">{{ issue.category }}</div>
      </div>
    </div>

    <!-- Empty -->
    <p v-else-if="hasResult" class="mt-2 text-sm text-amber-700">
      本轮表达很好，没有发现明显问题。
    </p>
    <p v-else class="mt-2 text-sm text-amber-700">
      先跑一轮对话，纠错结果会显示在这里。
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { useAppStore } from '@/core/store'
import type { CorrectionIssue } from '@/core/types'

const store = useAppStore()

const turnId = computed(() => store.currentTurnId)

const isAnalysing = computed(() =>
  turnId.value ? store.coachAnalysisStatus[turnId.value] === 'pending' : false,
)

const hasResult = computed(() =>
  turnId.value ? store.coachAnalysisStatus[turnId.value] === 'analyzed' : false,
)

const sortedCorrections = computed<CorrectionIssue[]>(() => {
  if (!turnId.value) return []
  const issues = store.correctionsByTurn[turnId.value] ?? []
  return [...issues].sort((a, b) => severityRank(b.severity) - severityRank(a.severity))
})

function severityRank(s?: string): number {
  return s === 'high' ? 2 : s === 'medium' ? 1 : 0
}

function severityLabel(s?: string): string {
  return s === 'high' ? '重要' : s === 'medium' ? '建议' : '轻微'
}

function severityClass(s?: string): string {
  if (s === 'high') return 'bg-rose-100 text-rose-700'
  if (s === 'medium') return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-500'
}
</script>
