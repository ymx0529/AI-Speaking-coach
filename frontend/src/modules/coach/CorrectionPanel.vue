<template>
  <div class="rounded-2xl border border-amber-200 bg-amber-50 p-4">
    <div class="text-sm font-medium text-amber-800">Correction Panel</div>
    <div v-if="store.currentCorrections.length" class="mt-3 space-y-3">
      <div
        v-for="(issue, index) in store.currentCorrections"
        :key="index"
        class="rounded-xl bg-white/70 p-3 text-sm text-amber-900"
      >
        <div class="font-medium">{{ issue.original }} → {{ issue.corrected }}</div>
        <div class="mt-1 text-xs text-amber-700">{{ issue.explanation }}</div>
      </div>
    </div>
    <p v-else class="mt-2 text-sm text-amber-700">
      当前还没有纠错结果，先跑一轮最小验证对话。
    </p>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/core/store'

const store = useAppStore()
</script>
