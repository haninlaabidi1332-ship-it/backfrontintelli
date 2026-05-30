<template>
  <div class="space-y-5">
    <!-- Toolbar -->
    <div class="flex items-center justify-between gap-4">
      <div class="flex items-center gap-3 flex-1">
        <div class="relative flex-1 max-w-xs">
          <Search :size="13" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input v-model="search" type="text" placeholder="Search OLTs..."
            class="w-full bg-white/5 border border-white/10 rounded-xl pl-8 pr-4 py-2 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-primary/50 focus:bg-white/10 transition-all" />
        </div>
        <select v-model="statusFilter"
          class="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-primary/50">
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="degraded">Degraded</option>
          <option value="maintenance">Maintenance</option>
        </select>
      </div>
      <button @click="showAdd = true" class="btn-primary flex items-center gap-2 text-sm">
        <Plus :size="14" /> Add OLT
      </button>
    </div>

    <!-- Summary cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div v-for="stat in statusStats" :key="stat.label" class="glass-card p-4 flex items-center gap-3">
        <div :class="['w-8 h-8 rounded-xl flex items-center justify-center', stat.bg]">
          <span :class="['text-sm font-bold', stat.color]">{{ stat.count }}</span>
        </div>
        <div>
          <p class="text-xs text-slate-500">{{ stat.label }}</p>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="glass-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="bg-white/[0.02] border-b border-white/10">
              <th class="table-header text-left">Device</th>
              <th class="table-header text-left">IP Address</th>
              <th class="table-header text-left">Site</th>
              <th class="table-header text-left">Status</th>
              <th class="table-header text-left">SNMP</th>
              <th class="table-header text-left">Last Poll</th>
              <th class="table-header text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading" v-for="n in 6" :key="n" class="border-b border-white/5">
              <td v-for="c in 8" :key="c" class="px-4 py-3">
                <div class="h-4 bg-white/5 rounded animate-pulse" />
              </td>
            </tr>
            <tr v-else v-for="olt in paginated" :key="olt.id"
              class="border-b border-white/5 hover:bg-white/[0.02] transition-colors group">
              <td class="table-cell">
                <div class="flex items-center gap-2">
                  <div :class="['w-2 h-2 rounded-full shrink-0', statusDot(olt.status)]" />
                  <div>
                    <p class="text-xs font-semibold text-white">{{ olt.hostname }}</p>
                    <p class="text-[10px] text-slate-500">{{ olt.vendor_name ?? '—' }}</p>
                  </div>
                </div>
              </td>
              <td class="table-cell font-mono text-xs">{{ olt.ip_address }}</td>
              <td class="table-cell text-xs">{{ olt.site_name ?? '—' }}</td>
              <td class="table-cell"><WidgetsAlertBadge :severity="olt.status" :label="olt.status" /></td>
              <td class="table-cell">
                <span class="text-[10px] font-mono text-slate-500">v{{ olt.snmp_version }}</span>
              </td>
              <td class="table-cell text-xs text-slate-500">{{ formatTime(olt.last_polled_at) }}</td>
              <td class="table-cell text-center">
                <div class="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click="navigateTo(`/olts/${olt.id}`)"
                    class="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-primary/20 text-slate-500 hover:text-primary transition-colors">
                    <Eye :size="12" />
                  </button>
                  <button @click="editOlt(olt)"
                    class="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-white/10 text-slate-500 hover:text-white transition-colors">
                    <Pencil :size="12" />
                  </button>
                  <button @click="confirmDelete(olt)"
                    class="w-6 h-6 flex items-center justify-center rounded-lg hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-colors">
                    <Trash2 :size="12" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && filtered.length === 0">
              <td colspan="8" class="px-4 py-12 text-center text-slate-600 text-xs">No OLTs found</td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Pagination -->
      <div class="flex items-center justify-between px-4 py-3 border-t border-white/10">
        <p class="text-xs text-slate-500">{{ filtered.length }} devices</p>
        <div class="flex items-center gap-1">
          <button @click="page = Math.max(1, page - 1)" :disabled="page === 1"
            class="w-7 h-7 glass-card flex items-center justify-center hover:border-primary/30 transition-all disabled:opacity-30">
            <ChevronLeft :size="12" class="text-slate-400" />
          </button>
          <span class="text-xs text-slate-400 px-2">{{ page }} / {{ totalPages }}</span>
          <button @click="page = Math.min(totalPages, page + 1)" :disabled="page >= totalPages"
            class="w-7 h-7 glass-card flex items-center justify-center hover:border-primary/30 transition-all disabled:opacity-30">
            <ChevronRight :size="12" class="text-slate-400" />
          </button>
        </div>
      </div>
    </div>

    <!-- Add OLT Modal -->
    <Teleport to="body">
      <div v-if="showAdd" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" @click.self="showAdd = false">
        <div class="glass-card p-6 w-full max-w-lg">
          <div class="flex items-center justify-between mb-5">
            <p class="text-sm font-semibold text-white">Add OLT Device</p>
            <button @click="showAdd = false" class="text-slate-500 hover:text-white transition-colors">
              <X :size="16" />
            </button>
          </div>
          <form @submit.prevent="submitAdd" class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="text-xs text-slate-500 mb-1 block">Hostname *</label>
                <input v-model="form.hostname" required placeholder="OLT-TUN-03"
                  class="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-primary/50" />
              </div>
              <div>
                <label class="text-xs text-slate-500 mb-1 block">IP Address *</label>
                <input v-model="form.ip_address" required placeholder="10.10.1.3"
                  class="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-primary/50" />
              </div>
              <div>
                <label class="text-xs text-slate-500 mb-1 block">Vendor *</label>
                <select v-model="form.vendor" required @change="form.device_type = ''"
                  class="w-full bg-[#0d1526] border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-primary/50">
                  <option value="">Select vendor</option>
                  <option v-for="v in vendors" :key="v.id" :value="v.id">{{ v.name }}</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-slate-500 mb-1 block">Device Type *</label>
                <select v-model="form.device_type" required
                  class="w-full bg-[#0d1526] border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-primary/50">
                  <option value="">Select model</option>
                  <option v-for="dt in filteredDeviceTypes" :key="dt.id" :value="dt.id">{{ dt.model }}</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-slate-500 mb-1 block">Site *</label>
                <select v-model="form.site" required
                  class="w-full bg-[#0d1526] border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-primary/50">
                  <option value="">Select site</option>
                  <option v-for="s in sites" :key="s.id" :value="s.id">{{ s.name }}</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-slate-500 mb-1 block">SNMP Version</label>
                <select v-model="form.snmp_version"
                  class="w-full bg-[#0d1526] border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-primary/50">
                  <option value="2c">v2c</option>
                  <option value="1">v1</option>
                  <option value="3">v3</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-slate-500 mb-1 block">Community</label>
                <input v-model="form.snmp_community" placeholder="public"
                  class="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-primary/50" />
              </div>
            </div>
            <div v-if="addError" class="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{{ addError }}</div>
            <div class="flex gap-3 pt-1">
              <button type="button" @click="showAdd = false" class="flex-1 btn-ghost text-sm">Cancel</button>
              <button type="submit" :disabled="addBusy" class="flex-1 btn-primary text-sm flex items-center justify-center gap-2">
                <Loader2 v-if="addBusy" :size="13" class="animate-spin" />
                {{ addBusy ? 'Adding...' : 'Add OLT' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- View/Edit OLT Modal -->
    <Teleport to="body">
      <div v-if="selectedOlt" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" @click.self="selectedOlt = null">
        <div class="glass-card p-6 w-full max-w-md">
          <div class="flex items-center justify-between mb-5">
            <div>
              <p class="text-sm font-semibold text-white">{{ selectedOlt.hostname }}</p>
              <p class="text-[10px] text-slate-500 font-mono">{{ selectedOlt.ip_address }}</p>
            </div>
            <button @click="selectedOlt = null" class="text-slate-500 hover:text-white transition-colors">
              <X :size="16" />
            </button>
          </div>
          <div class="space-y-2">
            <div v-for="(val, key) in oltDetails" :key="key" class="flex justify-between items-center py-1.5 border-b border-white/5">
              <span class="text-xs text-slate-500 capitalize">{{ key }}</span>
              <span class="text-xs font-mono text-slate-300">{{ val }}</span>
            </div>
          </div>
          <div v-if="editMode" class="mt-4 pt-4 border-t border-white/10 space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="text-xs text-slate-500 mb-1 block">Status</label>
                <select v-model="editForm.status"
                  class="w-full bg-[#0d1526] border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none">
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="degraded">Degraded</option>
                  <option value="maintenance">Maintenance</option>
                </select>
              </div>
              <div>
                <label class="text-xs text-slate-500 mb-1 block">Community</label>
                <input v-model="editForm.snmp_community"
                  class="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-300 focus:outline-none" />
              </div>
            </div>
            <div v-if="editError" class="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">{{ editError }}</div>
            <button @click="saveEdit" :disabled="editBusy" class="w-full btn-primary text-sm flex items-center justify-center gap-2">
              <Loader2 v-if="editBusy" :size="13" class="animate-spin" />
              {{ editBusy ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
          <div class="flex gap-3 mt-4">
            <button v-if="!editMode" @click="editMode = true" class="flex-1 btn-ghost text-sm flex items-center justify-center gap-1">
              <Pencil :size="13" /> Edit
            </button>
            <button v-else @click="editMode = false" class="flex-1 btn-ghost text-sm">Cancel Edit</button>
            <button @click="selectedOlt = null" class="flex-1 btn-ghost text-sm">Close</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" @click.self="deleteTarget = null">
        <div class="glass-card p-6 w-full max-w-sm">
          <div class="flex items-start gap-4 mb-5">
            <div class="w-10 h-10 rounded-xl bg-red-500/15 flex items-center justify-center shrink-0">
              <Trash2 :size="18" class="text-red-400" />
            </div>
            <div>
              <p class="text-sm font-semibold" :style="{ color: 'var(--text-primary)' }">Delete OLT</p>
              <p class="text-xs mt-1" :style="{ color: 'var(--text-muted)' }">
                Are you sure you want to delete <span class="font-semibold text-red-400">{{ deleteTarget.hostname }}</span>?
                This will remove all associated data. This action cannot be undone.
              </p>
            </div>
          </div>
          <div v-if="deleteError" class="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2 mb-3">{{ deleteError }}</div>
          <div class="flex gap-3">
            <button @click="deleteTarget = null" class="flex-1 btn-ghost text-sm">Cancel</button>
            <button @click="doDelete" :disabled="deleteBusy"
              class="flex-1 text-sm font-semibold px-4 py-2 rounded-xl bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 transition-all disabled:opacity-40 flex items-center justify-center gap-2">
              <Loader2 v-if="deleteBusy" :size="13" class="animate-spin" />
              {{ deleteBusy ? 'Deleting...' : 'Delete' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { Search, Plus, Eye, Pencil, ChevronLeft, ChevronRight, X, Loader2, Trash2 } from 'lucide-vue-next'

const api = useApi()
const { list, create, update, delete: deleteOlt } = useOlts()
const toast = useToast()
const olts = ref<any[]>([])
const loading = ref(true)
const search = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = 10

// Add OLT modal
const showAdd = ref(false)
const addBusy = ref(false)
const addError = ref('')
const vendors = ref<any[]>([])
const sites = ref<any[]>([])
const deviceTypes = ref<any[]>([])
const form = reactive({ hostname: '', ip_address: '', vendor: '', device_type: '', site: '', snmp_version: '2c', snmp_community: 'public', status: 'active' })

const filteredDeviceTypes = computed(() =>
  form.vendor ? deviceTypes.value.filter(dt => dt.vendor === form.vendor || dt.vendor_id === form.vendor) : deviceTypes.value
)

// Delete modal
const deleteTarget = ref<any>(null)
const deleteBusy = ref(false)
const deleteError = ref('')

function confirmDelete(olt: any) {
  deleteTarget.value = olt
  deleteError.value = ''
}

async function doDelete() {
  if (!deleteTarget.value) return
  deleteBusy.value = true
  deleteError.value = ''
  try {
    const name = deleteTarget.value.hostname
    await deleteOlt(deleteTarget.value.id)
    olts.value = olts.value.filter(o => o.id !== deleteTarget.value.id)
    deleteTarget.value = null
    toast.success(`OLT ${name} deleted`)
  } catch (err: any) {
    deleteError.value = err?.response?.data?.detail ?? err?.response?.data?.message ?? 'Failed to delete OLT'
    toast.error(deleteError.value)
  } finally {
    deleteBusy.value = false
  }
}

// View/Edit modal
const selectedOlt = ref<any>(null)
const editMode = ref(false)
const editBusy = ref(false)
const editError = ref('')
const editForm = reactive({ status: '', snmp_community: '' })

onMounted(async () => {
  try {
    const { data } = await list({ page_size: 50 })
    olts.value = data.results ?? data
  } catch { olts.value = [] }
  finally { loading.value = false }

  // Fetch vendors, sites, device types for the Add modal
  try {
    const [vRes, sRes, dtRes] = await Promise.all([
      api.get('/equipements/vendors/'),
      api.get('/equipements/sites/'),
      api.get('/equipements/device-types/?page_size=100')
    ])
    vendors.value = vRes.data.results ?? vRes.data
    sites.value = sRes.data.results ?? sRes.data
    deviceTypes.value = dtRes.data.results ?? dtRes.data
  } catch {}
})

const filtered = computed(() => {
  const q = search.value.toLowerCase()
  return olts.value.filter(o => {
    const matchSearch = !q || o.hostname?.toLowerCase().includes(q) || o.ip_address?.includes(q)
    const matchStatus = !statusFilter.value || o.status === statusFilter.value
    return matchSearch && matchStatus
  })
})

// Reset page when filters change
watch([search, statusFilter], () => { page.value = 1 })

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))
const paginated  = computed(() => filtered.value.slice((page.value - 1) * pageSize, page.value * pageSize))

const statusStats = computed(() => {
  const counts = { active: 0, inactive: 0, degraded: 0, maintenance: 0 }
  olts.value.forEach(o => { if (counts[o.status as keyof typeof counts] !== undefined) counts[o.status as keyof typeof counts]++ })
  return [
    { label: 'Active',      count: counts.active,      bg: 'bg-emerald-500/15', color: 'text-emerald-400' },
    { label: 'Inactive',    count: counts.inactive,    bg: 'bg-slate-500/15',   color: 'text-slate-400' },
    { label: 'Degraded',    count: counts.degraded,    bg: 'bg-amber-500/15',   color: 'text-amber-400' },
    { label: 'Maintenance', count: counts.maintenance, bg: 'bg-blue-500/15',    color: 'text-blue-400' }
  ]
})

function editOlt(olt: any) {
  selectedOlt.value = olt
  editMode.value = true
  editForm.status = olt.status
  editForm.snmp_community = olt.snmp_community ?? 'public'
}

const oltDetails = computed(() => {
  if (!selectedOlt.value) return {}
  const o = selectedOlt.value
  return {
    Vendor:        o.vendor_name ?? '—',
    Site:          o.site_name ?? '—',
    Status:        o.status,
    'SNMP Version': `v${o.snmp_version}`,
    'Max Ports':   o.max_pon_ports ?? 16,
    'Last Polled': formatTime(o.last_polled_at),
  }
})

async function submitAdd() {
  addBusy.value = true
  addError.value = ''
  try {
    const { data } = await create(form)
    olts.value.unshift(data)
    showAdd.value = false
    Object.assign(form, { hostname: '', ip_address: '', vendor: '', device_type: '', site: '', snmp_version: '2c', snmp_community: 'public', status: 'active' })
    toast.success(`OLT ${data.hostname} added successfully`)
  } catch (err: any) {
    const d = err?.response?.data
    if (d && typeof d === 'object' && !d.message && !d.detail) {
      // DRF field-level errors: { field: ["msg"], ... }
      const msgs = Object.entries(d)
        .map(([field, errs]) => `${field}: ${(errs as string[]).join(', ')}`)
        .join(' | ')
      addError.value = msgs
    } else {
      addError.value = d?.message ?? d?.detail ?? 'Failed to add OLT'
    }
  } finally {
    addBusy.value = false
  }
}

async function saveEdit() {
  editBusy.value = true
  editError.value = ''
  try {
    await update(selectedOlt.value.id, {
      status: editForm.status,
      snmp_community: editForm.snmp_community
    })
    // Directly update the item in the list by ID , avoids serializer mismatch
    const idx = olts.value.findIndex(o => o.id === selectedOlt.value.id)
    if (idx !== -1) {
      olts.value[idx].status = editForm.status
      olts.value[idx].snmp_community = editForm.snmp_community
    }
    editMode.value = false
    selectedOlt.value = null
    toast.success('OLT updated successfully')
  } catch (err: any) {
    const d = err?.response?.data
    if (d && typeof d === 'object' && !d.message && !d.detail) {
      editError.value = Object.entries(d)
        .map(([f, e]) => `${f}: ${(e as string[]).join(', ')}`)
        .join(' | ')
    } else {
      editError.value = d?.message ?? d?.detail ?? 'Failed to save changes'
    }
    toast.error(editError.value)
  } finally {
    editBusy.value = false
  }
}

const statusDot = (s: string) => ({
  active: 'bg-emerald-400', inactive: 'bg-slate-500', degraded: 'bg-amber-400', maintenance: 'bg-blue-400'
}[s] ?? 'bg-slate-500')

const formatTime = (ts: string) => ts ? new Date(ts).toLocaleString('en-GB', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' }) : '—'
</script>
