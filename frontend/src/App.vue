<template>
  <div class="min-h-screen bg-slate-100">
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
  </div>
</template>

<script setup lang="ts">
import CorrectionPanel from '@/modules/coach/CorrectionPanel.vue'
import SessionSummaryPanel from '@/modules/coach/SessionSummaryPanel.vue'
import ConversationRoom from '@/modules/conversation/ConversationRoom.vue'
import SceneSelector from '@/modules/conversation/SceneSelector.vue'
import { useAppStore } from '@/core/store'

const store = useAppStore()
</script>

