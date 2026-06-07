<template>
  <main>
    <HomePage
      v-if="store.phase === 'home'"
      @login="handleOpenLogin"
      @start="handleStartExperience"
    />

    <AuthView
      v-else-if="store.phase === 'auth'"
      :pending="store.authLoading"
      @back="store.phase = 'home'"
    />

    <SceneSelector
      v-else-if="store.phase === 'scene_select'"
      @back="store.phase = 'home'"
    />

    <ConversationRoom v-else-if="store.phase === 'in_session'">
      <template #correction>
        <CorrectionPanel />
      </template>
    </ConversationRoom>

    <SessionSummaryPanel
      v-else-if="store.phase === 'summary' && store.sessionId"
      :session-id="store.sessionId"
    />
  </main>
</template>

<script setup lang="ts">
import CorrectionPanel from '@/modules/coach/CorrectionPanel.vue'
import SessionSummaryPanel from '@/modules/coach/SessionSummaryPanel.vue'
import ConversationRoom from '@/modules/conversation/ConversationRoom.vue'
import SceneSelector from '@/modules/conversation/SceneSelector.vue'
import AuthView from '@/modules/auth/AuthView.vue'
import HomePage from '@/modules/home/HomePage.vue'
import { useAppStore } from '@/core/store'

const store = useAppStore()

async function ensureAuthForPractice() {
  if (store.currentUser) {
    store.phase = 'scene_select'
    return
  }

  const restored = await store.restoreAuth()
  store.phase = restored ? 'scene_select' : 'auth'
}

async function handleStartExperience() {
  await ensureAuthForPractice()
}

async function handleOpenLogin() {
  if (store.currentUser) {
    store.phase = 'scene_select'
    return
  }

  const restored = await store.restoreAuth()
  store.phase = restored ? 'scene_select' : 'auth'
}
</script>
