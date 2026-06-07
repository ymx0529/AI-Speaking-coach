<template>
  <section class="min-h-screen px-5 py-6 lg:px-8 lg:py-8">
    <div
      class="mx-auto grid max-w-6xl overflow-hidden rounded-[28px] border border-[color:var(--line-soft)] bg-[rgba(255,255,255,0.94)] shadow-[0_28px_80px_rgba(15,23,42,0.08)] lg:grid-cols-[minmax(0,1fr)_30rem]"
    >
      <aside class="relative overflow-hidden border-b border-[color:var(--line-soft)] px-6 py-8 lg:border-b-0 lg:border-r lg:px-8 lg:py-10">
        <div class="pointer-events-none absolute left-10 top-10 h-36 w-36 rounded-full bg-blue-500/[0.08] blur-3xl" />
        <div class="pointer-events-none absolute bottom-10 right-10 h-40 w-40 rounded-full bg-sky-300/[0.08] blur-3xl" />

        <button class="relative z-10 text-sm font-medium text-[var(--ink-3)] transition hover:text-[var(--ink-1)]" @click="$emit('back')">
          返回首页
        </button>

        <div class="relative z-10 mt-8 inline-flex rounded-full bg-[var(--brand-50)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--brand-500)]">
          Account
        </div>

        <h1 class="relative z-10 mt-5 max-w-[11ch] text-4xl font-semibold leading-[1.08] tracking-tight text-[var(--ink-1)] lg:text-5xl">
          登录后开始你的场景练习
        </h1>

        <p class="relative z-10 mt-5 max-w-xl text-sm leading-8 text-[var(--ink-3)]">
          你的练习记录、对话总结和自定义场景都会保存在账号里。登录成功后会直接进入练习页，继续上一次的节奏。
        </p>

        <div class="relative z-10 mt-8 grid gap-4 sm:grid-cols-3">
          <article class="rounded-[20px] border border-[color:var(--line-soft)] bg-white/80 px-4 py-4 shadow-sm">
            <div class="text-sm font-semibold text-[var(--ink-2)]">场景练习</div>
            <p class="mt-2 text-xs leading-6 text-[var(--ink-3)]">面试、点餐、会议和自定义情境都可保存。</p>
          </article>
          <article class="rounded-[20px] border border-[color:var(--line-soft)] bg-white/80 px-4 py-4 shadow-sm">
            <div class="text-sm font-semibold text-[var(--ink-2)]">实时对话</div>
            <p class="mt-2 text-xs leading-6 text-[var(--ink-3)]">录音后自动识别，再由 AI 继续追问。</p>
          </article>
          <article class="rounded-[20px] border border-[color:var(--line-soft)] bg-white/80 px-4 py-4 shadow-sm">
            <div class="text-sm font-semibold text-[var(--ink-2)]">课后反馈</div>
            <p class="mt-2 text-xs leading-6 text-[var(--ink-3)]">保留发音、表达和纠错结果，方便复练。</p>
          </article>
        </div>
      </aside>

      <section class="bg-[linear-gradient(180deg,#ffffff_0%,#f8fbff_100%)] px-6 py-8 lg:px-8 lg:py-10">
        <div class="inline-flex rounded-full bg-slate-100 p-1">
          <button
            class="rounded-full px-4 py-2 text-sm font-medium transition"
            :class="mode === 'login' ? 'bg-white text-[var(--ink-1)] shadow-sm' : 'text-[var(--ink-3)]'"
            @click="mode = 'login'"
          >
            登录
          </button>
          <button
            class="rounded-full px-4 py-2 text-sm font-medium transition"
            :class="mode === 'register' ? 'bg-white text-[var(--ink-1)] shadow-sm' : 'text-[var(--ink-3)]'"
            @click="mode = 'register'"
          >
            注册
          </button>
        </div>

        <div class="mt-6">
          <h2 class="text-2xl font-semibold tracking-tight text-[var(--ink-1)]">
            {{ mode === 'login' ? '欢迎回来' : '创建你的练习账号' }}
          </h2>
          <p class="mt-2 text-sm leading-7 text-[var(--ink-3)]">
            {{ mode === 'login' ? '登录后继续你的语音陪练和练习记录。' : '只需一步注册，就能开始保存你的练习进度。' }}
          </p>
        </div>

        <form class="mt-8 space-y-5" @submit.prevent="submit">
          <div v-if="mode === 'register'">
            <label class="mb-2 block text-sm font-medium text-[var(--ink-2)]">昵称</label>
            <input
              v-model.trim="form.name"
              class="w-full rounded-[16px] border border-[color:var(--line-strong)] bg-white px-4 py-3 text-sm outline-none transition focus:border-[var(--brand-500)] focus:ring-4 focus:ring-blue-100"
              placeholder="输入你的昵称"
              type="text"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-medium text-[var(--ink-2)]">邮箱</label>
            <input
              v-model.trim="form.email"
              class="w-full rounded-[16px] border border-[color:var(--line-strong)] bg-white px-4 py-3 text-sm outline-none transition focus:border-[var(--brand-500)] focus:ring-4 focus:ring-blue-100"
              placeholder="name@example.com"
              type="email"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-medium text-[var(--ink-2)]">密码</label>
            <input
              v-model="form.password"
              class="w-full rounded-[16px] border border-[color:var(--line-strong)] bg-white px-4 py-3 text-sm outline-none transition focus:border-[var(--brand-500)] focus:ring-4 focus:ring-blue-100"
              placeholder="输入密码"
              type="password"
            />
          </div>

          <div v-if="errorMessage" class="rounded-[16px] bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {{ errorMessage }}
          </div>

          <button
            class="w-full rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            :disabled="isDisabled"
            type="submit"
          >
            {{ pending ? '提交中...' : mode === 'login' ? '登录并进入练习' : '注册并进入练习' }}
          </button>
        </form>

        <div class="mt-6 rounded-[18px] border border-[color:var(--line-soft)] bg-white/80 px-4 py-4 text-sm text-[var(--ink-3)] shadow-sm">
          <div class="font-medium text-[var(--ink-2)]">提示</div>
          <p class="mt-2 leading-7">登录成功后，首页会显示当前账号，练习页也会保持同一份登录状态。</p>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import axios from 'axios'

import { useAppStore } from '@/core/store'

const props = defineProps<{
  pending?: boolean
}>()

defineEmits<{
  back: []
}>()

const store = useAppStore()
const mode = ref<'login' | 'register'>('login')
const errorMessage = ref('')
const form = reactive({
  name: '',
  email: '',
  password: '',
})

const isDisabled = computed(() => {
  if (!form.email || !form.password) return true
  if (mode.value === 'register' && !form.name) return true
  return !!props.pending
})

async function submit() {
  errorMessage.value = ''
  try {
    if (mode.value === 'login') {
      await store.login({
        email: form.email,
        password: form.password,
      })
    } else {
      await store.register({
        name: form.name,
        email: form.email,
        password: form.password,
      })
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      errorMessage.value = String(error.response?.data?.detail ?? '登录失败，请检查输入。')
      return
    }
    errorMessage.value = '登录失败，请稍后重试。'
  }
}
</script>
