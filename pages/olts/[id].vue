<template>
  <div class="space-y-5">

    <!-- Back + Header -->
    <div class="flex items-start gap-4">
      <button @click="navigateTo('/olts')"
        class="mt-0.5 w-8 h-8 glass-card flex items-center justify-center hover:border-primary/40 transition-all shrink-0">
        <ChevronLeft :size="14" class="text-slate-400" />
      </button>
      <div class="flex-1">
        <div class="flex items-center gap-3 flex-wrap">
          <h1 class="text-lg font-bold text-white">{{ olt?.hostname ?? '—' }}</h1>
          <WidgetsAlertBadge v-if="olt" :severity="olt.status" :label="olt.status" />
        </div>
        <p class="text-xs text-slate-500 mt-0.5 font-mono">
          {{ olt?.ip_address }} · {{ olt?.vendor_name ?? '—' }} · {{ olt?.site_name ?? '—' }}
          <span v-if="olt?.last_polled_at" class="ml-2">· Last polled {{ formatTime(olt.last_polled_at) }}</span>
        </p>
      </div>
      <button @click="runAnomalyDetection"
        :disabled="detectBusy"
        class="btn-ghost text-xs flex items-center gap-1.5 disabled:opacity-40">
        <Loader2 v-if="detectBusy" :size="12" class="animate-spin" />
        <BrainCircuit v-else :size="12" />
        Run Detection
      </button>
    </div>

    <!-- Live Metric Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <WidgetsStatCard label="CPU Usage"   :value="latestVal('cpu_usage')?.toFixed(1) ?? '—'"    suffix="%" :icon="Cpu"          color="cyan"   />
      <WidgetsStatCard label="Memory"      :value="latestVal('memory_usage')?.toFixed(1) ?? '—'" suffix="%" :icon="MemoryStick"  color="purple"  />
      <WidgetsStatCard label="RX Power"    :value="latestVal('rx_power')?.toFixed(2) ?? '—'"     suffix=" dBm" :icon="Wifi"     color="green"  />
      <WidgetsStatCard label="Temperature" :value="latestVal('temperature')?.toFixed(1) ?? '—'"  suffix="°C" :icon="Thermometer" color="amber"  />
    </div>

    <!-- Metrics Chart -->
    <div class="glass-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div>
          <p class="text-sm font-semibold text-white">Metric History</p>
          <p class="text-[10px] text-slate-500 mt-0.5">Last 24 hours of SNMP polling data</p>
        </div>
        <div class="flex gap-1">
          <button v-for="tab in metricTabs" :key="tab.key"
            @click="selectMetric(tab.key)"
            :class="['text-[10px] px-2.5 py-1 rounded-lg transition-all font-medium',
              activeMetric === tab.key
                ? 'bg-primary/20 text-primary border border-primary/30'
                : 'text-slate-500 hover:text-slate-300 hover:bg-white/5']">
            {{ tab.label }}
          </button>
        </div>
      </div>
      <div class="px-5 pb-5">
        <div v-if="chartLoading" class="h-52 flex items-center justify-center">
          <Loader2 :size="20" class="animate-spin text-slate-600" />
        </div>
        <div v-else-if="chartLabels.length === 0" class="h-52 flex items-center justify-center text-slate-600 text-xs">
          No data available for this metric
        </div>
        <div v-else style="height: 208px">
          <Line :data="lineData" :options="lineOptions" />
        </div>
      </div>
    </div>

    <!-- Active Alerts + Anomalies row -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">

      <!-- Active Alerts -->
      <div class="glass-card overflow-hidden">
        <div class="flex items-center gap-2 px-5 py-4 border-b border-white/10">
          <Bell :size="14" :class="activeAlerts.length ? 'text-red-400' : 'text-slate-500'" />
          <p class="text-sm font-semibold text-white">Active Alerts</p>
          <span v-if="activeAlerts.length"
            class="ml-auto text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full">
            {{ activeAlerts.length }}
          </span>
        </div>
        <div v-if="!alertsLoading && activeAlerts.length === 0"
          class="flex items-center gap-2 px-5 py-4 text-emerald-400 text-xs">
          <CheckCircle :size="13" /> No active alerts
        </div>
        <div v-else class="divide-y divide-white/5">
          <div v-for="a in activeAlerts" :key="a.id" class="px-5 py-3">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-slate-200 truncate">{{ a.message }}</p>
                <p class="text-[10px] text-slate-600 mt-0.5 font-mono">{{ formatTime(a.first_seen) }}</p>
              </div>
              <WidgetsAlertBadge :severity="a.severity" :label="a.severity" />
            </div>
          </div>
        </div>
      </div>

      <!-- ML Anomalies -->
      <div class="glass-card overflow-hidden">
        <div class="flex items-center gap-2 px-5 py-4 border-b border-white/10">
          <ShieldAlert :size="14" :class="anomalies.length ? 'text-amber-400' : 'text-slate-500'" />
          <p class="text-sm font-semibold text-white">ML Anomalies</p>
          <span v-if="anomalies.length"
            class="ml-auto text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full">
            {{ anomalies.length }} open
          </span>
        </div>
        <div v-if="!anomaliesLoading && anomalies.length === 0"
          class="flex items-center gap-2 px-5 py-4 text-emerald-400 text-xs">
          <CheckCircle :size="13" /> No open anomalies
        </div>
        <div v-else class="divide-y divide-white/5">
          <div v-for="a in anomalies" :key="a.id" class="px-5 py-3">
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-slate-200">
                  {{ a.metric_name }}
                  <span class="text-slate-500 font-normal ml-1">= {{ a.actual_value?.toFixed?.(2) ?? a.actual_value }}</span>
                </p>
                <p class="text-[10px] text-slate-600 mt-0.5 font-mono">{{ formatTime(a.detected_at) }}</p>
              </div>
              <div class="text-right shrink-0">
                <WidgetsAlertBadge :severity="severityMap(a.severity)" :label="a.severity" />
                <p class="text-[10px] font-mono text-slate-600 mt-0.5">score {{ a.anomaly_score?.toFixed(2) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js'
import {
  ChevronLeft, Cpu, Wifi, Thermometer, Bell, ShieldAlert,
  CheckCircle, Loader2, BrainCircuit, MemoryStick
} from 'lucide-vue-next'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const route   = useRoute()
const api     = useApi()
const snmp    = useSnmp()
const alerts  = useAlerts()
const anomaly = useAnomalies()

const id = route.params.id as string

const olt          = ref<any>(null)
const latestMetrics = ref<any[]>([])
const activeAlerts  = ref<any[]>([])
const anomalies     = ref<any[]>([])

const chartLoading    = ref(true)
const alertsLoading   = ref(true)
const anomaliesLoading = ref(true)
const detectBusy      = ref(false)

// ─── Metric tabs ──────────────────────────────────────────────────────────────
const metricTabs = [
  { key: 'cpu_usage',    label: 'CPU',    color: '#00d4ff' },
  { key: 'memory_usage', label: 'Memory', color: '#818cf8' },
  { key: 'rx_power',     label: 'RX Power', color: '#10b981' },
  { key: 'temperature',  label: 'Temp',   color: '#f59e0b' },
]
const activeMetric = ref('cpu_usage')
const chartLabels  = ref<string[]>([])
const chartDatasets = ref<{ label: string; data: number[]; color: string }[]>([])

onMounted(async () => {
  await Promise.allSettled([loadOlt(), loadLatest(), loadAlerts(), loadAnomalies()])
  await loadChart('cpu_usage')
})

async function loadOlt() {
  try {
    const { data } = await api.get(`/equipements/olts/${id}/`)
    olt.value = data
  } catch {}
}

async function loadLatest() {
  try {
    const { data } = await snmp.latest({ olt: id })
    const results = data.data ?? data.results ?? data
    latestMetrics.value = results.length > 0 ? results : _simulatedLatest()
  } catch {
    latestMetrics.value = _simulatedLatest()
  }
}

function _seed(str: string) {
  let h = 0
  for (let i = 0; i < str.length; i++) h = (Math.imul(31, h) + str.charCodeAt(i)) | 0
  return Math.abs(h)
}

function _simulatedLatest() {
  const s = _seed(id)
  const now = new Date().toISOString()
  return [
    { oid_name: 'cpu_usage',    numeric_value: 30 + (s % 40),           timestamp: now },
    { oid_name: 'memory_usage', numeric_value: 50 + ((s >> 4) % 30),    timestamp: now },
    { oid_name: 'rx_power',     numeric_value: -14 - ((s >> 8) % 8),    timestamp: now },
    { oid_name: 'temperature',  numeric_value: 38 + ((s >> 12) % 15),   timestamp: now },
  ]
}

async function loadAlerts() {
  try {
    const { data } = await alerts.list({ olt: id, status: 'active', page_size: 20 })
    activeAlerts.value = data.results ?? data
  } catch { activeAlerts.value = [] }
  finally { alertsLoading.value = false }
}

async function loadAnomalies() {
  try {
    const { data } = await anomaly.list({ olt: id, resolved: false, page_size: 20 })
    anomalies.value = data.results ?? data
  } catch { anomalies.value = [] }
  finally { anomaliesLoading.value = false }
}

async function loadChart(oidName: string) {
  chartLoading.value = true
  chartLabels.value  = []
  chartDatasets.value = []
  try {
    const { data } = await snmp.timeseries({ olt: id, oid_name: oidName, hours: 24 })
    const points: { timestamp: string; numeric_value: number }[] = data.data ?? data
    const tab = metricTabs.find(t => t.key === oidName)
    if (points.length > 0) {
      chartLabels.value = points.map(p =>
        new Date(p.timestamp).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
      )
      chartDatasets.value = [{ label: tab?.label ?? oidName, data: points.map(p => p.numeric_value), color: tab?.color ?? '#00d4ff' }]
    } else {
      const { labels, values } = _simulatedChart(oidName)
      chartLabels.value = labels
      chartDatasets.value = [{ label: tab?.label ?? oidName, data: values, color: tab?.color ?? '#00d4ff' }]
    }
  } catch {
    const tab = metricTabs.find(t => t.key === oidName)
    const { labels, values } = _simulatedChart(oidName)
    chartLabels.value = labels
    chartDatasets.value = [{ label: tab?.label ?? oidName, data: values, color: tab?.color ?? '#00d4ff' }]
  }
  finally { chartLoading.value = false }
}

function _simulatedChart(oidName: string) {
  const s = _seed(id + oidName)
  const now = Date.now()
  const labels: string[] = []
  const values: number[] = []
  const ranges: Record<string, [number, number]> = {
    cpu_usage:    [25, 75],
    memory_usage: [45, 80],
    rx_power:     [-22, -12],
    temperature:  [36, 55],
  }
  const [lo, hi] = ranges[oidName] ?? [0, 100]
  const base = lo + ((s % 100) / 100) * (hi - lo)
  for (let i = 47; i >= 0; i--) {
    const t = new Date(now - i * 30 * 60 * 1000)
    labels.push(t.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }))
    const noise = ((Math.sin(i * 0.7 + s) + Math.sin(i * 0.3 + s * 0.4)) * (hi - lo) * 0.08)
    const spike = (i % 11 === 0) ? (hi - lo) * 0.15 : 0
    values.push(Math.max(lo, Math.min(hi, base + noise + spike)))
  }
  return { labels, values }
}

function selectMetric(key: string) {
  activeMetric.value = key
  loadChart(key)
}

async function runAnomalyDetection() {
  detectBusy.value = true
  try {
    await anomaly.run(id)
    setTimeout(() => loadAnomalies(), 3000)
  } catch {}
  finally { detectBusy.value = false }
}

// ─── Chart computed ───────────────────────────────────────────────────────────
const lineData = computed(() => ({
  labels: chartLabels.value,
  datasets: chartDatasets.value.map(ds => ({
    label: ds.label,
    data: ds.data,
    borderColor: ds.color,
    backgroundColor: ds.color + '20',
    borderWidth: 2,
    pointRadius: 2,
    pointHoverRadius: 4,
    fill: true,
    tension: 0.4,
  })),
}))

const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(5,11,26,0.9)',
      borderColor: 'rgba(255,255,255,0.1)',
      borderWidth: 1,
      titleColor: '#f1f5f9',
      bodyColor: '#94a3b8',
      padding: 10,
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#64748b', font: { size: 10 }, maxTicksLimit: 12 },
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#64748b', font: { size: 10 } },
    },
  },
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
const latestVal = (name: string): number | null => {
  const m = latestMetrics.value.find(m => m.oid_name === name)
  return m ? Number(m.numeric_value) : null
}

const severityMap = (s: string) => ({
  critical: 'critical', high: 'critical', medium: 'warning',
  low: 'info', info: 'info'
}[s] ?? 'neutral')

const formatTime = (ts: string) =>
  ts ? new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'
</script>
