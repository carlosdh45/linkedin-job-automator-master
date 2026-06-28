<script setup lang="ts">
import type { BDWorkspaceStatus, BDImportHistoryEntry, BDRestorePreviewResult, BDRestoreResult, BDClearResult } from '~/types'

const api = useApi()

// ── State ──────────────────────────────────────────────────────────────────

const status = ref<BDWorkspaceStatus | null>(null)
const importHistory = ref<BDImportHistoryEntry[]>([])
const loadingStatus = ref(true)
const loadingHistory = ref(true)
const error = ref('')

// Restore
const restoreFile = ref<File | null>(null)
const parsedBackup = ref<Record<string, unknown> | null>(null)
const restorePreviewResult = ref<BDRestorePreviewResult | null>(null)
const restoreResult = ref<BDRestoreResult | null>(null)
const restoringPreview = ref(false)
const restoring = ref(false)
const restoreConfirmText = ref('')
const restoreError = ref('')
const RESTORE_CONFIRM = 'RESTORE DOBRYBOT WORKSPACE'

// Clear all
const clearConfirmText = ref('')
const clearResult = ref<BDClearResult | null>(null)
const clearing = ref(false)
const clearError = ref('')
const CLEAR_CONFIRM = 'CLEAR DOBRYBOT WORKSPACE'

// Clear demo
const clearDemoConfirmText = ref('')
const clearDemoResult = ref<BDClearResult | null>(null)
const clearingDemo = ref(false)
const clearDemoError = ref('')
const CLEAR_DEMO_CONFIRM = 'CLEAR DEMO DATA'

// Clear imported
const clearImportedConfirmText = ref('')
const clearImportedResult = ref<BDClearResult | null>(null)
const clearingImported = ref(false)
const clearImportedError = ref('')
const CLEAR_IMPORTED_CONFIRM = 'CLEAR IMPORTED DATA'

// ── Load ───────────────────────────────────────────────────────────────────

async function loadAll() {
  loadingStatus.value = true
  loadingHistory.value = true
  error.value = ''
  try {
    const [s, h] = await Promise.all([
      api.getWorkspaceStatus(),
      api.getImportHistory(),
    ])
    status.value = s
    importHistory.value = h
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load workspace data'
  } finally {
    loadingStatus.value = false
    loadingHistory.value = false
  }
}

onMounted(loadAll)

// ── Computed ───────────────────────────────────────────────────────────────

const totalRecords = computed(() => {
  if (!status.value) return 0
  return (
    status.value.total_companies +
    status.value.total_prospects +
    status.value.total_signals +
    status.value.total_opportunities +
    status.value.total_deal_packets +
    status.value.total_outreach_drafts +
    status.value.total_recommendations
  )
})

const sourceBreakdownEntries = computed(() => {
  if (!status.value?.source_breakdown) return []
  const order = ['demo', 'imported', 'manual', 'generated', 'legacy']
  const colors: Record<string, string> = {
    demo: 'bg-violet-100 text-violet-700',
    imported: 'bg-blue-100 text-blue-700',
    manual: 'bg-emerald-100 text-emerald-700',
    generated: 'bg-amber-100 text-amber-700',
    legacy: 'bg-gray-100 text-gray-600',
  }
  const bd = status.value.source_breakdown
  const keys = [...new Set([...order, ...Object.keys(bd)])].filter(k => bd[k] > 0)
  return keys.map(k => ({ key: k, count: bd[k], color: colors[k] ?? 'bg-gray-100 text-gray-600' }))
})

const hasImportedData = computed(() => (status.value?.source_breakdown?.imported ?? 0) > 0)
const hasDemoData = computed(() => (status.value?.source_breakdown?.demo ?? 0) > 0)

// ── Restore preview ────────────────────────────────────────────────────────

function onRestoreFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  restoreFile.value = target.files?.[0] ?? null
  restorePreviewResult.value = null
  restoreResult.value = null
  parsedBackup.value = null
  restoreError.value = ''
  restoreConfirmText.value = ''
}

async function runRestorePreview() {
  if (!restoreFile.value) return
  restoringPreview.value = true
  restoreError.value = ''
  restorePreviewResult.value = null
  restoreResult.value = null
  try {
    const text = await restoreFile.value.text()
    const parsed = JSON.parse(text)
    parsedBackup.value = parsed
    restorePreviewResult.value = await api.restorePreview(parsed)
  } catch (e: unknown) {
    restoreError.value = e instanceof Error ? e.message : 'Failed to preview restore file'
  } finally {
    restoringPreview.value = false
  }
}

async function runRestore() {
  if (!parsedBackup.value || restoreConfirmText.value !== RESTORE_CONFIRM) return
  restoring.value = true
  restoreError.value = ''
  restoreResult.value = null
  try {
    restoreResult.value = await api.restoreWorkspace(parsedBackup.value, restoreConfirmText.value, false)
    restoreConfirmText.value = ''
    await loadAll()
  } catch (e: unknown) {
    restoreError.value = e instanceof Error ? e.message : 'Failed to restore workspace'
  } finally {
    restoring.value = false
  }
}

// ── Clear all ──────────────────────────────────────────────────────────────

async function clearAll() {
  if (clearConfirmText.value !== CLEAR_CONFIRM) return
  clearing.value = true
  clearError.value = ''
  clearResult.value = null
  try {
    clearResult.value = await api.clearAllWorkspace(clearConfirmText.value)
    clearConfirmText.value = ''
    await loadAll()
  } catch (e: unknown) {
    clearError.value = e instanceof Error ? e.message : 'Failed to clear workspace'
  } finally {
    clearing.value = false
  }
}

// ── Clear demo ─────────────────────────────────────────────────────────────

async function clearDemo() {
  if (clearDemoConfirmText.value !== CLEAR_DEMO_CONFIRM) return
  clearingDemo.value = true
  clearDemoError.value = ''
  clearDemoResult.value = null
  try {
    clearDemoResult.value = await api.clearDemoData(clearDemoConfirmText.value)
    clearDemoConfirmText.value = ''
    await loadAll()
  } catch (e: unknown) {
    clearDemoError.value = e instanceof Error ? e.message : 'Failed to clear demo data'
  } finally {
    clearingDemo.value = false
  }
}

// ── Clear imported ─────────────────────────────────────────────────────────

async function clearImported() {
  if (clearImportedConfirmText.value !== CLEAR_IMPORTED_CONFIRM) return
  clearingImported.value = true
  clearImportedError.value = ''
  clearImportedResult.value = null
  try {
    clearImportedResult.value = await api.clearImportedData(clearImportedConfirmText.value)
    clearImportedConfirmText.value = ''
    await loadAll()
  } catch (e: unknown) {
    clearImportedError.value = e instanceof Error ? e.message : 'Failed to clear imported data'
  } finally {
    clearingImported.value = false
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}

function importTypeBadge(type: string): string {
  const map: Record<string, string> = {
    companies: 'bg-blue-100 text-blue-700',
    prospects: 'bg-violet-100 text-violet-700',
    signals: 'bg-amber-100 text-amber-700',
  }
  return map[type] ?? 'bg-gray-100 text-gray-600'
}
</script>

<template>
  <div class="flex flex-col h-full overflow-hidden">
    <!-- Header -->
    <header class="flex-shrink-0 border-b border-gray-200 bg-white px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-lg font-semibold text-gray-900">Workspace</h1>
          <p class="text-sm text-gray-500 mt-0.5">
            DobryBot stores and manages this workspace locally. Nothing is sent to external services.
          </p>
        </div>
        <button
          @click="loadAll"
          class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1.5"
        >
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Refresh
        </button>
      </div>
    </header>

    <div class="flex-1 overflow-y-auto px-6 py-6 space-y-6">
      <!-- Error -->
      <div v-if="error" class="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
        {{ error }}
      </div>

      <!-- ── Workspace Status ─────────────────────────────────────────────── -->
      <section>
        <h2 class="text-sm font-semibold text-gray-700 mb-3">Workspace Status</h2>

        <div v-if="loadingStatus" class="rounded-xl border border-gray-200 bg-white p-6 text-center text-sm text-gray-400">
          Loading…
        </div>

        <div v-else-if="status" class="rounded-xl border border-gray-200 bg-white divide-y divide-gray-100">
          <!-- Counts grid -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-px bg-gray-100">
            <div class="bg-white px-5 py-4 text-center">
              <div class="text-2xl font-bold text-gray-900">{{ status.total_companies }}</div>
              <div class="text-xs text-gray-500 mt-0.5">Companies</div>
            </div>
            <div class="bg-white px-5 py-4 text-center">
              <div class="text-2xl font-bold text-gray-900">{{ status.total_prospects }}</div>
              <div class="text-xs text-gray-500 mt-0.5">Prospects</div>
            </div>
            <div class="bg-white px-5 py-4 text-center">
              <div class="text-2xl font-bold text-gray-900">{{ status.total_signals }}</div>
              <div class="text-xs text-gray-500 mt-0.5">Signals</div>
            </div>
            <div class="bg-white px-5 py-4 text-center">
              <div class="text-2xl font-bold text-gray-900">{{ status.total_opportunities }}</div>
              <div class="text-xs text-gray-500 mt-0.5">Opportunities</div>
            </div>
            <div class="bg-white px-5 py-4 text-center">
              <div class="text-2xl font-bold text-gray-900">{{ status.total_deal_packets }}</div>
              <div class="text-xs text-gray-500 mt-0.5">Deal Packets</div>
            </div>
            <div class="bg-white px-5 py-4 text-center">
              <div class="text-2xl font-bold text-gray-900">{{ status.total_outreach_drafts }}</div>
              <div class="text-xs text-gray-500 mt-0.5">Outreach Drafts</div>
            </div>
            <div class="bg-white px-5 py-4 text-center">
              <div class="text-2xl font-bold text-gray-900">{{ status.total_recommendations }}</div>
              <div class="text-xs text-gray-500 mt-0.5">Recommendations</div>
            </div>
            <div class="bg-white px-5 py-4 text-center">
              <div class="text-2xl font-bold" :class="status.icp_configured ? 'text-emerald-600' : 'text-amber-500'">
                {{ status.icp_configured ? 'Yes' : 'No' }}
              </div>
              <div class="text-xs text-gray-500 mt-0.5">ICP Configured</div>
            </div>
          </div>
          <!-- Dates + safety notice -->
          <div class="px-5 py-3 text-xs text-gray-500 space-y-1">
            <div>Last import: <span class="font-medium text-gray-700">{{ fmtDate(status.last_import_date) }}</span></div>
            <div>Last activity: <span class="font-medium text-gray-700">{{ fmtDate(status.last_activity_date) }}</span></div>
            <div class="text-emerald-600">{{ status.safety_notice }}</div>
          </div>
        </div>
      </section>

      <!-- ── Source Breakdown ────────────────────────────────────────────── -->
      <section v-if="status">
        <h2 class="text-sm font-semibold text-gray-700 mb-3">Data Sources</h2>
        <div class="rounded-xl border border-gray-200 bg-white px-5 py-4">
          <div v-if="sourceBreakdownEntries.length === 0" class="text-sm text-gray-400">No data in workspace yet.</div>
          <div v-else>
            <div class="flex flex-wrap gap-2 mb-3">
              <span
                v-for="entry in sourceBreakdownEntries"
                :key="entry.key"
                class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold capitalize"
                :class="entry.color"
              >
                {{ entry.key }}
                <span class="font-bold">{{ entry.count }}</span>
              </span>
            </div>
            <div class="text-xs text-gray-500 space-y-0.5">
              <div><span class="font-medium">demo</span> — seeded demo data</div>
              <div><span class="font-medium">imported</span> — brought in via CSV import</div>
              <div><span class="font-medium">manual</span> — created manually in the UI</div>
              <div><span class="font-medium">generated</span> — system-created (recommendations, deal packets)</div>
              <div v-if="(status.source_breakdown?.legacy ?? 0) > 0"><span class="font-medium">legacy</span> — existing records without source tracking</div>
            </div>
          </div>
        </div>
      </section>

      <!-- ── Data Health ──────────────────────────────────────────────────── -->
      <section v-if="status">
        <h2 class="text-sm font-semibold text-gray-700 mb-3">Data Health</h2>
        <div class="rounded-xl border border-gray-200 bg-white px-5 py-4">
          <div v-if="status.data_health_warnings.length === 0" class="flex items-center gap-2 text-sm text-emerald-700">
            <svg class="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            No data health issues found
          </div>
          <ul v-else class="space-y-1.5">
            <li
              v-for="w in status.data_health_warnings"
              :key="w"
              class="flex items-start gap-2 text-sm text-amber-700"
            >
              <svg class="h-4 w-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
              {{ w }}
            </li>
          </ul>
        </div>
      </section>

      <!-- ── Import History ───────────────────────────────────────────────── -->
      <section>
        <h2 class="text-sm font-semibold text-gray-700 mb-3">Import History</h2>
        <div class="rounded-xl border border-gray-200 bg-white overflow-hidden">
          <div v-if="loadingHistory" class="px-5 py-4 text-sm text-gray-400">Loading…</div>
          <div v-else-if="importHistory.length === 0" class="px-5 py-4 text-sm text-gray-400">
            No committed imports yet. Use <NuxtLink to="/import" class="text-blue-600 hover:underline">Import Data</NuxtLink> to bring in companies, prospects, or signals.
          </div>
          <table v-else class="w-full text-sm">
            <thead class="bg-gray-50 border-b border-gray-100">
              <tr>
                <th class="text-left px-4 py-2.5 text-xs font-semibold text-gray-500">Type</th>
                <th class="text-left px-4 py-2.5 text-xs font-semibold text-gray-500">File</th>
                <th class="text-right px-4 py-2.5 text-xs font-semibold text-gray-500">Imported</th>
                <th class="text-right px-4 py-2.5 text-xs font-semibold text-gray-500">Skipped</th>
                <th class="text-right px-4 py-2.5 text-xs font-semibold text-gray-500">Dups</th>
                <th class="text-left px-4 py-2.5 text-xs font-semibold text-gray-500">Committed</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="entry in importHistory" :key="entry.id" class="hover:bg-gray-50">
                <td class="px-4 py-2.5">
                  <span class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium" :class="importTypeBadge(entry.import_type)">
                    {{ entry.import_type }}
                  </span>
                </td>
                <td class="px-4 py-2.5 text-gray-700 truncate max-w-[180px]">{{ entry.filename || '—' }}</td>
                <td class="px-4 py-2.5 text-right font-medium text-emerald-700">{{ entry.imported_count }}</td>
                <td class="px-4 py-2.5 text-right text-gray-500">{{ entry.skipped_count }}</td>
                <td class="px-4 py-2.5 text-right text-gray-500">{{ entry.duplicate_count }}</td>
                <td class="px-4 py-2.5 text-gray-500 text-xs">{{ fmtDate(entry.committed_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ── Export Data ──────────────────────────────────────────────────── -->
      <section>
        <h2 class="text-sm font-semibold text-gray-700 mb-3">Export Data</h2>
        <div class="rounded-xl border border-gray-200 bg-white px-5 py-4">
          <p class="text-xs text-gray-500 mb-4">
            All exports are generated locally. No external APIs are called. No secrets included.
          </p>
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <a
              :href="api.exportUrl('companies')"
              download="dobrybot_companies.csv"
              class="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300"
            >
              <svg class="h-4 w-4 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Companies CSV
            </a>
            <a
              :href="api.exportUrl('prospects')"
              download="dobrybot_prospects.csv"
              class="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300"
            >
              <svg class="h-4 w-4 text-violet-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Prospects CSV
            </a>
            <a
              :href="api.exportUrl('signals')"
              download="dobrybot_signals.csv"
              class="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300"
            >
              <svg class="h-4 w-4 text-amber-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Signals CSV
            </a>
            <a
              :href="api.exportUrl('opportunities')"
              download="dobrybot_opportunities.csv"
              class="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300"
            >
              <svg class="h-4 w-4 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Opportunities CSV
            </a>
            <a
              :href="api.exportUrl('workspace')"
              download="dobrybot_workspace.json"
              class="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300"
            >
              <svg class="h-4 w-4 text-gray-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Workspace JSON
            </a>
          </div>
        </div>
      </section>

      <!-- ── Backup Workspace ─────────────────────────────────────────────── -->
      <section>
        <h2 class="text-sm font-semibold text-gray-700 mb-3">Backup Workspace</h2>
        <div class="rounded-xl border border-gray-200 bg-white px-5 py-4">
          <p class="text-sm text-gray-600 mb-3">
            Download a full local backup including all BD data, ICP config, activity log, and import history.
            No secrets or credentials are included.
          </p>
          <a
            :href="api.backupWorkspace()"
            download="dobrybot_workspace_backup.json"
            class="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-semibold text-white hover:bg-gray-800"
          >
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Download Full Backup
          </a>
        </div>
      </section>

      <!-- ── Restore Workspace ───────────────────────────────────────────── -->
      <section>
        <h2 class="text-sm font-semibold text-gray-700 mb-3">Restore Workspace</h2>
        <div class="rounded-xl border border-gray-200 bg-white px-5 py-4 space-y-4">
          <p class="text-sm text-gray-600">
            Upload a backup file to preview and restore. Use Preview first. Restoring replaces all current data.
            Local only — no external services contacted.
          </p>

          <div class="space-y-2">
            <input
              type="file"
              accept=".json"
              class="block text-sm text-gray-600 file:mr-3 file:rounded-lg file:border file:border-gray-200 file:bg-gray-50 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-gray-700 hover:file:bg-gray-100"
              @change="onRestoreFileChange"
            />
            <button
              v-if="restoreFile"
              :disabled="restoringPreview"
              @click="runRestorePreview"
              class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {{ restoringPreview ? 'Previewing…' : 'Preview Backup' }}
            </button>
          </div>

          <div v-if="restoreError" class="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
            {{ restoreError }}
          </div>

          <!-- Preview result -->
          <div v-if="restorePreviewResult" class="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 space-y-3">
            <div class="text-sm font-semibold text-gray-700">Preview</div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div class="bg-white rounded border border-gray-200 px-2.5 py-2 text-center">
                <div class="font-bold text-gray-900">{{ restorePreviewResult.companies_count }}</div>
                <div class="text-gray-500">Companies</div>
              </div>
              <div class="bg-white rounded border border-gray-200 px-2.5 py-2 text-center">
                <div class="font-bold text-gray-900">{{ restorePreviewResult.prospects_count }}</div>
                <div class="text-gray-500">Prospects</div>
              </div>
              <div class="bg-white rounded border border-gray-200 px-2.5 py-2 text-center">
                <div class="font-bold text-gray-900">{{ restorePreviewResult.signals_count }}</div>
                <div class="text-gray-500">Signals</div>
              </div>
              <div class="bg-white rounded border border-gray-200 px-2.5 py-2 text-center">
                <div class="font-bold text-gray-900">{{ restorePreviewResult.opportunities_count }}</div>
                <div class="text-gray-500">Opportunities</div>
              </div>
            </div>
            <div v-if="restorePreviewResult.warnings.length" class="space-y-1">
              <div v-for="w in restorePreviewResult.warnings" :key="w" class="text-xs text-amber-700">⚠ {{ w }}</div>
            </div>
            <div class="text-xs text-emerald-700">{{ restorePreviewResult.safety_notice }}</div>

            <!-- Confirm restore -->
            <div v-if="restorePreviewResult.valid" class="border-t border-gray-200 pt-3 space-y-2">
              <div v-if="restoreResult" class="rounded bg-emerald-50 border border-emerald-200 px-3 py-2 text-sm text-emerald-700">
                Workspace restored. {{ restoreResult.companies_restored }} companies, {{ restoreResult.prospects_restored }} prospects, {{ restoreResult.signals_restored }} signals.
              </div>
              <label class="block text-xs font-semibold text-gray-700">
                Type <code class="bg-gray-100 px-1 rounded font-mono">RESTORE DOBRYBOT WORKSPACE</code> to confirm:
              </label>
              <input
                v-model="restoreConfirmText"
                type="text"
                placeholder="RESTORE DOBRYBOT WORKSPACE"
                class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-mono placeholder:text-gray-300 focus:border-blue-400 focus:outline-none"
              />
              <button
                :disabled="restoreConfirmText !== RESTORE_CONFIRM || restoring"
                @click="runRestore"
                class="rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {{ restoring ? 'Restoring…' : 'Restore Workspace' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- ── Safe Reset Zone ──────────────────────────────────────────────── -->
      <section>
        <h2 class="text-sm font-semibold text-red-600 mb-3">Safe Reset Zone</h2>
        <div class="rounded-xl border border-red-200 bg-red-50 px-5 py-5 space-y-6">
          <p class="text-sm text-red-700 font-medium">
            Clearing data is irreversible. Export or backup first.
          </p>

          <!-- Clear demo -->
          <div class="bg-white rounded-lg border border-red-100 px-4 py-4 space-y-2">
            <div class="text-sm font-semibold text-gray-800">Clear Demo Data</div>
            <p class="text-xs text-gray-500">Removes all records with <code class="bg-gray-100 px-1 rounded">source=demo</code>. Preserves imported, manual, and generated records.</p>

            <div v-if="clearDemoResult" class="rounded bg-emerald-50 border border-emerald-200 px-3 py-2 text-sm text-emerald-700">
              {{ clearDemoResult.records_removed }} demo records removed.
            </div>
            <div v-if="clearDemoError" class="rounded bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{{ clearDemoError }}</div>

            <div v-if="!hasDemoData && !clearDemoResult" class="text-xs text-gray-400">No demo data detected in workspace.</div>
            <template v-else>
              <label class="block text-xs font-semibold text-red-700">
                Type <code class="bg-red-100 px-1 rounded font-mono">CLEAR DEMO DATA</code> to confirm:
              </label>
              <input
                v-model="clearDemoConfirmText"
                type="text"
                placeholder="CLEAR DEMO DATA"
                class="w-full rounded-lg border border-red-200 bg-white px-3 py-2 text-sm font-mono placeholder:text-red-200 focus:border-red-400 focus:outline-none"
              />
              <button
                :disabled="clearDemoConfirmText !== CLEAR_DEMO_CONFIRM || clearingDemo"
                @click="clearDemo"
                class="rounded-lg bg-red-500 px-4 py-2 text-sm font-semibold text-white hover:bg-red-600 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {{ clearingDemo ? 'Clearing…' : 'Clear Demo Data' }}
              </button>
            </template>
          </div>

          <!-- Clear imported -->
          <div class="bg-white rounded-lg border border-red-100 px-4 py-4 space-y-2">
            <div class="text-sm font-semibold text-gray-800">Clear Imported Data</div>
            <p class="text-xs text-gray-500">Removes all records with <code class="bg-gray-100 px-1 rounded">source=imported</code>. Preserves demo, manual, and generated records.</p>

            <div v-if="clearImportedResult" class="rounded bg-emerald-50 border border-emerald-200 px-3 py-2 text-sm text-emerald-700">
              {{ clearImportedResult.records_removed }} imported records removed.
            </div>
            <div v-if="clearImportedError" class="rounded bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{{ clearImportedError }}</div>

            <div v-if="!hasImportedData && !clearImportedResult" class="text-xs text-gray-400">No imported data detected in workspace.</div>
            <template v-else>
              <label class="block text-xs font-semibold text-red-700">
                Type <code class="bg-red-100 px-1 rounded font-mono">CLEAR IMPORTED DATA</code> to confirm:
              </label>
              <input
                v-model="clearImportedConfirmText"
                type="text"
                placeholder="CLEAR IMPORTED DATA"
                class="w-full rounded-lg border border-red-200 bg-white px-3 py-2 text-sm font-mono placeholder:text-red-200 focus:border-red-400 focus:outline-none"
              />
              <button
                :disabled="clearImportedConfirmText !== CLEAR_IMPORTED_CONFIRM || clearingImported"
                @click="clearImported"
                class="rounded-lg bg-red-500 px-4 py-2 text-sm font-semibold text-white hover:bg-red-600 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {{ clearingImported ? 'Clearing…' : 'Clear Imported Data' }}
              </button>
            </template>
          </div>

          <!-- Clear all -->
          <div class="bg-white rounded-lg border border-red-200 px-4 py-4 space-y-2">
            <div class="text-sm font-semibold text-red-700">Clear All Workspace Data</div>
            <p class="text-xs text-gray-500">Removes everything — demo, imported, manual, and generated. Activity log is preserved. Irreversible.</p>

            <div v-if="clearResult" class="rounded bg-emerald-50 border border-emerald-200 px-3 py-2 text-sm text-emerald-700">
              Workspace cleared. {{ clearResult.records_removed }} records removed.
            </div>
            <div v-if="clearError" class="rounded bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">{{ clearError }}</div>

            <label class="block text-xs font-semibold text-red-700">
              Type <code class="bg-red-100 px-1 rounded font-mono">CLEAR DOBRYBOT WORKSPACE</code> to confirm:
            </label>
            <input
              v-model="clearConfirmText"
              type="text"
              placeholder="CLEAR DOBRYBOT WORKSPACE"
              class="w-full rounded-lg border border-red-200 bg-white px-3 py-2 text-sm font-mono placeholder:text-red-200 focus:border-red-400 focus:outline-none"
            />
            <button
              :disabled="clearConfirmText !== CLEAR_CONFIRM || clearing"
              @click="clearAll"
              class="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {{ clearing ? 'Clearing…' : 'Clear All Workspace Data' }}
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
