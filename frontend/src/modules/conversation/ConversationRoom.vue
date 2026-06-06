<template>
  <section class="mx-auto max-w-7xl px-6 py-8 lg:px-10">
    <div class="grid gap-6 xl:grid-cols-[1.7fr_0.85fr]">
      <div class="space-y-6">
        <div class="overflow-hidden rounded-[32px] border border-white/80 bg-white/90 shadow-[0_24px_70px_rgba(15,23,42,0.08)]">
          <div class="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-6 py-5">
            <div>
              <div class="text-xs uppercase tracking-[0.16em] text-slate-400">Conversation Scaffold</div>
              <h2 class="mt-2 text-3xl font-semibold capitalize text-slate-900">{{ store.sceneId }}</h2>
            </div>
            <div class="flex items-center gap-3">
              <div class="rounded-full bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-600">
                {{ store.sessionReady ? '对话已连接' : '准备中' }}
              </div>
              <button
                class="rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
                @click="finishSession()"
              >
                结束对话
              </button>
            </div>
          </div>

          <div class="grid gap-6 px-6 py-6 lg:grid-cols-[1.4fr_0.8fr]">
            <div class="space-y-5">
              <div class="rounded-[28px] bg-gradient-to-r from-indigo-50 via-white to-sky-50 px-5 py-4 text-sm text-slate-500">
                当前版本支持真实录音分片上传；如果浏览器或配置未准备好，你也可以继续用模拟模式验证主链路。
              </div>

              <div class="space-y-4">
                <div class="rounded-[26px] border border-slate-100 bg-slate-50/80 p-5">
                  <div class="flex items-center justify-between gap-4">
                    <div>
                      <div class="text-xs uppercase tracking-[0.14em] text-slate-400">ASR Text</div>
                      <div class="mt-3 text-base leading-7 text-slate-800">
                        {{ store.asrText || '还没有识别文本，点击下方按钮开始一轮真实录音或模拟输入。' }}
                      </div>
                    </div>
                    <div class="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-400 shadow-sm">
                      {{ store.currentTurnId ? '识别中 / 已完成' : '待开始' }}
                    </div>
                  </div>
                </div>

                <div class="rounded-[26px] border border-indigo-100 bg-white p-5 shadow-sm">
                  <div class="flex items-center justify-between gap-4">
                    <div>
                      <div class="text-xs uppercase tracking-[0.14em] text-slate-400">AI Reply</div>
                      <div class="mt-3 text-base leading-7 text-slate-800">
                        {{ store.aiReplyText || 'Reply placeholder.' }}
                      </div>
                    </div>
                    <div class="flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-600">
                      <span class="inline-block h-2 w-2 rounded-full" :class="store.isSpeaking ? 'bg-emerald-500' : 'bg-indigo-300'" />
                      {{ store.isSpeaking ? 'AI 正在播放' : '等待回复' }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="flex flex-col items-center gap-4 rounded-[28px] border border-slate-100 bg-white px-6 py-7 shadow-sm">
                <button
                  class="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-blue-500 text-3xl text-white shadow-[0_18px_40px_rgba(84,108,255,0.3)] transition hover:scale-[1.02]"
                  @click="toggleRecording()"
                >
                  {{ store.isRecording ? '■' : '🎙' }}
                </button>
                <div class="text-center">
                  <div class="text-sm font-semibold text-slate-900">
                    {{ store.isRecording ? '点击结束录音' : '点击开始录音' }}
                  </div>
                  <div class="mt-1 text-xs text-slate-400">
                    {{ recordingSupported ? '使用真实麦克风进行语音上传' : '当前浏览器不支持录音，请使用模拟模式' }}
                  </div>
                </div>
                <button
                  class="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                  @click="runMockTurn()"
                >
                  使用模拟模式
                </button>
                <div class="w-full rounded-2xl bg-slate-50 p-4 text-left text-xs text-slate-500">
                  <div class="font-semibold text-slate-700">录音调试信息</div>
                  <div class="mt-2 grid gap-1 sm:grid-cols-2">
                    <div>AudioContext: {{ debugInfo.audioContextState }}</div>
                    <div>Sample Rate: {{ debugInfo.sampleRate || '--' }}</div>
                    <div>Chunks: {{ debugInfo.chunkCount }}</div>
                    <div>Samples: {{ debugInfo.capturedSamples }}</div>
                    <div>Peak: {{ debugInfo.peakLevel.toFixed(4) }}</div>
                    <div>Sent Bytes: {{ debugInfo.sentBytes || '--' }}</div>
                    <div class="sm:col-span-2">Encoding: {{ debugInfo.lastEncoding || '--' }}</div>
                  </div>
                </div>
                <div v-if="errorMessage" class="rounded-full bg-rose-50 px-4 py-2 text-sm text-rose-700">
                  {{ errorMessage }}
                </div>
              </div>
            </div>

            <div class="space-y-5">
              <PronScoreBar :score="store.currentPronScore" />
            </div>
          </div>
        </div>
      </div>

      <aside class="space-y-5">
        <slot name="correction" />
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import { useAppStore } from '@/core/store'
import { ws } from '@/core/ws'

import PronScoreBar from './PronScoreBar.vue'
import { useConversation } from './useConversation'

const store = useAppStore()
const { debugInfo, errorMessage, finishCurrentSession, handleServerMessage, recordingSupported, runMockTurn, startRecording, stopRecording } =
  useConversation()
let unsubscribe: (() => void) | null = null

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

onMounted(() => {
  unsubscribe = ws.onMessage(handleServerMessage)
})

onUnmounted(() => {
  unsubscribe?.()
})
</script>
