<template>
  <div class="glass-card p-5">
    <p class="text-sm font-semibold text-white mb-4">{{ title }}</p>
    <div class="flex items-center gap-6">
      <div :style="{ width: size + 'px', height: size + 'px' }" class="shrink-0">
        <Doughnut v-if="ready" :data="chartData" :options="chartOptions" />
      </div>
      <div class="flex flex-col gap-2 flex-1">
        <div v-for="(item, i) in legend" :key="i" class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <span :style="{ background: item.color }" class="w-2.5 h-2.5 rounded-full shrink-0" />
            <span class="text-xs text-slate-400">{{ item.label }}</span>
          </div>
          <span class="text-xs font-semibold text-white tabular-nums">{{ item.value.toLocaleString() }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  title: string
  legend: { label: string; value: number; color: string }[]
  size?: number
}>()

const size = computed(() => props.size ?? 120)
const ready = computed(() => props.legend.length > 0)

const chartData = computed(() => ({
  labels: props.legend.map(l => l.label),
  datasets: [{
    data: props.legend.map(l => l.value),
    backgroundColor: props.legend.map(l => l.color + 'cc'),
    borderColor: props.legend.map(l => l.color),
    borderWidth: 2,
    hoverOffset: 4
  }]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '72%',
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(5,11,26,0.9)',
      borderColor: 'rgba(255,255,255,0.1)',
      borderWidth: 1,
      titleColor: '#f1f5f9',
      bodyColor: '#94a3b8',
      padding: 10
    }
  }
}
</script>
