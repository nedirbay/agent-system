<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { agentsApi, ApiError, workflowsApi, type AgentSpec } from '@/api'
import {
  agentMeta,
  applyEvent,
  isRealAgent,
  newRunState,
  phaseLabel,
  type Phase,
  type RunState,
} from '@/lib/agentRun'

const draft = ref('')
const running = ref(false)
const run = reactive<RunState>(newRunState())

// Agent catalogue (registry)
const catalog = ref<AgentSpec[]>([])
const catalogLoading = ref(true)

const suggestions = [
  'Summarize what the knowledge base says about the platform architecture.',
  'Analyze the indexed documents and report the key findings.',
  'What are the main risks mentioned across the documents?',
]

const TIER_LABEL: Record<string, string> = {
  reasoning: 'Reasoning',
  general: 'General',
  light: 'Lightweight',
}

onMounted(async () => {
  try {
    catalog.value = await agentsApi.registry()
  } catch {
    catalog.value = []
  } finally {
    catalogLoading.value = false
  }
})

async function start(text?: string) {
  const task = (text ?? draft.value).trim()
  if (!task || running.value) return

  Object.assign(run, newRunState())
  run.phase = 'planning' as Phase
  draft.value = task
  running.value = true

  try {
    await workflowsApi.runStream(task, (event) => applyEvent(run, event))
    if (run.phase === 'running') run.phase = 'completed'
  } catch (err) {
    run.error =
      err instanceof ApiError ? err.message : 'The orchestration service is unavailable.'
    run.phase = 'failed'
  } finally {
    running.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-6">
    <!-- Task composer -->
    <section
      class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-800"
    >
      <div class="mb-3 flex items-center gap-2.5">
        <span
          class="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/30"
        >
          <el-icon :size="18"><MagicStick /></el-icon>
        </span>
        <div>
          <h2 class="text-sm font-semibold text-slate-900 dark:text-white">Give the agents a task</h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">
            The orchestrator plans it, then routes each step to a specialized agent — live.
          </p>
        </div>
      </div>

      <el-input
        v-model="draft"
        type="textarea"
        :autosize="{ minRows: 2, maxRows: 5 }"
        resize="none"
        placeholder="Describe what you want done…"
        :disabled="running"
        @keydown.enter.exact.prevent="start()"
      />

      <div class="mt-3 flex flex-wrap items-center gap-2">
        <el-button type="primary" :loading="running" :disabled="!draft.trim()" @click="start()">
          {{ running ? 'Running…' : 'Run task' }}
        </el-button>
        <button
          v-for="s in suggestions"
          :key="s"
          :disabled="running"
          class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 transition-colors hover:border-indigo-300 hover:text-indigo-600 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-indigo-500/50"
          @click="start(s)"
        >
          {{ s }}
        </button>
      </div>
    </section>

    <!-- Live execution -->
    <section v-if="run.phase !== 'idle'" class="space-y-4">
      <div class="flex items-center gap-3">
        <span
          v-if="run.phase === 'planning' || run.phase === 'running'"
          class="h-2.5 w-2.5 animate-pulse rounded-full bg-indigo-500"
        />
        <span
          v-else
          class="h-2.5 w-2.5 rounded-full"
          :class="run.phase === 'completed' ? 'bg-emerald-500' : 'bg-rose-500'"
        />
        <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ phaseLabel(run.phase) }}</p>
        <el-tag v-if="run.fallback" type="warning" size="small" effect="light" class="ml-auto">
          Heuristic plan (LLM offline)
        </el-tag>
      </div>

      <p
        v-if="run.summary"
        class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
      >
        <span class="font-medium text-slate-800 dark:text-slate-100">Plan:</span> {{ run.summary }}
      </p>

      <ol class="relative space-y-3">
        <li
          v-for="step in run.steps"
          :key="step.order"
          class="relative flex gap-3 rounded-2xl border bg-white p-4 transition-all dark:bg-slate-800"
          :class="{
            'border-indigo-300 shadow-md shadow-indigo-500/10 ring-1 ring-indigo-200 dark:border-indigo-500/50 dark:ring-indigo-500/20':
              step.status === 'running',
            'border-slate-200 dark:border-slate-700':
              step.status === 'pending' || step.status === 'completed',
            'border-rose-300 dark:border-rose-500/40': step.status === 'failed',
            'border-amber-300 dark:border-amber-500/40': step.status === 'awaiting',
          }"
        >
          <div class="shrink-0">
            <span
              class="grid h-10 w-10 place-items-center rounded-xl bg-slate-100 dark:bg-slate-700"
              :class="step.status === 'pending' ? 'opacity-50' : ''"
            >
              <el-icon v-if="step.status === 'running'" :size="20" class="animate-spin text-indigo-500">
                <Loading />
              </el-icon>
              <el-icon v-else-if="step.status === 'completed'" :size="20" class="text-emerald-500">
                <CircleCheckFilled />
              </el-icon>
              <el-icon v-else-if="step.status === 'failed'" :size="20" class="text-rose-500">
                <CircleCloseFilled />
              </el-icon>
              <el-icon v-else-if="step.status === 'awaiting'" :size="20" class="text-amber-500">
                <WarningFilled />
              </el-icon>
              <el-icon v-else :size="20" :class="agentMeta(step.agent_type).tint">
                <component :is="agentMeta(step.agent_type).icon" />
              </el-icon>
            </span>
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-sm font-semibold text-slate-900 dark:text-white">{{ step.agent_type }}</span>
              <el-tag
                v-if="step.status === 'completed'"
                :type="isRealAgent(step) ? 'success' : 'info'"
                size="small"
                effect="light"
              >
                {{ isRealAgent(step) ? 'Real agent' : 'LLM' }}
              </el-tag>
              <el-tag v-if="step.requires_approval" type="warning" size="small" effect="plain">
                Needs approval
              </el-tag>
              <span v-if="step.attempts && step.attempts > 1" class="text-xs text-slate-400">
                {{ step.attempts }} attempts
              </span>
            </div>

            <p class="mt-0.5 text-sm text-slate-500 dark:text-slate-400">{{ step.objective }}</p>

            <p
              v-if="step.status === 'completed' && step.result"
              class="mt-2 line-clamp-4 whitespace-pre-wrap rounded-lg bg-slate-50 px-3 py-2 text-xs leading-relaxed text-slate-600 dark:bg-slate-900 dark:text-slate-300"
            >
              {{ step.result }}
            </p>
            <p
              v-else-if="step.status === 'failed'"
              class="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-600 dark:bg-rose-500/10 dark:text-rose-400"
            >
              {{ step.error ?? 'Step failed' }}
            </p>
            <p
              v-else-if="step.status === 'awaiting'"
              class="mt-2 text-xs font-medium text-amber-600 dark:text-amber-400"
            >
              Paused — this action needs human approval before it runs.
            </p>
          </div>
        </li>
      </ol>

      <p
        v-if="run.error"
        class="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-600 dark:bg-rose-500/10 dark:text-rose-400"
      >
        {{ run.error }}
      </p>
    </section>

    <!-- Agent catalogue -->
    <section class="space-y-3">
      <div class="flex items-center gap-2">
        <h2 class="text-sm font-semibold text-slate-900 dark:text-white">Available agents</h2>
        <span class="text-xs text-slate-400">{{ catalog.length }} in the registry</span>
      </div>

      <div v-if="catalogLoading" class="grid gap-3 sm:grid-cols-2">
        <el-skeleton v-for="i in 4" :key="i" :rows="2" animated class="rounded-2xl p-4" />
      </div>

      <div v-else class="grid gap-3 sm:grid-cols-2">
        <div
          v-for="agent in catalog"
          :key="agent.type"
          class="rounded-2xl border border-slate-200 bg-white p-4 transition-shadow hover:shadow-md dark:border-slate-700 dark:bg-slate-800"
        >
          <div class="flex items-start gap-3">
            <span
              class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-slate-100 dark:bg-slate-700"
            >
              <el-icon :size="20" :class="agentMeta(agent.type).tint">
                <component :is="agentMeta(agent.type).icon" />
              </el-icon>
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-sm font-semibold text-slate-900 dark:text-white">{{ agent.type }}</span>
                <el-tag size="small" effect="plain" type="info">
                  {{ TIER_LABEL[agent.tier] ?? agent.tier }}
                </el-tag>
                <el-tag v-if="agent.requires_approval" size="small" effect="plain" type="warning">
                  Approval
                </el-tag>
              </div>
              <p class="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                {{ agent.description }}
              </p>
              <div class="mt-2 flex flex-wrap gap-1">
                <span
                  v-for="cap in agent.capabilities"
                  :key="cap"
                  class="rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500 dark:bg-slate-700 dark:text-slate-300"
                >
                  {{ cap }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
