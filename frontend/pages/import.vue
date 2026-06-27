<script setup lang="ts">
import type { BDImportResult } from '~/types'

const api = useApi()

type ImportType = 'companies' | 'prospects' | 'signals'

const activeTab = ref<ImportType>('companies')
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const isRunning = ref(false)
const previewResult = ref<BDImportResult | null>(null)
const commitResult = ref<BDImportResult | null>(null)
const errorMsg = ref<string | null>(null)

const tabs: { key: ImportType; label: string; description: string }[] = [
  {
    key: 'companies',
    label: 'Companies',
    description: 'Import target accounts from a CSV. Required columns: name. Optional: domain, industry, size, region, description, website, linkedin_url, icp_notes, tags.',
  },
  {
    key: 'prospects',
    label: 'Prospects',
    description: 'Import contacts from a CSV. Required columns: full_name, company_name, role. Optional: seniority, email, linkedin_url, department, region, notes.',
  },
  {
    key: 'signals',
    label: 'Signals',
    description: 'Import buying signals from a CSV. Required columns: company_name, signal_type, description. Optional: strength, source, observed_at, title, url, notes.',
  },
]

const activeTabInfo = computed(() => tabs.find(t => t.key === activeTab.value)!)

function switchTab(tab: ImportType) {
  activeTab.value = tab
  clearState()
}

function clearState() {
  selectedFile.value = null
  previewResult.value = null
  commitResult.value = null
  errorMsg.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) setFile(input.files[0])
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) setFile(f)
}

function setFile(f: File) {
  if (!f.name.toLowerCase().endsWith('.csv')) {
    errorMsg.value = 'Only .csv files are accepted.'
    return
  }
  selectedFile.value = f
  previewResult.value = null
  commitResult.value = null
  errorMsg.value = null
}

async function runPreview() {
  if (!selectedFile.value) return
  isRunning.value = true
  errorMsg.value = null
  previewResult.value = null
  try {
    previewResult.value = await api.importCSV(activeTab.value, selectedFile.value, true)
  } catch (err: unknown) {
    errorMsg.value = (err as { data?: { detail?: string } })?.data?.detail ?? 'Preview failed — make sure the backend is running.'
  } finally {
    isRunning.value = false
  }
}

async function runCommit() {
  if (!selectedFile.value) return
  isRunning.value = true
  errorMsg.value = null
  commitResult.value = null
  try {
    commitResult.value = await api.importCSV(activeTab.value, selectedFile.value, false)
  } catch (err: unknown) {
    errorMsg.value = (err as { data?: { detail?: string } })?.data?.detail ?? 'Import failed — make sure the backend is running.'
  } finally {
    isRunning.value = false
  }
}

const activeResult = computed(() => commitResult.value ?? previewResult.value)

const statusColor: Record<string, string> = {
  ok:        'bg-emerald-50 text-emerald-700',
  duplicate: 'bg-amber-50 text-amber-700',
  error:     'bg-red-50 text-red-700',
}

function downloadTemplate(type: ImportType) {
  const url = api.downloadTemplate(type)
  const a = document.createElement('a')
  a.href = url
  a.download = `${type}_template.csv`
  a.click()
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Import Data"
      subtitle="Bring your own BD data into DobryBot from CSV files — local only, no external services"
    />

    <div class="flex-1 p-6 space-y-6 max-w-4xl w-full mx-auto">

      <!-- Privacy notice -->
      <div class="rounded-xl border border-emerald-100 bg-emerald-50 px-4 py-3 flex items-start gap-3">
        <svg class="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
        <p class="text-xs text-emerald-800 leading-relaxed">
          <strong>DobryBot imports your file locally.</strong>
          Nothing is sent to external services. No enrichment, no scraping, no API calls.
          All imported data is stored only on your machine.
        </p>
      </div>

      <!-- Tab switcher -->
      <div class="flex gap-1 rounded-xl border border-gray-200 bg-white p-1">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          :class="activeTab === tab.key
            ? 'bg-blue-600 text-white shadow-sm'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'"
          @click="switchTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Active tab description + template download -->
      <AppCard>
        <div class="px-5 py-4 flex items-start justify-between gap-4">
          <div>
            <h3 class="text-sm font-semibold text-gray-900">Import {{ activeTabInfo.label }}</h3>
            <p class="text-xs text-gray-500 mt-1 leading-relaxed max-w-lg">{{ activeTabInfo.description }}</p>
          </div>
          <button
            class="flex-shrink-0 inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            @click="downloadTemplate(activeTab)"
          >
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Download Template
          </button>
        </div>
      </AppCard>

      <!-- Drop zone -->
      <div
        class="rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors cursor-pointer"
        :class="isDragging
          ? 'border-blue-400 bg-blue-50'
          : selectedFile
            ? 'border-emerald-300 bg-emerald-50'
            : 'border-gray-300 bg-white hover:border-gray-400 hover:bg-gray-50'"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        @drop.prevent="onDrop"
        @click="fileInputRef?.click()"
      >
        <input
          ref="fileInputRef"
          type="file"
          accept=".csv"
          class="hidden"
          @change="onFileChange"
        />

        <template v-if="selectedFile">
          <svg class="h-8 w-8 text-emerald-500 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          <p class="text-sm font-semibold text-emerald-800">{{ selectedFile.name }}</p>
          <p class="text-xs text-emerald-600 mt-0.5">{{ (selectedFile.size / 1024).toFixed(1) }} KB · Click to change</p>
        </template>
        <template v-else>
          <svg class="h-8 w-8 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <p class="text-sm font-medium text-gray-700">Drop your CSV here, or click to browse</p>
          <p class="text-xs text-gray-400 mt-1">Only .csv files · Max 500 KB</p>
        </template>
      </div>

      <!-- Action buttons -->
      <div v-if="selectedFile" class="flex gap-3">
        <button
          class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
          :disabled="isRunning"
          @click="runPreview"
        >
          <span v-if="isRunning && !commitResult" class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
          <svg v-else class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Preview Import
        </button>
        <button
          v-if="previewResult && previewResult.imported_count > 0"
          class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:opacity-50"
          :disabled="isRunning"
          @click="runCommit"
        >
          <span v-if="isRunning && !commitResult" class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
          Commit Import ({{ previewResult.imported_count }} rows)
        </button>
        <button
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
          @click="clearState"
        >
          Clear
        </button>
      </div>

      <!-- Error -->
      <div v-if="errorMsg" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {{ errorMsg }}
      </div>

      <!-- Results -->
      <AppCard v-if="activeResult">
        <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 class="text-sm font-semibold text-gray-900">
              {{ activeResult.dry_run ? 'Preview Results' : 'Import Complete' }}
            </h3>
            <p class="text-xs text-gray-400 mt-0.5">
              {{ activeResult.dry_run
                ? 'No data has been saved yet — click Commit to finalize.'
                : 'Data saved locally. No external calls were made.' }}
            </p>
          </div>
          <span
            v-if="!activeResult.dry_run"
            class="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 px-2.5 py-1 rounded-full"
          >
            Committed
          </span>
          <span v-else class="text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-100 px-2.5 py-1 rounded-full">
            Dry Run
          </span>
        </div>

        <!-- Summary stats -->
        <div class="grid grid-cols-4 divide-x divide-gray-100 border-b border-gray-100">
          <div class="px-5 py-3 text-center">
            <p class="text-lg font-bold text-emerald-600 tabular-nums">{{ activeResult.imported_count }}</p>
            <p class="text-[10px] text-gray-400 mt-0.5">{{ activeResult.dry_run ? 'would import' : 'imported' }}</p>
          </div>
          <div class="px-5 py-3 text-center">
            <p class="text-lg font-bold text-amber-600 tabular-nums">{{ activeResult.duplicate_count }}</p>
            <p class="text-[10px] text-gray-400 mt-0.5">duplicates</p>
          </div>
          <div class="px-5 py-3 text-center">
            <p class="text-lg font-bold text-gray-500 tabular-nums">{{ activeResult.skipped_count }}</p>
            <p class="text-[10px] text-gray-400 mt-0.5">skipped</p>
          </div>
          <div class="px-5 py-3 text-center">
            <p class="text-lg font-bold text-red-500 tabular-nums">{{ activeResult.error_count }}</p>
            <p class="text-[10px] text-gray-400 mt-0.5">errors</p>
          </div>
        </div>

        <!-- Validation errors -->
        <div v-if="activeResult.errors.length" class="px-5 py-3 border-b border-gray-100 space-y-1">
          <p class="text-xs font-semibold text-red-700 mb-1">Validation errors:</p>
          <p v-for="(e, i) in activeResult.errors" :key="i" class="text-xs text-red-600">{{ e }}</p>
        </div>

        <!-- Row preview -->
        <div v-if="activeResult.preview_rows.length" class="overflow-x-auto">
          <table class="app-table">
            <thead>
              <tr>
                <th class="w-12">#</th>
                <th>Status</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in activeResult.preview_rows" :key="row.row">
                <td class="text-gray-400 tabular-nums">{{ row.row }}</td>
                <td>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize"
                    :class="statusColor[row.status] ?? 'bg-gray-100 text-gray-600'"
                  >
                    {{ row.status }}
                  </span>
                </td>
                <td class="text-gray-600 text-xs">{{ row.message }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Safety notice -->
        <div class="px-5 py-3 border-t border-gray-100">
          <p class="text-[11px] text-gray-400">{{ activeResult.safety_notice }}</p>
        </div>
      </AppCard>

    </div>
  </div>
</template>
