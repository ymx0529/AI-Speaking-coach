<template>
  <div class="flex items-center gap-3 rounded-full border border-[color:var(--line-soft)] bg-white px-3 py-2 shadow-sm">
    <div class="flex h-10 w-10 items-center justify-center rounded-full bg-slate-950 text-sm font-semibold text-white">
      {{ initials }}
    </div>
    <div class="min-w-0">
      <div class="truncate text-sm font-semibold text-[var(--ink-2)]">{{ store.currentUser?.name ?? '访客' }}</div>
      <div class="truncate text-xs text-[var(--ink-4)]">{{ store.currentUser?.email ?? '未登录' }}</div>
    </div>
    <button
      class="rounded-full border border-[color:var(--line-soft)] px-3 py-1.5 text-xs font-medium text-[var(--ink-3)] transition hover:bg-slate-50"
      @click="store.logout()"
    >
      退出
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { useAppStore } from '@/core/store'

const store = useAppStore()

const initials = computed(() => {
  const value = store.currentUser?.name?.trim() || store.currentUser?.email?.trim() || 'SC'
  return value.slice(0, 2).toUpperCase()
})
</script>
