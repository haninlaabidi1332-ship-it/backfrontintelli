<template>
  <div :class="['stat-card', glowClass]">
    <div class="flex items-start justify-between">
      <div :class="['w-10 h-10 rounded-xl flex items-center justify-center', iconBg]">
        <component :is="icon" :size="18" :class="iconColor" />
      </div>
      <div v-if="trend !== undefined" :class="['flex items-center gap-1 text-xs font-semibold', trend >= 0 ? 'text-emerald-400' : 'text-red-400']">
        <TrendingUp v-if="trend >= 0" :size="12" />
        <TrendingDown v-else :size="12" />
        {{ Math.abs(trend) }}%
      </div>
    </div>

    <div>
      <p class="text-2xl font-bold text-white tabular-nums">
        <span v-if="loading" class="inline-block w-16 h-7 bg-white/10 rounded animate-pulse" />
        <template v-else>{{ formattedValue }}</template>
      </p>
      <p class="text-xs text-slate-500 mt-0.5">{{ label }}</p>
    </div>

    <div v-if="sub" class="text-[10px] text-slate-600 border-t border-white/5 pt-2 mt-auto">
      {{ sub }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { TrendingUp, TrendingDown } from 'lucide-vue-next'

const props = defineProps<{
  label: string
  value: number | string
  icon: any
  color?: 'cyan' | 'green' | 'amber' | 'red' | 'purple'
  trend?: number
  sub?: string
  loading?: boolean
  suffix?: string
}>()

const colorMap = {
  cyan:   { bg: 'bg-primary/15',    icon: 'text-primary',      glow: 'glow-cyan' },
  green:  { bg: 'bg-emerald-500/15', icon: 'text-emerald-400', glow: 'glow-green' },
  amber:  { bg: 'bg-amber-500/15',  icon: 'text-amber-400',    glow: '' },
  red:    { bg: 'bg-red-500/15',    icon: 'text-red-400',      glow: 'glow-red' },
  purple: { bg: 'bg-purple-500/15', icon: 'text-purple-400',   glow: '' }
}

const c = computed(() => colorMap[props.color ?? 'cyan'])
const iconBg = computed(() => c.value.bg)
const iconColor = computed(() => c.value.icon)
const glowClass = computed(() => c.value.glow)

const formattedValue = computed(() => {
  if (props.suffix) return `${props.value}${props.suffix}`
  if (typeof props.value === 'number') return props.value.toLocaleString()
  return props.value
})
</script>
