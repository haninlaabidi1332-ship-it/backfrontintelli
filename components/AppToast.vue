<template>
  <Teleport to="body">
    <div class="fixed top-5 right-5 z-[100] flex flex-col gap-2 pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="flex items-start gap-3 px-4 py-3 rounded-2xl shadow-lg text-xs font-medium pointer-events-auto min-w-[260px] max-w-xs"
          :style="styles[toast.type]"
        >
          <component :is="icons[toast.type]" :size="14" class="shrink-0 mt-0.5" />
          <span class="flex-1 leading-relaxed">{{ toast.message }}</span>
          <button @click="remove(toast.id)" class="shrink-0 opacity-60 hover:opacity-100 transition-opacity">
            <X :size="12" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-vue-next'

const { toasts, remove } = useToast()

const icons: Record<string, any> = {
  success: CheckCircle2,
  error:   XCircle,
  warning: AlertTriangle,
  info:    Info,
}

const styles: Record<string, object> = {
  success: { background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)', color: '#34d399' },
  error:   { background: 'rgba(239,68,68,0.15)',  border: '1px solid rgba(239,68,68,0.3)',  color: '#f87171' },
  warning: { background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.3)', color: '#fbbf24' },
  info:    { background: 'rgba(0,212,255,0.15)',  border: '1px solid rgba(0,212,255,0.3)',  color: '#00d4ff' },
}
</script>

<style scoped>
.toast-enter-active { transition: all 0.25s ease; }
.toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from  { opacity: 0; transform: translateX(24px); }
.toast-leave-to    { opacity: 0; transform: translateX(24px); }
</style>
