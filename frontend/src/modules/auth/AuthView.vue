<template>
  <section class="mx-auto flex min-h-screen max-w-6xl items-center px-6 py-10 lg:px-10">
    <div class="grid w-full overflow-hidden rounded-[32px] border border-white/80 bg-white/90 shadow-[0_30px_90px_rgba(84,108,255,0.14)] lg:grid-cols-[0.9fr_1.1fr]">
      <div class="flex flex-col justify-between bg-slate-950 px-8 py-8 text-white lg:px-10">
        <div>
          <div class="flex items-center gap-3">
            <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-lg font-bold text-slate-950">
              S
            </div>
            <div>
              <div class="text-lg font-semibold">SpeakCoach</div>
              <div class="text-xs text-slate-300">AI English Speaking Coach</div>
            </div>
          </div>

          <div class="mt-16 max-w-sm space-y-4">
            <div class="text-xs font-semibold uppercase tracking-[0.18em] text-sky-300">Account Access</div>
            <h1 class="text-3xl font-semibold leading-tight md:text-4xl">
              登录后开始你的口语练习
            </h1>
            <p class="text-sm leading-7 text-slate-300">
              账号会用于保存当前练习入口和展示个人身份，方便后续扩展练习记录。
            </p>
          </div>
        </div>

        <div class="mt-12 grid gap-3 text-sm text-slate-300">
          <div class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">场景练习</div>
          <div class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">发音与表达反馈</div>
          <div class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">课后总结</div>
        </div>
      </div>

      <div class="px-6 py-8 sm:px-10 lg:px-14">
        <div class="mx-auto max-w-md">
          <div class="mb-8">
            <div class="text-sm font-medium text-indigo-600">{{ mode === 'login' ? '欢迎回来' : '创建账号' }}</div>
            <h2 class="mt-2 text-3xl font-semibold text-slate-900">
              {{ mode === 'login' ? '登录' : '注册' }}
            </h2>
            <p class="mt-2 text-sm text-slate-500">
              {{ mode === 'login' ? '使用邮箱和密码进入练习空间。' : '填写基础信息后即可开始练习。' }}
            </p>
          </div>

          <form class="space-y-5" @submit.prevent="submit">
            <label v-if="mode === 'register'" class="block">
              <span class="text-sm font-medium text-slate-700">昵称</span>
              <input
                v-model.trim="name"
                class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
                autocomplete="name"
                placeholder="例如 Xin"
                type="text"
              />
            </label>

            <label class="block">
              <span class="text-sm font-medium text-slate-700">邮箱</span>
              <input
                v-model.trim="email"
                class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
                autocomplete="email"
                placeholder="you@example.com"
                type="email"
              />
            </label>

            <label class="block">
              <span class="text-sm font-medium text-slate-700">密码</span>
              <input
                v-model="password"
                class="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
                :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
                placeholder="至少 6 位"
                type="password"
              />
            </label>

            <div v-if="errorMessage" class="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {{ errorMessage }}
            </div>

            <button
              class="w-full rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
              :disabled="store.authLoading"
              type="submit"
            >
              {{ store.authLoading ? '处理中...' : submitLabel }}
            </button>
          </form>

          <div class="mt-6 text-center text-sm text-slate-500">
            <span>{{ mode === 'login' ? '还没有账号？' : '已有账号？' }}</span>
            <button class="ml-2 font-semibold text-indigo-600 hover:text-indigo-500" type="button" @click="toggleMode">
              {{ mode === 'login' ? '去注册' : '去登录' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { useAppStore } from '@/core/store'

const store = useAppStore()
const mode = ref<'login' | 'register'>('login')
const name = ref('')
const email = ref('')
const password = ref('')
const errorMessage = ref('')

const submitLabel = computed(() => (mode.value === 'login' ? '登录' : '注册并进入'))

function toggleMode() {
  mode.value = mode.value === 'login' ? 'register' : 'login'
  errorMessage.value = ''
  store.authError = ''
}

function validateForm() {
  if (mode.value === 'register' && !name.value.trim()) {
    return '请输入昵称。'
  }
  if (!email.value.trim()) {
    return '请输入邮箱。'
  }
  if (!password.value) {
    return '请输入密码。'
  }
  if (password.value.length < 6) {
    return '密码至少需要 6 位。'
  }
  return ''
}

async function submit() {
  const validationMessage = validateForm()
  if (validationMessage) {
    errorMessage.value = validationMessage
    return
  }

  errorMessage.value = ''
  try {
    if (mode.value === 'login') {
      await store.login({ email: email.value, password: password.value })
    } else {
      await store.register({ name: name.value, email: email.value, password: password.value })
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '操作失败，请稍后重试。'
  }
}
</script>
