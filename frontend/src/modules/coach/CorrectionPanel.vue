<template>
  <div>
    <div>
      <div class="text-lg font-semibold text-[var(--ink-2)]">Coach Panel</div>
      <div class="mt-1 text-sm text-[var(--ink-3)]">实时纠错、表达优化和当前轮次陪练建议</div>
    </div>

    <div class="mt-4 space-y-4">
      <div class="rounded-[16px] bg-[linear-gradient(135deg,#eff6ff_0%,#ffffff_55%,#f8fafc_100%)] p-4">
        <div class="flex items-center justify-between gap-4">
          <div>
            <div class="text-sm font-semibold text-[var(--ink-1)]">
              {{ hasResult ? '本轮教练反馈已生成' : isAnalysing ? '正在分析这一轮表达' : '完成一轮对话后这里会出现反馈' }}
            </div>
            <p class="mt-2 text-sm leading-6 text-[var(--ink-3)]">
              {{ helperText }}
            </p>
          </div>
          <div class="flex h-14 w-14 items-center justify-center rounded-[16px] bg-white text-2xl">
            {{ hasResult ? '📝' : isAnalysing ? '⏳' : '📋' }}
          </div>
        </div>
      </div>

      <div class="grid gap-3 sm:grid-cols-2">
        <div class="rounded-[14px] bg-[var(--surface-2)] px-4 py-4">
          <div class="text-xs uppercase tracking-[0.14em] text-[var(--ink-4)]">发音纠正</div>
          <div class="mt-2 text-sm font-medium leading-6 text-[var(--ink-2)]">辅助定位发音问题，并提示需要反复练习的词。</div>
        </div>
        <div class="rounded-[14px] bg-[var(--surface-2)] px-4 py-4">
          <div class="text-xs uppercase tracking-[0.14em] text-[var(--ink-4)]">语法表达</div>
          <div class="mt-2 text-sm font-medium leading-6 text-[var(--ink-2)]">指出语法、措辞和表达方式中的可优化点。</div>
        </div>
      </div>

      <div v-if="sortedCorrections.length" class="space-y-3">
        <div class="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--ink-4)]">本轮纠错</div>
        <div
          v-for="(issue, index) in sortedCorrections"
          :key="index"
          class="rounded-[14px] border border-amber-100 bg-amber-50/80 p-4"
        >
          <div class="flex items-start justify-between gap-4">
            <div>
              <div class="text-sm font-semibold text-[var(--ink-1)]">{{ issue.original }} → {{ issue.corrected }}</div>
              <div class="mt-2 text-sm leading-6 text-[var(--ink-3)]">{{ issue.explanation }}</div>
            </div>
            <div class="flex flex-col items-end gap-2">
              <div class="rounded-full bg-white px-3 py-1 text-[11px] font-semibold text-amber-700">
                {{ issue.category }}
              </div>
              <div class="rounded-full px-3 py-1 text-[11px] font-semibold" :class="severityClass(issue.severity)">
                {{ severityLabel(issue.severity) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="rounded-[14px] border border-dashed border-[color:var(--line-soft)] px-4 py-5 text-sm leading-6 text-[var(--ink-3)]">
        暂时还没有纠错结果。先完成一轮录音或模拟输入，系统会在这里展示当前轮次的重点修改建议。
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

const isAnalysing = computed(() => (turnId.value ? store.coachAnalysisStatus[turnId.value] === 'pending' : false))
const hasResult = computed(() => (turnId.value ? store.coachAnalysisStatus[turnId.value] === 'analyzed' : false))

const helperText = computed(() => {
  if (hasResult.value) {
    return '你可以一边看纠错结果，一边继续下一轮练习，让表达逐步自然起来。'
  }
  if (isAnalysing.value) {
    return '系统正在根据本轮语音和文本结果生成纠错建议，请稍等片刻。'
  }
  return '完成一轮真实对话后，这里会显示语法纠错、表达优化和高频问题提示。'
})

const sortedCorrections = computed<CorrectionIssue[]>(() => {
  if (!turnId.value) return []
  const issues = store.correctionsByTurn[turnId.value] ?? []
  return [...issues].sort((a, b) => severityRank(b.severity) - severityRank(a.severity))
})

function severityRank(severity?: string): number {
  return severity === 'high' ? 2 : severity === 'medium' ? 1 : 0
}

function severityLabel(severity?: string): string {
  return severity === 'high' ? '重点' : severity === 'medium' ? '建议' : '轻微'
}

function severityClass(severity?: string): string {
  if (severity === 'high') return 'bg-rose-100 text-rose-700'
  if (severity === 'medium') return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-500'
}
</script>
