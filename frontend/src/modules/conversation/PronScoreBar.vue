<template>
  <div class="rounded-2xl bg-slate-900 p-4 text-white">
    <div class="text-sm text-slate-300">Pronunciation Score</div>
    <div class="mt-2 grid grid-cols-2 gap-3 text-sm">
      <div>Overall: {{ score?.overall ?? '--' }}</div>
      <div>Accuracy: {{ score?.accuracy ?? '--' }}</div>
      <div>Fluency: {{ score?.fluency ?? '--' }}</div>
      <div>Completeness: {{ score?.completeness ?? '--' }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PronScore } from '@/core/types'

defineProps<{
  score: PronScore | null
}>()
</script>

