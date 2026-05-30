<template>
  <div class="space-y-5">
    <!-- Period selector -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <button v-for="p in periods" :key="p.value"
          @click="period = p.value"
          :class="['px-3 py-1.5 rounded-xl text-xs font-medium transition-all',
            period === p.value ? 'bg-primary/20 text-primary border border-primary/30' : 'glass-card text-slate-400 hover:text-white']">
          {{ p.label }}
        </button>
      </div>
      <button @click="exportCsv" class="btn-ghost flex items-center gap-2 text-xs">
        <Download :size="13" /> Export CSV
      </button>
    </div>

    <!-- KPI Summary -->
    <div class="grid grid-cols-2 xl:grid-cols-4 gap-4">
      <WidgetsStatCard label="SNMP Success Rate" :value="latestKpi.snmp_success_rate ?? 0" :icon="CheckCircle" color="green" suffix="%" />
      <WidgetsStatCard label="BFD Up Sessions"   :value="latestKpi.bfd_up_sessions ?? 0"  :icon="Activity"   color="cyan"  />
      <WidgetsStatCard label="Anomaly Count"      :value="latestKpi.anomaly_count ?? 0"    :icon="Zap"        color="amber" />
      <WidgetsStatCard label="Alert Count"        :value="latestKpi.alert_count ?? 0"      :icon="Bell"       color="red"   />
    </div>

    <!-- Charts row -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <WidgetsLineChart
        title="Active OLTs"
        subtitle="Trend over selected period"
        :labels="oltLabels"
        :datasets="oltDatasets"
        :height="200"
      />
      <WidgetsLineChart
        title="Alerts & Anomalies"
        subtitle="Daily counts"
        :labels="alertLabels"
        :datasets="alertDatasets"
        :height="200"
      />
    </div>

    <!-- KPI History Table -->
    <div class="glass-card overflow-hidden">
      <div class="px-5 py-4 border-b border-white/10">
        <p class="text-sm font-semibold text-white">KPI History</p>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-white/[0.02] border-b border-white/10">
              <th class="table-header text-left">Timestamp</th>
              <th class="table-header text-left">Period</th>
              <th class="table-header text-right">OLTs</th>
              <th class="table-header text-right">CPU %</th>
              <th class="table-header text-right">Mem %</th>
              <th class="table-header text-right">SNMP Rate</th>
              <th class="table-header text-right">Alerts</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in kpis" :key="row.id" class="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
              <td class="table-cell text-xs font-mono">{{ formatTime(row.timestamp) }}</td>
              <td class="table-cell"><span class="badge-neutral capitalize">{{ row.period }}</span></td>
              <td class="table-cell text-right text-xs">{{ row.active_olts }}/{{ row.total_olts }}</td>
              <td class="table-cell text-right text-xs font-mono">{{ row.avg_cpu_usage?.toFixed(1) ?? '—' }}%</td>
              <td class="table-cell text-right text-xs font-mono">{{ row.avg_memory_usage?.toFixed(1) ?? '—' }}%</td>
              <td class="table-cell text-right text-xs font-mono">{{ row.snmp_success_rate?.toFixed(1) ?? '—' }}%</td>
              <td class="table-cell text-right text-xs">
                <span :class="row.alert_count > 0 ? 'text-red-400' : 'text-slate-500'">{{ row.alert_count }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Download, CheckCircle, Activity, Zap, Bell } from 'lucide-vue-next'

const { list, getCurrent } = useKpis()

const period = ref('hour')
const kpis = ref<any[]>([])
const latestKpi = ref<any>({})
const periods = [
  { label: 'Hourly', value: 'hour' },
  { label: 'Daily',  value: 'day' },
  { label: 'Weekly', value: 'week' }
]

onMounted(async () => {
  try {
    const [listRes, curRes] = await Promise.all([
      list({ period: period.value, page_size: 30 }),
      getCurrent()
    ])
    kpis.value = listRes.data.results ?? listRes.data
    latestKpi.value = curRes.data  // flat dict from /kpis/current/
  } catch { kpis.value = [] }
})

watch(period, async () => {
  const { data } = await list({ period: period.value, page_size: 30 })
  kpis.value = data.results ?? data
})

const oltLabels = computed(() => kpis.value.map(k => formatTime(k.timestamp)).reverse())
const oltDatasets = computed(() => [{
  label: 'Active OLTs', data: kpis.value.map(k => k.active_olts ?? 0).reverse(), color: '#00d4ff'
}])

const alertLabels = computed(() => kpis.value.map(k => formatTime(k.timestamp)).reverse())
const alertDatasets = computed(() => [
  { label: 'Alerts',    data: kpis.value.map(k => k.alert_count ?? 0).reverse(),   color: '#f87171' },
  { label: 'Anomalies', data: kpis.value.map(k => k.anomaly_count ?? 0).reverse(), color: '#f59e0b' }
])

const formatTime = (ts: string) => ts ? new Date(ts).toLocaleString('en-GB', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' }) : '—'

function exportCsv() {
  const headers = ['Timestamp', 'Period', 'Active OLTs', 'Total OLTs', 'CPU %', 'Memory %', 'SNMP Rate %', 'Alerts', 'Anomalies']
  const rows = kpis.value.map(k => [
    k.timestamp, k.period, k.active_olts, k.total_olts,
    k.avg_cpu_usage?.toFixed(1) ?? '', k.avg_memory_usage?.toFixed(1) ?? '',
    k.snmp_success_rate?.toFixed(1) ?? '', k.alert_count, k.anomaly_count
  ])
  const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `intelliolt-kpi-${period.value}-${new Date().toISOString().slice(0,10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
</script>
