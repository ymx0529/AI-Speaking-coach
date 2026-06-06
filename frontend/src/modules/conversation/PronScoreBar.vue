<template>
  <div class="overflow-hidden rounded-[28px] border border-white/80 bg-white p-5 shadow-[0_20px_60px_rgba(15,23,42,0.06)]">
    <div class="flex items-start justify-between gap-4">
      <div>
        <div class="text-sm font-semibold text-slate-900">发音反馈</div>
        <div class="mt-1 text-xs text-slate-400">Pronunciation Score</div>
      </div>
      <div class="flex h-20 w-20 items-center justify-center rounded-full border-[10px] border-emerald-100 bg-emerald-50 text-2xl font-bold text-emerald-600">
        {{ displayOverall }}
      </div>
    </div>

    <div class="mt-5 grid gap-3 sm:grid-cols-3">
      <div
        v-for="item in scoreItems"
        :key="item.label"
        class="rounded-2xl bg-slate-50 px-4 py-3"
      >
        <div class="text-xs text-slate-400">{{ item.label }}</div>
        <div class="mt-1 text-base font-semibold text-slate-900">{{ item.value }}</div>
      </div>
    </div>

    <div class="mt-5 rounded-2xl bg-slate-50 px-4 py-4">
      <div class="text-xs font-medium text-slate-500">重点单词</div>
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
      <div v-else class="mt-3 text-sm text-slate-400">
        暂无发音评分，先完成一轮语音输入。
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

