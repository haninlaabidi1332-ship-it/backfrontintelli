<template>
  <header class="h-14 flex items-center justify-between px-6 sticky top-0 z-30 backdrop-blur-sm transition-colors duration-200"
    :style="{ background: 'var(--bg-header)', borderBottom: '1px solid var(--border)' }">

    <div>
      <h1 class="text-sm font-semibold" :style="{ color: 'var(--text-primary)' }">{{ pageTitle }}</h1>
      <p class="text-[10px] font-mono" :style="{ color: 'var(--text-muted)' }">{{ currentTime }}</p>
    </div>

    <div class="flex items-center gap-3">
      <!-- Search -->
      <div class="relative hidden md:block">
        <Search :size="13" class="absolute left-3 top-1/2 -translate-y-1/2" :style="{ color: 'var(--text-muted)' }" />
        <input
          type="text"
          placeholder="Search..."
          class="rounded-xl pl-8 pr-4 py-1.5 text-xs w-48 transition-all focus:outline-none focus:ring-1 focus:ring-primary/50"
          :style="{ background: 'var(--bg-input)', border: '1px solid var(--border)', color: 'var(--text-primary)' }"
        />
      </div>

      <!-- Theme toggle -->
      <button @click="toggle"
        class="w-8 h-8 glass-card flex items-center justify-center hover:border-primary/30 transition-all"
        :title="isDark ? 'Light mode' : 'Dark mode'">
        <Sun v-if="isDark" :size="13" :style="{ color: 'var(--text-muted)' }" />
        <Moon v-else :size="13" :style="{ color: 'var(--text-muted)' }" />
      </button>

      <!-- Refresh -->
      <button @click="refresh" class="w-8 h-8 glass-card flex items-center justify-center hover:border-primary/30 transition-all group">
        <RefreshCw :size="13" :class="['transition-all group-hover:text-primary', isRefreshing ? 'animate-spin' : '']"
          :style="{ color: 'var(--text-muted)' }" />
      </button>

      <!-- Notifications -->
      <button class="relative w-8 h-8 glass-card flex items-center justify-center hover:border-primary/30 transition-all">
        <Bell :size="13" :style="{ color: 'var(--text-muted)' }" />
        <span class="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full" />
      </button>

      <!-- Status dot -->
      <div class="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full">
        <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse-slow" />
        <span class="text-[10px] font-semibold text-emerald-400">Live</span>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { Search, Bell, RefreshCw, Sun, Moon } from 'lucide-vue-next'
import { useRoute } from 'vue-router'

const route = useRoute()
const isRefreshing = ref(false)
const { isDark, toggle } = useTheme()

const titleMap: Record<string, string> = {
  '/': 'Network Dashboard',
  '/olts': 'OLT Devices',
  '/onts': 'ONT Clients',
  '/alerts': 'Alerts & Notifications',
  '/analytics': 'Analytics & KPIs',
  '/reports': 'Reports',
  '/anomalies': 'Anomaly Detection',
  '/bfd': 'BFD Sessions',
  '/snmp': 'SNMP Metrics',
  '/ai-models': 'ML Models'
}

const pageTitle = computed(() => titleMap[route.path] || 'IntelliOLT')

const currentTime = ref('')
onMounted(() => {
  const update = () => {
    currentTime.value = new Date().toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    })
  }
  update()
  setInterval(update, 1000)
})

const refresh = () => {
  isRefreshing.value = true
  setTimeout(() => { isRefreshing.value = false }, 1000)
}
</script>
