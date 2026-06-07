<template>
  <section class="h-[100dvh] overflow-hidden bg-[linear-gradient(180deg,#edf3ff_0%,#f7faff_52%,#eef4ff_100%)] px-3 py-3">
    <div
      class="mx-auto flex h-full max-w-[1280px] flex-col overflow-hidden rounded-[22px] border border-slate-200/80 bg-white/95 shadow-[0_18px_46px_rgba(15,23,42,0.06)]"
    >
      <header class="flex h-[64px] shrink-0 items-center justify-between border-b border-slate-200/70 px-6">
        <div class="flex items-center gap-3">
          <div
            class="flex h-10 w-10 items-center justify-center rounded-[12px] bg-[linear-gradient(145deg,#2563eb_0%,#3b82f6_62%,#38bdf8_100%)] text-lg font-semibold text-white shadow-[0_10px_20px_rgba(37,99,235,0.2)]"
          >
            S
          </div>

          <div>
            <div class="text-[1.45rem] font-semibold leading-none tracking-tight text-slate-950">SpeakCoach</div>
            <div class="mt-1 text-xs text-slate-500">专业的 AI 口语陪练</div>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <div
            v-if="store.currentUser"
            class="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-2.5 py-1.5 shadow-sm"
          >
            <div class="flex h-8 w-8 items-center justify-center rounded-full bg-slate-950 text-[11px] font-semibold text-white">
              {{ initials }}
            </div>
            <div class="min-w-0">
              <div class="max-w-[8rem] truncate text-sm font-semibold text-slate-900">
                {{ displayName }}
              </div>
              <div class="max-w-[8rem] truncate text-[11px] text-slate-500">
                {{ store.currentUser.email }}
              </div>
            </div>
          </div>

          <button
            v-else
            class="rounded-full border border-slate-200 bg-white px-5 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
            @click="$emit('login')"
          >
            登录
          </button>

          <button
            class="rounded-full bg-[#142c83] px-6 py-2 text-sm font-semibold text-white shadow-[0_10px_18px_rgba(20,44,131,0.16)] transition hover:bg-[#10246e]"
            @click="$emit('start')"
          >
            {{ store.currentUser ? '继续练习' : '开始体验' }}
          </button>
        </div>
      </header>

      <main
        class="relative mx-auto grid min-h-0 w-full max-w-[1180px] flex-1 items-center justify-center gap-8 overflow-hidden bg-[linear-gradient(135deg,#fbfdff_0%,#f6f9ff_48%,#f8fbff_100%)] px-4 py-4 lg:grid-cols-[minmax(0,480px)_minmax(0,610px)]"
      >
        <div class="pointer-events-none absolute left-8 top-10 h-32 w-32 rounded-full bg-blue-500/[0.03] blur-3xl" />
        <div class="pointer-events-none absolute bottom-8 right-10 h-40 w-40 rounded-full bg-sky-300/[0.035] blur-3xl" />

        <section class="relative z-10 flex min-h-0 flex-col justify-center">
          <div>
            <div
              class="inline-flex rounded-full bg-blue-50 px-4 py-1.5 text-[10px] font-semibold uppercase tracking-[0.22em] text-blue-600"
            >
              English Speaking Coach
            </div>

            <h1
              class="mt-3 max-w-[15ch] text-[2.72rem] font-semibold leading-[1.03] tracking-[-0.045em] text-slate-950 xl:text-[3.18rem]"
            >
              用真实场景练开口，
              <br />
              <span class="text-[#3b82f6]">让英语对话更自然。</span>
            </h1>

            <p class="mt-4 max-w-[31rem] text-[14px] leading-7 text-slate-600">
              SpeakCoach 会根据场景、难度和你的表达继续追问，让你在面试、点餐、会议和自定义情境里反复练习。
            </p>

            <div class="mt-5 flex flex-wrap gap-3">
              <button
                class="rounded-full bg-[linear-gradient(135deg,#1d4ed8_0%,#2563eb_64%,#38bdf8_100%)] px-7 py-3 text-sm font-semibold text-white shadow-[0_12px_24px_rgba(37,99,235,0.16)] transition hover:-translate-y-0.5"
                @click="$emit('start')"
              >
                {{ store.currentUser ? '继续练习' : '开始体验' }}
              </button>

              <button
                v-if="!store.currentUser"
                class="rounded-full border border-slate-300 bg-white/90 px-7 py-3 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
                @click="$emit('login')"
              >
                登录账号
              </button>

              <div
                v-else
                class="flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-4 py-3 text-sm shadow-sm"
              >
                <span class="text-slate-500">当前账号</span>
                <span class="font-semibold text-slate-900">{{ displayName }}</span>
              </div>
            </div>
          </div>

          <article
            class="mt-5 max-w-[31.5rem] rounded-[18px] border border-slate-200/85 bg-white/[0.92] p-4 shadow-[0_10px_24px_rgba(15,23,42,0.04)] backdrop-blur"
          >
            <div class="flex items-center gap-2.5">
              <div
                class="flex h-7 w-7 items-center justify-center rounded-[9px] bg-[linear-gradient(145deg,#1d4ed8_0%,#38bdf8_100%)] text-xs font-semibold text-white"
              >
                S
              </div>
              <div class="text-sm font-semibold text-slate-900">SpeakCoach</div>
            </div>

            <div class="mt-3 space-y-2.5">
              <div class="flex items-center gap-3">
                <div
                  class="max-w-[17rem] rounded-[14px] bg-slate-100/90 px-4 py-2.5 text-[13px] leading-6 text-slate-800"
                >
                  Let's start! What's your goal for this conversation?
                </div>

                <div class="hidden items-center gap-[4px] lg:flex">
                  <span
                    v-for="(height, index) in compactWaveHeights"
                    :key="`compact-wave-${index}`"
                    class="block w-[3.5px] rounded-full bg-blue-500"
                    :style="{ height }"
                  />
                </div>
              </div>

              <div class="flex items-center justify-end gap-3">
                <div
                  class="max-w-[15.5rem] rounded-[14px] bg-blue-50 px-4 py-2.5 text-[13px] leading-6 text-slate-800"
                >
                  I want to practice for a job interview.
                </div>

                <div
                  class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[10px] font-semibold text-slate-600"
                >
                  YU
                </div>
              </div>

              <div class="flex items-center gap-3">
                <div
                  class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-50 text-[10px] font-semibold text-blue-600"
                >
                  AI
                </div>

                <div
                  class="max-w-[17rem] rounded-[14px] border border-slate-200 bg-white px-4 py-2.5 text-[13px] leading-6 text-slate-800"
                >
                  Great! Can you tell me about your previous experience?
                </div>

                <div class="ml-auto flex items-center gap-1 rounded-full bg-blue-50 px-3 py-1.5 text-blue-500">
                  <span class="h-1.5 w-1.5 rounded-full bg-current opacity-40" />
                  <span class="h-1.5 w-1.5 rounded-full bg-current opacity-70" />
                  <span class="h-1.5 w-1.5 rounded-full bg-current" />
                </div>
              </div>
            </div>
          </article>
        </section>

        <aside class="relative z-10 grid w-full min-h-0 grid-rows-3 gap-4 self-center lg:min-h-[560px] xl:min-h-[590px]">
          <article
            v-for="feature in features"
            :key="feature.title"
            class="grid min-h-0 items-center gap-5 rounded-[22px] border border-slate-200/85 bg-white/[0.92] px-6 py-5 shadow-[0_14px_34px_rgba(15,23,42,0.045)] backdrop-blur transition hover:-translate-y-0.5 hover:bg-white hover:shadow-[0_18px_38px_rgba(15,23,42,0.065)] md:grid-cols-[5rem_minmax(0,1fr)_8.4rem]"
          >
            <div
              class="flex h-16 w-16 items-center justify-center rounded-[18px] bg-[linear-gradient(180deg,#ffffff_0%,#eef5ff_100%)] shadow-[0_10px_20px_rgba(37,99,235,0.045)]"
            >
              <div
                class="flex h-12 w-12 items-center justify-center rounded-[15px] border border-blue-100 bg-white text-blue-600 shadow-sm"
              >
                <svg
                  v-if="feature.kind === 'list'"
                  class="h-7 w-7"
                  viewBox="0 0 32 32"
                  fill="none"
                  aria-hidden="true"
                >
                  <circle cx="10" cy="11" r="3.5" fill="currentColor" opacity="0.18" />
                  <circle cx="22" cy="11" r="3.5" fill="currentColor" opacity="0.18" />
                  <circle cx="16" cy="22" r="4.5" fill="currentColor" opacity="0.18" />
                  <circle cx="10" cy="11" r="3.5" stroke="currentColor" stroke-width="2" />
                  <circle cx="22" cy="11" r="3.5" stroke="currentColor" stroke-width="2" />
                  <circle cx="16" cy="22" r="4.5" stroke="currentColor" stroke-width="2" />
                </svg>

                <svg
                  v-else-if="feature.kind === 'wave'"
                  class="h-7 w-7"
                  viewBox="0 0 32 32"
                  fill="none"
                  aria-hidden="true"
                >
                  <rect x="11" y="5" width="10" height="16" rx="5" fill="currentColor" opacity="0.18" />
                  <rect x="11" y="5" width="10" height="16" rx="5" stroke="currentColor" stroke-width="2" />
                  <path
                    d="M7 14v1a9 9 0 0 0 18 0v-1M16 24v4M12 28h8"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                  />
                </svg>

                <svg
                  v-else
                  class="h-7 w-7"
                  viewBox="0 0 32 32"
                  fill="none"
                  aria-hidden="true"
                >
                  <rect x="8" y="7" width="16" height="19" rx="3" fill="currentColor" opacity="0.15" />
                  <rect x="8" y="7" width="16" height="19" rx="3" stroke="currentColor" stroke-width="2" />
                  <path
                    d="M12 14h8M12 19h5M21 5v5M11 5v5"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                  />
                  <path
                    d="M18 22l2 2 4-5"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </div>
            </div>

            <div>
              <div class="text-[1.55rem] font-semibold leading-tight tracking-[-0.035em] text-slate-950">
                {{ feature.title }}
              </div>
              <p class="mt-2 max-w-[20rem] text-[15px] leading-[1.85] text-slate-600">
                {{ feature.description }}
              </p>
            </div>

            <div class="flex items-center justify-center">
              <div
                v-if="feature.kind === 'list'"
                class="w-full max-w-[7.5rem] rounded-[17px] border border-blue-100 bg-[linear-gradient(180deg,#ffffff_0%,#f3f7ff_100%)] p-3 shadow-[0_10px_22px_rgba(37,99,235,0.06)]"
              >
                <div class="mb-2.5 flex items-center gap-1.5">
                  <span class="h-2 w-2 rounded-full bg-rose-300" />
                  <span class="h-2 w-2 rounded-full bg-amber-300" />
                  <span class="h-2 w-2 rounded-full bg-sky-300" />
                </div>

                <div class="space-y-2">
                  <div
                    v-for="item in ['面试', '点餐', '会议', '自定义']"
                    :key="item"
                    class="flex items-center gap-2 rounded-[10px] border border-blue-100 bg-white px-2.5 py-1.5 text-[12px] font-medium text-slate-700"
                  >
                    <span class="h-2 w-2 rounded-full bg-blue-500/80" />
                    {{ item }}
                  </div>
                </div>
              </div>

              <div v-else-if="feature.kind === 'wave'" class="flex items-center gap-[5px]">
                <span
                  v-for="(height, index) in featureWaveHeights"
                  :key="`feature-wave-${index}`"
                  class="block w-[4.5px] rounded-full bg-blue-500"
                  :style="{ height }"
                />
              </div>

              <div
                v-else
                class="relative flex h-[5.6rem] w-[5rem] items-center justify-center rounded-[18px] border border-blue-100 bg-[linear-gradient(180deg,#ffffff_0%,#f2f7ff_100%)] shadow-sm"
              >
                <div class="absolute -bottom-2 -right-2 flex h-9 w-9 items-center justify-center rounded-full bg-blue-500 text-white shadow-[0_8px_18px_rgba(37,99,235,0.22)]">
                  <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M6 12.5l3.5 3.5L18 7.5"
                      stroke="currentColor"
                      stroke-width="2.4"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </div>

                <div class="relative z-10 w-12 space-y-2">
                  <div class="h-2 rounded-full bg-blue-200" />
                  <div class="h-2 w-[85%] rounded-full bg-blue-300/80" />
                  <div class="h-2 rounded-full bg-blue-200" />
                  <div class="h-2 w-[70%] rounded-full bg-blue-300/80" />
                </div>
              </div>
            </div>
          </article>
        </aside>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { useAppStore } from '@/core/store'

defineEmits<{
  start: []
  login: []
}>()

const store = useAppStore()
const displayName = computed(() => store.currentUser?.name?.trim() || store.currentUser?.email?.trim() || '访客')
const initials = computed(() => displayName.value.slice(0, 2).toUpperCase())

const features = [
  {
    title: '场景对练',
    description: '支持面试、点餐、会议，也能输入你自己的对话背景。',
    kind: 'list',
  },
  {
    title: '实时语音',
    description: '录音后自动识别文本，再由 AI 按当前场景继续对话。',
    kind: 'wave',
  },
  {
    title: '课后反馈',
    description: '保留对话记录，给出发音、表达和纠错建议，方便你继续练习。',
    kind: 'report',
  },
] as const

const compactWaveHeights = ['8px', '13px', '17px', '10px', '21px', '13px', '8px', '15px']

const featureWaveHeights = ['10px', '18px', '28px', '38px', '26px', '18px', '10px', '18px', '28px', '38px', '26px', '18px', '10px']
</script>
