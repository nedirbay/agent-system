<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { ApiError, qaApi, type QaCitation } from '@/api'

interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  grounded?: boolean
  llmUsed?: boolean
  citations?: QaCitation[]
  error?: boolean
}

const messages = ref<ChatMessage[]>([])
const draft = ref('')
const sending = ref(false)
const scroller = ref<HTMLElement | null>(null)

const suggestions = [
  'What documents are in the knowledge base?',
  'Summarize the refund policy.',
  'What are the key findings so far?',
]

async function scrollToBottom() {
  await nextTick()
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: 'smooth' })
}

async function send(text?: string) {
  const question = (text ?? draft.value).trim()
  if (!question || sending.value) return

  messages.value.push({ role: 'user', text: question })
  draft.value = ''
  sending.value = true
  await scrollToBottom()

  try {
    const answer = await qaApi.ask(question)
    messages.value.push({
      role: 'assistant',
      text: answer.answer,
      grounded: answer.grounded,
      llmUsed: answer.llm_used,
      citations: answer.citations,
    })
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      error: true,
      text:
        err instanceof ApiError
          ? `Could not answer: ${err.message}`
          : 'The Q&A service is unavailable.',
    })
  } finally {
    sending.value = false
    await scrollToBottom()
  }
}
</script>

<template>
  <div class="mx-auto flex h-[calc(100vh-9rem)] max-w-3xl flex-col">
    <!-- Messages -->
    <div ref="scroller" class="flex-1 space-y-5 overflow-y-auto pb-4">
      <!-- Empty state -->
      <div
        v-if="messages.length === 0"
        class="flex h-full flex-col items-center justify-center text-center"
      >
        <span
          class="mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/30"
        >
          <el-icon :size="28"><ChatDotRound /></el-icon>
        </span>
        <h2 class="text-lg font-semibold text-slate-900 dark:text-white">
          Ask the platform anything
        </h2>
        <p class="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">
          Grounded answers from your indexed documents, with citations.
        </p>
        <div class="mt-6 flex flex-wrap justify-center gap-2">
          <button
            v-for="s in suggestions"
            :key="s"
            class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 transition-colors hover:border-indigo-300 hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-indigo-500/50 dark:hover:text-indigo-400"
            @click="send(s)"
          >
            {{ s }}
          </button>
        </div>
      </div>

      <!-- Bubbles -->
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="flex gap-3"
        :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          v-if="m.role === 'assistant'"
          class="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white"
        >
          <el-icon :size="16"><Cpu /></el-icon>
        </div>
        <div
          class="max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed"
          :class="
            m.role === 'user'
              ? 'bg-indigo-600 text-white'
              : m.error
                ? 'bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400'
                : 'bg-white text-slate-700 shadow-sm dark:bg-slate-800 dark:text-slate-200'
          "
        >
          <p class="whitespace-pre-wrap">{{ m.text }}</p>

          <!-- Answer metadata + citations -->
          <div v-if="m.role === 'assistant' && !m.error" class="mt-3 space-y-2">
            <div class="flex flex-wrap gap-1.5">
              <el-tag :type="m.grounded ? 'success' : 'info'" size="small" effect="light">
                {{ m.grounded ? 'Grounded' : 'No sources' }}
              </el-tag>
              <el-tag :type="m.llmUsed ? 'primary' : 'warning'" size="small" effect="light">
                {{ m.llmUsed ? 'LLM' : 'Extractive' }}
              </el-tag>
            </div>
            <details v-if="m.citations?.length" class="group">
              <summary
                class="cursor-pointer text-xs font-medium text-indigo-600 dark:text-indigo-400"
              >
                {{ m.citations.length }} citation{{ m.citations.length > 1 ? 's' : '' }}
              </summary>
              <ul class="mt-2 space-y-1.5">
                <li
                  v-for="c in m.citations"
                  :key="c.index"
                  class="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:bg-slate-900 dark:text-slate-400"
                >
                  <span class="font-medium text-slate-700 dark:text-slate-300">
                    [{{ c.index }}]
                  </span>
                  {{ c.snippet }}
                  <span class="text-slate-400">· score {{ c.score.toFixed(2) }}</span>
                </li>
              </ul>
            </details>
          </div>
        </div>
      </div>

      <!-- Typing indicator -->
      <div v-if="sending" class="flex gap-3">
        <div
          class="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white"
        >
          <el-icon :size="16"><Cpu /></el-icon>
        </div>
        <div class="rounded-2xl bg-white px-4 py-3 shadow-sm dark:bg-slate-800">
          <span class="flex gap-1">
            <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
            <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
            <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
          </span>
        </div>
      </div>
    </div>

    <!-- Composer -->
    <div
      class="flex items-end gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm dark:border-slate-700 dark:bg-slate-800"
    >
      <el-input
        v-model="draft"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 5 }"
        resize="none"
        placeholder="Ask a question…"
        class="!border-0"
        @keydown.enter.exact.prevent="send()"
      />
      <el-button
        type="primary"
        :icon="'Promotion'"
        circle
        size="large"
        :loading="sending"
        :disabled="!draft.trim()"
        @click="send()"
      />
    </div>
  </div>
</template>
