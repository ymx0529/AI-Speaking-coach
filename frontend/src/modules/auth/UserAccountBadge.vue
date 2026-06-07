<template>
  <div
    v-if="store.currentUser"
    class="flex items-center gap-3 rounded-full border border-slate-200 bg-white/90 px-3 py-2 shadow-sm"
  >
    <div class="flex h-10 w-10 items-center justify-center rounded-full bg-slate-950 text-sm font-semibold text-white">
      {{ initials }}
    </div>
    <div class="hidden min-w-0 sm:block">
      <div class="truncate text-sm font-semibold text-slate-900">{{ store.currentUser.name }}</div>
      <div class="truncate text-xs text-slate-500">{{ store.currentUser.email }}</div>
    </div>
    <button
      class="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-200"
      type="button"
      @click="logout"
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
  const user = store.currentUser
  if (!user) return 'U'
  const source = user.name || user.email
  return source.trim().slice(0, 2).toUpperCase()
})

async function logout() {
  await store.logout()
}
</script>
