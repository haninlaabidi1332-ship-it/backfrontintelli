<template>
  <div class="space-y-4">

    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <p class="text-sm font-semibold text-white">Network Topology</p>
        <p class="text-xs text-slate-500 mt-0.5">
          {{ sites.length }} sites · {{ bfdSessions.length }} WAN sessions · SOTETEL Tunisia
        </p>
      </div>
      <div class="flex items-center gap-4 flex-wrap">
        <!-- Legend -->
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-1.5">
            <svg width="24" height="8"><line x1="0" y1="4" x2="24" y2="4" stroke="#06b6d4" stroke-width="2"/></svg>
            <span class="text-[10px] text-slate-500">IPSec</span>
          </div>
          <div class="flex items-center gap-1.5">
            <svg width="24" height="8"><line x1="0" y1="4" x2="24" y2="4" stroke="#a78bfa" stroke-width="2" stroke-dasharray="5,3"/></svg>
            <span class="text-[10px] text-slate-500">MPLS</span>
          </div>
          <div v-for="leg in statusLegend" :key="leg.label" class="flex items-center gap-1.5">
            <span :class="['w-2 h-2 rounded-full shrink-0', leg.dot]" />
            <span class="text-[10px] text-slate-500">{{ leg.label }}</span>
          </div>
        </div>
        <button @click="refresh" :disabled="loading"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-[11px] text-slate-400 hover:text-white transition-all disabled:opacity-40">
          <RefreshCw :size="11" :class="loading ? 'animate-spin' : ''" /> Refresh
        </button>
      </div>
    </div>

    <!-- Main grid -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">

      <!-- SVG Map (2/3 width) -->
      <div class="xl:col-span-2 glass-card overflow-hidden relative" style="min-height: 440px;">
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center z-10">
          <div class="w-7 h-7 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        </div>

        <svg v-else viewBox="0 0 460 285" class="w-full h-full" style="min-height: 400px"
          @mouseleave="hovered = null">

          <!-- Background grid -->
          <defs>
            <pattern id="topo-grid" width="30" height="30" patternUnits="userSpaceOnUse">
              <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(255,255,255,0.02)" stroke-width="0.5"/>
            </pattern>
            <filter id="node-glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" result="blur"/>
              <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
          </defs>
          <rect width="460" height="285" fill="url(#topo-grid)"/>

          <!-- Tunisia outline (shifted down 20px) -->
          <g transform="translate(0,20)">
            <path
              d="M 139,21 C 190,8 222,7 246,7 L 278,11 299,18 C 335,15 368,13 385,14 C 372,27 354,38 331,39 L 331,60 C 355,65 372,70 380,71 L 358,100 C 342,116 312,130 278,128 C 305,136 350,140 385,143 L 428,156 260,258 54,258 C 48,215 44,175 43,128 L 139,111 C 125,90 100,65 86,36 C 100,28 120,22 139,21 Z"
              fill="rgba(255,255,255,0.015)"
              stroke="rgba(255,255,255,0.055)"
              stroke-width="1"
              stroke-linejoin="round"
            />
          </g>

          <!-- ISP-WAN cloud badge -->
          <g transform="translate(215,18)">
            <rect x="-42" y="-9" width="84" height="18" rx="9"
              fill="rgba(99,102,241,0.12)" stroke="rgba(99,102,241,0.35)" stroke-width="0.8"/>
            <text text-anchor="middle" y="5" fill="rgba(167,139,250,0.85)"
              font-size="6.5" font-family="Inter,sans-serif" font-weight="600">
              ISP-WAN · EVE-NG
            </text>
          </g>

          <!-- WAN links -->
          <g v-for="link in computedLinks" :key="'link-' + link.id">

            <!-- IPSec line -->
            <line
              :x1="link.ipsec.x1" :y1="link.ipsec.y1"
              :x2="link.ipsec.x2" :y2="link.ipsec.y2"
              :stroke="ipsecColor(link.ipsecState)"
              stroke-width="1.8"
              stroke-linecap="round"
              :stroke-opacity="link.ipsecState === 'up' ? 0.9 : 0.5"
            >
              <animate v-if="link.ipsecState === 'up'"
                attributeName="stroke-opacity" values="0.55;1;0.55" dur="3s" repeatCount="indefinite"/>
            </line>

            <!-- IPSec label -->
            <text
              :x="link.labelMidX + link.lpx * 2.5"
              :y="link.labelMidY + link.lpy * 2.5 - 3"
              text-anchor="middle"
              :fill="ipsecColor(link.ipsecState)"
              font-size="5.5" font-family="Inter,sans-serif" opacity="0.85"
            >IPSec</text>

            <!-- MPLS dashed line -->
            <line
              :x1="link.mpls.x1" :y1="link.mpls.y1"
              :x2="link.mpls.x2" :y2="link.mpls.y2"
              :stroke="mplsColor(link.mplsState)"
              stroke-width="1.8"
              stroke-dasharray="6,3"
              stroke-linecap="round"
              :stroke-opacity="link.mplsState === 'up' ? 0.9 : 0.5"
            >
              <animate attributeName="stroke-dashoffset" from="0" to="-18" dur="1.5s" repeatCount="indefinite"/>
            </line>

            <!-- MPLS label -->
            <text
              :x="link.labelMidX - link.lpx * 2.5"
              :y="link.labelMidY - link.lpy * 2.5 + 9"
              text-anchor="middle"
              :fill="mplsColor(link.mplsState)"
              font-size="5.5" font-family="Inter,sans-serif" opacity="0.85"
            >MPLS</text>
          </g>

          <!-- Site nodes -->
          <g v-for="site in sites" :key="'node-' + site.key"
            class="cursor-pointer"
            @mouseenter="hovered = site"
            @mouseleave="hovered = null"
            @click="selected = (selected?.key === site.key ? null : site)">

            <!-- Pulse ring (active) -->
            <circle v-if="site.status === 'active'"
              :cx="site.x" :cy="site.y" r="16"
              :fill="nodeColors[site.status]?.ring ?? 'transparent'">
              <animate attributeName="r" values="16;26;16" dur="2.8s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.4;0;0.4" dur="2.8s" repeatCount="indefinite"/>
            </circle>

            <!-- Outer glow circle -->
            <circle
              :cx="site.x" :cy="site.y" r="15"
              :fill="nodeColors[site.status]?.fill ?? 'rgba(100,116,139,0.2)'"
              :stroke="nodeColors[site.status]?.stroke ?? '#64748b'"
              stroke-width="1.8"
              :filter="site.status === 'active' ? 'url(#node-glow)' : ''"
            />

            <!-- HQ: hexagon marker -->
            <polygon v-if="site.isHQ"
              :points="hexPoints(site.x, site.y, 7)"
              :fill="nodeColors[site.status]?.stroke ?? '#64748b'"
            />
            <!-- Branch: solid dot -->
            <circle v-else :cx="site.x" :cy="site.y" r="5.5"
              :fill="nodeColors[site.status]?.stroke ?? '#64748b'"
            />

            <!-- Site label -->
            <text :x="site.x" :y="site.labelY"
              text-anchor="middle"
              fill="rgba(226,232,240,0.95)"
              font-size="9" font-family="Inter,sans-serif" font-weight="600"
            >{{ site.city }}</text>

            <!-- OLT hostname -->
            <text :x="site.x" :y="site.labelY + 11"
              text-anchor="middle"
              fill="rgba(100,116,139,0.85)"
              font-size="7" font-family="Inter,sans-serif"
            >{{ site.hostname }}</text>
          </g>

        </svg>
      </div>

      <!-- Right panel (1/3 width) -->
      <div class="flex flex-col gap-3">

        <!-- Summary stats -->
        <div class="glass-card p-4 grid grid-cols-2 gap-3">
          <div class="text-center">
            <p class="text-[10px] text-slate-500 mb-1">Sites</p>
            <p class="text-2xl font-bold text-white">{{ sites.length }}</p>
          </div>
          <div class="text-center">
            <p class="text-[10px] text-slate-500 mb-1">Active OLTs</p>
            <p class="text-2xl font-bold text-emerald-400">{{ sites.filter(s => s.status === 'active').length }}</p>
          </div>
          <div class="text-center">
            <p class="text-[10px] text-slate-500 mb-1">BFD UP</p>
            <p class="text-2xl font-bold text-cyan-400">
              {{ bfdSessions.filter(s => s.state === 'up').length }}
              <span class="text-sm text-slate-500">/ {{ bfdSessions.length }}</span>
            </p>
          </div>
          <div class="text-center">
            <p class="text-[10px] text-slate-500 mb-1">Link Pairs</p>
            <p class="text-2xl font-bold text-purple-400">{{ computedLinks.length }}</p>
          </div>
        </div>

        <!-- Selected site detail -->
        <transition name="tip-fade">
          <div v-if="activeInfo" class="glass-card p-4">
            <div class="flex items-center gap-2 mb-3">
              <span :class="['w-2 h-2 rounded-full shrink-0', nodeColors[activeInfo.status]?.dot ?? 'bg-slate-500']"/>
              <p class="text-xs font-semibold text-white">{{ activeInfo.city }}</p>
              <span class="ml-auto text-[10px] capitalize px-2 py-0.5 rounded-full"
                :class="activeInfo.status === 'active' ? 'text-emerald-400 bg-emerald-500/10' :
                        activeInfo.status === 'degraded' ? 'text-amber-400 bg-amber-500/10' :
                        'text-slate-400 bg-white/5'">
                {{ activeInfo.status }}
              </span>
            </div>
            <div class="space-y-2 text-[10px]">
              <div class="flex justify-between gap-4">
                <span class="text-slate-500">OLT</span>
                <span class="text-slate-300 font-mono">{{ activeInfo.hostname }}</span>
              </div>
              <div class="flex justify-between gap-4">
                <span class="text-slate-500">IP Address</span>
                <span class="text-slate-300 font-mono">{{ activeInfo.ip }}</span>
              </div>
              <div class="flex justify-between gap-4">
                <span class="text-slate-500">Site name</span>
                <span class="text-slate-400 truncate max-w-[120px]">{{ activeInfo.siteName }}</span>
              </div>
              <div class="flex justify-between gap-4">
                <span class="text-slate-500">Last poll</span>
                <span class="text-slate-400">{{ formatTime(activeInfo.lastPoll) }}</span>
              </div>
            </div>
            <!-- Site link sessions -->
            <div v-if="activeInfo.key !== 'hq'" class="mt-3 pt-3 border-t border-white/8 space-y-1.5">
              <p class="text-[10px] text-slate-500 font-semibold mb-2">WAN to HQ</p>
              <div v-for="sess in sessionsForSite(activeInfo.key)" :key="sess.id"
                class="flex items-center justify-between">
                <span class="text-[10px] text-slate-400">
                  {{ sess.name.toLowerCase().includes('mpls') ? 'MPLS' : 'IPSec' }}
                  <span class="text-slate-600 font-mono ml-1">{{ sess.peer_ip }}</span>
                </span>
                <span :class="['text-[10px] font-semibold uppercase',
                  sess.state === 'up' ? 'text-emerald-400' : 'text-red-400']">
                  {{ sess.state }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="glass-card p-4 flex flex-col items-center justify-center gap-2 min-h-[110px]">
            <MousePointer2 :size="18" class="text-slate-700"/>
            <p class="text-[10px] text-slate-600 text-center">Click or hover a site<br>to view details</p>
          </div>
        </transition>

        <!-- BFD sessions list -->
        <div class="glass-card overflow-hidden flex-1">
          <div class="px-4 py-3 border-b border-white/10 flex items-center justify-between">
            <p class="text-xs font-semibold text-white">WAN Sessions</p>
            <span class="text-[10px] text-slate-500">{{ bfdSessions.filter(s => s.state === 'up').length }} UP · {{ bfdSessions.filter(s => s.state !== 'up').length }} DOWN</span>
          </div>
          <div class="divide-y divide-white/5 overflow-y-auto" style="max-height: 220px">
            <div v-for="s in bfdSessions" :key="s.id"
              class="px-4 py-2.5 flex items-center justify-between hover:bg-white/[0.02] transition-colors">
              <div class="flex-1 min-w-0">
                <p class="text-[11px] font-medium text-slate-300 truncate">{{ s.name }}</p>
                <p class="text-[10px] text-slate-600 font-mono">{{ s.peer_ip }}</p>
              </div>
              <div class="flex items-center gap-2 shrink-0 ml-2">
                <span class="text-[9px] text-slate-600 uppercase">{{ s.session_type?.replace('_', '-') }}</span>
                <span :class="['flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full',
                  s.state === 'up'
                    ? 'bg-emerald-500/15 text-emerald-400'
                    : 'bg-red-500/15 text-red-400']">
                  <span :class="['w-1 h-1 rounded-full', s.state === 'up' ? 'bg-emerald-400 animate-pulse' : 'bg-red-400']"/>
                  {{ s.state?.toUpperCase() }}
                </span>
              </div>
            </div>
            <div v-if="bfdSessions.length === 0" class="px-4 py-6 text-center text-slate-600 text-xs">
              No sessions found
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RefreshCw, MousePointer2 } from 'lucide-vue-next'

const { list: listOlts } = useOlts()
const { sessions } = useBfd()

// ─── State ────────────────────────────────────────────────────────────────────
const olts        = ref<any[]>([])
const bfdSessions = ref<any[]>([])
const loading     = ref(true)
const hovered     = ref<any>(null)
const selected    = ref<any>(null)

const activeInfo = computed(() => hovered.value ?? selected.value ?? null)

// ─── Geo coordinates (ViewBox 0 0 460 285, shifted 20px down from SiteMap) ───
const CITY_COORDS: Record<string, { x: number; y: number; labelY: number; isHQ: boolean; key: string }> = {
  'Tunis':  { x: 286, y: 45,  labelY: 64,  isHQ: true,  key: 'hq'     },
  'Nabeul': { x: 345, y: 57,  labelY: 76,  isHQ: false, key: 'nabeul' },
  'El Kef': { x: 130, y: 67,  labelY: 86,  isHQ: false, key: 'elkef'  },
  'Sfax':   { x: 349, y: 118, labelY: 137, isHQ: false, key: 'sfax'   },
}

// ─── Colors ───────────────────────────────────────────────────────────────────
const nodeColors: Record<string, any> = {
  active:      { fill: 'rgba(16,185,129,0.22)',  stroke: '#10b981', ring: 'rgba(16,185,129,0.18)', dot: 'bg-emerald-400' },
  degraded:    { fill: 'rgba(245,158,11,0.22)',  stroke: '#f59e0b', ring: 'rgba(245,158,11,0.18)', dot: 'bg-amber-400'   },
  maintenance: { fill: 'rgba(59,130,246,0.22)',  stroke: '#3b82f6', ring: 'rgba(59,130,246,0.18)', dot: 'bg-blue-400'    },
  inactive:    { fill: 'rgba(239,68,68,0.22)',   stroke: '#ef4444', ring: 'rgba(239,68,68,0.18)',  dot: 'bg-red-400'     },
  unknown:     { fill: 'rgba(100,116,139,0.22)', stroke: '#64748b', ring: 'rgba(100,116,139,0.1)', dot: 'bg-slate-500'   },
}

const statusLegend = [
  { label: 'Active',   dot: 'bg-emerald-400' },
  { label: 'Degraded', dot: 'bg-amber-400'   },
  { label: 'Down',     dot: 'bg-red-400'     },
]

// ─── Derived sites ────────────────────────────────────────────────────────────
function cityFromSiteName(siteName: string): string {
  if (!siteName) return ''
  const s = siteName.toLowerCase()
  if (s.includes('tunis') || s.includes('hq')) return 'Tunis'
  if (s.includes('nabeul'))                     return 'Nabeul'
  if (s.includes('sfax'))                       return 'Sfax'
  if (s.includes('kef'))                        return 'El Kef'
  return siteName
}

const sites = computed(() => {
  const siteMap = new Map<string, any>()
  for (const olt of olts.value) {
    const city   = cityFromSiteName(olt.site_name)
    const coords = CITY_COORDS[city]
    if (!coords || siteMap.has(coords.key)) continue
    siteMap.set(coords.key, {
      ...coords,
      city,
      hostname:  olt.hostname,
      ip:        olt.ip_address,
      siteName:  olt.site_name,
      status:    olt.status ?? 'unknown',
      lastPoll:  olt.last_polled_at,
    })
  }
  return Array.from(siteMap.values())
})

// ─── Derived links ────────────────────────────────────────────────────────────
function getBranch(name: string): string {
  const n = name.toLowerCase()
  if (n.includes('sfax') || n.includes('sfx'))    return 'sfax'
  if (n.includes('nabeul') || n.includes('nbl'))  return 'nabeul'
  if (n.includes('kef'))                          return 'elkef'
  return ''
}

const computedLinks = computed(() => {
  const hq = sites.value.find(s => s.key === 'hq')
  if (!hq) return []

  const branchMap: Record<string, { ipsec?: any; mpls?: any }> = {}
  for (const s of bfdSessions.value) {
    const branch = getBranch(s.name)
    if (!branch) continue
    const type = s.name.toLowerCase().includes('mpls') ? 'mpls' : 'ipsec'
    if (!branchMap[branch]) branchMap[branch] = {}
    branchMap[branch][type] = s
  }

  const OFFSET = 4
  return Object.entries(branchMap).map(([branch, sess]) => {
    const br = sites.value.find(s => s.key === branch)
    if (!br) return null

    const dx = br.x - hq.x
    const dy = br.y - hq.y
    const len = Math.sqrt(dx * dx + dy * dy) || 1
    const px = (-dy / len) * OFFSET
    const py = ( dx / len) * OFFSET

    return {
      id: branch,
      ipsec: { x1: hq.x + px, y1: hq.y + py, x2: br.x + px, y2: br.y + py },
      mpls:  { x1: hq.x - px, y1: hq.y - py, x2: br.x - px, y2: br.y - py },
      ipsecState: sess.ipsec?.state ?? 'unknown',
      mplsState:  sess.mpls?.state  ?? 'unknown',
      labelMidX: (hq.x + br.x) / 2,
      labelMidY: (hq.y + br.y) / 2,
      lpx: px, lpy: py,
    }
  }).filter(Boolean)
})

function sessionsForSite(siteKey: string) {
  return bfdSessions.value.filter(s => getBranch(s.name) === siteKey)
}

// ─── Colors ───────────────────────────────────────────────────────────────────
const ipsecColor = (state: string) =>
  state === 'up' ? '#06b6d4' : state === 'down' ? '#ef4444' : '#475569'

const mplsColor = (state: string) =>
  state === 'up' ? '#a78bfa' : state === 'down' ? '#ef4444' : '#475569'

// ─── Helpers ─────────────────────────────────────────────────────────────────
function hexPoints(cx: number, cy: number, r: number): string {
  return Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 3) * i - Math.PI / 6
    return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`
  }).join(' ')
}

const formatTime = (ts: string) =>
  ts ? new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'

// ─── Data fetching ────────────────────────────────────────────────────────────
async function refresh() {
  loading.value = true
  try {
    const [oltRes, bfdRes] = await Promise.all([
      listOlts({ page_size: 50 }),
      sessions({ page_size: 50 }),
    ])
    olts.value        = oltRes.data.results ?? oltRes.data
    bfdSessions.value = bfdRes.data.results ?? bfdRes.data
  } catch {
    olts.value = []
    bfdSessions.value = []
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>

<style scoped>
.tip-fade-enter-active, .tip-fade-leave-active { transition: opacity 0.15s ease; }
.tip-fade-enter-from, .tip-fade-leave-to       { opacity: 0; }
</style>
