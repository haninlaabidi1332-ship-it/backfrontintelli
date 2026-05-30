<template>
  <div class="space-y-5">
    <!-- Filters -->
    <div class="flex items-center gap-3">
      <button v-for="s in ['all','low','medium','high','critical']" :key="s"
        @click="severityFilter = s"
        :class="['px-3 py-1.5 rounded-xl text-xs font-medium capitalize transition-all',
          severityFilter === s ? 'bg-primary/20 text-primary border border-primary/30' : 'glass-card text-slate-400 hover:text-white']">
        {{ s }}
      </button>
      <div class="flex items-center gap-2 ml-auto">
        <label class="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
          <input type="checkbox" v-model="unresolvedOnly" class="accent-primary w-3 h-3" />
          Unresolved only
        </label>
      </div>
    </div>

    <!-- Anomaly cards -->
    <div v-if="loading" class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <div v-for="n in 4" :key="n" class="glass-card p-5 animate-pulse">
        <div class="h-4 bg-white/5 rounded mb-3 w-1/2" />
        <div class="h-3 bg-white/5 rounded mb-2" />
        <div class="h-3 bg-white/5 rounded w-2/3" />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <div v-for="anomaly in filtered" :key="anomaly.id"
        class="glass-card-hover p-5 cursor-pointer" @click="selected = anomaly">
        <div class="flex items-start justify-between mb-3">
          <div>
            <p class="text-sm font-semibold text-white">{{ anomaly.metric_name }}</p>
            <p class="text-[10px] text-slate-500 font-mono mt-0.5">{{ anomaly.olt_hostname ?? 'Global' }}</p>
          </div>
          <WidgetsAlertBadge :severity="anomaly.severity" />
        </div>

        <div class="grid grid-cols-3 gap-3 mb-3">
          <div class="glass-card px-3 py-2 text-center">
            <p class="text-[10px] text-slate-500">Actual</p>
            <p class="text-sm font-bold text-white font-mono">{{ anomaly.actual_value?.toFixed(2) }}</p>
          </div>
          <div class="glass-card px-3 py-2 text-center">
            <p class="text-[10px] text-slate-500">Expected</p>
            <p class="text-sm font-bold text-slate-400 font-mono">{{ anomaly.expected_value?.toFixed(2) ?? '—' }}</p>
          </div>
          <div class="glass-card px-3 py-2 text-center">
            <p class="text-[10px] text-slate-500">Score</p>
            <p :class="['text-sm font-bold font-mono', scoreColor(anomaly.anomaly_score)]">{{ anomaly.anomaly_score?.toFixed(2) }}</p>
          </div>
        </div>

        <!-- Score bar -->
        <div class="h-1.5 bg-white/10 rounded-full overflow-hidden mb-3">
          <div :style="{ width: (anomaly.anomaly_score * 100) + '%' }"
            :class="['h-full rounded-full transition-all', scoreBarColor(anomaly.anomaly_score)]" />
        </div>

        <div class="flex items-center justify-between">
          <p class="text-[10px] text-slate-500">{{ formatTime(anomaly.detected_at) }}</p>
          <button v-if="!anomaly.resolved" @click.stop="resolve(anomaly)"
            class="text-[10px] px-2 py-1 rounded-lg bg-emerald-500/15 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/25 transition-colors">
            Resolve
          </button>
          <span v-else class="badge-success text-[10px]">Resolved</span>
        </div>

        <p v-if="anomaly.explanation" class="text-[10px] text-slate-500 mt-3 border-t border-white/5 pt-3 line-clamp-2">
          {{ anomaly.explanation }}
        </p>
      </div>

      <div v-if="filtered.length === 0" class="xl:col-span-2 glass-card p-12 text-center text-slate-600 text-sm">
        No anomalies found
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { list, resolve: resolveAnomaly } = useAnomalies()
const anomalies = ref<any[]>([])
const loading = ref(true)
const selected = ref<any>(null)
const severityFilter = ref('all')
const unresolvedOnly = ref(false)

onMounted(async () => {
  try {
    const { data } = await list({ page_size: 50 })
    anomalies.value = data.results ?? data
  } catch { anomalies.value = [] }
  finally { loading.value = false }
})

const filtered = computed(() => anomalies.value.filter(a => {
  const matchSeverity = severityFilter.value === 'all' || a.severity === severityFilter.value
  const matchResolved = !unresolvedOnly.value || !a.resolved
  return matchSeverity && matchResolved
}))

const resolve = async (anomaly: any) => {
  await resolveAnomaly(anomaly.id)
  anomaly.resolved = true
  anomaly.resolved_at = new Date().toISOString()
}

const scoreColor = (s: number) => s >= 0.8 ? 'text-red-400' : s >= 0.6 ? 'text-amber-400' : 'text-emerald-400'
const scoreBarColor = (s: number) => s >= 0.8 ? 'bg-red-500' : s >= 0.6 ? 'bg-amber-500' : 'bg-emerald-500'
const formatTime = (ts: string) => ts ? new Date(ts).toLocaleString('en-GB', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' }) : '—'
</script>
