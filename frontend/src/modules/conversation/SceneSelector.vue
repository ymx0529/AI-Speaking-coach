<template>
  <section class="min-h-screen px-5 py-6 lg:px-8 lg:py-8">
    <div class="mx-auto max-w-7xl rounded-[28px] border border-[color:var(--line-soft)] bg-[var(--surface-0)] shadow-[var(--shadow-soft)]">
      <header class="flex flex-wrap items-center justify-between gap-4 border-b border-[color:var(--line-soft)] px-6 py-5 lg:px-8">
        <div>
          <button class="text-sm font-medium text-[var(--ink-3)] transition hover:text-[var(--ink-1)]" @click="$emit('back')">
            返回首页
          </button>
          <h1 class="mt-3 text-3xl font-semibold tracking-tight text-[var(--ink-1)] lg:text-4xl">选择练习方式</h1>
          <p class="mt-2 text-sm leading-7 text-[var(--ink-3)]">先选难度，再进入固定场景，或者直接创建一个自己的对话背景。</p>
        </div>
        <UserAccountBadge />
      </header>

      <div class="grid gap-6 px-6 py-8 lg:grid-cols-[18rem_minmax(0,1fr)] lg:px-8 lg:py-8">
        <aside class="rounded-[24px] bg-[linear-gradient(180deg,#0f172a_0%,#1d4ed8_100%)] p-5 text-white shadow-[0_24px_60px_rgba(29,78,216,0.18)]">
          <div class="text-xs uppercase tracking-[0.18em] text-sky-100/80">Difficulty</div>
          <div class="mt-3 text-2xl font-semibold">先选难度</div>
          <div class="mt-2 text-sm leading-7 text-sky-50/80">难度越高，追问越紧，表达要求也更完整。</div>

          <div class="mt-6 space-y-3">
            <button
              v-for="item in difficultyOptions"
              :key="item.value"
              class="w-full rounded-[18px] border px-4 py-4 text-left transition"
              :class="
                selectedDifficulty === item.value
                  ? 'border-white/70 bg-white/16'
                  : 'border-white/12 bg-white/6 hover:bg-white/10'
              "
              @click="selectedDifficulty = item.value"
            >
              <div class="flex items-center justify-between gap-3">
                <div>
                  <div class="text-base font-semibold">{{ item.label }}</div>
                  <div class="mt-1 text-sm text-sky-50/80">{{ item.description }}</div>
                </div>
                <div class="flex h-7 w-7 items-center justify-center rounded-full border border-white/20 text-xs">
                  {{ item.value }}
                </div>
              </div>
            </button>
          </div>
        </aside>

        <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_24rem]">
          <section class="space-y-5">
            <div>
              <div class="text-sm font-semibold text-[var(--ink-2)]">固定场景</div>
              <p class="mt-1 text-sm text-[var(--ink-3)]">选择一个场景，系统会自动用对应身份继续陪练。</p>
            </div>

            <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              <article
                v-for="scene in fixedScenes"
                :key="scene.id"
                class="flex flex-col rounded-[24px] border border-[color:var(--line-soft)] bg-white p-5"
              >
                <div class="flex h-12 w-12 items-center justify-center rounded-[16px] text-xl" :class="scene.iconClass">
                  {{ scene.icon }}
                </div>
                <div class="mt-5 text-2xl font-semibold tracking-tight text-[var(--ink-1)]">{{ scene.title }}</div>
                <div class="mt-2 text-xs uppercase tracking-[0.18em] text-[var(--ink-4)]">{{ scene.subtitle }}</div>
                <p class="mt-4 flex-1 text-sm leading-7 text-[var(--ink-3)]">{{ scene.description }}</p>
                <div class="mt-5 flex items-center justify-between">
                  <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-[var(--ink-3)]">
                    难度：{{ currentDifficultyLabel }}
                  </span>
                  <button
                    class="rounded-full bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="startingSceneId === scene.id"
                    @click="startFixedScene(scene.id, scene.personaId)"
                  >
                    {{ startingSceneId === scene.id ? '进入中...' : '开始' }}
                  </button>
                </div>
              </article>
            </div>
          </section>

          <aside class="rounded-[24px] border border-[color:var(--line-soft)] bg-white p-5">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-[var(--ink-2)]">自定义场景</div>
                <p class="mt-1 text-sm text-[var(--ink-3)]">写下背景、目标或难点，让 AI 按你的情境继续对话。</p>
              </div>
              <span class="rounded-full bg-[var(--brand-50)] px-3 py-1 text-xs font-semibold text-[var(--brand-500)]">
                AI 生成
              </span>
            </div>

            <div class="mt-5">
              <label class="mb-2 block text-sm font-medium text-[var(--ink-2)]">场景背景</label>
              <textarea
                v-model.trim="customBackground"
                class="h-52 w-full resize-none rounded-[18px] border border-[color:var(--line-strong)] bg-[var(--surface-2)] px-4 py-3 text-sm leading-7 outline-none transition focus:border-[var(--brand-500)]"
                maxlength="240"
                placeholder="例如：我要向客户解释项目延期一周，并争取对方接受新的时间。"
              />
              <div class="mt-2 flex items-center justify-between text-xs text-[var(--ink-4)]">
                <span>建议写清角色、目标和难点。</span>
                <span>{{ customBackground.length }}/240</span>
              </div>
            </div>

            <div class="mt-5 grid gap-3 sm:grid-cols-2">
              <div class="rounded-[18px] bg-[var(--surface-2)] px-4 py-4">
                <div class="text-xs uppercase tracking-[0.16em] text-[var(--ink-4)]">当前难度</div>
                <div class="mt-2 text-lg font-semibold text-[var(--ink-1)]">{{ currentDifficultyLabel }}</div>
              </div>
              <div class="rounded-[18px] bg-[var(--surface-2)] px-4 py-4">
                <div class="text-xs uppercase tracking-[0.16em] text-[var(--ink-4)]">AI 会怎么练</div>
                <div class="mt-2 text-sm leading-7 text-[var(--ink-3)]">{{ difficultyHint }}</div>
              </div>
            </div>

            <button
              class="mt-5 w-full rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500"
              :disabled="!canStartCustom || startingSceneId === 'custom'"
              @click="startCustomScene()"
            >
              {{ startingSceneId === 'custom' ? '进入中...' : '开始自定义陪练' }}
            </button>
          </aside>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { useAppStore } from '@/core/store'
import type { Difficulty } from '@/core/types'
import { ws } from '@/core/ws'
import UserAccountBadge from '@/modules/auth/UserAccountBadge.vue'

const emit = defineEmits<{
  back: []
}>()

const store = useAppStore()
const selectedDifficulty = ref<Difficulty>(store.difficulty)
const customBackground = ref(store.customBackground)
const startingSceneId = ref<string | null>(null)

const difficultyOptions: Array<{ value: Difficulty; label: string; description: string }> = [
  { value: 1, label: '入门', description: '短句更简单，节奏更慢。' },
  { value: 2, label: '进阶', description: '更接近日常交流。' },
  { value: 3, label: '困难', description: '追问更紧，表达更复杂。' },
]

const fixedScenes = [
  {
    id: 'interview',
    title: '求职面试',
    subtitle: 'Job Interview',
    description: '练自我介绍、项目经历和追问应答。',
    personaId: 'strict_interviewer',
    icon: '💼',
    iconClass: 'bg-sky-100',
  },
  {
    id: 'restaurant',
    title: '餐厅点餐',
    subtitle: 'Restaurant Order',
    description: '练点餐、偏好和补充说明。',
    personaId: 'friendly_waiter',
    icon: '🍽',
    iconClass: 'bg-emerald-100',
  },
  {
    id: 'meeting',
    title: '商务会议',
    subtitle: 'Business Meeting',
    description: '练表达观点、解释方案和推进讨论。',
    personaId: 'colleague',
    icon: '👥',
    iconClass: 'bg-amber-100',
  },
]

const currentDifficultyLabel = computed(() => difficultyOptions.find((item) => item.value === selectedDifficulty.value)?.label ?? '入门')
const difficultyHint = computed(() => difficultyOptions.find((item) => item.value === selectedDifficulty.value)?.description ?? '短句更简单，节奏更慢。')
const canStartCustom = computed(() => customBackground.value.trim().length > 0)

async function connectAndStart(payload: {
  sceneId: string
  personaId: string
  difficulty: Difficulty
  customBackground?: string
}) {
  if (!store.authToken) {
    store.phase = 'auth'
    return
  }

  const newSessionId =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : `session-${Date.now()}`
  startingSceneId.value = payload.sceneId

  try {
    ws.disconnect()
    await ws.connect(newSessionId, store.authToken)

    store.startSession({
      sessionId: newSessionId,
      sceneId: payload.sceneId,
      difficulty: payload.difficulty,
      personaId: payload.personaId,
      customBackground: payload.customBackground ?? '',
    })

    ws.send({
      type: 'session.start',
      session_id: newSessionId,
      scene_id: payload.sceneId,
      difficulty: payload.difficulty,
      persona_id: payload.personaId,
      custom_background: payload.customBackground,
      client_ts: Date.now(),
    })
  } catch {
    ws.disconnect()
    store.phase = 'auth'
  } finally {
    startingSceneId.value = null
  }
}

async function startFixedScene(sceneId: string, personaId: string) {
  await connectAndStart({
    sceneId,
    personaId,
    difficulty: selectedDifficulty.value,
  })
}

async function startCustomScene() {
  if (!canStartCustom.value) return
  await connectAndStart({
    sceneId: 'custom',
    personaId: 'adaptive_coach',
    difficulty: selectedDifficulty.value,
    customBackground: customBackground.value.trim(),
  })
}
</script>
