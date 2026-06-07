<template>
  <section class="min-h-screen px-4 py-4 lg:px-6 lg:py-6">
    <div
      class="relative min-h-[calc(100vh-2rem)] overflow-hidden rounded-[24px] border border-[color:var(--line-soft)] bg-[var(--surface-0)] shadow-[0_28px_80px_rgba(15,23,42,0.08)]"
    >
      <div
        class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.14),transparent_28%),radial-gradient(circle_at_top_right,rgba(34,197,94,0.08),transparent_24%),linear-gradient(180deg,rgba(255,255,255,0.6),rgba(248,250,252,0.86))]"
      />

      <div
        class="relative grid min-h-[calc(100vh-2rem)] gap-0 xl:grid-cols-[minmax(0,1fr)_24rem] 2xl:grid-cols-[minmax(0,1fr)_26rem]"
      >
        <div class="flex min-h-0 flex-col xl:border-r xl:border-[color:var(--line-soft)]">
          <header class="border-b border-[color:var(--line-soft)] px-6 py-5 lg:px-8">
            <div class="flex flex-wrap items-start justify-between gap-5">
              <div class="max-w-3xl">
                <div class="text-xs uppercase tracking-[0.22em] text-[var(--ink-4)]">Immersive Speaking Workspace</div>
                <h2 class="mt-2 text-3xl font-semibold tracking-tight text-[var(--ink-1)] lg:text-4xl">
                  {{ sceneTitle }}
                </h2>
                <div class="mt-4 flex flex-wrap items-center gap-2 text-sm text-[var(--ink-3)]">
                  <span class="rounded-full bg-slate-100 px-3 py-1">难度：{{ difficultyLabel }}</span>
                  <span
                    class="rounded-full px-3 py-1"
                    :class="store.sessionReady ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'"
                  >
                    {{ store.sessionReady ? '对话已连接' : '正在准备会话' }}
                  </span>
                  <span class="rounded-full bg-sky-50 px-3 py-1 text-sky-700">
                    {{ store.messages.length }} 条消息
                  </span>
                </div>
                <p
                  v-if="store.customBackground"
                  class="mt-4 max-w-3xl rounded-[16px] bg-[var(--surface-1)] px-4 py-3 text-sm leading-7 text-[var(--ink-3)]"
                >
                  {{ store.customBackground }}
                </p>
              </div>

              <div class="flex items-center gap-3">
                <div class="hidden rounded-[18px] bg-slate-950 px-4 py-3 text-sm font-medium text-white shadow-lg lg:block">
                  {{ audioStatusLabel }}
                </div>
                <button
                  class="rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
                  aria-label="结束当前对话"
                  @click="finishSession()"
                >
                  结束对话
                </button>
              </div>
            </div>
          </header>

          <div class="flex min-h-0 flex-1 flex-col">
            <div class="border-b border-[color:var(--line-soft)] px-6 py-4 lg:px-8">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div class="text-base font-semibold text-[var(--ink-2)]">实时对话区</div>
                  <div class="mt-1 text-sm text-[var(--ink-3)]">
                    你的发言和 AI 回复都会保留在这里，方便连续练习和回看上下文。
                  </div>
                </div>
                <div class="rounded-full bg-white px-3 py-1 text-xs font-medium text-[var(--ink-3)] shadow-sm">
                  主对话流
                </div>
              </div>
            </div>

            <div class="min-h-0 flex-1 px-4 py-4 lg:px-6 lg:py-5">
              <div
                ref="conversationScrollRef"
                aria-label="对话消息记录"
                class="flex h-full min-h-[24rem] flex-col gap-5 overflow-y-auto px-1 pb-2 pr-3 pt-1"
              >
                <template v-if="conversationMessages.length">
                  <div
                    v-for="message in conversationMessages"
                    :key="message.id"
                    class="flex"
                    :class="
                      message.role === 'user'
                        ? 'justify-end'
                        : message.role === 'assistant'
                          ? 'justify-start'
                          : 'justify-center'
                    "
                  >
                    <div class="max-w-[84%]">
                      <div
                        class="mb-2 flex items-center gap-2 px-1 text-[11px] font-semibold uppercase tracking-[0.16em]"
                        :class="
                          message.role === 'user'
                            ? 'justify-end text-sky-700'
                            : message.role === 'assistant'
                              ? 'text-slate-500'
                              : 'justify-center text-slate-400'
                        "
                      >
                        <span>{{ message.role === 'user' ? 'You' : message.role === 'assistant' ? 'AI Coach' : 'System' }}</span>
                        <span
                          v-if="message.state === 'streaming' && message.role !== 'system'"
                          class="rounded-full bg-[var(--surface-1)] px-2 py-0.5 text-[10px] normal-case tracking-normal text-[var(--ink-3)]"
                        >
                          识别中
                        </span>
                      </div>
                      <div class="rounded-[18px] px-5 py-4 text-sm leading-8" :class="messageBubbleClass(message.role)">
                        {{ message.text || '...' }}
                      </div>
                    </div>
                  </div>
                </template>

                <div v-else class="flex flex-1 items-center justify-center">
                  <div class="max-w-lg text-center">
                    <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-[20px] bg-[var(--surface-accent)] text-4xl">
                      🎤
                    </div>
                    <div class="mt-5 text-2xl font-semibold text-[var(--ink-1)]">开始你的第一轮真实对话</div>
                    <p class="mt-3 text-sm leading-8 text-[var(--ink-3)]">
                      点击底部开始录音，或者先用模拟模式测试。识别文本和 AI 回复会实时出现在这个对话区里。
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div class="border-t border-[color:var(--line-soft)] px-4 pb-4 pt-3 lg:px-6 lg:pb-6">
              <div
                class="grid gap-4 rounded-[18px] bg-[linear-gradient(145deg,#0f172a_0%,#1d4ed8_58%,#38bdf8_100%)] p-5 text-white shadow-[0_24px_60px_rgba(29,78,216,0.18)] lg:grid-cols-[minmax(0,1fr)_18rem]"
              >
                <div class="flex flex-wrap items-center gap-4">
                  <button
                    class="flex h-20 w-20 items-center justify-center rounded-full bg-white/14 text-4xl shadow-[0_20px_45px_rgba(15,23,42,0.25)] transition hover:scale-[1.02]"
                    :aria-label="store.isRecording ? '结束录音' : '开始录音'"
                    :aria-pressed="store.isRecording"
                    @click="toggleRecording()"
                  >
                    {{ store.isRecording ? '■' : '🎙' }}
                  </button>

                  <div class="min-w-0 flex-1">
                    <div class="text-lg font-semibold">
                      {{ store.isRecording ? '点击结束录音' : '点击开始录音' }}
                    </div>
                    <div class="mt-2 max-w-2xl text-sm leading-7 text-sky-50/84">
                      {{
                        recordingSupported
                          ? '使用真实麦克风上传英语语音，系统会自动识别并继续对话。'
                          : '当前浏览器不支持录音，可以先使用模拟模式验证完整流程。'
                      }}
                    </div>

                    <div class="mt-4 flex flex-wrap items-center gap-3">
                      <button
                        class="rounded-full border border-white/30 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/10"
                        aria-label="使用模拟模式开始一轮对话"
                        @click="runMockTurn()"
                      >
                        使用模拟模式
                      </button>
                      <div class="rounded-full bg-white/12 px-3 py-1 text-xs text-sky-50/80">
                        {{ store.aiReplyText ? 'AI 已回复，可以继续下一轮' : '等待新的语音输入' }}
                      </div>
                    </div>
                  </div>
                </div>

                <div class="rounded-[14px] bg-white/10 p-4 text-xs text-sky-50/82">
                  <div class="font-semibold text-white">录音调试信息</div>
                  <div class="mt-3 grid gap-2 sm:grid-cols-2">
                    <div>AudioContext: {{ debugInfo.audioContextState }}</div>
                    <div>Sample Rate: {{ debugInfo.sampleRate || '--' }}</div>
                    <div>Chunks: {{ debugInfo.chunkCount }}</div>
                    <div>Samples: {{ debugInfo.capturedSamples }}</div>
                    <div>Peak: {{ debugInfo.peakLevel.toFixed(4) }}</div>
                    <div>Sent Bytes: {{ debugInfo.sentBytes || '--' }}</div>
                    <div class="sm:col-span-2">Encoding: {{ debugInfo.lastEncoding || '--' }}</div>
                  </div>
                </div>
              </div>

              <div v-if="errorMessage" class="mt-3 rounded-[16px] bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {{ errorMessage }}
              </div>
            </div>
          </div>
        </div>

        <aside class="border-t border-[color:var(--line-soft)] bg-[var(--surface-2)]/60 p-3 xl:border-l xl:border-t-0 xl:p-4">
          <div class="sticky top-4 overflow-hidden rounded-[20px] border border-[color:var(--line-soft)] bg-[var(--surface-1)] shadow-[var(--shadow-soft)]">
            <div class="border-b border-[color:var(--line-soft)] px-5 py-5">
              <div class="text-sm font-semibold text-[var(--ink-2)]">分析侧边栏</div>
              <p class="mt-2 text-sm leading-7 text-[var(--ink-3)]">
                发音反馈、表达优化和当前轮次摘要都在这里，让对话区保持更干净的主舞台节奏。
              </p>
            </div>

            <section class="px-5 py-5">
              <PronScoreBar :score="store.currentPronScore" />
            </section>

            <section class="border-t border-[color:var(--line-soft)] px-5 py-5">
              <div class="text-sm font-semibold text-[var(--ink-2)]">即时概览</div>
              <div class="mt-4 space-y-4 text-sm text-[var(--ink-3)]">
                <div>
                  <div class="text-xs uppercase tracking-[0.14em] text-[var(--ink-4)]">最新识别文本</div>
                  <div class="mt-2 leading-7">{{ store.asrText || '还没有识别文本。' }}</div>
                </div>
                <div class="h-px bg-[var(--line-soft)]" />
                <div>
                  <div class="text-xs uppercase tracking-[0.14em] text-[var(--ink-4)]">最新 AI 回复</div>
                  <div class="mt-2 leading-7">{{ store.aiReplyText || 'AI 回复生成后会显示在这里。' }}</div>
                </div>
              </div>
            </section>

            <section class="border-t border-[color:var(--line-soft)] px-5 py-5">
              <slot name="correction" />
            </section>
          </div>
        </aside>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

import { SCENES } from '@/core/scenes'
import { useAppStore } from '@/core/store'
import type { ConversationMessage } from '@/core/types'
import { ws } from '@/core/ws'

import PronScoreBar from './PronScoreBar.vue'
import { useConversation } from './useConversation'

const store = useAppStore()
const {
  debugInfo,
  errorMessage,
  finishCurrentSession,
  handleServerMessage,
  recordingSupported,
  runMockTurn,
  startRecording,
  stopRecording,
} = useConversation()

let unsubscribe: (() => void) | null = null
const conversationScrollRef = ref<HTMLElement | null>(null)

const difficultyMap = {
  1: '入门',
  2: '进阶',
  3: '困难',
} as const

const sceneTitle = computed(() => {
  if (!store.sceneId) return 'Conversation'
  return SCENES[store.sceneId]?.name_zh ?? store.sceneId
})

const difficultyLabel = computed(() => difficultyMap[store.difficulty] ?? '入门')
const conversationMessages = computed<ConversationMessage[]>(() => store.messages)

const audioStatusLabel = computed(() => {
  if (store.isSpeaking) return 'AI 正在播放语音'
  if (store.isReplyAudioPending) return 'AI 正在生成回复'
  if (store.isRecording) return '正在录音'
  return '等待下一轮输入'
})

function messageBubbleClass(role: ConversationMessage['role']) {
  if (role === 'user') {
    return 'bg-[linear-gradient(135deg,#2563eb_0%,#38bdf8_100%)] text-white'
  }
  if (role === 'assistant') {
    return 'bg-[var(--surface-accent)] text-[var(--ink-2)]'
  }
  return 'bg-slate-100 text-[var(--ink-3)]'
}

function isConversationNearBottom() {
  const container = conversationScrollRef.value
  if (!container) return false
  const threshold = 96
  return container.scrollHeight - container.scrollTop - container.clientHeight <= threshold
}

function scrollConversationToBottom(force = false) {
  const container = conversationScrollRef.value
  if (!container) return
  if (!force && !isConversationNearBottom()) return
  container.scrollTop = container.scrollHeight
}

async function finishSession() {
  await finishCurrentSession()
}

async function toggleRecording() {
  if (store.isRecording) {
    await stopRecording()
    return
  }
  await startRecording()
}

watch(
  () => store.messages.length,
  async () => {
    await nextTick()
    scrollConversationToBottom(true)
  },
)

watch(
  () => [store.asrText, store.aiReplyText],
  async () => {
    await nextTick()
    scrollConversationToBottom(false)
  },
)

onMounted(() => {
  unsubscribe = ws.onMessage(handleServerMessage)
  void nextTick().then(() => scrollConversationToBottom(true))
})

onUnmounted(() => {
  unsubscribe?.()
})
</script>
