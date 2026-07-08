<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ApiError,
  connectorsApi,
  type ConnectorConnection,
  type ConnectorSpec,
} from '@/api'

const catalog = ref<ConnectorSpec[]>([])
const connections = ref<ConnectorConnection[]>([])
const loading = ref(true)

// Connect dialog
const dialogOpen = ref(false)
const activeSpec = ref<ConnectorSpec | null>(null)
const form = reactive<{ label: string; values: Record<string, string> }>({
  label: '',
  values: {},
})
const submitting = ref(false)

const CATEGORY_LABEL: Record<string, string> = {
  messaging: 'Messaging',
  email: 'Email',
  productivity: 'Productivity',
  custom: 'Custom',
}

/** Index the catalogue by type so connections can show their icon/name. */
const specByType = computed<Record<string, ConnectorSpec>>(() =>
  Object.fromEntries(catalog.value.map((s) => [s.type, s])),
)

async function refresh() {
  loading.value = true
  try {
    const [cat, conns] = await Promise.all([
      connectorsApi.catalog(),
      connectorsApi.list(),
    ])
    catalog.value = cat
    connections.value = conns
  } catch (err) {
    ElMessage.error(
      err instanceof ApiError ? err.message : 'Could not load connectors',
    )
  } finally {
    loading.value = false
  }
}

onMounted(refresh)

function openConnect(spec: ConnectorSpec) {
  activeSpec.value = spec
  form.label = ''
  form.values = Object.fromEntries(spec.fields.map((f) => [f.key, '']))
  dialogOpen.value = true
}

function missingRequired(): boolean {
  const spec = activeSpec.value
  if (!spec) return true
  return spec.fields.some((f) => f.required && !form.values[f.key]?.trim())
}

async function submit() {
  const spec = activeSpec.value
  if (!spec || missingRequired()) return
  submitting.value = true
  try {
    // Drop blank optional fields so they aren't sent as empty strings.
    const values: Record<string, string> = {}
    for (const [k, v] of Object.entries(form.values)) {
      if (v.trim()) values[k] = v.trim()
    }
    await connectorsApi.add(spec.type, form.label.trim() || null, values)
    ElMessage.success(`${spec.name} connected`)
    dialogOpen.value = false
    await refresh()
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : 'Could not connect')
  } finally {
    submitting.value = false
  }
}

async function remove(conn: ConnectorConnection) {
  const name = specByType.value[conn.connector_type]?.name ?? conn.connector_type
  try {
    await ElMessageBox.confirm(
      `Remove “${conn.label}” (${name})? Its stored credentials will be deleted.`,
      'Remove connection',
      { type: 'warning', confirmButtonText: 'Remove', cancelButtonText: 'Cancel' },
    )
  } catch {
    return // cancelled
  }
  try {
    await connectorsApi.remove(conn.id)
    ElMessage.success('Connection removed')
    await refresh()
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : 'Could not remove')
  }
}

function statusType(status: string): 'success' | 'danger' | 'info' {
  if (status === 'connected') return 'success'
  if (status === 'error') return 'danger'
  return 'info'
}
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-3">
      <span
        class="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/30"
      >
        <el-icon :size="20"><Connection /></el-icon>
      </span>
      <div>
        <h1 class="text-lg font-semibold text-slate-900 dark:text-white">Connectors</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          Connect external systems so agents can act on them. Tokens are encrypted at rest.
        </p>
      </div>
    </div>

    <!-- Your connections -->
    <section v-if="connections.length || loading" class="space-y-3">
      <h2 class="text-sm font-semibold text-slate-900 dark:text-white">Your connections</h2>

      <div v-if="loading" class="grid gap-3 sm:grid-cols-2">
        <el-skeleton v-for="i in 2" :key="i" :rows="2" animated class="rounded-2xl p-4" />
      </div>

      <div v-else class="grid gap-3 sm:grid-cols-2">
        <div
          v-for="conn in connections"
          :key="conn.id"
          class="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800"
        >
          <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-slate-100 text-indigo-500 dark:bg-slate-700">
            <el-icon :size="20">
              <component :is="specByType[conn.connector_type]?.icon ?? 'Connection'" />
            </el-icon>
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <span class="truncate text-sm font-semibold text-slate-900 dark:text-white">
                {{ conn.label }}
              </span>
              <el-tag :type="statusType(conn.status)" size="small" effect="light">
                {{ conn.status }}
              </el-tag>
            </div>
            <p class="text-xs text-slate-500 dark:text-slate-400">
              {{ specByType[conn.connector_type]?.name ?? conn.connector_type }}
            </p>
            <p v-if="conn.secret_hint" class="mt-1 font-mono text-xs text-slate-400">
              token {{ conn.secret_hint }}
            </p>
          </div>
          <el-button
            text
            type="danger"
            size="small"
            :icon="'Delete'"
            @click="remove(conn)"
          />
        </div>
      </div>
    </section>

    <!-- Available connectors -->
    <section class="space-y-3">
      <div class="flex items-center gap-2">
        <h2 class="text-sm font-semibold text-slate-900 dark:text-white">Available connectors</h2>
        <span class="text-xs text-slate-400">{{ catalog.length }} integrations</span>
      </div>

      <div class="grid gap-3 sm:grid-cols-2">
        <div
          v-for="spec in catalog"
          :key="spec.type"
          class="flex flex-col rounded-2xl border border-slate-200 bg-white p-4 transition-shadow hover:shadow-md dark:border-slate-700 dark:bg-slate-800"
        >
          <div class="flex items-start gap-3">
            <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-slate-100 text-indigo-500 dark:bg-slate-700">
              <el-icon :size="20"><component :is="spec.icon" /></el-icon>
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-sm font-semibold text-slate-900 dark:text-white">{{ spec.name }}</span>
                <el-tag size="small" effect="plain" type="info">
                  {{ CATEGORY_LABEL[spec.category] ?? spec.category }}
                </el-tag>
              </div>
              <p class="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                {{ spec.description }}
              </p>
            </div>
          </div>
          <div class="mt-3 flex justify-end">
            <el-button type="primary" plain size="small" :icon="'Plus'" @click="openConnect(spec)">
              Connect
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- Connect dialog: prompts for the connector's credentials -->
    <el-dialog
      v-model="dialogOpen"
      :title="activeSpec ? `Connect ${activeSpec.name}` : 'Connect'"
      width="460px"
    >
      <div v-if="activeSpec" class="space-y-4">
        <p class="text-sm text-slate-500 dark:text-slate-400">{{ activeSpec.description }}</p>

        <el-form label-position="top" @submit.prevent>
          <el-form-item label="Name (optional)">
            <el-input v-model="form.label" :placeholder="activeSpec.name" />
          </el-form-item>

          <el-form-item
            v-for="field in activeSpec.fields"
            :key="field.key"
            :required="field.required"
          >
            <template #label>
              <span class="flex items-center gap-1.5">
                {{ field.label }}
                <el-icon v-if="field.kind === 'secret'" :size="13" class="text-amber-500">
                  <Lock />
                </el-icon>
              </span>
            </template>
            <el-input
              v-model="form.values[field.key]"
              :type="field.kind === 'secret' ? 'password' : 'text'"
              :show-password="field.kind === 'secret'"
              :placeholder="field.placeholder"
            />
            <p v-if="field.help" class="mt-1 text-xs text-slate-400">{{ field.help }}</p>
          </el-form-item>
        </el-form>

        <p
          class="flex items-center gap-1.5 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:bg-slate-900 dark:text-slate-400"
        >
          <el-icon :size="13"><Lock /></el-icon>
          Secrets are encrypted before storage and never shown again.
        </p>

        <a
          v-if="activeSpec.docs_url"
          :href="activeSpec.docs_url"
          target="_blank"
          rel="noopener"
          class="inline-block text-xs text-indigo-500 hover:underline"
        >
          Where do I find these? →
        </a>
      </div>

      <template #footer>
        <el-button @click="dialogOpen = false">Cancel</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          :disabled="missingRequired()"
          @click="submit"
        >
          Connect
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
