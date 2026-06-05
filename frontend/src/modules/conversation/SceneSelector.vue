<template>
  <section class="mx-auto flex min-h-screen max-w-4xl items-center justify-center p-6">
    <div class="w-full rounded-3xl bg-white p-8 shadow-sm">
      <h1 class="text-3xl font-semibold text-slate-900">SpeakCoach</h1>
      <p class="mt-2 text-sm text-slate-500">选择一个场景，进入口语练习骨架页面。</p>

      <div class="mt-6 grid gap-4 md:grid-cols-3">
        <button
          v-for="(scene, sceneId) in SCENES"
          :key="sceneId"
          class="rounded-2xl border border-slate-200 p-4 text-left transition hover:border-slate-400"
          @click="start(sceneId)"
        >
          <div class="text-lg font-medium text-slate-900">{{ scene.name_zh }}</div>
          <div class="mt-1 text-sm text-slate-500">{{ scene.name }}</div>
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { SCENES } from '@/core/scenes'
import { useAppStore } from '@/core/store'
import { ws } from '@/core/ws'

const store = useAppStore()

async function start(sceneId: string) {
  const personaId = Object.keys(SCENES[sceneId].personas)[0]
  const sessionId = crypto.randomUUID()
  store.startSession({
    sessionId,
    sceneId,
    difficulty: 1,
    personaId,
  })

  try {
    await ws.connect(sessionId)
    ws.send({
      type: 'session_start',
      scene_id: sceneId,
      difficulty: 1,
      persona_id: personaId,
    })
  } catch (error) {
    console.error('Failed to connect websocket', error)
  }
}
</script>
