<template>
  <section class="mx-auto max-w-7xl px-6 py-10 lg:px-10">
    <div class="overflow-hidden rounded-[32px] border border-white/70 bg-white/80 shadow-[0_30px_80px_rgba(84,108,255,0.14)] backdrop-blur">
      <div class="border-b border-slate-100/80 px-6 py-5 lg:px-8">
        <div class="flex items-center justify-between gap-4">
          <div class="flex items-center gap-3">
            <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-blue-500 text-lg font-bold text-white shadow-lg shadow-indigo-200">
              S
            </div>
            <div>
              <div class="text-lg font-semibold text-slate-900">SpeakCoach</div>
              <div class="text-xs text-slate-500">AI 英语口语陪练</div>
            </div>
          </div>
          <div class="rounded-full border border-indigo-100 bg-indigo-50 px-4 py-2 text-xs font-medium text-indigo-600">
            练习记录
          </div>
        </div>
      </div>

      <div class="grid gap-10 px-6 py-8 lg:grid-cols-[1.25fr_0.85fr] lg:px-8 lg:py-10">
        <div class="space-y-8">
          <div class="space-y-4">
            <div class="inline-flex items-center rounded-full bg-amber-50 px-4 py-2 text-xs font-semibold text-amber-600">
              选择场景，开始你的口语练习吧
            </div>
            <div class="max-w-2xl space-y-4">
              <h1 class="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
                在真实场景中练习表达，
                <span class="bg-gradient-to-r from-indigo-600 to-sky-500 bg-clip-text text-transparent">
                  更自然地说英语
                </span>
              </h1>
              <p class="text-sm leading-7 text-slate-500 md:text-base">
                选择一个练习场景，进入连续对话体验。当前版本保留现有交互逻辑，但整体视觉会更接近你给的效果图。
              </p>
            </div>
          </div>

          <div class="grid gap-5 xl:grid-cols-3">
            <button
              v-for="(scene, sceneId) in sceneCards"
              :key="sceneId"
              class="group relative overflow-hidden rounded-[28px] border border-slate-100 bg-white p-5 text-left shadow-[0_18px_50px_rgba(15,23,42,0.06)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_24px_60px_rgba(84,108,255,0.14)]"
              @click="start(sceneId)"
            >
              <div
                class="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl text-2xl shadow-lg"
                :class="scene.iconBg"
              >
                {{ scene.icon }}
              </div>
              <div class="space-y-2">
                <div class="text-lg font-semibold text-slate-900">{{ scene.name_zh }}</div>
                <div class="text-xs font-medium uppercase tracking-[0.16em] text-slate-400">
                  {{ scene.name }}
                </div>
                <p class="min-h-[64px] text-sm leading-6 text-slate-500">
                  {{ scene.description }}
                </p>
              </div>

              <div class="mt-5 flex items-center justify-between">
                <div class="rounded-full bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500">
                  难度：入门
                </div>
                <div class="flex h-9 w-9 items-center justify-center rounded-full bg-slate-50 text-slate-500 transition group-hover:bg-indigo-50 group-hover:text-indigo-600">
                  →
                </div>
              </div>

              <div class="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-gradient-to-br from-indigo-50 to-transparent opacity-80" />
            </button>
          </div>

          <div class="flex flex-wrap items-center gap-3 text-xs text-slate-400">
            <span>更多场景即将上线</span>
            <span class="h-1 w-1 rounded-full bg-slate-300" />
            <span>当前优先体验对话主链路</span>
          </div>
        </div>

        <div class="relative">
          <div class="relative flex h-full min-h-[360px] flex-col justify-between overflow-hidden rounded-[30px] bg-gradient-to-br from-indigo-50 via-white to-sky-50 p-8 shadow-inner">
            <div class="space-y-4">
              <div class="inline-flex items-center rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-indigo-500 shadow-sm">
                Realtime Speaking Practice
              </div>
              <div class="text-2xl font-semibold leading-snug text-slate-900">
                边说边练，
                <br />
                让反馈更即时
              </div>
              <p class="max-w-sm text-sm leading-7 text-slate-500">
                你会体验到场景选择、实时识别、AI 回复与总结页串联的完整练习流。
              </p>
            </div>

            <div class="relative mt-8 flex items-center justify-center py-6">
              <div class="absolute h-56 w-56 rounded-full bg-gradient-to-br from-indigo-200 via-sky-100 to-transparent blur-2xl" />
              <div class="relative flex h-56 w-56 items-center justify-center rounded-full bg-white/90 shadow-[0_25px_55px_rgba(84,108,255,0.14)]">
                <div class="absolute left-6 top-10 rounded-full bg-gradient-to-r from-indigo-500 to-sky-400 px-4 py-2 text-xs font-semibold text-white shadow-md">
                  实时识别
                </div>
                <div class="flex h-28 w-28 items-center justify-center rounded-[30px] bg-gradient-to-br from-indigo-500 to-blue-500 text-5xl text-white shadow-xl">
                  AI
                </div>
                <div class="absolute bottom-8 right-6 rounded-full bg-white px-4 py-2 text-xs font-semibold text-slate-500 shadow-md">
                  反馈更自然
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { SCENES } from '@/core/scenes'
import { useAppStore } from '@/core/store'
import { ws } from '@/core/ws'

const store = useAppStore()

const sceneCards = computed(() => ({
  interview: {
    ...SCENES.interview,
    icon: '💼',
    iconBg: 'bg-gradient-to-br from-blue-100 to-indigo-100',
    description: '模拟真实面试场景，提升自我介绍、项目表达与应答能力。',
  },
  restaurant: {
    ...SCENES.restaurant,
    icon: '🍽',
    iconBg: 'bg-gradient-to-br from-emerald-100 to-lime-100',
    description: '在餐厅点餐、沟通口味偏好，练习日常交流表达。',
  },
  meeting: {
    ...SCENES.meeting,
    icon: '👥',
    iconBg: 'bg-gradient-to-br from-amber-100 to-orange-100',
    description: '参与商务讨论与汇报，提升职场沟通和提案表达能力。',
  },
}))

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
      type: 'session.start',
      session_id: sessionId,
      scene_id: sceneId,
      difficulty: 1,
      persona_id: personaId,
      client_ts: Date.now(),
    })
  } catch (error) {
    console.error('Failed to connect websocket', error)
  }
}
</script>
