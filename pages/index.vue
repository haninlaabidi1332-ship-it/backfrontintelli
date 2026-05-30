<template>
  <div class="space-y-6">

    <!-- Auto-refresh indicator -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        <span class="text-[11px] text-slate-500">Live · refreshes in <span class="text-slate-400 font-mono tabular-nums">{{ countdown }}s</span></span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-[11px] text-slate-600">Last updated {{ lastUpdated }}</span>
        <button @click="refreshAll" :disabled="refreshing"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-[11px] text-slate-400 hover:text-white hover:bg-white/10 transition-all disabled:opacity-40">
          <RefreshCw :size="11" :class="refreshing ? 'animate-spin' : ''" />
          Refresh
        </button>
      </div>
    </div>

    <!-- KPI Grid -->
    <div class="grid grid-cols-2 xl:grid-cols-4 gap-4">
      <WidgetsStatCard
        label="Active OLTs"
        :value="kpi.active_olts ?? 0"
        :icon="Router"
        color="cyan"
        :loading="loadingKpi"
        :sub="`of ${kpi.total_olts ?? 0} total`"
      />
      <WidgetsStatCard
        label="Sites Reachable"
        :value="kpi.reachable_sites ?? 0"
        :icon="MapPin"
        color="green"
        :loading="loadingKpi"
        :sub="`of ${kpi.total_sites ?? 0} sites`"
      />
      <WidgetsStatCard
        label="Active Alerts"
        :value="alertCount"
        :icon="Bell"
        color="red"
        :loading="loadingAlerts"
        sub="Requires attention"
      />
      <WidgetsStatCard
        label="Anomalies"
        :value="anomalyCount"
        :icon="ShieldAlert"
        color="amber"
        :loading="loadingAnomalies"
        sub="Last 24 hours"
      />
    </div>

    <!-- Second row: CPU/Mem + BFD Status -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <!-- CPU chart -->
      <div class="xl:col-span-2">
        <WidgetsLineChart
          title="CPU & Memory Usage"
          subtitle="7-day trend across all OLTs"
          :labels="trendLabels"
          :datasets="usageDatasets"
          :height="220"
        />
      </div>

      <!-- BFD donut -->
      <WidgetsDonutChart
        title="BFD Session Status"
        :legend="bfdLegend"
      />
    </div>

    <!-- Third row: Site status map -->
    <WidgetsSiteMap />

    <!-- Fourth row: OLT table + Recent alerts -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <!-- OLT table -->
      <div class="xl:col-span-2 glass-card overflow-hidden">
        <div class="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <p class="text-sm font-semibold text-white">OLT Devices</p>
          <NuxtLink to="/olts" class="text-xs text-primary hover:underline">View all</NuxtLink>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="bg-white/[0.02]">
                <th class="table-header text-left">Hostname</th>
                <th class="table-header text-left">IP Address</th>
                <th class="table-header text-left">Status</th>
                <th class="table-header text-left">Last Poll</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingOlts" v-for="n in 4" :key="n">
                <td colspan="5" class="table-cell">
                  <div class="h-4 bg-white/5 rounded animate-pulse" />
                </td>
              </tr>
              <tr v-else v-for="olt in olts" :key="olt.id" class="hover:bg-white/[0.02] transition-colors">
                <td class="table-cell">
                  <div class="flex items-center gap-2">
                    <span :class="['w-1.5 h-1.5 rounded-full shrink-0', statusDot(olt.status)]" />
                    <span class="font-medium text-white text-xs">{{ olt.hostname }}</span>
                  </div>
                </td>
                <td class="table-cell font-mono text-xs">{{ olt.ip_address }}</td>
                <td class="table-cell"><WidgetsAlertBadge :severity="olt.status" :label="olt.status" /></td>
                <td class="table-cell text-xs text-slate-500">{{ formatTime(olt.last_polled_at) }}</td>
              </tr>
              <tr v-if="!loadingOlts && olts.length === 0">
                <td colspan="4" class="px-4 py-8 text-center text-slate-600 text-xs">No OLTs found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Recent alerts -->
      <div class="glass-card overflow-hidden">
        <div class="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <p class="text-sm font-semibold text-white">Recent Alerts</p>
          <NuxtLink to="/alerts" class="text-xs text-primary hover:underline">View all</NuxtLink>
        </div>
        <div class="divide-y divide-white/5 max-h-72 overflow-y-auto">
          <div v-if="loadingAlerts" v-for="n in 4" :key="n" class="px-4 py-3 flex gap-3 items-start">
            <div class="w-2 h-2 mt-1 rounded-full bg-white/10 animate-pulse" />
            <div class="flex-1 space-y-1">
              <div class="h-3 bg-white/5 rounded animate-pulse" />
              <div class="h-2 w-2/3 bg-white/5 rounded animate-pulse" />
            </div>
          </div>
          <div v-else v-for="alert in recentAlerts" :key="alert.id" class="px-4 py-3 flex gap-3 items-start hover:bg-white/[0.02] transition-colors">
            <span :class="['w-2 h-2 mt-1.5 rounded-full shrink-0', severityDot(alert.severity)]" />
            <div class="flex-1 min-w-0">
              <p class="text-xs text-slate-300 truncate">{{ alert.message }}</p>
              <p class="text-[10px] text-slate-600 mt-0.5">{{ formatTime(alert.first_seen) }}</p>
            </div>
            <WidgetsAlertBadge :severity="alert.severity" />
          </div>
          <div v-if="!loadingAlerts && recentAlerts.length === 0" class="px-4 py-8 text-center text-slate-600 text-xs">
            No active alerts
          </div>
        </div>
      </div>
    </div>

    <!-- Fourth row: BFD + Anomalies -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">

      <!-- BFD Sessions -->
      <div class="glass-card overflow-hidden">
        <div class="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <p class="text-sm font-semibold text-white">BFD Sessions</p>
          <NuxtLink to="/bfd" class="text-xs text-primary hover:underline">View all</NuxtLink>
        </div>
        <div class="divide-y divide-white/5 max-h-64 overflow-y-auto">
          <div v-for="session in bfdSessions" :key="session.id" class="px-4 py-3 flex items-center justify-between hover:bg-white/[0.02] transition-colors">
            <div>
              <p class="text-xs font-medium text-white">{{ session.name }}</p>
              <p class="text-[10px] text-slate-500 font-mono">{{ session.peer_ip }}</p>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-[10px] text-slate-500">{{ session.loss_rate_pct?.toFixed(1) }}% loss</span>
              <WidgetsAlertBadge :severity="session.state === 'up' ? 'resolved' : 'active'" :label="session.state?.toUpperCase()" />
            </div>
          </div>
          <div v-if="bfdSessions.length === 0" class="px-4 py-8 text-center text-slate-600 text-xs">No BFD sessions</div>
        </div>
      </div>

      <!-- Anomalies -->
      <div class="glass-card overflow-hidden">
        <div class="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <p class="text-sm font-semibold text-white">Recent Anomalies</p>
          <NuxtLink to="/anomalies" class="text-xs text-primary hover:underline">View all</NuxtLink>
        </div>
        <div class="divide-y divide-white/5 max-h-64 overflow-y-auto">
          <div v-for="anomaly in anomalies" :key="anomaly.id" class="px-4 py-3 flex items-center justify-between hover:bg-white/[0.02] transition-colors">
            <div class="flex-1 min-w-0">
              <p class="text-xs font-medium text-white truncate">{{ anomaly.metric_name }}</p>
              <p class="text-[10px] text-slate-500">
                Score: <span class="text-amber-400 font-mono">{{ anomaly.anomaly_score?.toFixed(2) }}</span>
                · {{ formatTime(anomaly.detected_at) }}
              </p>
            </div>
            <WidgetsAlertBadge :severity="anomaly.severity" />
          </div>
          <div v-if="anomalies.length === 0" class="px-4 py-8 text-center text-slate-600 text-xs">No anomalies detected</div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { Router, MapPin, Bell, ShieldAlert, RefreshCw } from 'lucide-vue-next'

const { getCurrent, getTrend } = useKpis()
const { list: listOlts } = useOlts()
const { list: listAlerts } = useAlerts()
const { list: listAnomalies } = useAnomalies()
const { sessions } = useBfd()

// KPI
const kpi = ref<any>({})
const loadingKpi = ref(true)

// OLTs
const olts = ref<any[]>([])
const loadingOlts = ref(true)

// Alerts
const recentAlerts = ref<any[]>([])
const alertCount = ref(0)
const loadingAlerts = ref(true)

// Anomalies
const anomalies = ref<any[]>([])
const anomalyCount = ref(0)
const loadingAnomalies = ref(true)

// BFD
const bfdSessions = ref<any[]>([])

// Charts
const trendLabels = ref<string[]>([])
const usageDatasets = ref<any[]>([])

// Auto-refresh
const REFRESH_INTERVAL = 60
const countdown  = ref(REFRESH_INTERVAL)
const refreshing = ref(false)
const lastUpdated = ref(',')

let refreshTimer: ReturnType<typeof setInterval> | null = null
let countdownTimer: ReturnType<typeof setInterval> | null = null

function startCountdown() {
  countdown.value = REFRESH_INTERVAL
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) countdown.value = REFRESH_INTERVAL
  }, 1000)
}

async function refreshAll() {
  if (refreshing.value) return
  refreshing.value = true
  countdown.value = REFRESH_INTERVAL
  await Promise.allSettled([fetchKpi(), fetchOlts(), fetchAlerts(), fetchAnomalies(), fetchBfd()])
  lastUpdated.value = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  refreshing.value = false
}

onMounted(async () => {
  await Promise.allSettled([
    fetchKpi(),
    fetchOlts(),
    fetchAlerts(),
    fetchAnomalies(),
    fetchBfd(),
    fetchTrend()
  ])
  lastUpdated.value = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

  startCountdown()
  refreshTimer = setInterval(refreshAll, REFRESH_INTERVAL * 1000)
})

onUnmounted(() => {
  if (refreshTimer)   clearInterval(refreshTimer)
  if (countdownTimer) clearInterval(countdownTimer)
})

async function fetchKpi() {
  try {
    const { data } = await getCurrent()
    kpi.value = data
  } catch { kpi.value = { active_olts: 0, total_olts: 0, reachable_sites: 0, total_sites: 0 } }
  finally { loadingKpi.value = false }
}

async function fetchOlts() {
  try {
    const { data } = await listOlts({ page_size: 8 })
    olts.value = data.results ?? data
  } catch { olts.value = [] }
  finally { loadingOlts.value = false }
}

async function fetchAlerts() {
  try {
    const { data } = await listAlerts({ status: 'active', page_size: 6 })
    recentAlerts.value = data.results ?? data
    alertCount.value = data.count ?? recentAlerts.value.length
  } catch { recentAlerts.value = [] }
  finally { loadingAlerts.value = false }
}

async function fetchAnomalies() {
  try {
    const { data } = await listAnomalies({ resolved: false, page_size: 6 })
    anomalies.value = data.results ?? data
    anomalyCount.value = data.count ?? anomalies.value.length
  } catch { anomalies.value = [] }
  finally { loadingAnomalies.value = false }
}

async function fetchBfd() {
  try {
    const { data } = await sessions({ page_size: 6 })
    bfdSessions.value = data.results ?? data
  } catch { bfdSessions.value = [] }
}

async function fetchTrend() {
  try {
    const [cpuRes, memRes] = await Promise.all([
      getTrend('avg_cpu_usage', 7),
      getTrend('avg_memory_usage', 7)
    ])
    const cpuData = cpuRes.data
    trendLabels.value = cpuData.map((p: any) => new Date(p.timestamp).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' }))
    usageDatasets.value = [
      { label: 'CPU %',    data: cpuData.map((p: any) => p.value ?? 0), color: '#00d4ff' },
      { label: 'Memory %', data: memRes.data.map((p: any) => p.value ?? 0), color: '#10b981' }
    ]
  } catch {
    // fallback demo data
    trendLabels.value = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    usageDatasets.value = [
      { label: 'CPU %',    data: [12,18,15,22,19,14,16], color: '#00d4ff' },
      { label: 'Memory %', data: [45,48,51,47,50,46,49], color: '#10b981' }
    ]
  }
}

const bfdLegend = computed(() => {
  const up   = bfdSessions.value.filter((s: any) => s.state === 'up').length
  const down = bfdSessions.value.filter((s: any) => s.state !== 'up').length
  return [
    { label: 'UP',   value: up,   color: '#10b981' },
    { label: 'DOWN', value: down, color: '#f87171' }
  ]
})

// Helpers
const statusDot = (s: string) => ({
  active:      'bg-emerald-400',
  inactive:    'bg-slate-500',
  degraded:    'bg-amber-400',
  maintenance: 'bg-blue-400'
}[s] ?? 'bg-slate-500')

const severityDot = (s: string) => ({
  critical: 'bg-red-400',
  major:    'bg-orange-400',
  warning:  'bg-amber-400',
  info:     'bg-primary'
}[s] ?? 'bg-slate-500')

const formatTime = (ts: string) => {
  if (!ts) return ','
  return new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}
</script>
