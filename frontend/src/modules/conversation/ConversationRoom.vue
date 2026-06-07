<template>
  <section class="h-[100dvh] overflow-hidden px-4 py-4 lg:px-6 lg:py-6">
    <div
      class="relative h-[calc(100dvh-2rem)] overflow-hidden rounded-[24px] border border-[color:var(--line-soft)] bg-[var(--surface-0)] shadow-[0_28px_80px_rgba(15,23,42,0.08)] lg:h-[calc(100dvh-3rem)]"
    >
      <div
        class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.14),transparent_28%),radial-gradient(circle_at_top_right,rgba(34,197,94,0.08),transparent_24%),linear-gradient(180deg,rgba(255,255,255,0.68),rgba(248,250,252,0.92))]"
      />

      <div class="relative grid h-full grid-rows-[auto_auto] overflow-y-auto xl:grid-cols-[minmax(0,1fr)_24rem] xl:grid-rows-none xl:overflow-hidden 2xl:grid-cols-[minmax(0,1fr)_26rem]">
        <div class="flex h-full min-h-0 flex-col xl:border-r xl:border-[color:var(--line-soft)]">
          <header class="shrink-0 border-b border-[color:var(--line-soft)] px-6 py-5 lg:px-8">
            <div class="flex flex-wrap items-start justify-between gap-5">
              <div class="max-w-3xl">
                <div class="text-xs uppercase tracking-[0.22em] text-[var(--ink-4)]">Workspace</div>
                <h2 class="mt-2 text-3xl font-semibold tracking-tight text-[var(--ink-1)] lg:text-4xl">
                  {{ sceneTitle }}
                </h2>
                <div class="mt-4 flex flex-wrap items-center gap-2 text-sm text-[var(--ink-3)]">
                  <span class="rounded-full bg-slate-100 px-3 py-1">难度：{{ difficultyLabel }}</span>
                  <span
                    class="rounded-full px-3 py-1"
                    :class="store.sessionReady ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'"
                  >
                    {{ store.sessionReady ? '已连接' : '准备中' }}
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
                <UserAccountBadge />
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

          <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
            <div class="shrink-0 border-b border-[color:var(--line-soft)] px-6 py-4 lg:px-8">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div class="text-base font-semibold text-[var(--ink-2)]">对话区</div>
                  <div class="mt-1 text-sm text-[var(--ink-3)]">你的发言和 AI 回复都会显示在这里。</div>
                </div>
                <div class="rounded-full bg-white px-3 py-1 text-xs font-medium text-[var(--ink-3)] shadow-sm">
                  主对话流
                </div>
              </div>
            </div>

            <div class="flex-1 overflow-hidden px-4 py-4 lg:px-6 lg:py-5 xl:min-h-0">
              <div
                ref="conversationScrollRef"
                aria-label="对话消息记录"
                class="conversation-panel flex h-[clamp(24rem,52vh,40rem)] min-h-0 flex-col gap-5 overflow-y-auto rounded-[20px] border border-[color:var(--line-soft)] px-4 pb-4 pt-4 xl:h-full"
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
                          class="rounded-full bg-white/70 px-2 py-0.5 text-[10px] normal-case tracking-normal text-[var(--ink-3)]"
                        >
                          识别中
                        </span>
                      </div>
                      <div class="rounded-[18px] px-5 py-4 text-sm leading-8 shadow-sm" :class="messageBubbleClass(message.role)">
                        {{ message.text || '...' }}
                      </div>
                    </div>
                  </div>
                </template>

                <div v-else class="flex flex-1 items-center justify-center">
                  <div class="max-w-lg text-center">
                    <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-[20px] bg-white/80 text-4xl shadow-sm">
                      🎙
                    </div>
                    <div class="mt-5 text-2xl font-semibold text-[var(--ink-1)]">开始第一轮对话</div>
                    <p class="mt-3 text-sm leading-8 text-[var(--ink-3)]">
                      点击下方开始说话，系统会识别你的英文并继续陪练。
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div class="shrink-0 border-t border-[color:var(--line-soft)] px-4 pb-4 pt-3 lg:px-6 lg:pb-6">
              <div class="recording-stage rounded-[22px] p-[1px] shadow-[0_20px_55px_rgba(37,99,235,0.16)]">
                <div class="rounded-[21px] px-5 py-5 text-white lg:px-6 lg:py-6">
                  <div class="flex flex-wrap items-center justify-between gap-4">
                    <div class="flex min-w-0 items-center gap-4">
                      <button
                        class="flex h-20 w-20 shrink-0 items-center justify-center rounded-full border border-white/12 bg-white/12 text-4xl shadow-[0_20px_45px_rgba(15,23,42,0.22)] transition hover:scale-[1.02]"
                        :aria-label="store.isRecording ? '结束说话' : '开始说话'"
                        :aria-pressed="store.isRecording"
                        @click="toggleRecording()"
                      >
                        {{ store.isRecording ? '■' : '🎙' }}
                      </button>

                      <div class="min-w-0">
                        <div class="text-lg font-semibold">
                          {{ store.isRecording ? '点击结束说话' : '点击开始说话' }}
                        </div>
                        <div class="mt-2 max-w-2xl text-sm leading-7 text-sky-50/88">
                          {{ recordingSupported ? '上传真实语音后，系统会自动识别并给出继续追问。' : '当前浏览器不支持录音，请更换浏览器后再试。' }}
                        </div>
                      </div>
                    </div>

                    <div class="flex items-center gap-2">
                      <div
                        class="rounded-full px-3 py-1 text-xs font-medium"
                        :class="store.isRecording ? 'bg-rose-500/20 text-rose-50' : 'bg-white/12 text-sky-50/85'"
                      >
                        {{ store.isRecording ? '正在收音' : '等待输入' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="errorMessage" class="mt-3 rounded-[16px] bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {{ errorMessage }}
              </div>
            </div>
          </div>
        </div>

        <aside class="border-t border-[color:var(--line-soft)] bg-[var(--surface-2)]/60 p-3 xl:h-full xl:overflow-y-auto xl:border-l xl:border-t-0 xl:p-4">
          <div class="sticky top-4 overflow-hidden rounded-[20px] border border-[color:var(--line-soft)] bg-[var(--surface-1)] shadow-[var(--shadow-soft)]">
            <div class="border-b border-[color:var(--line-soft)] px-5 py-5">
              <div class="text-sm font-semibold text-[var(--ink-2)]">分析栏</div>
              <p class="mt-2 text-sm leading-7 text-[var(--ink-3)]">
                发音、纠错和本轮摘要都在这里。
              </p>
            </div>

            <section class="px-5 py-5">
              <PronScoreBar :score="store.currentPronScore" />
            </section>

            <section class="border-t border-[color:var(--line-soft)] px-5 py-5">
              <div class="text-sm font-semibold text-[var(--ink-2)]">即时概览</div>
              <div class="mt-4 space-y-4 text-sm text-[var(--ink-3)]">
                <div>
                  <div class="text-xs uppercase tracking-[0.14em] text-[var(--ink-4)]">最新识别</div>
                  <div class="mt-2 leading-7">{{ store.asrText || '还没有文本。' }}</div>
                </div>
                <div class="h-px bg-[var(--line-soft)]" />
                <div>
                  <div class="text-xs uppercase tracking-[0.14em] text-[var(--ink-4)]">最新回复</div>
                  <div class="mt-2 leading-7">{{ store.aiReplyText || 'AI 回复会显示在这里。' }}</div>
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
import UserAccountBadge from '@/modules/auth/UserAccountBadge.vue'

import PronScoreBar from './PronScoreBar.vue'
import { useConversation } from './useConversation'

const store = useAppStore()
const { errorMessage, finishCurrentSession, handleServerMessage, recordingSupported, startRecording, stopRecording } = useConversation()

let unsubscribe: (() => void) | null = null
const conversationScrollRef = ref<HTMLElement | null>(null)

const difficultyMap = { 1: '入门', 2: '进阶', 3: '困难' } as const

const sceneTitle = computed(() => {
  if (!store.sceneId) return 'Conversation'
  return SCENES[store.sceneId]?.name_zh ?? store.sceneId
})

const difficultyLabel = computed(() => difficultyMap[store.difficulty] ?? '入门')
const conversationMessages = computed<ConversationMessage[]>(() => store.messages)

const audioStatusLabel = computed(() => {
  if (store.isSpeaking) return 'AI 播放中'
  if (store.isReplyAudioPending) return 'AI 回复中'
  if (store.isRecording) return '录音中'
  return '等待输入'
})

function messageBubbleClass(role: ConversationMessage['role']) {
  if (role === 'user') return 'bg-[linear-gradient(135deg,#2563eb_0%,#38bdf8_100%)] text-white'
  if (role === 'assistant') return 'bg-[rgba(255,255,255,0.82)] text-[var(--ink-2)]'
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

<style scoped>
.conversation-panel {
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.12), transparent 24%),
    radial-gradient(circle at bottom left, rgba(125, 211, 252, 0.16), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.8), rgba(248, 250, 252, 0.92));
}

.recording-stage {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(29, 78, 216, 0.94) 55%, rgba(56, 189, 248, 0.94));
}
</style>
