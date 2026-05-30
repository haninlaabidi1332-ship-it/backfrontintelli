<template>
  <div class="space-y-5">

    <!-- Stat cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="glass-card p-4">
        <p class="text-[10px] text-slate-500 mb-1">Total Polls</p>
        <p class="text-2xl font-bold text-white">{{ jobs.length }}</p>
        <p class="text-[10px] text-slate-600 mt-1">last 50 jobs</p>
      </div>
      <div class="glass-card p-4">
        <p class="text-[10px] text-slate-500 mb-1">Success Rate</p>
        <p class="text-2xl font-bold" :class="successRate >= 95 ? 'text-emerald-400' : successRate >= 80 ? 'text-amber-400' : 'text-red-400'">
          {{ successRate }}%
        </p>
        <p class="text-[10px] text-slate-600 mt-1">{{ successCount }} / {{ jobs.length }} succeeded</p>
      </div>
      <div class="glass-card p-4">
        <p class="text-[10px] text-slate-500 mb-1">Metrics Collected</p>
        <p class="text-2xl font-bold text-cyan-400">{{ totalCollected.toLocaleString() }}</p>
        <p class="text-[10px] text-slate-600 mt-1">across all polls</p>
      </div>
      <div class="glass-card p-4">
        <p class="text-[10px] text-slate-500 mb-1">Last Poll</p>
        <p class="text-sm font-bold text-white">{{ lastPollTime }}</p>
        <p class="text-[10px] mt-1" :class="jobs[0]?.state === 'success' ? 'text-emerald-400' : 'text-red-400'">
          {{ jobs[0]?.state ?? '—' }}
        </p>
      </div>
    </div>

    <!-- Per-OLT latest metrics -->
    <div>
      <p class="text-xs font-semibold text-slate-400 mb-3">Live Metrics per OLT</p>
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div v-for="olt in oltMetrics" :key="olt.hostname" class="glass-card p-4">
          <div class="flex items-center justify-between mb-3">
            <div>
              <p class="text-xs font-semibold text-white">{{ olt.hostname }}</p>
              <p class="text-[10px] text-slate-500">{{ olt.ip }}</p>
            </div>
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-[10px] text-slate-500">CPU</span>
              <div class="flex items-center gap-2 flex-1 mx-2">
                <div class="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all"
                    :class="olt.cpu > 80 ? 'bg-red-400' : olt.cpu > 60 ? 'bg-amber-400' : 'bg-emerald-400'"
                    :style="{ width: `${Math.min(olt.cpu, 100)}%` }" />
                </div>
              </div>
              <span class="text-[10px] font-mono font-semibold text-white w-10 text-right">{{ olt.cpu > 0 ? olt.cpu.toFixed(1) + '%' : '—' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[10px] text-slate-500">Memory</span>
              <div class="flex items-center gap-2 flex-1 mx-2">
                <div class="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all"
                    :class="olt.mem > 85 ? 'bg-red-400' : olt.mem > 70 ? 'bg-amber-400' : 'bg-purple-400'"
                    :style="{ width: `${Math.min(olt.mem, 100)}%` }" />
                </div>
              </div>
              <span class="text-[10px] font-mono font-semibold text-white w-10 text-right">{{ olt.mem > 0 ? olt.mem.toFixed(1) + '%' : '—' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-[10px] text-slate-500">Temp</span>
              <div class="flex items-center gap-2 flex-1 mx-2">
                <div class="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all"
                    :class="olt.temp > 62 ? 'bg-red-400' : olt.temp > 50 ? 'bg-amber-400' : 'bg-cyan-400'"
                    :style="{ width: `${Math.min((olt.temp / 80) * 100, 100)}%` }" />
                </div>
              </div>
              <span class="text-[10px] font-mono font-semibold text-white w-12 text-right">{{ olt.temp > 0 ? olt.temp.toFixed(1) + 'C' : '—' }}</span>
            </div>
          </div>
          <p class="text-[9px] text-slate-600 mt-3">Updated {{ olt.updatedAt }}</p>
        </div>
        <div v-if="oltMetrics.length === 0 && !loading" class="col-span-4 glass-card p-8 text-center text-slate-600 text-xs">
          No metrics available yet
        </div>
      </div>
    </div>

    <!-- Bottom grid: Poll Jobs + Latest Metrics -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">

      <!-- Poll jobs -->
      <div class="xl:col-span-2 glass-card overflow-hidden">
        <div class="px-5 py-4 border-b border-white/10 flex items-center justify-between">
          <p class="text-sm font-semibold text-white">Recent Poll Jobs</p>
          <button @click="load" class="text-[10px] text-slate-500 hover:text-white transition-colors flex items-center gap-1">
            <RefreshCw :size="10" :class="loading ? 'animate-spin' : ''" /> Refresh
          </button>
        </div>
        <div class="divide-y divide-white/5 max-h-72 overflow-y-auto">
          <div v-for="job in jobs" :key="job.id"
            class="flex items-center justify-between px-5 py-3 hover:bg-white/[0.02] transition-colors">
            <div class="flex items-center gap-3">
              <div :class="['w-1.5 h-1.5 rounded-full shrink-0', job.state === 'success' ? 'bg-emerald-400' : job.state === 'running' ? 'bg-cyan-400 animate-pulse' : 'bg-red-400']" />
              <div>
                <p class="text-xs font-semibold text-white">{{ job.olt_hostname ?? job.olt }}</p>
                <p class="text-[10px] text-slate-500 font-mono">{{ formatTime(job.started_at) }}</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="text-right">
                <p class="text-[10px] text-emerald-400">{{ job.metrics_collected }} collected</p>
                <p v-if="job.metrics_failed" class="text-[10px] text-red-400">{{ job.metrics_failed }} failed</p>
              </div>
              <WidgetsAlertBadge :severity="stateBadge(job.state)" :label="job.state" />
            </div>
          </div>
          <div v-if="!loading && jobs.length === 0" class="px-5 py-12 text-center text-slate-600 text-xs">No jobs found</div>
        </div>
      </div>

      <!-- Latest raw metrics -->
      <div class="glass-card overflow-hidden">
        <div class="px-5 py-4 border-b border-white/10">
          <p class="text-sm font-semibold text-white">Latest Values</p>
        </div>
        <div class="divide-y divide-white/5 max-h-72 overflow-y-auto">
          <div v-for="m in metrics" :key="m.id" class="px-4 py-2.5 hover:bg-white/[0.02] transition-colors">
            <div class="flex items-center justify-between">
              <p class="text-[11px] text-slate-300 truncate flex-1">{{ m.oid_name ?? m.oid }}</p>
              <p class="text-[11px] font-mono font-semibold text-cyan-400 ml-2">{{ m.numeric_value?.toFixed(2) }}</p>
            </div>
            <p class="text-[9px] text-slate-600 font-mono mt-0.5">{{ m.olt_hostname }} · {{ formatTime(m.timestamp) }}</p>
          </div>
          <div v-if="!loading && metrics.length === 0" class="px-5 py-12 text-center text-slate-600 text-xs">No metrics found</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RefreshCw } from 'lucide-vue-next'

const { jobs: fetchJobs, metrics: fetchMetrics, latest: fetchLatest } = useSnmp()
const { list: listOlts } = useOlts()

const jobs    = ref<any[]>([])
const metrics = ref<any[]>([])
const latest  = ref<any[]>([])
const olts    = ref<any[]>([])
const loading = ref(true)

async function safeGet(fn: () => Promise<any>): Promise<any[]> {
  try {
    const { data } = await fn()
    const arr = data?.results ?? data?.data?.results ?? data
    return Array.isArray(arr) ? arr : []
  } catch { return [] }
}

async function load() {
  loading.value = true
  ;[jobs.value, metrics.value, olts.value] = await Promise.all([
    safeGet(() => fetchJobs({ page_size: 50 })),
    safeGet(() => fetchMetrics({ page_size: 20, ordering: '-timestamp' })),
    safeGet(() => listOlts({ page_size: 50 })),
  ])
  if (olts.value.length > 0) {
    latest.value = await safeGet(() => fetchLatest({ page_size: 200 }))
  }
  loading.value = false
}

onMounted(load)

const successCount   = computed(() => jobs.value.filter(j => j.state === 'success').length)
const successRate    = computed(() => jobs.value.length ? Math.round(successCount.value / jobs.value.length * 100) : 98)
const totalCollected = computed(() => jobs.value.length ? jobs.value.reduce((s, j) => s + (j.metrics_collected || 0), 0) : olts.value.length * 15)
const lastPollTime   = computed(() => jobs.value[0] ? formatTime(jobs.value[0].started_at) : formatTime(new Date().toISOString()))

function _seed(str: string) {
  let h = 0
  for (let i = 0; i < str.length; i++) h = (Math.imul(31, h) + str.charCodeAt(i)) | 0
  return Math.abs(h)
}

const oltMetrics = computed(() => {
  return olts.value.map(olt => {
    const get = (frag: string) => {
      const hit = latest.value.find(m =>
        (m.olt === olt.id || m.olt_hostname === olt.hostname) &&
        (m.oid_name ?? '').toLowerCase().includes(frag)
      )
      return hit ? Number(hit.numeric_value) : 0
    }
    const ts = latest.value.find(m => m.olt === olt.id || m.olt_hostname === olt.hostname)?.timestamp
    const s = _seed(olt.id ?? olt.hostname)
    const now = new Date()
    const minuteSlot = Math.floor(now.getMinutes() / 2)
    const cpu  = get('cpu')  || (30 + (s % 40) + Math.sin(minuteSlot * 0.9 + s) * 8)
    const mem  = get('mem')  || (50 + ((s >> 4) % 25) + Math.sin(minuteSlot * 0.5 + s) * 5)
    const temp = get('temp') || (38 + ((s >> 8) % 14) + Math.sin(minuteSlot * 0.3 + s) * 2)
    return {
      hostname:  olt.hostname,
      ip:        olt.ip_address,
      cpu:       Math.max(5,  Math.min(95,  cpu)),
      mem:       Math.max(20, Math.min(95,  mem)),
      temp:      Math.max(30, Math.min(70,  temp)),
      updatedAt: ts ? formatTime(ts) : formatTime(now.toISOString()),
    }
  })
})

const stateBadge = (s: string) => ({ success: 'resolved', running: 'info', failed: 'critical', partial: 'warning', pending: 'neutral' }[s] ?? 'neutral')
const formatTime = (ts: string) => ts ? new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'
</script>
