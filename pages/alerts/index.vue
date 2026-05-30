<template>
  <div class="space-y-5">
    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3">
      <div class="flex items-center gap-2">
        <button v-for="s in ['all','active','acknowledged','resolved']" :key="s"
          @click="statusFilter = s"
          :class="['px-3 py-1.5 rounded-xl text-xs font-medium transition-all capitalize',
            statusFilter === s ? 'bg-primary/20 text-primary border border-primary/30' : 'glass-card text-slate-400 hover:text-white']">
          {{ s }}
        </button>
      </div>
      <div class="flex items-center gap-2 ml-auto">
        <select v-model="severityFilter"
          class="bg-white/5 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none">
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="major">Major</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>
        <button v-if="selected.length" @click="bulkAck"
          class="btn-primary flex items-center gap-2 text-xs py-1.5">
          <CheckCheck :size="13" /> Acknowledge ({{ selected.length }})
        </button>
      </div>
    </div>

    <!-- Alert list -->
    <div class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-white/[0.02] border-b border-white/10">
              <th class="px-4 py-3 w-8">
                <input type="checkbox" @change="toggleAll" class="accent-primary w-3 h-3" />
              </th>
              <th class="table-header text-left">Severity</th>
              <th class="table-header text-left">Message</th>
              <th class="table-header text-left">OLT</th>
              <th class="table-header text-left">Status</th>
              <th class="table-header text-left">First Seen</th>
              <th class="table-header text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading" v-for="n in 5" :key="n" class="border-b border-white/5">
              <td v-for="c in 7" :key="c" class="px-4 py-3"><div class="h-4 bg-white/5 rounded animate-pulse" /></td>
            </tr>
            <tr v-else v-for="alert in filtered" :key="alert.id"
              class="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
              <td class="px-4 py-3">
                <input type="checkbox" v-model="selected" :value="alert.id" class="accent-primary w-3 h-3" />
              </td>
              <td class="table-cell">
                <div class="flex items-center gap-2">
                  <span :class="['w-2 h-2 rounded-full shrink-0', severityDot(alert.severity)]" />
                  <WidgetsAlertBadge :severity="alert.severity" />
                </div>
              </td>
              <td class="table-cell max-w-xs">
                <p class="text-xs text-slate-300 truncate">{{ alert.message }}</p>
                <p v-if="alert.value" class="text-[10px] text-slate-600 font-mono">val: {{ alert.value }}</p>
              </td>
              <td class="table-cell text-xs font-mono">{{ alert.olt_hostname ?? '—' }}</td>
              <td class="table-cell"><WidgetsAlertBadge :severity="alert.status" /></td>
              <td class="table-cell text-xs text-slate-500">{{ formatTime(alert.first_seen) }}</td>
              <td class="table-cell text-center">
                <button v-if="alert.status === 'active'" @click="ack(alert.id)"
                  class="text-[10px] px-2 py-1 rounded-lg bg-primary/15 text-primary hover:bg-primary/25 transition-colors border border-primary/20">
                  Acknowledge
                </button>
                <span v-else class="text-[10px] text-slate-600">,</span>
              </td>
            </tr>
            <tr v-if="!loading && filtered.length === 0">
              <td colspan="7" class="px-4 py-12 text-center text-slate-600 text-xs">No alerts found</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="flex items-center justify-between px-4 py-3 border-t border-white/10">
        <p class="text-xs text-slate-500">{{ filtered.length }} alerts</p>
        <p v-if="selected.length" class="text-xs text-primary">{{ selected.length }} selected</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CheckCheck } from 'lucide-vue-next'

const { list, acknowledge, bulkAcknowledge } = useAlerts()
const alerts = ref<any[]>([])
const loading = ref(true)
const selected = ref<string[]>([])
const statusFilter = ref('all')
const severityFilter = ref('')

onMounted(async () => {
  try {
    const { data } = await list({ page_size: 100 })
    alerts.value = data.results ?? data
  } catch { alerts.value = [] }
  finally { loading.value = false }
})

const filtered = computed(() => alerts.value.filter(a => {
  const matchStatus = statusFilter.value === 'all' || a.status === statusFilter.value
  const matchSeverity = !severityFilter.value || a.severity === severityFilter.value
  return matchStatus && matchSeverity
}))

const toggleAll = (e: Event) => {
  selected.value = (e.target as HTMLInputElement).checked ? filtered.value.map(a => a.id) : []
}

const ack = async (id: string) => {
  await acknowledge(id)
  const alert = alerts.value.find(a => a.id === id)
  if (alert) alert.status = 'acknowledged'
}

const bulkAck = async () => {
  await bulkAcknowledge(selected.value)
  selected.value.forEach(id => {
    const alert = alerts.value.find(a => a.id === id)
    if (alert) alert.status = 'acknowledged'
  })
  selected.value = []
}

const severityDot = (s: string) => ({ critical: 'bg-red-400', major: 'bg-orange-400', warning: 'bg-amber-400', info: 'bg-primary' }[s] ?? 'bg-slate-500')
const formatTime = (ts: string) => ts ? new Date(ts).toLocaleString('en-GB', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' }) : '—'
</script>
