<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top,#f8fbff_0%,#eef4ff_45%,#edf2f7_100%)]">
    <div v-if="!store.authReady" class="flex min-h-screen items-center justify-center px-6">
      <div class="text-center">
        <div class="text-sm font-medium text-slate-500">正在恢复登录状态...</div>
        <button
          class="mt-4 rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
          type="button"
          @click="resetLoginState"
        >
          重新登录
        </button>
      </div>
    </div>
    <AuthView v-else-if="!store.currentUser" />
    <template v-else>
      <SceneSelector v-if="store.phase === 'scene_select'" />
      <ConversationRoom v-else-if="store.phase === 'in_session'">
        <template #correction>
          <CorrectionPanel />
        </template>
      </ConversationRoom>
      <SessionSummaryPanel
        v-else-if="store.phase === 'summary'"
        :session-id="store.sessionId ?? 'mock-session'"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import CorrectionPanel from '@/modules/coach/CorrectionPanel.vue'
import SessionSummaryPanel from '@/modules/coach/SessionSummaryPanel.vue'
import { useCoach } from '@/modules/coach/useCoach'
import AuthView from '@/modules/auth/AuthView.vue'
import ConversationRoom from '@/modules/conversation/ConversationRoom.vue'
import SceneSelector from '@/modules/conversation/SceneSelector.vue'
import { useAppStore } from '@/core/store'

const store = useAppStore()

// Single WS subscription for all Coach analysis events (v1 + v2)
useCoach()

onMounted(() => {
  void store.restoreAuth()
})

function resetLoginState() {
  store.clearAuthSession()
  store.authReady = true
}
</script>

