<script setup lang="ts">
import type {
  ResumeProfile,
  ResumeProfileUpdate,
  ResumeExperienceItem,
  ResumeEducationItem,
  ResumeProjectItem,
  ResumeInfo,
} from '~/types'

const api = useApi()

// ── Load state ────────────────────────────────────────────────────────────────
const loading = ref(true)
const loadError = ref(false)
const saving = ref(false)
const saveResult = ref<'idle' | 'success' | 'error'>('idle')
const generating = ref(false)
const previewContent = ref('')
const copied = ref(false)

// ── CV upload state ────────────────────────────────────────────────────────────
const resumeInfo = ref<ResumeInfo | null>(null)
const selectedFile = ref<File | null>(null)
const dragOver = ref(false)
const uploading = ref(false)
const uploadResult = ref<'idle' | 'success' | 'error'>('idle')
const uploadError = ref('')

// ── Form state ────────────────────────────────────────────────────────────────
const form = reactive<Omit<ResumeProfile, 'updated_at'>>({
  headline: '',
  professional_summary: '',
  target_role: '',
  location: '',
  email: '',
  phone: '',
  linkedin_url: '',
  portfolio_url: '',
  github_url: '',
  skills: [],
  experience_items: [],
  project_items: [],
  education_items: [],
  certifications: [],
  languages: [],
  achievements: [],
})

const skillsInput = ref('')
const certsText = ref('')
const langsText = ref('')
const achievementsText = ref('')

// ── Completion score ──────────────────────────────────────────────────────────
const completionScore = computed(() => {
  let pts = 0
  if (form.headline) pts += 15
  if (form.professional_summary) pts += 15
  if (form.email) pts += 10
  if (form.skills.length > 0) pts += 15
  if (form.experience_items.length > 0) pts += 20
  if (form.education_items.length > 0) pts += 10
  if (form.linkedin_url) pts += 10
  if (resumeInfo.value) pts += 5
  return Math.min(pts, 100)
})

const completionLabel = computed(() => {
  const s = completionScore.value
  if (s >= 80) return 'Excellent'
  if (s >= 60) return 'Good'
  if (s >= 40) return 'Fair'
  return 'Getting started'
})

const completionBarColor = computed(() => {
  const s = completionScore.value
  if (s >= 80) return 'bg-emerald-500'
  if (s >= 60) return 'bg-blue-500'
  if (s >= 40) return 'bg-amber-500'
  return 'bg-gray-300'
})

const missingFields = computed(() => {
  const m: string[] = []
  if (!form.headline) m.push('Headline')
  if (!form.professional_summary) m.push('Summary')
  if (!form.email) m.push('Email')
  if (form.skills.length === 0) m.push('Skills')
  if (form.experience_items.length === 0) m.push('Experience')
  if (form.education_items.length === 0) m.push('Education')
  if (!form.linkedin_url) m.push('LinkedIn')
  return m
})

// ── Load ──────────────────────────────────────────────────────────────────────
async function loadAll() {
  loading.value = true
  loadError.value = false
  try {
    const [profileResult, previewResult, infoResult] = await Promise.allSettled([
      api.getResumeProfile(),
      api.getResumePreview(),
      api.getResumeInfo(),
    ])

    if (profileResult.status === 'fulfilled') {
      const p = profileResult.value
      form.headline = p.headline
      form.professional_summary = p.professional_summary
      form.target_role = p.target_role
      form.location = p.location
      form.email = p.email
      form.phone = p.phone
      form.linkedin_url = p.linkedin_url
      form.portfolio_url = p.portfolio_url
      form.github_url = p.github_url
      form.skills = [...p.skills]
      form.experience_items = p.experience_items.map(e => ({
        ...e, bullets: [...e.bullets],
      }))
      form.project_items = p.project_items.map(pr => ({
        ...pr, technologies: [...pr.technologies], bullets: [...pr.bullets],
      }))
      form.education_items = p.education_items.map(e => ({ ...e }))
      form.certifications = [...p.certifications]
      form.languages = [...p.languages]
      form.achievements = [...p.achievements]
      certsText.value = p.certifications.join('\n')
      langsText.value = p.languages.join('\n')
      achievementsText.value = p.achievements.join('\n')
    } else {
      loadError.value = true
    }

    if (previewResult.status === 'fulfilled' && previewResult.value.has_content) {
      previewContent.value = previewResult.value.preview
    }
    if (infoResult.status === 'fulfilled') {
      resumeInfo.value = infoResult.value
    }
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)

// ── Skills ────────────────────────────────────────────────────────────────────
function addSkillsFromInput() {
  const items = skillsInput.value.split(',').map(s => s.trim()).filter(Boolean)
  form.skills = [...new Set([...form.skills, ...items])]
  skillsInput.value = ''
}

function onSkillsKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault()
    addSkillsFromInput()
  }
}

function removeSkill(idx: number) {
  form.skills.splice(idx, 1)
}

// ── Experience ────────────────────────────────────────────────────────────────
function addExperience() {
  form.experience_items.push({
    company: '',
    title: '',
    location: '',
    start_date: '',
    end_date: '',
    currently_working: false,
    bullets: [],
  })
}

function removeExperience(idx: number) {
  form.experience_items.splice(idx, 1)
}

function getExpBullets(exp: ResumeExperienceItem): string {
  return exp.bullets.join('\n')
}

function setExpBullets(exp: ResumeExperienceItem, text: string) {
  exp.bullets = text.split('\n').map(s => s.trim()).filter(Boolean)
}

// ── Education ─────────────────────────────────────────────────────────────────
function addEducation() {
  form.education_items.push({ institution: '', degree: '', dates: '' })
}

function removeEducation(idx: number) {
  form.education_items.splice(idx, 1)
}

// ── Projects ──────────────────────────────────────────────────────────────────
function addProject() {
  form.project_items.push({ name: '', description: '', technologies: [], bullets: [] })
}

function removeProject(idx: number) {
  form.project_items.splice(idx, 1)
}

function getProjBullets(proj: ResumeProjectItem): string {
  return proj.bullets.join('\n')
}

function setProjBullets(proj: ResumeProjectItem, text: string) {
  proj.bullets = text.split('\n').map(s => s.trim()).filter(Boolean)
}

function getProjTech(proj: ResumeProjectItem): string {
  return proj.technologies.join(', ')
}

function setProjTech(proj: ResumeProjectItem, text: string) {
  proj.technologies = text.split(',').map(s => s.trim()).filter(Boolean)
}

// ── Save ──────────────────────────────────────────────────────────────────────
async function save() {
  saving.value = true
  saveResult.value = 'idle'
  try {
    // Flush textarea-based fields before saving
    form.certifications = certsText.value.split('\n').map(s => s.trim()).filter(Boolean)
    form.languages = langsText.value.split('\n').map(s => s.trim()).filter(Boolean)
    form.achievements = achievementsText.value.split('\n').map(s => s.trim()).filter(Boolean)

    const updates: ResumeProfileUpdate = {
      headline: form.headline,
      professional_summary: form.professional_summary,
      target_role: form.target_role,
      location: form.location,
      email: form.email,
      phone: form.phone,
      linkedin_url: form.linkedin_url,
      portfolio_url: form.portfolio_url,
      github_url: form.github_url,
      skills: form.skills,
      experience_items: form.experience_items,
      project_items: form.project_items,
      education_items: form.education_items,
      certifications: form.certifications,
      languages: form.languages,
      achievements: form.achievements,
    }
    await api.updateResumeProfile(updates)
    saveResult.value = 'success'
    setTimeout(() => { saveResult.value = 'idle' }, 3000)
  } catch {
    saveResult.value = 'error'
  } finally {
    saving.value = false
  }
}

// ── Regenerate ────────────────────────────────────────────────────────────────
async function regenerate() {
  generating.value = true
  try {
    await save()
    const result = await api.generateResumeDraft()
    if (result.generated) {
      previewContent.value = result.preview
    }
  } catch {
    // save already sets saveResult
  } finally {
    generating.value = false
  }
}

// ── Copy ──────────────────────────────────────────────────────────────────────
async function copyDraft() {
  if (!previewContent.value) return
  try {
    await navigator.clipboard.writeText(previewContent.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2500)
  } catch {
    // clipboard not available in some dev environments
  }
}

// ── CV Upload ─────────────────────────────────────────────────────────────────
const ACCEPTED_EXT = ['.pdf', '.docx']
const MAX_MB = 5

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function onFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) selectFile(input.files[0])
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  e.preventDefault()
  const file = e.dataTransfer?.files?.[0]
  if (file) selectFile(file)
}

function selectFile(file: File) {
  uploadResult.value = 'idle'
  uploadError.value = ''
  const ext = '.' + file.name.split('.').pop()?.toLowerCase()
  if (!ACCEPTED_EXT.includes(ext)) {
    uploadError.value = `Only PDF and DOCX files are accepted.`
    selectedFile.value = null
    return
  }
  if (file.size > MAX_MB * 1024 * 1024) {
    uploadError.value = `File too large. Max ${MAX_MB} MB.`
    selectedFile.value = null
    return
  }
  selectedFile.value = file
}

async function uploadCV() {
  if (!selectedFile.value) return
  uploading.value = true
  uploadResult.value = 'idle'
  uploadError.value = ''
  try {
    await api.uploadResume(selectedFile.value)
    uploadResult.value = 'success'
    selectedFile.value = null
    resumeInfo.value = await api.getResumeInfo()
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
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader title="Resume Studio" subtitle="Build, organise, and preview your professional resume" />

    <!-- Loading / Error -->
    <div v-if="loading" class="flex-1 flex items-center justify-center p-8">
      <LoadingSpinner label="Loading Resume Studio…" />
    </div>

    <div v-else-if="loadError" class="flex-1 p-6 max-w-2xl mx-auto w-full">
      <AppCard>
        <ErrorState
          message="Could not reach the backend. Make sure uvicorn is running on port 8000."
          :show-retry="true"
          @retry="loadAll"
        />
      </AppCard>
    </div>

    <template v-else>
      <!-- Privacy notice -->
      <div class="px-6 pt-4">
        <div class="flex items-start gap-3 rounded-xl bg-emerald-50 border border-emerald-100 px-4 py-3 max-w-7xl mx-auto">
          <svg class="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
          <p class="text-sm text-emerald-700">
            All resume data is stored <strong>locally only</strong>. Nothing is sent to any external service, API, or AI in this phase.
          </p>
        </div>
      </div>

      <!-- Completion score bar -->
      <div class="px-6 pt-4">
        <div class="max-w-7xl mx-auto">
          <div class="flex items-center gap-4">
            <div class="flex-1">
              <div class="flex items-center justify-between mb-1.5">
                <span class="text-xs font-semibold text-gray-600">Profile completeness</span>
                <span class="text-xs font-semibold" :class="{
                  'text-emerald-600': completionScore >= 80,
                  'text-blue-600': completionScore >= 60 && completionScore < 80,
                  'text-amber-600': completionScore >= 40 && completionScore < 60,
                  'text-gray-400': completionScore < 40,
                }">{{ completionScore }}% · {{ completionLabel }}</span>
              </div>
              <div class="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="completionBarColor"
                  :style="{ width: `${completionScore}%` }"
                />
              </div>
            </div>
            <div v-if="missingFields.length > 0" class="flex items-center gap-1.5 flex-wrap">
              <span class="text-xs text-gray-400">Missing:</span>
              <span
                v-for="f in missingFields.slice(0, 4)"
                :key="f"
                class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500"
              >{{ f }}</span>
              <span v-if="missingFields.length > 4" class="text-xs text-gray-400">+{{ missingFields.length - 4 }} more</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Two-column layout -->
      <div class="flex-1 p-6 grid grid-cols-1 xl:grid-cols-2 gap-6 max-w-7xl mx-auto w-full items-start">

        <!-- ── LEFT: Form ──────────────────────────────────────────────────── -->
        <div class="space-y-5">

          <!-- CV Upload card -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h3 class="text-sm font-semibold text-gray-900">Source CV File</h3>
                <p class="text-xs text-gray-500 mt-0.5">PDF or DOCX · Max 5 MB · Stored locally, never sent</p>
              </div>
              <span v-if="resumeInfo" class="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700">Active</span>
              <span v-else class="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-400">None</span>
            </div>
            <div class="px-5 py-4 space-y-3">
              <!-- Current file info -->
              <div v-if="resumeInfo" class="flex items-center gap-3 rounded-lg bg-blue-50 border border-blue-100 px-3 py-2.5">
                <svg class="h-4 w-4 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-blue-900 truncate">{{ resumeInfo.original_filename }}</p>
                  <p class="text-xs text-blue-500">Uploaded {{ formatDate(resumeInfo.uploaded_at) }}</p>
                </div>
              </div>

              <!-- Drop zone -->
              <div
                class="relative rounded-xl border-2 border-dashed px-5 py-5 text-center transition-colors cursor-pointer"
                :class="dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'"
                @dragover.prevent="dragOver = true"
                @dragleave="dragOver = false"
                @drop="onDrop"
                @click="($refs.fileInput as HTMLInputElement).click()"
              >
                <input ref="fileInput" type="file" accept=".pdf,.docx" class="sr-only" @change="onFileInput" />
                <svg class="mx-auto h-6 w-6 text-gray-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                <p class="text-sm text-gray-500">Drop file or click to browse</p>
                <p class="text-xs text-gray-400">PDF or DOCX · Max 5 MB</p>
              </div>

              <!-- Selected file -->
              <div v-if="selectedFile" class="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5">
                <svg class="h-4 w-4 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900 truncate">{{ selectedFile.name }}</p>
                  <p class="text-xs text-gray-400">{{ formatBytes(selectedFile.size) }}</p>
                </div>
                <button class="text-gray-400 hover:text-gray-600" @click.stop="clearSelection">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <!-- Errors / success -->
              <div v-if="uploadError" class="flex items-center gap-2 rounded-lg bg-red-50 border border-red-100 px-3 py-2">
                <svg class="h-4 w-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <span class="text-sm text-red-700">{{ uploadError }}</span>
              </div>
              <div v-if="uploadResult === 'success'" class="flex items-center gap-2 rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-2">
                <svg class="h-4 w-4 text-emerald-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span class="text-sm text-emerald-700">CV stored locally. Not sent anywhere.</span>
              </div>

              <div v-if="selectedFile" class="flex justify-end">
                <button
                  :disabled="uploading"
                  class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  @click="uploadCV"
                >
                  <svg v-if="uploading" class="h-3.5 w-3.5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                  </svg>
                  {{ uploading ? 'Uploading…' : 'Upload CV' }}
                </button>
              </div>
            </div>
          </AppCard>

          <!-- Headline & Basics -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100">
              <h3 class="text-sm font-semibold text-gray-900">Identity & Headline</h3>
            </div>
            <div class="px-5 py-4 space-y-3.5">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Professional Headline</label>
                <input
                  v-model="form.headline"
                  type="text"
                  placeholder="e.g. Staff Backend Engineer · Python & Cloud"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Target Role</label>
                  <input
                    v-model="form.target_role"
                    type="text"
                    placeholder="Backend Engineer"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                  />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Location</label>
                  <input
                    v-model="form.location"
                    type="text"
                    placeholder="London, UK"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                  />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Email</label>
                  <input
                    v-model="form.email"
                    type="email"
                    placeholder="jane@example.com"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                  />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Phone</label>
                  <input
                    v-model="form.phone"
                    type="text"
                    placeholder="+44 7700 900000"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                  />
                </div>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">LinkedIn URL</label>
                <input
                  v-model="form.linkedin_url"
                  type="url"
                  placeholder="https://linkedin.com/in/yourname"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                />
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">GitHub URL</label>
                  <input
                    v-model="form.github_url"
                    type="url"
                    placeholder="https://github.com/yourname"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                  />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Portfolio URL</label>
                  <input
                    v-model="form.portfolio_url"
                    type="url"
                    placeholder="https://yoursite.com"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                  />
                </div>
              </div>
            </div>
          </AppCard>

          <!-- Professional Summary -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100">
              <h3 class="text-sm font-semibold text-gray-900">Professional Summary</h3>
            </div>
            <div class="px-5 py-4">
              <textarea
                v-model="form.professional_summary"
                rows="4"
                placeholder="A concise summary of your background, strengths, and what you bring to a role…"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition resize-none"
              />
            </div>
          </AppCard>

          <!-- Skills -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100">
              <h3 class="text-sm font-semibold text-gray-900">Skills</h3>
            </div>
            <div class="px-5 py-4 space-y-3">
              <!-- Chip display -->
              <div v-if="form.skills.length > 0" class="flex flex-wrap gap-1.5">
                <span
                  v-for="(skill, i) in form.skills"
                  :key="skill"
                  class="inline-flex items-center gap-1 rounded-full bg-blue-50 border border-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700"
                >
                  {{ skill }}
                  <button class="ml-0.5 text-blue-400 hover:text-blue-700" @click="removeSkill(i)">
                    <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              </div>
              <div v-else class="text-xs text-gray-400">No skills added yet.</div>

              <!-- Input -->
              <div class="flex gap-2">
                <input
                  v-model="skillsInput"
                  type="text"
                  placeholder="Python, FastAPI, Vue — press Enter or comma to add"
                  class="flex-1 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                  @keydown="onSkillsKeydown"
                />
                <button
                  class="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 transition"
                  @click="addSkillsFromInput"
                >
                  Add
                </button>
              </div>
              <p class="text-xs text-gray-400">Separate multiple skills with commas, or press Enter after each one.</p>
            </div>
          </AppCard>

          <!-- Experience -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-semibold text-gray-900">Experience</h3>
              <button
                class="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700 transition"
                @click="addExperience"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Add Role
              </button>
            </div>
            <div class="divide-y divide-gray-100">
              <div v-if="form.experience_items.length === 0" class="px-5 py-5 text-center">
                <p class="text-sm text-gray-400">No experience added. Click "Add Role" to get started.</p>
              </div>
              <div
                v-for="(exp, i) in form.experience_items"
                :key="i"
                class="px-5 py-4 space-y-3"
              >
                <div class="flex items-center justify-between">
                  <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Role {{ i + 1 }}</p>
                  <button class="text-xs text-red-400 hover:text-red-600 transition" @click="removeExperience(i)">Remove</button>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">Job Title</label>
                    <input v-model="exp.title" type="text" placeholder="Senior Engineer"
                      class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition" />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">Company</label>
                    <input v-model="exp.company" type="text" placeholder="Acme Corp"
                      class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition" />
                  </div>
                </div>
                <div class="grid grid-cols-3 gap-3">
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">Start</label>
                    <input v-model="exp.start_date" type="text" placeholder="2021-03"
                      class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition" />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">End</label>
                    <input v-model="exp.end_date" type="text" placeholder="2024-06"
                      :disabled="exp.currently_working"
                      class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition disabled:bg-gray-50 disabled:text-gray-400" />
                  </div>
                  <div class="flex items-end pb-2">
                    <label class="flex items-center gap-2 cursor-pointer">
                      <input v-model="exp.currently_working" type="checkbox"
                        class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                      <span class="text-xs text-gray-600">Current</span>
                    </label>
                  </div>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Location</label>
                  <input v-model="exp.location" type="text" placeholder="London / Remote"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Key Accomplishments</label>
                  <textarea
                    :value="getExpBullets(exp)"
                    rows="3"
                    placeholder="One accomplishment per line — lead with a strong action verb and quantify results…"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition resize-none"
                    @input="setExpBullets(exp, ($event.target as HTMLTextAreaElement).value)"
                  />
                  <p class="text-xs text-gray-400 mt-1">One bullet per line.</p>
                </div>
              </div>
            </div>
          </AppCard>

          <!-- Education -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-semibold text-gray-900">Education</h3>
              <button
                class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition"
                @click="addEducation"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Add
              </button>
            </div>
            <div class="divide-y divide-gray-100">
              <div v-if="form.education_items.length === 0" class="px-5 py-5 text-center">
                <p class="text-sm text-gray-400">No education added yet.</p>
              </div>
              <div v-for="(edu, i) in form.education_items" :key="i" class="px-5 py-4 space-y-3">
                <div class="flex items-center justify-between">
                  <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Entry {{ i + 1 }}</p>
                  <button class="text-xs text-red-400 hover:text-red-600" @click="removeEducation(i)">Remove</button>
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">Degree</label>
                    <input v-model="edu.degree" type="text" placeholder="BSc Computer Science"
                      class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition" />
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">Institution</label>
                    <input v-model="edu.institution" type="text" placeholder="University of London"
                      class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition" />
                  </div>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Dates</label>
                  <input v-model="edu.dates" type="text" placeholder="2017 – 2021"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition" />
                </div>
              </div>
            </div>
          </AppCard>

          <!-- Projects -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-semibold text-gray-900">Projects</h3>
              <button
                class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 transition"
                @click="addProject"
              >
                <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                Add
              </button>
            </div>
            <div class="divide-y divide-gray-100">
              <div v-if="form.project_items.length === 0" class="px-5 py-5 text-center">
                <p class="text-sm text-gray-400">No projects added yet.</p>
              </div>
              <div v-for="(proj, i) in form.project_items" :key="i" class="px-5 py-4 space-y-3">
                <div class="flex items-center justify-between">
                  <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Project {{ i + 1 }}</p>
                  <button class="text-xs text-red-400 hover:text-red-600" @click="removeProject(i)">Remove</button>
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Project Name</label>
                  <input v-model="proj.name" type="text" placeholder="My Open Source Tool"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Description</label>
                  <input v-model="proj.description" type="text" placeholder="Short description of what it does"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Technologies</label>
                  <input
                    :value="getProjTech(proj)"
                    type="text"
                    placeholder="Python, FastAPI, Vue"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                    @input="setProjTech(proj, ($event.target as HTMLInputElement).value)"
                  />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-600 mb-1">Highlights</label>
                  <textarea
                    :value="getProjBullets(proj)"
                    rows="2"
                    placeholder="One highlight per line…"
                    class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition resize-none"
                    @input="setProjBullets(proj, ($event.target as HTMLTextAreaElement).value)"
                  />
                </div>
              </div>
            </div>
          </AppCard>

          <!-- Certs, Languages, Achievements -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100">
              <h3 class="text-sm font-semibold text-gray-900">Certifications, Languages &amp; Achievements</h3>
            </div>
            <div class="px-5 py-4 space-y-4">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Certifications</label>
                <textarea v-model="certsText" rows="3" placeholder="AWS Solutions Architect&#10;Google Professional Data Engineer"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition resize-none" />
                <p class="text-xs text-gray-400 mt-1">One per line.</p>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Languages</label>
                <textarea v-model="langsText" rows="2" placeholder="English (Native)&#10;Spanish (B2)"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition resize-none" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Key Achievements</label>
                <textarea v-model="achievementsText" rows="3" placeholder="Led platform migration to microservices serving 2M+ users&#10;Open-source tool with 1.2k GitHub stars"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition resize-none" />
              </div>
            </div>
          </AppCard>

          <!-- Save row -->
          <div class="flex items-center justify-between pb-4">
            <transition name="fade">
              <div v-if="saveResult === 'success'" class="flex items-center gap-1.5 text-sm text-emerald-600">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Profile saved
              </div>
              <div v-else-if="saveResult === 'error'" class="text-sm text-red-500">
                Could not save — is the backend running?
              </div>
            </transition>
            <button
              :disabled="saving"
              class="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-semibold text-white hover:bg-gray-800 disabled:opacity-60 transition shadow-sm"
              @click="save"
            >
              <svg v-if="saving" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
              <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
              </svg>
              {{ saving ? 'Saving…' : 'Save Profile' }}
            </button>
          </div>
        </div>

        <!-- ── RIGHT: Preview ──────────────────────────────────────────────── -->
        <div class="xl:sticky xl:top-6 space-y-4">
          <!-- Action bar -->
          <div class="flex items-center gap-2 flex-wrap">
            <button
              :disabled="generating"
              class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition shadow-sm"
              @click="regenerate"
            >
              <svg v-if="generating" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
              <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
              {{ generating ? 'Generating…' : 'Regenerate Draft' }}
            </button>

            <button
              :disabled="!previewContent"
              class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition"
              @click="copyDraft"
            >
              <svg v-if="copied" class="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
              </svg>
              {{ copied ? 'Copied!' : 'Copy Draft' }}
            </button>

            <button
              disabled
              class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-400 opacity-50 cursor-not-allowed"
              title="Coming in a future phase"
            >
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              Export PDF
              <span class="ml-1 text-[10px] bg-gray-100 text-gray-400 rounded px-1.5 py-0.5 font-medium">Soon</span>
            </button>
          </div>

          <!-- Preview card -->
          <div class="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-semibold text-gray-900">Live Preview</h3>
              <span class="text-xs text-gray-400">Markdown draft — click "Regenerate Draft" to refresh</span>
            </div>

            <!-- Empty state -->
            <div v-if="!previewContent" class="px-5 py-10 text-center">
              <svg class="mx-auto h-10 w-10 text-gray-200 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              <p class="text-sm font-medium text-gray-500">No draft generated yet</p>
              <p class="text-xs text-gray-400 mt-1">Fill in your details and click "Regenerate Draft" to create a resume draft.</p>
            </div>

            <!-- Live preview rendering -->
            <div v-else class="px-6 py-6 font-mono text-xs leading-relaxed text-gray-700 max-h-[680px] overflow-y-auto">
              <!-- Header -->
              <div class="mb-4">
                <h1 class="text-xl font-bold text-gray-900 font-sans">
                  {{ form.headline || form.target_role || 'My Resume' }}
                </h1>
                <p v-if="form.target_role && form.headline" class="text-sm font-semibold text-blue-700 font-sans mt-0.5">
                  {{ form.target_role }}
                </p>
                <div class="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-xs text-gray-500 font-sans">
                  <span v-if="form.location">{{ form.location }}</span>
                  <span v-if="form.email">{{ form.email }}</span>
                  <span v-if="form.phone">{{ form.phone }}</span>
                  <span v-if="form.linkedin_url" class="text-blue-600">LinkedIn</span>
                  <span v-if="form.github_url" class="text-gray-600">GitHub</span>
                </div>
              </div>
              <hr class="border-gray-200 my-3" />

              <!-- Summary -->
              <div v-if="form.professional_summary" class="mb-4">
                <h2 class="text-xs font-bold text-gray-900 uppercase tracking-wider font-sans mb-1.5">Professional Summary</h2>
                <p class="text-xs text-gray-700 leading-relaxed font-sans">{{ form.professional_summary }}</p>
                <hr class="border-gray-200 mt-3" />
              </div>

              <!-- Skills -->
              <div v-if="form.skills.length > 0" class="mb-4">
                <h2 class="text-xs font-bold text-gray-900 uppercase tracking-wider font-sans mb-1.5">Skills</h2>
                <p class="text-xs text-gray-700 font-sans">{{ form.skills.join(' · ') }}</p>
                <hr class="border-gray-200 mt-3" />
              </div>

              <!-- Experience -->
              <div v-if="form.experience_items.length > 0" class="mb-4">
                <h2 class="text-xs font-bold text-gray-900 uppercase tracking-wider font-sans mb-2">Experience</h2>
                <div v-for="(exp, i) in form.experience_items" :key="i" class="mb-3">
                  <div class="flex items-baseline justify-between">
                    <p class="text-xs font-bold text-gray-900 font-sans">
                      {{ exp.title || '(Role)' }}
                      <span v-if="exp.company"> — {{ exp.company }}</span>
                    </p>
                    <span class="text-[10px] text-gray-400 font-sans flex-shrink-0 ml-2">
                      {{ exp.start_date }}{{ exp.currently_working ? ' – Present' : exp.end_date ? ` – ${exp.end_date}` : '' }}
                    </span>
                  </div>
                  <p v-if="exp.location" class="text-[10px] text-gray-400 font-sans">{{ exp.location }}</p>
                  <ul v-if="exp.bullets.length > 0" class="mt-1 space-y-0.5">
                    <li v-for="(b, bi) in exp.bullets" :key="bi" class="flex items-start gap-1.5 text-xs text-gray-700 font-sans">
                      <span class="text-gray-400 flex-shrink-0 mt-0.5">·</span>
                      <span>{{ b }}</span>
                    </li>
                  </ul>
                </div>
                <hr class="border-gray-200 mt-3" />
              </div>

              <!-- Education -->
              <div v-if="form.education_items.length > 0" class="mb-4">
                <h2 class="text-xs font-bold text-gray-900 uppercase tracking-wider font-sans mb-2">Education</h2>
                <div v-for="(edu, i) in form.education_items" :key="i" class="mb-2">
                  <p class="text-xs font-bold text-gray-900 font-sans">{{ edu.degree || '(Degree)' }}</p>
                  <p class="text-[10px] text-gray-500 font-sans">{{ edu.institution }}<span v-if="edu.dates"> · {{ edu.dates }}</span></p>
                </div>
                <hr class="border-gray-200 mt-3" />
              </div>

              <!-- Certs -->
              <div v-if="form.certifications.length > 0" class="mb-4">
                <h2 class="text-xs font-bold text-gray-900 uppercase tracking-wider font-sans mb-1.5">Certifications</h2>
                <ul class="space-y-0.5">
                  <li v-for="(c, i) in form.certifications" :key="i" class="flex items-start gap-1.5 text-xs text-gray-700 font-sans">
                    <span class="text-gray-400">·</span><span>{{ c }}</span>
                  </li>
                </ul>
              </div>

              <!-- Languages -->
              <div v-if="form.languages.length > 0" class="mb-4">
                <h2 class="text-xs font-bold text-gray-900 uppercase tracking-wider font-sans mb-1.5">Languages</h2>
                <p class="text-xs text-gray-700 font-sans">{{ form.languages.join(' · ') }}</p>
              </div>

              <!-- Achievements -->
              <div v-if="form.achievements.length > 0" class="mb-2">
                <h2 class="text-xs font-bold text-gray-900 uppercase tracking-wider font-sans mb-1.5">Key Achievements</h2>
                <ul class="space-y-0.5">
                  <li v-for="(a, i) in form.achievements" :key="i" class="flex items-start gap-1.5 text-xs text-gray-700 font-sans">
                    <span class="text-gray-400">·</span><span>{{ a }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Privacy footer -->
          <div class="rounded-xl border border-gray-100 bg-gray-50 px-4 py-3 space-y-1.5">
            <p class="text-xs font-semibold text-gray-500">Data Privacy</p>
            <div class="space-y-1">
              <div class="flex items-center gap-2 text-xs text-gray-500">
                <svg class="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                Resume profile stored in <code class="bg-gray-100 px-1 rounded font-mono text-[10px]">data/resume_profile.json</code>
              </div>
              <div class="flex items-center gap-2 text-xs text-gray-500">
                <svg class="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                Draft saved to <code class="bg-gray-100 px-1 rounded font-mono text-[10px]">data/resume_preview.md</code>
              </div>
              <div class="flex items-center gap-2 text-xs text-gray-500">
                <svg class="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                Both files are in <code class="bg-gray-100 px-1 rounded font-mono text-[10px]">.gitignore</code> — never committed
              </div>
              <div class="flex items-center gap-2 text-xs text-gray-400">
                <svg class="h-3.5 w-3.5 text-gray-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
                Not sent to AI, LinkedIn, or any external service
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
