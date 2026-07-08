<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ApiError, documentsApi, type DocumentRecord, type ParseResult } from '@/api'

const documents = ref<DocumentRecord[]>([])
const loading = ref(false)
const uploading = ref(false)
const parsingId = ref<string | null>(null)

const previewOpen = ref(false)
const preview = ref<ParseResult | null>(null)

const stats = computed(() => {
  const total = documents.value.length
  const parsed = documents.value.filter((d) =>
    ['parsed', 'analyzed', 'indexed'].includes(d.status ?? ''),
  ).length
  return { total, parsed, pending: total - parsed }
})

async function refresh() {
  loading.value = true
  try {
    documents.value = await documentsApi.list()
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : 'Failed to load documents')
  } finally {
    loading.value = false
  }
}

async function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploading.value = true
  try {
    await documentsApi.upload(file)
    ElMessage.success(`Uploaded ${file.name}`)
    await refresh()
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : 'Upload failed')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function parse(doc: DocumentRecord) {
  parsingId.value = doc.id
  try {
    preview.value = await documentsApi.parse(doc.id)
    previewOpen.value = true
    await refresh()
  } catch (err) {
    ElMessage.error(err instanceof ApiError ? err.message : 'Parse failed')
  } finally {
    parsingId.value = null
  }
}

function statusType(status: string | null): 'success' | 'warning' | 'info' {
  if (!status) return 'info'
  if (['parsed', 'analyzed', 'indexed'].includes(status)) return 'success'
  if (status === 'uploaded') return 'warning'
  return 'info'
}

function formatSize(bytes: number | null): string {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

onMounted(refresh)
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-6">
    <!-- Header + upload -->
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold text-slate-900 dark:text-white">Workspace</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400">
          Upload, parse, and manage every document in one place.
        </p>
      </div>
      <label>
        <input type="file" class="hidden" @change="onFileChange" />
        <span
          class="inline-flex cursor-pointer items-center gap-2 rounded-full bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-500/30 transition-colors hover:bg-indigo-700"
          :class="uploading && 'pointer-events-none opacity-70'"
        >
          <el-icon :size="16"><UploadFilled /></el-icon>
          {{ uploading ? 'Uploading…' : 'Upload document' }}
        </span>
      </label>
    </div>

    <!-- Stat strip -->
    <div class="grid grid-cols-3 gap-4">
      <div
        v-for="s in [
          { label: 'Total', value: stats.total },
          { label: 'Parsed', value: stats.parsed },
          { label: 'Pending', value: stats.pending },
        ]"
        :key="s.label"
        class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
      >
        <p class="text-2xl font-semibold text-slate-900 dark:text-white">{{ s.value }}</p>
        <p class="text-xs text-slate-500 dark:text-slate-400">{{ s.label }}</p>
      </div>
    </div>

    <!-- Document table -->
    <div
      class="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
    >
      <el-table v-loading="loading" :data="documents" style="width: 100%" empty-text="No documents yet — upload one to get started.">
        <el-table-column prop="file_name" label="File" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <el-icon class="text-slate-400"><Document /></el-icon>
              <span class="truncate font-medium text-slate-700 dark:text-slate-200">
                {{ row.file_name ?? 'unnamed' }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="mime_type" label="Type" width="140">
          <template #default="{ row }">
            <span class="text-xs text-slate-500">{{ row.mime_type ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Size" width="100">
          <template #default="{ row }">
            <span class="text-xs text-slate-500">{{ formatSize(row.size) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="Status" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">
              {{ row.status ?? 'unknown' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="120" align="right">
          <template #default="{ row }">
            <el-button
              size="small"
              :loading="parsingId === row.id"
              @click="parse(row as DocumentRecord)"
            >
              Parse
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Parse preview -->
    <el-dialog v-model="previewOpen" title="Parse result" width="640px">
      <div v-if="preview" class="space-y-4">
        <div class="flex flex-wrap gap-2">
          <el-tag type="success" effect="light">{{ preview.char_count }} chars</el-tag>
          <el-tag effect="light">{{ preview.page_count ?? 0 }} pages</el-tag>
          <el-tag v-if="preview.ocr_used" type="warning" effect="light">OCR used</el-tag>
          <el-tag type="info" effect="light">{{ preview.status }}</el-tag>
        </div>
        <pre
          class="max-h-80 overflow-auto rounded-xl bg-slate-50 p-4 text-xs whitespace-pre-wrap text-slate-600 dark:bg-slate-950 dark:text-slate-300"
        >{{ preview.text_preview || '(no extractable text)' }}</pre>
      </div>
    </el-dialog>
  </div>
</template>
