<template>
  <!-- Floating button -->
  <button
    @click="open = !open"
    class="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full bg-cyan-500 hover:bg-cyan-400 shadow-lg shadow-cyan-500/30 flex items-center justify-center transition-all hover:scale-110"
    :title="open ? 'Close AI Assistant' : 'Ask AI Assistant'"
  >
    <MessageCircle v-if="!open" :size="20" class="text-white" />
    <X v-else :size="20" class="text-white" />
  </button>

  <!-- Chat panel -->
  <Transition name="chat">
    <div
      v-if="open"
      class="fixed bottom-22 right-6 z-50 w-80 sm:w-96 flex flex-col rounded-2xl border border-white/10 bg-[#0a1628]/95 backdrop-blur-xl shadow-2xl shadow-black/50 overflow-hidden"
      style="height: 480px;"
    >
      <!-- Header -->
      <div class="flex items-center gap-3 px-4 py-3 border-b border-white/10 bg-white/[0.03]">
        <div class="w-7 h-7 rounded-full bg-cyan-500/20 flex items-center justify-center">
          <Bot :size="14" class="text-cyan-400" />
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-xs font-semibold text-white">IntelliOLT AI</p>
          <p class="text-[10px] text-emerald-400 flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
            Ollama · llama3.2:3b · local
          </p>
        </div>
        <button @click="messages = []" title="Clear chat" class="text-slate-600 hover:text-slate-400 transition-colors">
          <Trash2 :size="13" />
        </button>
      </div>

      <!-- Messages -->
      <div ref="scrollEl" class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        <!-- Welcome -->
        <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-center gap-3 pb-4">
          <div class="w-12 h-12 rounded-full bg-cyan-500/10 flex items-center justify-center">
            <Bot :size="22" class="text-cyan-400" />
          </div>
          <p class="text-xs text-slate-400 max-w-[220px]">
            Ask me anything about your network , anomalies, OLT status, traffic, alerts.
          </p>
          <div class="flex flex-col gap-1.5 w-full mt-1">
            <button
              v-for="s in suggestions"
              :key="s"
              @click="sendSuggestion(s)"
              class="text-left text-[11px] px-3 py-2 rounded-lg border border-white/10 bg-white/[0.03] hover:bg-white/[0.07] text-slate-400 hover:text-slate-200 transition-all"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <!-- Message bubbles -->
        <template v-else>
          <div
            v-for="(msg, i) in messages"
            :key="i"
            :class="['flex gap-2', msg.role === 'user' ? 'flex-row-reverse' : 'flex-row']"
          >
            <!-- Avatar -->
            <div :class="['w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center text-[10px] mt-0.5',
              msg.role === 'user' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-slate-700 text-slate-300']">
              <User v-if="msg.role === 'user'" :size="11" />
              <Bot v-else :size="11" />
            </div>
            <!-- Bubble -->
            <div :class="['max-w-[78%] px-3 py-2 rounded-2xl text-[12px] leading-relaxed',
              msg.role === 'user'
                ? 'bg-cyan-500/20 text-cyan-100 rounded-tr-sm'
                : 'bg-white/[0.06] text-slate-300 rounded-tl-sm']">
              {{ msg.content }}
            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="loading" class="flex gap-2">
            <div class="w-6 h-6 rounded-full bg-slate-700 flex-shrink-0 flex items-center justify-center mt-0.5">
              <Bot :size="11" class="text-slate-300" />
            </div>
            <div class="bg-white/[0.06] px-3 py-2 rounded-2xl rounded-tl-sm flex items-center gap-1">
              <span v-for="n in 3" :key="n" :style="`animation-delay: ${(n-1)*0.15}s`"
                class="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" />
            </div>
          </div>
        </template>
      </div>

      <!-- Input -->
      <div class="px-3 py-3 border-t border-white/10 bg-white/[0.02]">
        <form @submit.prevent="send" class="flex gap-2 items-end">
          <textarea
            v-model="input"
            @keydown.enter.exact.prevent="send"
            placeholder="Ask about your network..."
            rows="1"
            class="flex-1 resize-none bg-white/[0.05] border border-white/10 rounded-xl px-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 focus:bg-white/[0.08] transition-all"
            :disabled="loading"
          />
          <button
            type="submit"
            :disabled="!input.trim() || loading"
            class="w-8 h-8 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition-all flex-shrink-0"
          >
            <SendHorizonal :size="14" class="text-white" />
          </button>
        </form>
        <p class="text-[10px] text-slate-700 mt-1.5 text-center">Runs locally · no data leaves your server</p>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { MessageCircle, X, Bot, User, Trash2, SendHorizonal } from 'lucide-vue-next'

const { ask } = useAiAssistant()

const open = ref(false)
const input = ref('')
const loading = ref(false)
const scrollEl = ref<HTMLElement | null>(null)

const messages = ref<{ role: 'user' | 'assistant'; content: string }[]>([])

const suggestions = [
  'What is the current global network status?',
  'Are there any unresolved critical anomalies?',
  'Which OLTs are degraded and why?',
  'Analyze active alerts and prioritize interventions.',
]

async function send() {
  const q = input.value.trim()
  if (!q || loading.value) return

  messages.value.push({ role: 'user', content: q })
  input.value = ''
  loading.value = true
  await nextTick()
  scrollToBottom()

  try {
    const { data } = await ask(q)
    messages.value.push({ role: 'assistant', content: data.answer })
  } catch {
    messages.value.push({ role: 'assistant', content: 'Sorry, I could not reach the AI. Make sure Ollama is running.' })
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

async function sendSuggestion(s: string) {
  input.value = s
  await send()
}

function scrollToBottom() {
  if (scrollEl.value) scrollEl.value.scrollTop = scrollEl.value.scrollHeight
}
</script>

<style scoped>
.chat-enter-active, .chat-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.chat-enter-from, .chat-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.97);
}
</style>
