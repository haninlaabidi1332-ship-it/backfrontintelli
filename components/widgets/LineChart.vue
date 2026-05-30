<template>
  <div class="glass-card p-5">
    <div class="flex items-center justify-between mb-4">
      <div>
        <p class="text-sm font-semibold text-white">{{ title }}</p>
        <p v-if="subtitle" class="text-xs text-slate-500 mt-0.5">{{ subtitle }}</p>
      </div>
      <slot name="actions" />
    </div>
    <div :style="{ height: height + 'px' }">
      <Line v-if="ready" :data="chartData" :options="chartOptions" />
      <div v-else class="h-full flex items-center justify-center">
        <span class="text-slate-600 text-xs">Loading chart...</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const props = defineProps<{
  title: string
  subtitle?: string
  labels: string[]
  datasets: { label: string; data: number[]; color?: string }[]
  height?: number
}>()

const height = computed(() => props.height ?? 200)
const ready = computed(() => props.labels.length > 0)

const colors = ['#00d4ff', '#10b981', '#f59e0b', '#f87171', '#a78bfa']

const chartData = computed(() => ({
  labels: props.labels,
  datasets: props.datasets.map((ds, i) => ({
    label: ds.label,
    data: ds.data,
    borderColor: ds.color ?? colors[i % colors.length],
    backgroundColor: (ds.color ?? colors[i % colors.length]) + '20',
    borderWidth: 2,
    pointRadius: 3,
    pointHoverRadius: 5,
    fill: true,
    tension: 0.4
  }))
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: '#94a3b8', font: { size: 11 }, boxWidth: 10, padding: 12 }
    },
    tooltip: {
      backgroundColor: 'rgba(5,11,26,0.9)',
      borderColor: 'rgba(255,255,255,0.1)',
      borderWidth: 1,
      titleColor: '#f1f5f9',
      bodyColor: '#94a3b8',
      padding: 10
    }
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
      ticks: { color: '#64748b', font: { size: 10 } }
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.04)', drawBorder: false },
      ticks: { color: '#64748b', font: { size: 10 } }
    }
  }
}
</script>
