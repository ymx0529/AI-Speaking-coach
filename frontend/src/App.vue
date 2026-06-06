<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top,#f8fbff_0%,#eef4ff_45%,#edf2f7_100%)]">
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
import { useCoach } from '@/modules/coach/useCoach'
import ConversationRoom from '@/modules/conversation/ConversationRoom.vue'
import SceneSelector from '@/modules/conversation/SceneSelector.vue'
import { useAppStore } from '@/core/store'

const store = useAppStore()

// Single WS subscription for all Coach analysis events (v1 + v2)
useCoach()
</script>

