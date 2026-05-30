<template>
  <span :class="badgeClass">{{ label ?? severity }}</span>
</template>

<script setup lang="ts">
const props = defineProps<{
  severity: string
  label?: string
}>()

const badgeClass = computed(() => {
  const map: Record<string, string> = {
    critical: 'badge-danger',
    major:    'badge bg-orange-500/20 text-orange-400 border border-orange-500/30',
    warning:  'badge-warning',
    info:     'badge-info',
    low:      'badge-neutral',
    medium:   'badge-warning',
    high:     'badge bg-orange-500/20 text-orange-400 border border-orange-500/30',
    active:   'badge-danger',
    acknowledged: 'badge-warning',
    resolved: 'badge-success'
  }
  return map[props.severity?.toLowerCase()] ?? 'badge-neutral'
})
</script>
