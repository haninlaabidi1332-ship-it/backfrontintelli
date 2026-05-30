<template>
  <div class="space-y-5">
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="model in models" :key="model.id" class="glass-card-hover p-5">
        <div class="flex items-start justify-between mb-4">
          <div>
            <p class="text-sm font-semibold text-white">{{ model.name }}</p>
            <p class="text-[10px] text-slate-500 font-mono mt-0.5">v{{ model.version }}</p>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="model.is_active" class="flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
              <span class="w-1 h-1 bg-emerald-400 rounded-full animate-pulse-slow" /> Active
            </span>
            <WidgetsAlertBadge :severity="statusBadge(model.status)" :label="model.status" />
          </div>
        </div>

        <div class="space-y-2 mb-4">
          <div class="flex justify-between text-xs">
            <span class="text-slate-500">Type</span>
            <span class="text-slate-300 font-mono capitalize">{{ model.model_type?.replace('_', ' ') }}</span>
          </div>
          <div v-if="model.accuracy_score" class="flex justify-between text-xs">
            <span class="text-slate-500">Accuracy</span>
            <span class="text-emerald-400 font-mono">{{ (model.accuracy_score * 100).toFixed(1) }}%</span>
          </div>
          <div v-if="model.last_trained_at" class="flex justify-between text-xs">
            <span class="text-slate-500">Last Trained</span>
            <span class="text-slate-400 font-mono">{{ formatTime(model.last_trained_at) }}</span>
          </div>
        </div>

        <p v-if="model.description" class="text-[10px] text-slate-600 border-t border-white/5 pt-3 mb-4 line-clamp-2">
          {{ model.description }}
        </p>

        <!-- Inline train form -->
        <div v-if="showTrainForm[model.id]" class="mb-3 p-3 rounded-xl bg-white/[0.04] border border-white/10 space-y-2">
          <p class="text-[10px] text-slate-400 font-semibold">Training date range</p>
          <div class="flex gap-2">
            <div class="flex-1">
              <label class="text-[10px] text-slate-500 block mb-1">From</label>
              <input
                v-model="trainDates[model.id].start"
                type="date"
                class="w-full bg-white/[0.05] border border-white/10 rounded-lg px-2 py-1.5 text-[11px] text-slate-200 focus:outline-none focus:border-primary/50"
              />
            </div>
            <div class="flex-1">
              <label class="text-[10px] text-slate-500 block mb-1">To</label>
              <input
                v-model="trainDates[model.id].end"
                type="date"
                class="w-full bg-white/[0.05] border border-white/10 rounded-lg px-2 py-1.5 text-[11px] text-slate-200 focus:outline-none focus:border-primary/50"
              />
            </div>
          </div>
          <div class="flex gap-2 pt-1">
            <button
              @click="submitTrain(model)"
              :disabled="busy[model.id] === 'train'"
              class="flex-1 btn-primary text-xs flex items-center justify-center gap-1 disabled:opacity-50"
            >
              <Loader2 v-if="busy[model.id] === 'train'" :size="11" class="animate-spin" />
              <PlayCircle v-else :size="11" /> Start Training
            </button>
            <button @click="showTrainForm[model.id] = false" class="btn-ghost text-xs px-3">Cancel</button>
          </div>
        </div>

        <!-- Feedback message -->
        <p v-if="feedback[model.id]" class="text-[10px] mb-2 px-2 py-1 rounded-lg"
          :class="feedback[model.id].ok ? 'text-emerald-400 bg-emerald-500/10' : 'text-red-400 bg-red-500/10'">
          {{ feedback[model.id].msg }}
        </p>

        <div v-if="!showTrainForm[model.id]" class="flex gap-2">
          <button @click="openTrainForm(model)"
            :disabled="!!busy[model.id]"
            class="flex-1 btn-ghost text-xs flex items-center justify-center gap-1 disabled:opacity-50">
            <PlayCircle :size="12" /> Train
          </button>
          <button v-if="!model.is_active"
            @click="activate(model)"
            :disabled="!!busy[model.id]"
            class="flex-1 btn-primary text-xs flex items-center justify-center gap-1 disabled:opacity-50">
            <Loader2 v-if="busy[model.id] === 'activate'" :size="12" class="animate-spin" />
            <Zap v-else :size="12" /> Activate
          </button>
          <span v-else class="flex-1 text-center text-[10px] text-emerald-400 flex items-center justify-center gap-1">
            <CheckCircle :size="11" /> In use
          </span>
        </div>
      </div>

      <div v-if="models.length === 0" class="md:col-span-2 xl:col-span-3 glass-card p-12 text-center text-slate-600 text-sm">
        No ML models configured
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PlayCircle, Zap, Loader2, CheckCircle } from 'lucide-vue-next'
import { useAiModels } from '~/composables/useApi'

const { list, activate: activateModel, train: trainModel } = useAiModels()

const models = ref<any[]>([])
const busy = ref<Record<string, string | false>>({})
const feedback = ref<Record<string, { ok: boolean; msg: string }>>({})
const showTrainForm = ref<Record<string, boolean>>({})
const trainDates = ref<Record<string, { start: string; end: string }>>({})

onMounted(async () => {
  try {
    const { data } = await list()
    models.value = data.results ?? data
  } catch { models.value = [] }
})

function openTrainForm(model: any) {
  const now = new Date()
  const end = now.toISOString().slice(0, 10)
  const start = new Date(now.setDate(now.getDate() - 30)).toISOString().slice(0, 10)
  trainDates.value[model.id] = { start, end }
  showTrainForm.value[model.id] = true
}

async function submitTrain(model: any) {
  const { start, end } = trainDates.value[model.id] ?? {}
  if (!start || !end) return
  busy.value[model.id] = 'train'
  feedback.value[model.id] = { ok: false, msg: '' }
  try {
    await trainModel(model.id, start, end)
    showTrainForm.value[model.id] = false
    feedback.value[model.id] = { ok: true, msg: `Training queued for ${start} → ${end}` }
  } catch (err: any) {
    const msg = err?.response?.data?.message ?? 'Training requires Celery worker to be running'
    feedback.value[model.id] = { ok: false, msg }
  } finally {
    busy.value[model.id] = false
    setTimeout(() => { delete feedback.value[model.id] }, 5000)
  }
}

async function activate(model: any) {
  busy.value[model.id] = 'activate'
  feedback.value[model.id] = { ok: false, msg: '' }
  try {
    await activateModel(model.id)
    model.is_active = true
    models.value.forEach(m => { if (m.id !== model.id && m.model_type === model.model_type) m.is_active = false })
    feedback.value[model.id] = { ok: true, msg: 'Model activated successfully' }
  } catch {
    feedback.value[model.id] = { ok: false, msg: 'Activation failed' }
  } finally {
    busy.value[model.id] = false
    setTimeout(() => { delete feedback.value[model.id] }, 3000)
  }
}

const statusBadge = (s: string) => ({ active: 'resolved', training: 'info', failed: 'critical', pending: 'neutral', archived: 'neutral' }[s] ?? 'neutral')
const formatTime = (ts: string) => ts ? new Date(ts).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'
</script>
