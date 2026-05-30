<template>
  <div class="glass-card p-5">

    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <p class="text-sm font-semibold text-white">Site Status Map</p>
        <p class="text-xs text-slate-500 mt-0.5">Real-time coverage · Tunisia</p>
      </div>
      <div class="flex items-center gap-4">
        <div v-for="leg in legend" :key="leg.label" class="flex items-center gap-1.5">
          <span :class="['w-2 h-2 rounded-full', leg.dot]" />
          <span class="text-[10px] text-slate-500">{{ leg.label }}</span>
        </div>
      </div>
    </div>

    <!-- Map -->
    <div class="relative rounded-xl overflow-hidden bg-[#060d1f]" style="height: 240px">

      <!-- Loading -->
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center">
        <div class="w-6 h-6 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>

      <svg v-else viewBox="0 0 460 260" class="w-full h-full" @mouseleave="tooltip = null">

        <!-- Grid -->
        <defs>
          <pattern id="sitemap-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.025)" stroke-width="0.5" />
          </pattern>
        </defs>
        <rect width="460" height="260" fill="url(#sitemap-grid)" />

        <!-- Tunisia simplified outline -->
        <path
          d="M 139,21 C 190,8 222,7 246,7 L 278,11 299,18 C 335,15 368,13 385,14 C 372,27 354,38 331,39 L 331,60 C 355,65 372,70 380,71 L 358,100 C 342,116 312,130 278,128 C 305,136 350,140 385,143 L 428,156 260,258 54,258 C 48,215 44,175 43,128 L 139,111 C 125,90 100,65 86,36 C 100,28 120,22 139,21 Z"
          fill="rgba(255,255,255,0.018)"
          stroke="rgba(255,255,255,0.08)"
          stroke-width="1"
          stroke-linejoin="round"
        />

        <!-- Connection lines: HQ → each branch -->
        <g v-for="site in branchSites" :key="'line-' + site.key">
          <line
            :x1="hqSite.svgX" :y1="hqSite.svgY"
            :x2="site.svgX"   :y2="site.svgY"
            stroke="rgba(0,212,255,0.2)"
            stroke-width="1"
            stroke-dasharray="5,4"
          >
            <animate attributeName="stroke-dashoffset" from="0" to="-18" dur="1.5s" repeatCount="indefinite" />
          </line>
        </g>

        <!-- Site nodes -->
        <g
          v-for="site in mappedSites" :key="site.key"
          class="cursor-pointer"
          @mouseenter="onHover(site, $event)"
          @mouseleave="tooltip = null"
        >
          <!-- Pulse ring (active only) -->
          <circle
            v-if="site.status === 'active'"
            :cx="site.svgX" :cy="site.svgY" r="9"
            :fill="colors[site.status]?.ring ?? 'transparent'"
          >
            <animate attributeName="r"       values="9;17;9"      dur="2.5s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.35;0;0.35" dur="2.5s" repeatCount="indefinite" />
          </circle>

          <!-- Outer glow circle -->
          <circle
            :cx="site.svgX" :cy="site.svgY" r="10"
            :fill="colors[site.status]?.fill ?? colors.inactive.fill"
            :stroke="colors[site.status]?.stroke ?? colors.inactive.stroke"
            stroke-width="1.5"
          />

          <!-- HQ: hexagon marker -->
          <polygon
            v-if="site.key === 'hq'"
            :points="hexPoints(site.svgX, site.svgY, 5)"
            :fill="colors[site.status]?.stroke ?? colors.inactive.stroke"
          />
          <!-- Branch: solid dot -->
          <circle
            v-else
            :cx="site.svgX" :cy="site.svgY" r="4"
            :fill="colors[site.status]?.stroke ?? colors.inactive.stroke"
          />

          <!-- City label -->
          <text
            :x="site.svgX"
            :y="site.labelOffsetY ?? (site.svgY + 23)"
            :text-anchor="site.labelAnchor ?? 'middle'"
            fill="rgba(203,213,225,0.85)"
            font-size="8.5"
            font-family="Inter, sans-serif"
            font-weight="500"
          >{{ site.city }}</text>
        </g>
      </svg>

      <!-- Tooltip -->
      <transition name="tip-fade">
        <div
          v-if="tooltip"
          class="absolute pointer-events-none glass-card px-3 py-2.5 min-w-[175px] shadow-xl z-20"
          :style="{ left: tooltip.px + 'px', top: tooltip.py + 'px', transform: 'translate(-50%, -120%)' }"
        >
          <div class="flex items-center gap-2 mb-1.5">
            <span :class="['w-2 h-2 rounded-full shrink-0', colors[tooltip.site.status]?.dot ?? 'bg-slate-500']" />
            <p class="text-xs font-semibold text-white leading-tight">{{ tooltip.site.site_name }}</p>
          </div>
          <p class="text-[10px] text-slate-500 font-mono mb-2">{{ tooltip.site.site_name }}</p>
          <div class="border-t border-white/10 pt-2 space-y-1">
            <div class="flex justify-between gap-6 text-[10px]">
              <span class="text-slate-500">OLTs</span>
              <span class="text-white font-semibold font-mono">{{ tooltip.site.oltList?.length ?? 0 }}</span>
            </div>
            <div class="flex justify-between gap-6 text-[10px]">
              <span class="text-slate-500">Status</span>
              <span :class="tooltip.site.status === 'active' ? 'text-emerald-400' : tooltip.site.status === 'degraded' ? 'text-amber-400' : 'text-slate-400'" class="font-semibold capitalize">{{ tooltip.site.status }}</span>
            </div>
            <div class="flex justify-between gap-6 text-[10px]">
              <span class="text-slate-500">Last poll</span>
              <span class="text-white">{{ formatTime(tooltip.site.last_polled_at) }}</span>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- Bottom summary strip -->
    <div class="mt-3 grid grid-cols-4 gap-2">
      <div
        v-for="site in mappedSites" :key="'strip-' + site.key"
        class="rounded-xl bg-white/[0.03] border border-white/5 px-3 py-2.5 hover:bg-white/[0.06] transition-colors"
      >
        <div class="flex items-center gap-1.5 mb-1">
          <span :class="['w-1.5 h-1.5 rounded-full shrink-0', colors[site.status]?.dot ?? 'bg-slate-500']" />
          <span class="text-[10px] font-semibold text-white truncate">{{ site.city }}</span>
        </div>
        <p class="text-[10px] text-slate-500">{{ site.oltList?.length ?? 0 }} OLT{{ (site.oltList?.length ?? 0) !== 1 ? 's' : '' }}</p>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
const { list } = useOlts()

// ─── Geographic SVG coordinates ───────────────────────────────────────────────
// ViewBox 0 0 460 260 , approximate geo-projection of Tunisia
// x = (lon − 7.5) × 107   |   y = (37.5 − lat) × 35.6
const CITY_COORDS: Record<string, { x: number; y: number; key: string; labelOffsetY?: number; labelAnchor?: string }> = {
  'Tunis':  { x: 286, y: 25, key: 'hq' },
  'Nabeul': { x: 345, y: 37, key: 'nabeul', labelOffsetY: 60, labelAnchor: 'middle' },
  'El Kef': { x: 130, y: 47, key: 'elkef' },
  'Sfax':   { x: 349, y: 98, key: 'sfax'  },
}

// ─── Status color tokens ──────────────────────────────────────────────────────
const colors: Record<string, { fill: string; stroke: string; ring: string; dot: string }> = {
  active:      { fill: 'rgba(16,185,129,0.22)',  stroke: '#10b981', ring: 'rgba(16,185,129,0.18)', dot: 'bg-emerald-400' },
  degraded:    { fill: 'rgba(245,158,11,0.22)',  stroke: '#f59e0b', ring: 'rgba(245,158,11,0.18)', dot: 'bg-amber-400'   },
  maintenance: { fill: 'rgba(59,130,246,0.22)',  stroke: '#3b82f6', ring: 'rgba(59,130,246,0.18)', dot: 'bg-blue-400'    },
  inactive:    { fill: 'rgba(100,116,139,0.22)', stroke: '#64748b', ring: 'rgba(100,116,139,0.1)', dot: 'bg-slate-500'   },
  down:        { fill: 'rgba(239,68,68,0.22)',   stroke: '#ef4444', ring: 'rgba(239,68,68,0.18)', dot: 'bg-red-400'     },
}

const legend = [
  { label: 'Active',      dot: 'bg-emerald-400' },
  { label: 'Degraded',    dot: 'bg-amber-400'   },
  { label: 'Down',        dot: 'bg-red-400'     },
  { label: 'Maintenance', dot: 'bg-blue-400'    },
]

// ─── State ────────────────────────────────────────────────────────────────────
const olts    = ref<any[]>([])
const loading = ref(true)
const tooltip = ref<{ site: any; px: number; py: number } | null>(null)

onMounted(async () => {
  try {
    const { data } = await list({ page_size: 50 })
    olts.value = data.results ?? data
  } catch {
    olts.value = []
  } finally {
    loading.value = false
  }
})

// ─── Derived data ─────────────────────────────────────────────────────────────
function cityFromSiteName(siteName: string): string {
  if (!siteName) return ''
  const s = siteName.toLowerCase()
  if (s.includes('tunis') || s.includes('hq')) return 'Tunis'
  if (s.includes('nabeul'))                     return 'Nabeul'
  if (s.includes('sfax'))                       return 'Sfax'
  if (s.includes('kef'))                        return 'El Kef'
  return siteName.replace(/^Branch\s+/i, '').split(/\s/)[0]
}

// Status priority: degraded > inactive > active
const STATUS_PRIORITY: Record<string, number> = { degraded: 3, inactive: 2, maintenance: 1, active: 0 }

const mappedSites = computed(() => {
  const siteMap = new Map<string, any>()
  for (const olt of olts.value) {
    const city   = cityFromSiteName(olt.site_name)
    const coords = CITY_COORDS[city] ?? { x: 230, y: 130, key: olt.id }
    if (!siteMap.has(city)) {
      siteMap.set(city, {
        city,
        site_name: olt.site_name,
        svgX: coords.x, svgY: coords.y,
        labelOffsetY: coords.labelOffsetY, labelAnchor: coords.labelAnchor,
        key: coords.key,
        status: olt.status,
        oltList: [olt],
        last_polled_at: olt.last_polled_at,
      })
    } else {
      const site = siteMap.get(city)!
      site.oltList.push(olt)
      // Worst status wins
      if ((STATUS_PRIORITY[olt.status] ?? 0) > (STATUS_PRIORITY[site.status] ?? 0))
        site.status = olt.status
      // Keep most recent poll timestamp
      if (olt.last_polled_at && (!site.last_polled_at || olt.last_polled_at > site.last_polled_at))
        site.last_polled_at = olt.last_polled_at
    }
  }
  return Array.from(siteMap.values())
})

const hqSite      = computed(() => mappedSites.value.find(s => s.key === 'hq') ?? { svgX: 286, svgY: 25 })
const branchSites = computed(() => mappedSites.value.filter(s => s.key !== 'hq'))

// ─── Tooltip ──────────────────────────────────────────────────────────────────
function onHover(site: any, event: MouseEvent) {
  const svgEl = (event.currentTarget as SVGGElement).ownerSVGElement!
  const { width, height } = svgEl.getBoundingClientRect()
  tooltip.value = {
    site,
    px: site.svgX * (width  / 460),
    py: site.svgY * (height / 260),
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function hexPoints(cx: number, cy: number, r: number): string {
  return Array.from({ length: 6 }, (_, i) => {
    const a = (Math.PI / 3) * i - Math.PI / 6
    return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`
  }).join(' ')
}

const formatTime = (ts: string) => {
  if (!ts) return ','
  return new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.tip-fade-enter-active,
.tip-fade-leave-active { transition: opacity 0.12s ease; }
.tip-fade-enter-from,
.tip-fade-leave-to     { opacity: 0; }
</style>
