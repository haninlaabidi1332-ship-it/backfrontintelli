<template>
  <div class="space-y-5">

    <!-- Stat cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <WidgetsStatCard label="Total Sessions" :value="sessions.length"      :icon="Activity"  color="cyan"  />
      <WidgetsStatCard label="UP Sessions"    :value="upCount"              :icon="ArrowUp"   color="green" />
      <WidgetsStatCard label="DOWN Sessions"  :value="downCount"            :icon="ArrowDown" color="red"   />
      <WidgetsStatCard label="Avg Loss Rate"  :value="avgLoss.toFixed(2)"   :icon="Wifi"      color="amber" suffix="%" />
    </div>

    <!-- ── Active BFD Alerts ───────────────────────────────────────────────── -->
    <div class="glass-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-4 border-b border-white/10"
        :class="activeAlerts.length ? 'bg-red-500/5' : ''">
        <div class="flex items-center gap-2">
          <ShieldAlert :size="14" :class="activeAlerts.length ? 'text-red-400' : 'text-slate-500'" />
          <p class="text-sm font-semibold text-white">BFD Alerts</p>
          <span v-if="activeAlerts.length"
            class="text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30 px-2 py-0.5 rounded-full">
            {{ activeAlerts.length }} active
          </span>
        </div>
      </div>

      <!-- No alerts state -->
      <div v-if="!loadingAlerts && activeAlerts.length === 0"
        class="flex items-center gap-3 px-5 py-4 text-emerald-400">
        <CheckCircle :size="14" />
        <span class="text-xs font-medium">No active BFD alerts , all sessions within thresholds</span>
      </div>

      <!-- Alerts table -->
      <div v-else-if="activeAlerts.length" class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-white/[0.02] border-b border-white/10">
              <th class="table-header text-left">Session</th>
              <th class="table-header text-left">Site</th>
              <th class="table-header text-left">Severity</th>
              <th class="table-header text-left">Message</th>
              <th class="table-header text-right">First Seen</th>
              <th class="table-header text-center">Status</th>
              <th class="table-header text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in activeAlerts" :key="a.id"
              class="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
              <td class="table-cell text-xs font-mono text-slate-300">{{ a.session_name }}</td>
              <td class="table-cell text-xs text-slate-400">{{ getSite(a.session_name) }}</td>
              <td class="table-cell">
                <WidgetsAlertBadge :severity="a.severity" :label="a.severity" />
              </td>
              <td class="table-cell text-xs text-slate-400 max-w-[260px] truncate">{{ a.message }}</td>
              <td class="table-cell text-right text-xs text-slate-500 font-mono">{{ formatTime(a.first_seen) }}</td>
              <td class="table-cell text-center">
                <span :class="['text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full',
                  a.status === 'active'       ? 'bg-red-500/15 text-red-400' :
                  a.status === 'acknowledged' ? 'bg-amber-500/15 text-amber-400' :
                  'bg-emerald-500/15 text-emerald-400']">
                  {{ a.status }}
                </span>
              </td>
              <td class="table-cell text-center">
                <button v-if="a.status === 'active'"
                  @click="acknowledge(a)"
                  :disabled="ackBusy[a.id]"
                  class="text-[10px] px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-all disabled:opacity-40">
                  Acknowledge
                </button>
                <span v-else class="text-[10px] text-slate-600">,</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Sessions table ─────────────────────────────────────────────────── -->
    <div class="glass-card overflow-hidden">
      <div class="px-5 py-4 border-b border-white/10">
        <p class="text-sm font-semibold text-white">WAN Sessions</p>
        <p class="text-[10px] text-slate-500 mt-0.5">IPSec + MPLS dual-path monitoring · HQ ↔ Branches</p>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-white/[0.02] border-b border-white/10">
              <th class="table-header text-left">Site</th>
              <th class="table-header text-left">Link</th>
              <th class="table-header text-left">Session</th>
              <th class="table-header text-left">State</th>
              <th class="table-header text-right">Loss Rate</th>
              <th class="table-header text-right">Availability</th>
              <th class="table-header text-right">Flaps</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading" v-for="n in 6" :key="n" class="border-b border-white/5">
              <td v-for="c in 7" :key="c" class="px-4 py-3">
                <div class="h-4 bg-white/5 rounded animate-pulse" />
              </td>
            </tr>
            <tr v-else v-for="s in sessions" :key="s.id"
              class="border-b border-white/5 hover:bg-white/[0.02] transition-colors">

              <!-- Site -->
              <td class="table-cell">
                <div class="flex items-center gap-1.5">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                  <span class="text-xs font-medium text-slate-300">{{ getSite(s.name) }}</span>
                </div>
              </td>

              <!-- Link type -->
              <td class="table-cell">
                <span :class="['text-[10px] font-semibold px-2 py-0.5 rounded-full border',
                  ismpls(s.name)
                    ? 'bg-purple-500/15 text-purple-400 border-purple-500/25'
                    : 'bg-cyan-500/15 text-cyan-400 border-cyan-500/25']">
                  {{ ismpls(s.name) ? 'MPLS' : 'IPSec' }}
                </span>
              </td>

              <!-- Session name -->
              <td class="table-cell">
                <p class="text-xs font-medium text-white">{{ s.name }}</p>
                <p class="text-[10px] text-slate-600 font-mono">{{ s.peer_ip }}</p>
              </td>

              <!-- State -->
              <td class="table-cell">
                <div class="flex items-center gap-1.5">
                  <span :class="['w-2 h-2 rounded-full shrink-0',
                    s.state === 'up' ? 'bg-emerald-400 animate-pulse-slow' : 'bg-red-400']" />
                  <span :class="['text-xs font-semibold uppercase',
                    s.state === 'up' ? 'text-emerald-400' : 'text-red-400']">
                    {{ s.state }}
                  </span>
                </div>
              </td>

              <!-- Loss rate -->
              <td class="table-cell text-right">
                <span :class="['text-xs font-mono',
                  s.loss_rate_pct > 5  ? 'text-red-400' :
                  s.loss_rate_pct > 1  ? 'text-amber-400' : 'text-emerald-400']">
                  {{ s.loss_rate_pct?.toFixed(2) }}%
                </span>
              </td>

              <!-- Availability -->
              <td class="table-cell text-right text-xs font-mono text-slate-300">
                {{ s.availability_pct?.toFixed(1) }}%
              </td>

              <!-- Flaps -->
              <td class="table-cell text-right">
                <span :class="['text-xs font-mono',
                  s.flap_count > 5 ? 'text-amber-400' : 'text-slate-400']">
                  {{ s.flap_count ?? 0 }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── State History ──────────────────────────────────────────────────── -->
    <div class="glass-card overflow-hidden">
      <div class="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div>
          <p class="text-sm font-semibold text-white">State History</p>
          <p class="text-[10px] text-slate-500 mt-0.5">Recent UP ↔ DOWN transitions detected by BFD</p>
        </div>
        <span class="text-[10px] text-slate-500">{{ stateHistory.length }} transitions</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-white/[0.02] border-b border-white/10">
              <th class="table-header text-left">Session</th>
              <th class="table-header text-left">Site</th>
              <th class="table-header text-left">Link</th>
              <th class="table-header text-left">Transition</th>
              <th class="table-header text-right">Duration Before</th>
              <th class="table-header text-right">Detected At</th>
              <th class="table-header text-center">Alert</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingHistory" v-for="n in 5" :key="n" class="border-b border-white/5">
              <td v-for="c in 7" :key="c" class="px-4 py-3">
                <div class="h-4 bg-white/5 rounded animate-pulse" />
              </td>
            </tr>
            <tr v-else v-for="h in stateHistory" :key="h.id"
              class="border-b border-white/5 hover:bg-white/[0.02] transition-colors">

              <td class="table-cell text-xs font-mono text-slate-300">{{ h.session_name }}</td>

              <td class="table-cell text-xs text-slate-400">{{ getSite(h.session_name) }}</td>

              <td class="table-cell">
                <span :class="['text-[10px] font-semibold px-2 py-0.5 rounded-full border',
                  ismpls(h.session_name)
                    ? 'bg-purple-500/15 text-purple-400 border-purple-500/25'
                    : 'bg-cyan-500/15 text-cyan-400 border-cyan-500/25']">
                  {{ ismpls(h.session_name) ? 'MPLS' : 'IPSec' }}
                </span>
              </td>

              <!-- Transition badge -->
              <td class="table-cell">
                <div class="flex items-center gap-1.5">
                  <span :class="['text-[10px] font-bold uppercase px-1.5 py-0.5 rounded',
                    h.previous_state === 'up' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400']">
                    {{ h.previous_state?.toUpperCase() }}
                  </span>
                  <ArrowRight :size="10" class="text-slate-600" />
                  <span :class="['text-[10px] font-bold uppercase px-1.5 py-0.5 rounded',
                    h.new_state === 'up' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400']">
                    {{ h.new_state?.toUpperCase() }}
                  </span>
                </div>
              </td>

              <td class="table-cell text-right text-xs font-mono text-slate-500">
                {{ formatDuration(h.duration_previous_ms) }}
              </td>

              <td class="table-cell text-right text-xs font-mono text-slate-500">
                {{ formatTime(h.timestamp) }}
              </td>

              <td class="table-cell text-center">
                <span v-if="h.triggered_alert" class="text-[10px] text-red-400 font-semibold">⚠ Yes</span>
                <span v-else class="text-[10px] text-slate-600">,</span>
              </td>
            </tr>
            <tr v-if="!loadingHistory && stateHistory.length === 0">
              <td colspan="7" class="px-4 py-8 text-center text-slate-600 text-xs">
                No state transitions recorded yet
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { Activity, ArrowUp, ArrowDown, Wifi, ShieldAlert, CheckCircle, ArrowRight } from 'lucide-vue-next'

const { sessions: fetchSessions, history: fetchHistory, alerts: fetchAlerts, acknowledgeAlert } = useBfd()

const sessions     = ref<any[]>([])
const stateHistory = ref<any[]>([])
const activeAlerts = ref<any[]>([])
const ackBusy      = ref<Record<string, boolean>>({})

const loading        = ref(true)
const loadingHistory = ref(true)
const loadingAlerts  = ref(true)

onMounted(async () => {
  await Promise.allSettled([loadSessions(), loadHistory(), loadAlerts()])
})

async function loadSessions() {
  try {
    const { data } = await fetchSessions({ page_size: 100 })
    sessions.value = data.results ?? data
  } catch { sessions.value = [] }
  finally { loading.value = false }
}

async function loadHistory() {
  try {
    const { data } = await fetchHistory({ page_size: 50 })
    stateHistory.value = data.results ?? data
  } catch { stateHistory.value = [] }
  finally { loadingHistory.value = false }
}

async function loadAlerts() {
  try {
    const { data } = await fetchAlerts({ page_size: 50 })
    activeAlerts.value = data.results ?? data
  } catch { activeAlerts.value = [] }
  finally { loadingAlerts.value = false }
}

async function acknowledge(alert: any) {
  ackBusy.value[alert.id] = true
  try {
    await acknowledgeAlert(alert.id)
    alert.status = 'acknowledged'
  } catch { /* silent */ }
  finally { ackBusy.value[alert.id] = false }
}

// ─── Computed ─────────────────────────────────────────────────────────────────
const upCount   = computed(() => sessions.value.filter(s => s.state === 'up').length)
const downCount = computed(() => sessions.value.filter(s => s.state !== 'up').length)
const avgLoss   = computed(() => {
  if (!sessions.value.length) return 0
  return sessions.value.reduce((sum, s) => sum + (s.loss_rate_pct ?? 0), 0) / sessions.value.length
})

// ─── Helpers ──────────────────────────────────────────────────────────────────
function getSite(name: string): string {
  const n = name?.toLowerCase() ?? ''
  if (n.includes('sfax') || n.includes('sfx'))   return 'Sfax'
  if (n.includes('nabeul') || n.includes('nbl')) return 'Nabeul'
  if (n.includes('kef'))                          return 'El Kef'
  return 'HQ'
}

const ismpls = (name: string) => name?.toLowerCase().includes('mpls')

function formatDuration(ms: number | null): string {
  if (!ms) return '—'
  if (ms < 60_000)      return `${(ms / 1000).toFixed(0)}s`
  if (ms < 3_600_000)   return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
  return `${Math.floor(ms / 3_600_000)}h ${Math.floor((ms % 3_600_000) / 60000)}m`
}

const formatTime = (ts: string) =>
  ts ? new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—'
</script>
