<template>
  <div class="overflow-hidden rounded-[28px] border border-white/80 bg-white shadow-[0_18px_50px_rgba(15,23,42,0.05)]">
    <div class="border-b border-slate-100 px-5 py-4">
      <div class="text-sm font-semibold text-slate-900">Coach Panel</div>
      <div class="mt-1 text-xs text-slate-400">实时纠错与表达提示</div>
    </div>

    <div class="p-5">
      <div v-if="store.currentCorrections.length" class="space-y-3">
      <div
        v-for="(issue, index) in sortedCorrections"
        :key="index"
        class="rounded-2xl border border-amber-100 bg-amber-50/70 p-4 text-sm text-slate-700"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <div class="font-medium text-slate-900">{{ issue.original }} → {{ issue.corrected }}</div>
            <div class="mt-2 text-xs leading-6 text-slate-500">{{ issue.explanation }}</div>
          </div>
          <div class="rounded-full bg-white px-3 py-1 text-[11px] font-semibold text-amber-600">
            {{ issue.category }}
          </div>
        </div>
      </div>
      </div>
      <div v-else class="rounded-[24px] bg-gradient-to-br from-amber-50 via-white to-slate-50 px-5 py-6">
        <div class="flex items-center justify-between gap-4">
          <div class="space-y-2">
            <div class="text-sm font-semibold text-slate-900">当前还没有纠错结果</div>
            <p class="max-w-sm text-sm leading-6 text-slate-500">
              先完成一轮对话，系统会在右侧展示语法纠错、表达优化和重点反馈。
            </p>
          </div>
          <div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-2xl shadow-sm">
            📋
          </div>
        </div>
      </div>

      <div class="mt-4 grid gap-3 sm:grid-cols-2">
        <div class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
          <div class="text-xs text-slate-400">发音纠正</div>
          <div class="mt-2 text-sm font-medium text-slate-700">辅助定位发音问题</div>
        </div>
        <div class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
          <div class="text-xs text-slate-400">语法纠错</div>
          <div class="mt-2 text-sm font-medium text-slate-700">指出表达与用词问题</div>
        </div>
      </div>
    </div>
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
