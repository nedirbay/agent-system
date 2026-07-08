<script setup lang="ts">
import { nextTick, reactive, ref } from 'vue'
import { ApiError, workflowsApi } from '@/api'
import {
  agentMeta,
  applyEvent,
  isRealAgent,
  newRunState,
  type Phase,
  type RunState,
} from '@/lib/agentRun'

interface ChatMessage {
  role: 'user' | 'assistant'
  text?: string
  run?: RunState
}

const messages = ref<ChatMessage[]>([])
const draft = ref('')
const sending = ref(false)
const scroller = ref<HTMLElement | null>(null)

const suggestions = [
  'What documents are in the knowledge base?',
  'Summarize the key findings and write a short report.',
  'Analyze the indexed documents for risks.',
]

async function scrollToBottom() {
  await nextTick()
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: 'smooth' })
}

async function send(text?: string) {
  const question = (text ?? draft.value).trim()
  if (!question || sending.value) return

  messages.value.push({ role: 'user', text: question })
  const run = reactive<RunState>(newRunState())
  run.phase = 'planning' as Phase
  messages.value.push({ role: 'assistant', run })
  draft.value = ''
  sending.value = true
  await scrollToBottom()

  try {
    await workflowsApi.runStream(question, (event) => {
      applyEvent(run, event)
      void scrollToBottom()
    })
    if (run.phase === 'running') run.phase = 'completed'
  } catch (err) {
    run.error =
      err instanceof ApiError ? err.message : 'The agents are unavailable right now.'
    run.phase = 'failed'
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
        <h2 class="text-lg font-semibold text-slate-900 dark:text-white">Ask the platform anything</h2>
        <p class="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">
          The orchestrator picks the right agents for your request and shows them working live.
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
      <template v-for="(m, i) in messages" :key="i">
        <!-- User -->
        <div v-if="m.role === 'user'" class="flex justify-end">
          <div class="max-w-[80%] rounded-2xl bg-indigo-600 px-4 py-3 text-sm leading-relaxed text-white">
            {{ m.text }}
          </div>
        </div>

        <!-- Assistant: live orchestration -->
        <div v-else class="flex gap-3">
          <div
            class="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white"
          >
            <el-icon :size="16"><Cpu /></el-icon>
          </div>

          <div class="max-w-[85%] flex-1 space-y-2">
            <!-- Agent activity timeline -->
            <div
              v-if="m.run && m.run.steps.length"
              class="space-y-1.5 rounded-2xl bg-white p-3 shadow-sm dark:bg-slate-800"
            >
              <p class="px-1 text-xs font-medium text-slate-400">
                {{ m.run.phase === 'completed' ? 'Agents used' : 'Working…' }}
              </p>
              <div
                v-for="step in m.run.steps"
                :key="step.order"
                class="flex items-center gap-2.5 rounded-lg px-2 py-1.5"
                :class="step.status === 'running' ? 'bg-indigo-50 dark:bg-indigo-500/10' : ''"
              >
                <el-icon v-if="step.status === 'running'" :size="15" class="animate-spin text-indigo-500">
                  <Loading />
                </el-icon>
                <el-icon v-else-if="step.status === 'completed'" :size="15" class="text-emerald-500">
                  <CircleCheckFilled />
                </el-icon>
                <el-icon v-else-if="step.status === 'failed'" :size="15" class="text-rose-500">
                  <CircleCloseFilled />
                </el-icon>
                <el-icon v-else-if="step.status === 'awaiting'" :size="15" class="text-amber-500">
                  <WarningFilled />
                </el-icon>
                <el-icon v-else :size="15" :class="agentMeta(step.agent_type).tint">
                  <component :is="agentMeta(step.agent_type).icon" />
                </el-icon>

                <span class="text-xs font-medium text-slate-700 dark:text-slate-200">
                  {{ step.agent_type }}
                </span>
                <el-tag
                  v-if="step.status === 'completed' && isRealAgent(step)"
                  type="success"
                  size="small"
                  effect="light"
                  class="!h-4 !px-1 !text-[10px]"
                >
                  real
                </el-tag>
                <span class="truncate text-xs text-slate-400">{{ step.objective }}</span>
              </div>
            </div>

            <!-- Planning placeholder -->
            <div
              v-else-if="m.run && (m.run.phase === 'planning' || m.run.phase === 'running')"
              class="inline-flex items-center gap-2 rounded-2xl bg-white px-4 py-3 shadow-sm dark:bg-slate-800"
            >
              <span class="flex gap-1">
                <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
                <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
                <span class="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
              </span>
              <span class="text-xs text-slate-400">Planning…</span>
            </div>

            <!-- Final answer -->
            <div
              v-if="m.run && m.run.phase === 'completed' && m.run.finalAnswer"
              class="rounded-2xl bg-white px-4 py-3 text-sm leading-relaxed text-slate-700 shadow-sm dark:bg-slate-800 dark:text-slate-200"
            >
              <p class="whitespace-pre-wrap">{{ m.run.finalAnswer }}</p>
            </div>

            <!-- Error -->
            <div
              v-if="m.run && m.run.phase === 'failed'"
              class="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:bg-rose-500/10 dark:text-rose-400"
            >
              {{ m.run.error || 'The task could not be completed.' }}
            </div>
          </div>
        </div>
      </template>
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
        placeholder="Ask a question or describe a task…"
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
