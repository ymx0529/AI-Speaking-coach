<template>
  <section class="mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">
    <div class="overflow-hidden rounded-[24px] border border-[color:var(--line-soft)] bg-[var(--surface-0)] shadow-[0_24px_70px_rgba(15,23,42,0.08)]">
      <div class="border-b border-[color:var(--line-soft)] px-6 py-5 lg:px-8">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-4">
            <div
              class="flex h-14 w-14 items-center justify-center rounded-[22px] bg-[linear-gradient(135deg,#2563eb_0%,#38bdf8_100%)] text-xl font-bold text-white shadow-[0_18px_40px_rgba(37,99,235,0.28)]"
            >
              S
            </div>
            <div>
              <div class="text-2xl font-semibold tracking-tight text-[var(--ink-2)]">SpeakCoach</div>
              <div class="mt-1 text-sm text-[var(--ink-3)]">AI 英语口语陪练，按你的场景和难度即时生成对话</div>
            </div>
          </div>

          <div class="flex items-center gap-3 rounded-full border border-[color:var(--line-soft)] bg-[var(--brand-50)] px-4 py-2 text-sm font-medium text-[var(--brand-500)]">
            <span class="inline-block h-2.5 w-2.5 rounded-full bg-sky-500" />
            当前支持实时录音与 Qwen 陪练
          </div>
        </div>
      </div>

      <div class="grid gap-8 px-6 py-7 lg:grid-cols-[1.4fr_0.95fr] lg:px-8 lg:py-9">
        <div class="space-y-7">
          <div class="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
            <div class="rounded-[20px] bg-[radial-gradient(circle_at_top_left,#fef3c7_0%,#ffffff_34%,#eef4ff_100%)] p-7">
              <div class="inline-flex items-center rounded-full bg-amber-100/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-amber-700">
                Scenario Practice
              </div>
              <h1 class="mt-5 max-w-xl text-4xl font-semibold leading-tight tracking-tight text-slate-950 lg:text-[3.2rem]">
                在真实场景中练表达，
                <span class="text-[var(--brand-500)]">让 AI 更懂你的陪练目标</span>
              </h1>
              <p class="mt-5 max-w-2xl text-base leading-8 text-[var(--ink-3)]">
                先选难度，再进入固定场景，或者直接输入你自己的背景。AI 会根据场景压力、角色关系和目标，
                给出更贴近真实交流的追问和回应。
              </p>

              <div class="mt-7 flex flex-wrap gap-3">
                <div class="rounded-[16px] border border-white/80 bg-white/80 px-4 py-3 shadow-sm">
                  <div class="text-xs uppercase tracking-[0.14em] text-[var(--ink-4)]">训练模式</div>
                  <div class="mt-1 text-sm font-semibold text-[var(--ink-2)]">固定场景 / 自定义场景</div>
                </div>
                <div class="rounded-[16px] border border-white/80 bg-white/80 px-4 py-3 shadow-sm">
                  <div class="text-xs uppercase tracking-[0.14em] text-slate-400">难度控制</div>
                  <div class="mt-1 text-sm font-semibold text-slate-800">入门 / 进阶 / 困难</div>
                </div>
                <div class="rounded-[16px] border border-white/80 bg-white/80 px-4 py-3 shadow-sm">
                  <div class="text-xs uppercase tracking-[0.14em] text-slate-400">陪练风格</div>
                  <div class="mt-1 text-sm font-semibold text-slate-800">按背景动态追问</div>
                </div>
              </div>
            </div>

            <div class="rounded-[20px] bg-[linear-gradient(160deg,#0f172a_0%,#1d4ed8_55%,#38bdf8_100%)] p-7 text-white shadow-[0_22px_54px_rgba(37,99,235,0.2)]">
              <div class="text-xs uppercase tracking-[0.18em] text-sky-100/80">Difficulty Router</div>
              <div class="mt-4 text-2xl font-semibold leading-snug">
                先定训练强度，
                <br />
                再开始这一轮对话
              </div>
              <p class="mt-4 text-sm leading-7 text-sky-50/85">
                你选择的难度会直接影响 AI 的词汇复杂度、追问深度和场景压迫感。
              </p>

              <div class="mt-6 space-y-3">
                <button
                  v-for="option in difficultyOptions"
                  :key="option.value"
                  type="button"
                  class="flex w-full items-start justify-between rounded-[16px] border px-4 py-4 text-left transition"
                  :class="
                    selectedDifficulty === option.value
                      ? 'border-white/60 bg-white/18 shadow-[0_12px_30px_rgba(15,23,42,0.18)]'
                      : 'border-white/15 bg-white/8 hover:bg-white/12'
                  "
                  @click="selectedDifficulty = option.value"
                >
                  <div>
                    <div class="text-base font-semibold">{{ option.label }}</div>
                    <div class="mt-1 text-sm leading-6 text-sky-50/78">{{ option.description }}</div>
                  </div>
                  <div
                    class="mt-1 flex h-6 w-6 items-center justify-center rounded-full border text-xs"
                    :class="selectedDifficulty === option.value ? 'border-white bg-white text-slate-900' : 'border-white/40 text-white/80'"
                  >
                    {{ selectedDifficulty === option.value ? '✓' : option.short }}
                  </div>
                </button>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="flex items-center justify-between gap-4">
              <div>
                <div class="text-sm font-semibold text-slate-900">固定场景</div>
                <div class="mt-1 text-sm text-slate-500">选择一个现成场景，直接开始一轮针对性的英语口语练习。</div>
              </div>
              <div class="rounded-full bg-slate-100 px-4 py-2 text-xs font-medium text-slate-500">
                当前难度：{{ difficultyLabel }}
              </div>
            </div>

            <div class="grid gap-4 md:grid-cols-3">
              <button
                v-for="(scene, sceneId) in fixedSceneCards"
                :key="sceneId"
                type="button"
                class="group relative overflow-hidden rounded-[18px] border border-slate-100 bg-white p-5 text-left shadow-[0_16px_40px_rgba(15,23,42,0.05)] transition duration-300 hover:-translate-y-1 hover:border-sky-200 hover:shadow-[0_22px_54px_rgba(59,130,246,0.12)]"
                :aria-label="`开始${scene.name_zh}场景，当前难度${difficultyLabel}`"
                @click="start(sceneId)"
              >
                <div class="pointer-events-none absolute inset-x-0 top-0 h-24 bg-[radial-gradient(circle_at_top_right,rgba(56,189,248,0.16),transparent_58%)]" />
                <div class="relative">
                  <div class="flex h-14 w-14 items-center justify-center rounded-[14px] text-2xl shadow-lg" :class="scene.iconBg">
                    {{ scene.icon }}
                  </div>
                  <div class="mt-5 text-lg font-semibold text-slate-900">{{ scene.name_zh }}</div>
                  <div class="mt-1 text-xs font-medium uppercase tracking-[0.16em] text-slate-400">
                    {{ scene.name }}
                  </div>
                  <p class="mt-4 min-h-[92px] text-sm leading-7 text-slate-500">
                    {{ scene.description }}
                  </p>

                  <div class="mt-5 flex items-center justify-between">
                    <div class="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-500">
                      {{ difficultyLabel }}
                    </div>
                    <div class="flex h-10 w-10 items-center justify-center rounded-full bg-sky-50 text-sky-600 transition group-hover:translate-x-1">
                      →
                    </div>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>

        <div class="space-y-5">
          <div class="overflow-hidden rounded-[20px] bg-[linear-gradient(180deg,#f8fbff_0%,#eef6ff_100%)] p-6 shadow-inner">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="text-xs uppercase tracking-[0.18em] text-sky-500">Custom Lab</div>
                <div class="mt-2 text-2xl font-semibold tracking-tight text-slate-950">自定义场景陪练</div>
              </div>
              <div class="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-500 shadow-sm">
                实时生成提示词
              </div>
            </div>

            <p class="mt-4 text-sm leading-7 text-slate-600">
              描述你的真实背景、角色关系、目标和压力点。AI 会把这些信息作为场景上下文，用更贴合的英语来跟你对练。
            </p>

            <div class="mt-5 rounded-[18px] border border-white/70 bg-white/88 p-4 shadow-sm">
              <label class="mb-2 block text-sm font-semibold text-slate-800" for="custom-background">
                场景背景
              </label>
              <textarea
                id="custom-background"
                v-model.trim="customBackground"
                rows="7"
                class="w-full resize-none rounded-[16px] border border-slate-200 bg-slate-50 px-4 py-4 text-sm leading-7 text-slate-700 outline-none transition placeholder:text-slate-400 focus:border-sky-300 focus:bg-white focus:ring-4 focus:ring-sky-100"
                placeholder="例如：我要模拟和美国客户开会，解释项目延期一周的原因，并争取对方接受新的交付时间。对方比较强势，我希望练习更自然、更有说服力的表达。"
              />

              <div class="mt-3 flex items-center justify-between gap-3 text-xs text-slate-400">
                <span>建议写清楚角色、目标和难点，这样 AI 追问会更精准。</span>
                <span>{{ customBackground.length }}/240</span>
              </div>
            </div>

            <div class="mt-5 grid gap-3 sm:grid-cols-2">
              <div class="rounded-[16px] bg-white/88 p-4 shadow-sm">
                <div class="text-xs uppercase tracking-[0.14em] text-slate-400">当前难度</div>
                <div class="mt-2 text-lg font-semibold text-slate-900">{{ difficultyLabel }}</div>
                <div class="mt-2 text-sm leading-6 text-slate-500">{{ currentDifficultyDescription }}</div>
              </div>
              <div class="rounded-[16px] bg-white/88 p-4 shadow-sm">
                <div class="text-xs uppercase tracking-[0.14em] text-slate-400">AI 将会</div>
                <div class="mt-2 text-sm leading-7 text-slate-600">
                  读取你的背景，模拟对应角色，并围绕关键冲突点持续追问。
                </div>
              </div>
            </div>

            <div class="mt-5 flex flex-col gap-3">
              <button
                type="button"
                class="w-full rounded-[22px] px-5 py-4 text-sm font-semibold text-white shadow-[0_20px_45px_rgba(14,116,144,0.26)] transition"
                :class="
                  canStartCustom
                    ? 'bg-[linear-gradient(135deg,#0f172a_0%,#2563eb_55%,#06b6d4_100%)] hover:-translate-y-0.5'
                    : 'cursor-not-allowed bg-slate-300 shadow-none'
                "
                :disabled="!canStartCustom"
                :aria-label="`开始自定义场景陪练，当前难度${difficultyLabel}`"
                @click="start('custom')"
              >
                开始自定义陪练
              </button>
              <div v-if="!canStartCustom" class="text-sm text-amber-600">
                先填写场景背景，按钮就会自动启用。
              </div>
              <div v-if="errorMessage" class="rounded-[20px] bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {{ errorMessage }}
              </div>
            </div>
          </div>

          <div class="rounded-[20px] bg-slate-950 p-6 text-white shadow-[0_24px_60px_rgba(15,23,42,0.2)]">
            <div class="text-xs uppercase tracking-[0.18em] text-sky-300/90">How It Feels</div>
            <div class="mt-3 text-2xl font-semibold leading-snug">像一个真的对话对象，而不是只会机械提问的脚本</div>
            <ul class="mt-5 space-y-3 text-sm leading-7 text-slate-300">
              <li>固定场景适合快速进入状态，马上开口。</li>
              <li>自定义场景适合模拟你自己的面试、会议、客户沟通和汇报压力。</li>
              <li>难度越高，AI 的英语越自然、追问越紧、场景越接近真实工作环境。</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { SCENES } from '@/core/scenes'
import { useAppStore } from '@/core/store'
import type { Difficulty } from '@/core/types'
import { ws } from '@/core/ws'

const store = useAppStore()
const selectedDifficulty = ref<Difficulty>(1)
const customBackground = ref('')
const errorMessage = ref('')

const difficultyOptions = [
  {
    value: 1 as Difficulty,
    label: '入门',
    short: '1',
    description: '句子更简单，推进节奏更慢，适合刚开始练习开口表达。',
  },
  {
    value: 2 as Difficulty,
    label: '进阶',
    short: '2',
    description: '更贴近日常工作交流，追问更自然，也更考验临场组织能力。',
  },
  {
    value: 3 as Difficulty,
    label: '困难',
    short: '3',
    description: '场景压力更强，表达更复杂，连续追问也会更密集。',
  },
]

const difficultyLabel = computed(() => difficultyOptions.find((option) => option.value === selectedDifficulty.value)?.label ?? '入门')
const currentDifficultyDescription = computed(
  () => difficultyOptions.find((option) => option.value === selectedDifficulty.value)?.description ?? ''
)
const canStartCustom = computed(() => customBackground.value.trim().length > 0)

const fixedSceneCards = computed(() => ({
  interview: {
    ...SCENES.interview,
    icon: '💼',
    iconBg: 'bg-[linear-gradient(135deg,#dbeafe_0%,#c7d2fe_100%)]',
    description: '模拟真实求职面试，练习自我介绍、项目讲述、追问回答和临场表达。',
  },
  restaurant: {
    ...SCENES.restaurant,
    icon: '🍽',
    iconBg: 'bg-[linear-gradient(135deg,#dcfce7_0%,#fef9c3_100%)]',
    description: '围绕点餐、偏好、加单和确认细节来练习更自然的生活口语。',
  },
  meeting: {
    ...SCENES.meeting,
    icon: '📊',
    iconBg: 'bg-[linear-gradient(135deg,#fee2e2_0%,#fde68a_100%)]',
    description: '模拟商务会议发言、提案解释、风险说明和方案讨论。',
  },
}))

async function start(sceneId: string) {
  errorMessage.value = ''

  if (sceneId === 'custom' && !canStartCustom.value) {
    errorMessage.value = '请先填写你的自定义场景背景。'
    return
  }

  const scene = SCENES[sceneId]
  if (!scene) {
    errorMessage.value = '未找到对应场景，请刷新页面后重试。'
    return
  }

  const personaId = Object.keys(scene.personas)[0]
  const sessionId = crypto.randomUUID()
  const normalizedBackground = sceneId === 'custom' ? customBackground.value.trim() : ''

  store.startSession({
    sessionId,
    sceneId,
    difficulty: selectedDifficulty.value,
    personaId,
    customBackground: normalizedBackground,
  })

  try {
    await ws.connect(sessionId)
    ws.send({
      type: 'session.start',
      session_id: sessionId,
      scene_id: sceneId,
      difficulty: selectedDifficulty.value,
      persona_id: personaId,
      custom_background: normalizedBackground || undefined,
      client_ts: Date.now(),
    })
  } catch (error) {
    errorMessage.value = '连接会话失败，请稍后重试。'
    console.error('Failed to connect websocket', error)
  }
}
</script>
