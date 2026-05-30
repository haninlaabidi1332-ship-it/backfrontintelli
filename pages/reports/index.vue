<template>
  <div class="space-y-5">
    <!-- Generate report form -->
    <div class="glass-card p-5">
      <p class="text-sm font-semibold mb-4" :style="{ color: 'var(--text-primary)' }">Generate Report</p>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label class="text-xs mb-1 block" :style="{ color: 'var(--text-muted)' }">Report Name</label>
          <input v-model="form.name" type="text" placeholder="Q2 Network Report"
            class="w-full rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
            :style="{ background: 'var(--bg-input)', border: '1px solid var(--border)', color: 'var(--text-primary)' }" />
        </div>
        <div>
          <label class="text-xs mb-1 block" :style="{ color: 'var(--text-muted)' }">Type</label>
          <select v-model="form.report_type"
            class="w-full rounded-xl px-3 py-2 text-xs focus:outline-none"
            :style="{ background: 'var(--bg-input)', border: '1px solid var(--border)', color: 'var(--text-primary)' }">
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="custom">Custom</option>
          </select>
        </div>
        <div>
          <label class="text-xs mb-1 block" :style="{ color: 'var(--text-muted)' }">From</label>
          <input v-model="form.date_from" type="datetime-local"
            class="w-full rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary/50"
            :style="{ background: 'var(--bg-input)', border: '1px solid var(--border)', color: 'var(--text-primary)' }" />
        </div>
        <div>
          <label class="text-xs mb-1 block" :style="{ color: 'var(--text-muted)' }">To</label>
          <input v-model="form.date_to" type="datetime-local"
            class="w-full rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary/50"
            :style="{ background: 'var(--bg-input)', border: '1px solid var(--border)', color: 'var(--text-primary)' }" />
        </div>
      </div>

      <div v-if="genError" class="mt-3 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
        {{ genError }}
      </div>

      <div class="flex items-center gap-3 mt-4">
        <button @click="generateReport('pdf')" :disabled="genBusy"
          class="btn-primary flex items-center gap-2 text-sm disabled:opacity-40">
          <Loader2 v-if="genBusy && genFormat === 'pdf'" :size="14" class="animate-spin" />
          <FileText v-else :size="14" />
          Generate PDF
        </button>
        <button @click="generateReport('xlsx')" :disabled="genBusy"
          class="btn-ghost flex items-center gap-2 text-sm disabled:opacity-40">
          <Loader2 v-if="genBusy && genFormat === 'xlsx'" :size="14" class="animate-spin" />
          <Table2 v-else :size="14" />
          Generate Excel
        </button>
      </div>
    </div>

    <!-- Reports list -->
    <div class="glass-card overflow-hidden">
      <div class="px-5 py-4" :style="{ borderBottom: '1px solid var(--border)' }">
        <p class="text-sm font-semibold" :style="{ color: 'var(--text-primary)' }">Generated Reports</p>
      </div>
      <div class="divide-y" :style="{ '--tw-divide-opacity': 1 }">
        <div v-for="report in reports" :key="report.id"
          class="flex items-center justify-between px-5 py-4 transition-colors hover:bg-white/[0.02]">
          <div class="flex items-center gap-3">
            <div :class="['w-9 h-9 rounded-xl flex items-center justify-center', report.format === 'pdf' ? 'bg-red-500/15' : 'bg-emerald-500/15']">
              <FileText :size="15" :class="report.format === 'pdf' ? 'text-red-400' : 'text-emerald-400'" />
            </div>
            <div>
              <p class="text-xs font-semibold" :style="{ color: 'var(--text-primary)' }">{{ report.name }}</p>
              <p class="text-[10px]" :style="{ color: 'var(--text-muted)' }">
                {{ report.report_type }} · {{ report.format?.toUpperCase() }} · {{ formatTime(report.generated_at) }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <WidgetsAlertBadge :severity="statusBadge(report.status)" :label="report.status" />
            <button v-if="report.status === 'ready'" @click="download(report)"
              class="w-7 h-7 glass-card flex items-center justify-center hover:border-primary/30 transition-all">
              <Download :size="12" class="text-slate-400 hover:text-primary" />
            </button>
          </div>
        </div>
        <div v-if="reports.length === 0" class="px-5 py-12 text-center text-xs" :style="{ color: 'var(--text-muted)' }">
          No reports yet
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FileText, Table2, Download, Loader2 } from 'lucide-vue-next'

const { list, create, download: downloadReport } = useReports()
const reports = ref<any[]>([])
const genBusy = ref(false)
const genFormat = ref('')
const genError = ref('')

const form = reactive({
  name: '',
  report_type: 'daily',
  date_from: '',
  date_to: ''
})

onMounted(async () => {
  try {
    const { data } = await list()
    reports.value = data.results ?? data
  } catch {}
})

// Convert datetime-local string "2026-05-21T18:00" → ISO "2026-05-21T18:00:00Z"
function toISO(local: string) {
  if (!local) return ''
  return new Date(local).toISOString()
}

const generateReport = async (format: string) => {
  genBusy.value = true
  genFormat.value = format
  genError.value = ''
  try {
    const payload = {
      name: form.name || `${form.report_type} report`,
      report_type: form.report_type,
      format,
      date_from: toISO(form.date_from),
      date_to: toISO(form.date_to)
    }
    const { data } = await create(payload)
    reports.value.unshift(data)
  } catch (err: any) {
    const d = err?.response?.data
    if (d && typeof d === 'object' && !d.message && !d.detail) {
      genError.value = Object.entries(d).map(([f, e]) => `${f}: ${(e as string[]).join(', ')}`).join(' | ')
    } else {
      genError.value = d?.message ?? d?.detail ?? 'Failed to generate report'
    }
  } finally {
    genBusy.value = false
    genFormat.value = ''
  }
}

const download = async (report: any) => {
  try {
    const { data } = await downloadReport(report.id)
    const ext = report.format === 'pdf' ? 'pdf' : 'xlsx'
    const mime = report.format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    const url = URL.createObjectURL(new Blob([data], { type: mime }))
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.name ?? 'report'}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    genError.value = 'Failed to download report'
  }
}

const statusBadge = (s: string) => ({ ready: 'resolved', pending: 'info', generating: 'warning', failed: 'critical' }[s] ?? 'neutral')
const formatTime = (ts: string) => ts ? new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'
</script>
