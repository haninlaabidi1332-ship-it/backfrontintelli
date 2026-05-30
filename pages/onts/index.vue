<template>
  <div class="space-y-5">
    <div class="flex items-center gap-3">
      <div class="relative flex-1 max-w-sm">
        <Search :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
        <input v-model="search" type="text" placeholder="Search by serial, IP, customer..."
          class="w-full bg-white/5 border border-white/10 rounded-xl pl-8 pr-4 py-2 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-primary/50 transition-all" />
      </div>
      <select v-model="statusFilter" class="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none">
        <option value="">All Status</option>
        <option value="online">Online</option>
        <option value="offline">Offline</option>
        <option value="los">LOS</option>
        <option value="degraded">Degraded</option>
      </select>
    </div>

    <!-- Status summary -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div v-for="stat in stats" :key="stat.label" :class="['glass-card p-4 flex items-center gap-3', stat.glow]">
        <div :class="['w-8 h-8 rounded-xl flex items-center justify-center text-sm font-bold', stat.bg, stat.color]">
          {{ stat.count }}
        </div>
        <p class="text-xs text-slate-400">{{ stat.label }}</p>
      </div>
    </div>

    <!-- Table -->
    <div class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-white/[0.02] border-b border-white/10">
              <th class="table-header text-left">Serial</th>
              <th class="table-header text-left">MAC Address</th>
              <th class="table-header text-left">OLT</th>
              <th class="table-header text-left">Status</th>
              <th class="table-header text-right">RX Power</th>
              <th class="table-header text-right">TX Power</th>
              <th class="table-header text-left">Service</th>
              <th class="table-header text-left">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading" v-for="n in 6" :key="n" class="border-b border-white/5">
              <td v-for="c in 8" :key="c" class="px-4 py-3"><div class="h-4 bg-white/5 rounded animate-pulse" /></td>
            </tr>
            <tr v-else v-for="ont in filtered" :key="ont.id" class="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
              <td class="table-cell font-mono text-xs text-white">{{ ont.serial_number }}</td>
              <td class="table-cell font-mono text-xs">{{ ont.mac_address }}</td>
              <td class="table-cell text-xs">{{ ont.olt_hostname ?? '—' }}</td>
              <td class="table-cell">
                <div class="flex items-center gap-1.5">
                  <span :class="['w-1.5 h-1.5 rounded-full', statusDot(ont.status)]" />
                  <WidgetsAlertBadge :severity="statusBadge(ont.status)" :label="ont.status" />
                </div>
              </td>
              <td class="table-cell text-right">
                <span :class="['text-xs font-mono', rxColor(ont.rx_power)]">{{ ont.rx_power?.toFixed(1) ?? '—' }} dBm</span>
              </td>
              <td class="table-cell text-right text-xs font-mono text-slate-400">{{ ont.tx_power?.toFixed(1) ?? '—' }} dBm</td>
              <td class="table-cell"><span class="badge-neutral capitalize text-[10px]">{{ ont.service_type }}</span></td>
              <td class="table-cell text-xs text-slate-500">{{ formatTime(ont.last_seen_at) }}</td>
            </tr>
            <tr v-if="!loading && filtered.length === 0">
              <td colspan="8" class="px-4 py-12 text-center text-slate-600 text-xs">No ONTs found</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="px-4 py-3 border-t border-white/10">
        <p class="text-xs text-slate-500">{{ filtered.length }} ONTs</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search } from 'lucide-vue-next'

const { list } = useOnts()
const onts = ref<any[]>([])
const loading = ref(true)
const search = ref('')
const statusFilter = ref('')

onMounted(async () => {
  try {
    const { data } = await list({ page_size: 100 })
    onts.value = data.results ?? data
  } catch { onts.value = [] }
  finally { loading.value = false }
})

const filtered = computed(() => onts.value.filter(o => {
  const q = search.value.toLowerCase()
  const matchSearch = !q || o.serial_number?.toLowerCase().includes(q) || o.mac_address?.includes(q) || o.ip_address?.includes(q)
  const matchStatus = !statusFilter.value || o.status === statusFilter.value
  return matchSearch && matchStatus
}))

const stats = computed(() => {
  const c = { online: 0, offline: 0, los: 0, degraded: 0 }
  onts.value.forEach(o => { if (o.status in c) c[o.status as keyof typeof c]++ })
  return [
    { label: 'Online',   count: c.online,   bg: 'bg-emerald-500/15', color: 'text-emerald-400', glow: 'glow-green' },
    { label: 'Offline',  count: c.offline,  bg: 'bg-slate-500/15',   color: 'text-slate-400',   glow: '' },
    { label: 'LOS',      count: c.los,      bg: 'bg-red-500/15',     color: 'text-red-400',     glow: 'glow-red' },
    { label: 'Degraded', count: c.degraded, bg: 'bg-amber-500/15',   color: 'text-amber-400',   glow: '' }
  ]
})

const statusDot = (s: string) => ({ online: 'bg-emerald-400', offline: 'bg-slate-500', los: 'bg-red-400', degraded: 'bg-amber-400' }[s] ?? 'bg-slate-500')
const statusBadge = (s: string) => ({ online: 'resolved', offline: 'neutral', los: 'critical', degraded: 'warning' }[s] ?? 'neutral')
const rxColor = (v: number) => v && v < -27 ? 'text-red-400' : v && v < -20 ? 'text-amber-400' : 'text-emerald-400'
const formatTime = (ts: string) => ts ? new Date(ts).toLocaleString('en-GB', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' }) : '—'
</script>
