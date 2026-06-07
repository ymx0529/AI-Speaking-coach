<template>
  <div>
    <div class="flex items-start justify-between gap-4">
      <div>
        <div class="text-sm font-semibold text-[var(--ink-2)]">发音反馈</div>
        <div class="mt-1 text-xs uppercase tracking-[0.16em] text-[var(--ink-4)]">Pronunciation Score</div>
      </div>
      <div
        class="relative flex h-24 w-24 items-center justify-center rounded-full bg-[conic-gradient(from_180deg_at_50%_50%,#86efac_0%,#34d399_45%,#d1fae5_100%)] p-[10px]"
      >
        <div class="flex h-full w-full items-center justify-center rounded-full bg-white text-2xl font-semibold text-emerald-600">
          {{ displayOverall }}
        </div>
      </div>
    </div>

    <div class="mt-5 grid gap-3 sm:grid-cols-3">
      <div v-for="item in scoreItems" :key="item.label" class="rounded-[12px] bg-[var(--surface-2)] px-4 py-4">
        <div class="text-xs text-[var(--ink-4)]">{{ item.label }}</div>
        <div class="mt-2 text-lg font-semibold text-[var(--ink-1)]">{{ item.value }}</div>
      </div>
    </div>

    <div class="mt-5 rounded-[14px] bg-[var(--surface-2)] px-4 py-4">
      <div class="text-xs font-medium uppercase tracking-[0.14em] text-[var(--ink-4)]">重点单词</div>
      <div v-if="score?.words?.length" class="mt-3 flex flex-wrap gap-2">
        <span
          v-for="word in score.words.slice(0, 6)"
          :key="`${word.word}-${word.accuracy_score}`"
          class="rounded-full px-3 py-1 text-xs font-medium"
          :class="word.accuracy_score < 70 ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'"
        >
          {{ word.word }} · {{ Math.round(word.accuracy_score) }}
        </span>
      </div>
      <div v-else class="mt-3 text-sm leading-6 text-[var(--ink-3)]">
        暂无发音评分，完成一轮语音输入后会在这里展示重点单词和分数。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { PronScore } from '@/core/types'

const props = defineProps<{
  score: PronScore | null
}>()

const displayOverall = computed(() => (props.score ? Math.round(props.score.overall) : '--'))

const scoreItems = computed(() => [
  { label: '准确度', value: props.score ? `${Math.round(props.score.accuracy)}%` : '--' },
  { label: '流利度', value: props.score ? `${Math.round(props.score.fluency)}%` : '--' },
  { label: '完整度', value: props.score ? `${Math.round(props.score.completeness)}%` : '--' },
])
</script>
