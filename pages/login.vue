<template>
  <div class="min-h-screen bg-[#050b1a] flex items-center justify-center p-4">
    <!-- Background glows -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute top-1/4 left-1/3 w-96 h-96 bg-primary/8 rounded-full blur-3xl" />
      <div class="absolute bottom-1/4 right-1/3 w-80 h-80 bg-indigo-500/8 rounded-full blur-3xl" />
    </div>

    <div class="w-full max-w-sm relative">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-14 h-14 rounded-2xl bg-primary/20 border border-primary/40 flex items-center justify-center mx-auto mb-4 glow-cyan">
          <span class="text-primary font-bold text-xl">IO</span>
        </div>
        <h1 class="text-xl font-bold text-white">IntelliOLT</h1>
        <p class="text-xs text-slate-500 mt-1 font-mono">Network Intelligence Platform</p>
      </div>

      <!-- Card -->
      <div class="glass-card p-6">
        <p class="text-sm font-semibold text-white mb-5">Sign in to your account</p>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <!-- Email -->
          <div>
            <label class="text-xs text-slate-500 mb-1.5 block">Email address</label>
            <div class="relative">
              <Mail :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                v-model="form.email"
                type="email"
                placeholder="admin@intelliolt.tn"
                required
                class="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-sm text-slate-300
                       placeholder-slate-600 focus:outline-none focus:border-primary/50 focus:bg-white/10 transition-all"
              />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label class="text-xs text-slate-500 mb-1.5 block">Password</label>
            <div class="relative">
              <Lock :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                required
                class="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-10 py-2.5 text-sm text-slate-300
                       placeholder-slate-600 focus:outline-none focus:border-primary/50 focus:bg-white/10 transition-all"
              />
              <button type="button" @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors">
                <Eye v-if="!showPassword" :size="13" />
                <EyeOff v-else :size="13" />
              </button>
            </div>
          </div>

          <!-- Error -->
          <div v-if="error" class="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2.5">
            <AlertCircle :size="13" class="text-red-400 shrink-0" />
            <p class="text-xs text-red-400">{{ error }}</p>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full btn-primary py-2.5 flex items-center justify-center gap-2 text-sm mt-2"
          >
            <Loader2 v-if="loading" :size="14" class="animate-spin" />
            <LogIn v-else :size="14" />
            {{ loading ? 'Signing in...' : 'Sign in' }}
          </button>
        </form>
      </div>

      <p class="text-center text-[10px] text-slate-600 mt-5">
        IntelliOLT &copy; 2026 , ISP Network Supervision Platform
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Mail, Lock, Eye, EyeOff, AlertCircle, Loader2, LogIn } from 'lucide-vue-next'

definePageMeta({ layout: false })

const form = reactive({ email: '', password: '' })
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

const accessToken = useCookie('access_token', { maxAge: 3600 })
const refreshToken = useCookie('refresh_token', { maxAge: 604800 })

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    const { data } = await useApi().post('/auth/jwt/token/', {
      email: form.email,
      password: form.password
    })
    accessToken.value = data.access
    refreshToken.value = data.refresh
    await navigateTo('/')
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    error.value = detail ?? 'Invalid credentials. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
