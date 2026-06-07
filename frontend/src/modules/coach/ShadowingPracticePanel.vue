<template>
  <section class="rounded-[28px] bg-white px-6 py-6 shadow-sm">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div class="text-xs uppercase tracking-[0.18em] text-sky-500">Shadowing Lab</div>
        <h3 class="mt-2 text-xl font-semibold text-slate-950">跟读训练</h3>
        <p class="mt-2 max-w-3xl text-sm leading-7 text-slate-500">
          从本次对话中挑 3 句关键表达，先听标准句，再录音跟读，系统会对相似度、重音、语调、连读和停顿给出反馈。
        </p>
      </div>
      <div class="rounded-full bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-700">
        {{ completedCount }}/{{ items.length || 3 }} 已完成
      </div>
    </div>

    <div v-if="loading" class="mt-5 rounded-[18px] bg-slate-50 px-4 py-5 text-sm text-slate-500">
      正在准备跟读句...
    </div>

    <div v-else-if="items.length === 0" class="mt-5 rounded-[18px] bg-amber-50 px-4 py-5 text-sm leading-7 text-amber-700">
      暂时没有可跟读的句子。完成至少一轮对话并生成纠错后，这里会自动出现训练内容。
    </div>

    <div v-else class="mt-5 grid gap-4 xl:grid-cols-3">
      <article
        v-for="(item, index) in items"
        :key="item.id"
        class="flex min-h-[31rem] flex-col rounded-[22px] border border-slate-100 bg-slate-50/75 px-5 py-5"
      >
        <div class="flex items-start justify-between gap-3">
          <div>
            <div class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Sentence {{ index + 1 }}</div>
            <div class="mt-2 text-sm font-semibold text-sky-700">{{ item.note || sourceLabel(item.source) }}</div>
          </div>
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-sm font-semibold text-slate-700 shadow-sm">
            {{ index + 1 }}
          </div>
        </div>

        <p class="mt-5 min-h-[6rem] text-base font-semibold leading-8 text-slate-900">
          {{ item.text }}
        </p>

        <div v-if="item.focus_words.length" class="mt-3 flex flex-wrap gap-2">
          <span
            v-for="word in item.focus_words"
            :key="`${item.id}-${word}`"
            class="rounded-full bg-white px-3 py-1 text-xs font-semibold text-rose-600"
          >
            {{ word }}
          </span>
        </div>

        <div class="mt-5 grid gap-2 sm:grid-cols-2">
          <button
            class="rounded-full border border-sky-200 bg-white px-4 py-2 text-sm font-semibold text-sky-700 transition hover:bg-sky-50 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="playingId === item.id || assessingId === item.id"
            :aria-label="`播放标准句 ${index + 1}`"
            @click="playStandard(item)"
          >
            {{ playingId === item.id ? '播放中' : '播放标准句' }}
          </button>
          <button
            class="rounded-full px-4 py-2 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60"
            :class="recordingId === item.id ? 'bg-rose-600 hover:bg-rose-500' : 'bg-slate-950 hover:bg-slate-800'"
            :disabled="assessingId === item.id || (recordingId !== null && recordingId !== item.id)"
            :aria-label="recordingId === item.id ? `结束跟读录音 ${index + 1}` : `开始跟读录音 ${index + 1}`"
            @click="toggleRecording(item)"
          >
            {{ recordingId === item.id ? '结束录音' : '开始跟读' }}
          </button>
        </div>

        <div v-if="assessingId === item.id" class="mt-4 rounded-[16px] bg-white px-4 py-3 text-sm text-slate-500">
          正在分析跟读表现...
        </div>

        <div v-if="results[item.id]" class="mt-5 flex-1 rounded-[18px] bg-white px-4 py-4">
          <div class="flex items-end justify-between gap-3">
            <div>
              <div class="text-xs uppercase tracking-[0.14em] text-slate-400">Similarity</div>
              <div class="mt-1 text-3xl font-semibold text-slate-950">
                {{ Math.round(results[item.id].similarity_score) }}
              </div>
            </div>
            <div class="text-right text-xs font-medium text-slate-400">/100</div>
          </div>

          <div class="mt-4 space-y-3">
            <div v-for="metric in metricRows(results[item.id])" :key="metric.label">
              <div class="flex justify-between text-xs font-medium text-slate-500">
                <span>{{ metric.label }}</span>
                <span>{{ Math.round(metric.value) }}</span>
              </div>
              <div class="mt-1 h-2 rounded-full bg-slate-100">
                <div class="h-2 rounded-full bg-sky-500" :style="{ width: `${scorePercent(metric.value)}%` }" />
              </div>
            </div>
          </div>

          <div v-if="results[item.id].weak_words.length" class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="word in results[item.id].weak_words"
              :key="`${item.id}-${word.word}-${word.accuracy_score}`"
              class="rounded-full bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-600"
            >
              {{ word.word }} · {{ Math.round(word.accuracy_score) }}
            </span>
          </div>

          <div class="mt-4 space-y-2 text-sm leading-6 text-slate-500">
            <div v-for="tip in results[item.id].tips" :key="`${item.id}-${tip}`">
              {{ tip }}
            </div>
          </div>
        </div>
      </article>
    </div>

    <div v-if="panelError" class="mt-4 rounded-[16px] bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {{ panelError }}
    </div>
  </section>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'

import { blobToBase64, encodeWav, getAudioContextCtor, getAudioMimeType, mergeFloat32Chunks } from '@/core/audio'
import { useAppStore } from '@/core/store'
import type {
  ShadowingAssessmentResponse,
  ShadowingItem,
  ShadowingItemsResponse,
  ShadowingTtsResponse,
  SessionSummaryResponse,
} from '@/core/types'

const props = defineProps<{
  sessionId: string
  summary: SessionSummaryResponse
}>()

const store = useAppStore()
const items = ref<ShadowingItem[]>([])
const loading = ref(false)
const panelError = ref('')
const playingId = ref<string | null>(null)
const recordingId = ref<string | null>(null)
const assessingId = ref<string | null>(null)
const results = reactive<Record<string, ShadowingAssessmentResponse>>({})
const ttsCache = reactive<Record<string, ShadowingTtsResponse>>({})

let activeAudio: HTMLAudioElement | null = null
let mediaStream: MediaStream | null = null
let audioContext: AudioContext | null = null
let sourceNode: MediaStreamAudioSourceNode | null = null
let processorNode: ScriptProcessorNode | null = null
let muteNode: GainNode | null = null
let recordedChunks: Float32Array[] = []
let recordedSampleRate = 16000

const recordingSupported = computed(() => {
  return typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && !!getAudioContextCtor()
})

const completedCount = computed(() => Object.keys(results).length)

function authHeaders() {
  return store.authToken
    ? {
        Authorization: `Bearer ${store.authToken}`,
      }
    : undefined
}

async function loadItems() {
  loading.value = true
  panelError.value = ''
  clearRecord(results)
  clearRecord(ttsCache)
  try {
    const response = await axios.get<ShadowingItemsResponse>(`/api/sessions/${props.sessionId}/shadowing/items`, {
      headers: authHeaders(),
    })
    items.value = response.data.items.length ? response.data.items : fallbackItems()
  } catch {
    items.value = fallbackItems()
    if (!items.value.length) {
      panelError.value = '跟读句获取失败，请确认后端已启动并且当前登录用户拥有这场会话。'
    }
  } finally {
    loading.value = false
  }
}

function clearRecord<T>(record: Record<string, T>) {
  Object.keys(record).forEach((key) => {
    delete record[key]
  })
}

function fallbackItems(): ShadowingItem[] {
  return props.summary.turns
    .map((turn, index) => ({
      id: `${turn.turn_id}-fallback`,
      text: turn.sample_answer || turn.user_text,
      source_turn_id: turn.turn_id,
      source: 'sample_answer' as const,
      focus_words: turn.pron_score.words
        .filter((word) => word.word.trim().toLowerCase() !== 'sil' && word.accuracy_score < 80)
        .map((word) => word.word)
        .slice(0, 3),
      note: `第 ${index + 1} 轮你的表达升级`,
    }))
    .filter((item) => item.text.split(/\s+/).length >= 4)
    .slice(0, 3)
}

async function playStandard(item: ShadowingItem) {
  panelError.value = ''
  stopPlaying()
  try {
    if (!ttsCache[item.id]) {
      const response = await axios.post<ShadowingTtsResponse>(
        '/api/shadowing/tts',
        {
          text: item.text,
        },
        {
          headers: authHeaders(),
        },
      )
      ttsCache[item.id] = response.data
    }
    const audioPayload = ttsCache[item.id]
    const audio = new Audio(`data:${getAudioMimeType(audioPayload.audio_format)};base64,${audioPayload.data}`)
    activeAudio = audio
    playingId.value = item.id
    audio.onended = stopPlaying
    audio.onerror = stopPlaying
    const playPromise = audio.play()
    if (playPromise) {
      await playPromise.catch(() => {
        panelError.value = '标准句播放失败，请重试。'
        stopPlaying()
      })
    }
  } catch {
    panelError.value = '标准句生成失败，请检查 TTS 配置。'
    stopPlaying()
  }
}

function stopPlaying() {
  if (activeAudio) {
    activeAudio.pause()
    activeAudio.src = ''
  }
  activeAudio = null
  playingId.value = null
}

async function toggleRecording(item: ShadowingItem) {
  if (recordingId.value === item.id) {
    await stopRecording(item)
    return
  }
  await startRecording(item)
}

async function startRecording(item: ShadowingItem) {
  panelError.value = ''
  if (!recordingSupported.value) {
    panelError.value = '当前浏览器不支持录音，请换用 Chrome/Edge 后再试。'
    return
  }

  stopPlaying()
  cleanupRecorder()
  recordedChunks = []

  try {
    const AudioContextCtor = getAudioContextCtor()
    if (!AudioContextCtor) {
      panelError.value = '当前浏览器不支持 AudioContext。'
      return
    }

    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioContext = new AudioContextCtor()
    await audioContext.resume()
    recordedSampleRate = audioContext.sampleRate
    sourceNode = audioContext.createMediaStreamSource(mediaStream)
    processorNode = audioContext.createScriptProcessor(4096, 1, 1)
    muteNode = audioContext.createGain()
    muteNode.gain.value = 0

    processorNode.onaudioprocess = (event: AudioProcessingEvent) => {
      recordedChunks.push(new Float32Array(event.inputBuffer.getChannelData(0)))
    }

    sourceNode.connect(processorNode)
    processorNode.connect(muteNode)
    muteNode.connect(audioContext.destination)
    recordingId.value = item.id
  } catch {
    panelError.value = '无法访问麦克风，请检查浏览器权限。'
    cleanupRecorder()
  }
}

async function stopRecording(item: ShadowingItem) {
  if (recordingId.value !== item.id) return
  recordingId.value = null

  if (!recordedChunks.length) {
    panelError.value = '没有采集到录音数据，请重试。'
    cleanupRecorder()
    return
  }

  assessingId.value = item.id
  try {
    const wavBlob = encodeWav(mergeFloat32Chunks(recordedChunks), recordedSampleRate)
    const audioB64 = await blobToBase64(wavBlob)
    const response = await axios.post<ShadowingAssessmentResponse>(
      `/api/sessions/${props.sessionId}/shadowing/assess`,
      {
        item_id: item.id,
        text: item.text,
        audio_b64: audioB64,
        audio_format: 'wav_pcm16',
      },
      {
        headers: authHeaders(),
      },
    )
    results[item.id] = response.data
  } catch {
    panelError.value = '跟读评测失败，请确认发音评测 API 已配置。'
  } finally {
    assessingId.value = null
    cleanupRecorder()
  }
}

function cleanupRecorder() {
  processorNode?.disconnect()
  sourceNode?.disconnect()
  muteNode?.disconnect()
  if (audioContext) {
    void audioContext.close()
  }
  mediaStream?.getTracks().forEach((track) => track.stop())
  mediaStream = null
  audioContext = null
  sourceNode = null
  processorNode = null
  muteNode = null
  recordedChunks = []
}

function sourceLabel(source: ShadowingItem['source']) {
  if (source === 'user_sentence') return '原句复练'
  return '你的表达升级'
}

function metricRows(result: ShadowingAssessmentResponse) {
  return [
    { label: '重音', value: result.stress_score },
    { label: '语调', value: result.intonation_score },
    { label: '连读', value: result.liaison_score },
    { label: '停顿', value: result.pause_score },
  ]
}

function scorePercent(value: number) {
  return Math.max(0, Math.min(100, Math.round(value)))
}

watch(() => props.sessionId, () => {
  void loadItems()
})

onMounted(() => {
  void loadItems()
})

onUnmounted(() => {
  stopPlaying()
  cleanupRecorder()
})
</script>
