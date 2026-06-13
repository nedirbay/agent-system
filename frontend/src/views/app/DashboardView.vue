<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  dashboardApi,
  documentsApi,
  type AgentRecord,
  type DocumentRecord,
  type WorkflowRecord,
} from '@/api'

const loading = ref(true)
const documents = ref<DocumentRecord[]>([])
const agents = ref<AgentRecord[]>([])
const workflows = ref<WorkflowRecord[]>([])
const offline = ref(false)

function countBy<T>(items: T[], key: (item: T) => string | null): Record<string, number> {
  const out: Record<string, number> = {}
  for (const item of items) {
    const k = key(item) ?? 'unknown'
    out[k] = (out[k] ?? 0) + 1
  }
  return out
}

const cards = computed(() => [
  { label: 'Documents', value: documents.value.length, icon: 'Document', accent: 'from-sky-500 to-cyan-500' },
  { label: 'Agents', value: agents.value.length, icon: 'Cpu', accent: 'from-indigo-500 to-violet-500' },
  { label: 'Workflows', value: workflows.value.length, icon: 'Share', accent: 'from-emerald-500 to-teal-500' },
  {
    label: 'Parsed docs',
    value: documents.value.filter((d) => ['parsed', 'analyzed', 'indexed'].includes(d.status ?? '')).length,
    icon: 'CircleCheck',
    accent: 'from-amber-500 to-orange-500',
  },
])

const docStatus = computed(() => countBy(documents.value, (d) => d.status))
const workflowStatus = computed(() => countBy(workflows.value, (w) => w.status))
const agentTypes = computed(() => countBy(agents.value, (a) => a.agent_type))

const recentDocuments = computed(() =>
  [...documents.value]
    .sort((a, b) => (b.created_at ?? '').localeCompare(a.created_at ?? ''))
    .slice(0, 5),
)

function maxOf(record: Record<string, number>): number {
  return Math.max(1, ...Object.values(record))
}

async function load() {
  loading.value = true
  const [docs, ag, wf] = await Promise.allSettled([
    documentsApi.list(),
    dashboardApi.agents(),
    dashboardApi.workflows(),
  ])
  documents.value = docs.status === 'fulfilled' ? docs.value : []
  agents.value = ag.status === 'fulfilled' ? ag.value : []
  workflows.value = wf.status === 'fulfilled' ? wf.value : []
  offline.value = [docs, ag, wf].every((r) => r.status === 'rejected')
  loading.value = false
}

onMounted(load)
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-6">
    <div class="flex items-end justify-between">
      <div>
        <h2 class="text-xl font-semibold text-slate-900 dark:text-white">Dashboard</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          Live system state across documents, agents, and workflows.
        </p>
      </div>
      <el-button :icon="'Refresh'" :loading="loading" @click="load">Refresh</el-button>
    </div>

    <el-alert
      v-if="offline"
      type="warning"
      show-icon
      :closable="false"
      title="Backend unreachable — showing empty state. Start the API to see live data."
    />

    <!-- Stat cards -->
    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div
        v-for="c in cards"
        :key="c.label"
        class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
      >
        <span
          class="mb-3 grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br text-white"
          :class="c.accent"
        >
          <el-icon :size="20"><component :is="c.icon" /></el-icon>
        </span>
        <p class="text-3xl font-semibold text-slate-900 dark:text-white">{{ c.value }}</p>
        <p class="text-sm text-slate-500 dark:text-slate-400">{{ c.label }}</p>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <!-- Breakdown bars -->
      <div
        class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
      >
        <h3 class="mb-4 text-sm font-semibold text-slate-900 dark:text-white">
          Documents by status
        </h3>
        <el-empty v-if="!Object.keys(docStatus).length" description="No documents" :image-size="60" />
        <div v-else class="space-y-3">
          <div v-for="(count, status) in docStatus" :key="status">
            <div class="mb-1 flex justify-between text-xs text-slate-500 dark:text-slate-400">
              <span class="capitalize">{{ status }}</span>
              <span>{{ count }}</span>
            </div>
            <div class="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                class="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
                :style="{ width: `${(count / maxOf(docStatus)) * 100}%` }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Workflow + agent breakdown -->
      <div
        class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
      >
        <h3 class="mb-4 text-sm font-semibold text-slate-900 dark:text-white">
          Workflows by status
        </h3>
        <el-empty v-if="!Object.keys(workflowStatus).length" description="No workflows" :image-size="60" />
        <div v-else class="flex flex-wrap gap-2">
          <el-tag
            v-for="(count, status) in workflowStatus"
            :key="status"
            effect="light"
            size="large"
          >
            {{ status }} · {{ count }}
          </el-tag>
        </div>

        <h3 class="mt-6 mb-3 text-sm font-semibold text-slate-900 dark:text-white">
          Agents by type
        </h3>
        <el-empty v-if="!Object.keys(agentTypes).length" description="No agents" :image-size="60" />
        <div v-else class="flex flex-wrap gap-2">
          <el-tag
            v-for="(count, type) in agentTypes"
            :key="type"
            type="info"
            effect="plain"
            size="large"
          >
            {{ type }} · {{ count }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- Recent documents -->
    <div
      class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
    >
      <h3 class="mb-4 text-sm font-semibold text-slate-900 dark:text-white">
        Recent documents
      </h3>
      <el-empty v-if="!recentDocuments.length" description="Nothing yet" :image-size="60" />
      <ul v-else class="divide-y divide-slate-100 dark:divide-slate-800">
        <li
          v-for="doc in recentDocuments"
          :key="doc.id"
          class="flex items-center gap-3 py-3"
        >
          <el-icon class="text-slate-400"><Document /></el-icon>
          <span class="flex-1 truncate text-sm text-slate-700 dark:text-slate-200">
            {{ doc.file_name ?? 'unnamed' }}
          </span>
          <el-tag size="small" effect="light">{{ doc.status ?? 'unknown' }}</el-tag>
        </li>
      </ul>
    </div>
  </div>
</template>
