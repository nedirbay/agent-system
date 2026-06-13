<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const route = useRoute()
const { login, register } = useAuth()

const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  password: '',
  email: '',
  full_name: '',
})

function switchMode(next: 'login' | 'register') {
  mode.value = next
  error.value = ''
}

async function onSubmit() {
  error.value = ''
  if (form.username.length < 3) {
    error.value = 'Username must be at least 3 characters.'
    return
  }
  if (form.password.length < 8) {
    error.value = 'Password must be at least 8 characters.'
    return
  }

  loading.value = true
  try {
    if (mode.value === 'login') {
      await login(form.username, form.password)
    } else {
      await register({
        username: form.username,
        password: form.password,
        email: form.email || null,
        full_name: form.full_name || null,
      })
    }
    const redirect = (route.query.redirect as string) || '/app/chat'
    router.push(redirect)
  } catch (err) {
    error.value =
      err instanceof ApiError ? err.message : 'Something went wrong. Try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="relative grid min-h-screen place-items-center overflow-hidden bg-slate-50 px-4 dark:bg-slate-950"
  >
    <div class="bg-grid pointer-events-none absolute inset-0 opacity-60" />
    <div
      class="blob pointer-events-none absolute -top-32 -left-24 h-96 w-96 rounded-full bg-indigo-500/20 blur-3xl"
    />

    <div
      class="relative w-full max-w-md rounded-3xl border border-slate-200 bg-white/90 p-8 shadow-2xl shadow-slate-300/30 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/40"
    >
      <RouterLink to="/" class="mb-8 flex items-center justify-center gap-2.5">
        <span
          class="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/30"
        >
          <el-icon :size="22"><Cpu /></el-icon>
        </span>
        <span class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
          Agent<span class="text-indigo-600 dark:text-indigo-400">OS</span>
        </span>
      </RouterLink>

      <div class="mb-6 grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1 dark:bg-slate-800">
        <button
          v-for="tab in (['login', 'register'] as const)"
          :key="tab"
          class="rounded-lg py-2 text-sm font-medium capitalize transition-colors"
          :class="
            mode === tab
              ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-white'
              : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
          "
          @click="switchMode(tab)"
        >
          {{ tab === 'login' ? 'Sign in' : 'Create account' }}
        </button>
      </div>

      <el-form label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="Username">
          <el-input
            v-model="form.username"
            size="large"
            placeholder="operator"
            :prefix-icon="'User'"
          />
        </el-form-item>

        <template v-if="mode === 'register'">
          <el-form-item label="Full name">
            <el-input v-model="form.full_name" size="large" placeholder="Ada Lovelace" />
          </el-form-item>
          <el-form-item label="Email">
            <el-input v-model="form.email" size="large" placeholder="ada@example.com" />
          </el-form-item>
        </template>

        <el-form-item label="Password">
          <el-input
            v-model="form.password"
            type="password"
            size="large"
            show-password
            placeholder="••••••••"
            :prefix-icon="'Lock'"
            @keyup.enter="onSubmit"
          />
        </el-form-item>

        <p v-if="error" class="mb-3 text-sm text-rose-500">{{ error }}</p>

        <el-button
          type="primary"
          size="large"
          round
          class="w-full"
          :loading="loading"
          @click="onSubmit"
        >
          {{ mode === 'login' ? 'Sign in' : 'Create account' }}
        </el-button>
      </el-form>

      <p class="mt-6 text-center text-xs text-slate-400">
        Connects to the live backend at <code>/api/v1/auth</code>.
      </p>
    </div>
  </div>
</template>
