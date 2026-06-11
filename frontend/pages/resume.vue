<script setup lang="ts">
import type { ResumeInfo } from '~/types'

const api = useApi()

const resumeInfo = ref<ResumeInfo | null>(null)
const loadingInfo = ref(true)
const loadError = ref(false)

async function loadResumeInfo() {
  loadingInfo.value = true
  loadError.value = false
  try {
    resumeInfo.value = await api.getResumeInfo()
  } catch (err: unknown) {
    const status = (err as { status?: number })?.status
    if (status === 404) {
      resumeInfo.value = null
    } else {
      loadError.value = true
    }
  } finally {
    loadingInfo.value = false
  }
}

onMounted(loadResumeInfo)

// Upload state
const selectedFile = ref<File | null>(null)
const dragOver = ref(false)
const uploading = ref(false)
const uploadResult = ref<'idle' | 'success' | 'error'>('idle')
const uploadError = ref('')

const ACCEPTED = ['.pdf', '.docx']
const MAX_MB = 5

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function onFileInput(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.[0]) selectFile(input.files[0])
}

function onDrop(event: DragEvent) {
  dragOver.value = false
  event.preventDefault()
  const file = event.dataTransfer?.files?.[0]
  if (file) selectFile(file)
}

function selectFile(file: File) {
  uploadResult.value = 'idle'
  uploadError.value = ''
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  if (!ACCEPTED.includes(ext)) {
    uploadError.value = `Only PDF and DOCX are accepted. Got: ${ext}`
    selectedFile.value = null
    return
  }
  if (file.size > MAX_MB * 1024 * 1024) {
    uploadError.value = `File too large. Maximum is ${MAX_MB} MB. Got: ${formatBytes(file.size)}`
    selectedFile.value = null
    return
  }
  selectedFile.value = file
}

async function upload() {
  if (!selectedFile.value) return
  uploading.value = true
  uploadResult.value = 'idle'
  uploadError.value = ''
  try {
    await api.uploadResume(selectedFile.value)
    uploadResult.value = 'success'
    selectedFile.value = null
    await loadResumeInfo()
  } catch {
    uploadResult.value = 'error'
    uploadError.value = 'Upload failed — is the backend running?'
  } finally {
    uploading.value = false
  }
}

function clearSelection() {
  selectedFile.value = null
  uploadResult.value = 'idle'
  uploadError.value = ''
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader title="Resume / CV" subtitle="Manage your CV for opportunity scoring context" />

    <div class="flex-1 p-6 space-y-6 max-w-2xl w-full mx-auto">
      <!-- Safety notice -->
      <div class="flex items-start gap-3 rounded-xl bg-emerald-50 border border-emerald-100 px-4 py-3">
        <svg class="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
        <span class="text-sm text-emerald-700">
          Your CV is stored locally in this development build and is <strong>not sent anywhere</strong>. It is not parsed by AI in this phase.
        </span>
      </div>

      <!-- Current CV status -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Current CV</h3>
        </div>
        <div class="px-5 py-4">
          <LoadingSpinner v-if="loadingInfo" label="Loading…" />
          <div v-else-if="loadError" class="text-sm text-red-500">
            Could not load CV info — is the backend running?
          </div>
          <div v-else-if="resumeInfo" class="flex items-center gap-4">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 flex-shrink-0">
              <svg class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-gray-900 truncate">{{ resumeInfo.original_filename }}</p>
              <p class="text-xs text-gray-400 mt-0.5">Uploaded {{ formatDate(resumeInfo.uploaded_at) }}</p>
            </div>
            <span class="flex-shrink-0 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">Active</span>
          </div>
          <div v-else class="flex items-center gap-3 text-sm text-gray-400">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            No CV uploaded yet
          </div>
        </div>
      </AppCard>

      <!-- Upload card -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Upload CV</h3>
          <p class="text-xs text-gray-500 mt-0.5">PDF or DOCX · Max 5 MB · Replaces previous upload</p>
        </div>
        <div class="px-5 py-5 space-y-4">
          <!-- Drop zone -->
          <div
            class="relative rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors cursor-pointer"
            :class="dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'"
            @dragover.prevent="dragOver = true"
            @dragleave="dragOver = false"
            @drop="onDrop"
            @click="($refs.fileInput as HTMLInputElement).click()"
          >
            <input
              ref="fileInput"
              type="file"
              accept=".pdf,.docx"
              class="sr-only"
              @change="onFileInput"
            />
            <svg class="mx-auto h-8 w-8 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <p class="text-sm font-medium text-gray-700">Drop your CV here, or click to browse</p>
            <p class="text-xs text-gray-400 mt-1">PDF or DOCX · Max 5 MB</p>
          </div>

          <!-- Selected file -->
          <div v-if="selectedFile" class="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
            <svg class="h-5 w-5 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 truncate">{{ selectedFile.name }}</p>
              <p class="text-xs text-gray-400">{{ formatBytes(selectedFile.size) }}</p>
            </div>
            <button
              class="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
              @click.stop="clearSelection"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Validation error -->
          <div v-if="uploadError" class="flex items-center gap-2 rounded-lg bg-red-50 border border-red-100 px-3 py-2.5">
            <svg class="h-4 w-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span class="text-sm text-red-700">{{ uploadError }}</span>
          </div>

          <!-- Success -->
          <div v-if="uploadResult === 'success'" class="flex items-center gap-2 rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-2.5">
            <svg class="h-4 w-4 text-emerald-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span class="text-sm text-emerald-700">CV uploaded and stored locally. Not sent anywhere.</span>
          </div>

          <!-- Upload button -->
          <div class="flex justify-end">
            <button
              :disabled="!selectedFile || uploading"
              class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
              @click="upload"
            >
              <svg v-if="uploading" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
              <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
              {{ uploading ? 'Uploading…' : 'Upload CV' }}
            </button>
          </div>
        </div>
      </AppCard>

      <!-- What happens to your file -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">What happens to your file</h3>
        </div>
        <div class="px-5 py-4 space-y-2.5">
          <div class="flex items-start gap-2.5 text-sm text-gray-600">
            <svg class="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            Stored in <code class="text-xs bg-gray-100 px-1.5 py-0.5 rounded font-mono">uploads/resumes/</code> on your local machine only
          </div>
          <div class="flex items-start gap-2.5 text-sm text-gray-600">
            <svg class="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            Excluded from git — the <code class="text-xs bg-gray-100 px-1.5 py-0.5 rounded font-mono">uploads/</code> directory is in <code class="text-xs bg-gray-100 px-1.5 py-0.5 rounded font-mono">.gitignore</code>
          </div>
          <div class="flex items-start gap-2.5 text-sm text-gray-600">
            <svg class="h-4 w-4 text-gray-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Not parsed by AI in this phase (Phase 4 roadmap)
          </div>
          <div class="flex items-start gap-2.5 text-sm text-gray-600">
            <svg class="h-4 w-4 text-gray-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Not sent to LinkedIn, email, or any external service
          </div>
        </div>
      </AppCard>
    </div>
  </div>
</template>
