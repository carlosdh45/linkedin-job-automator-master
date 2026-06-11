<script setup lang="ts">
import type { ApplicationPacket, ApplicationPacketUpdate, ChecklistItem, ResumeQualityReport } from '~/types'

const api = useApi()

// ── State ─────────────────────────────────────────────────────────────────────
const loading = ref(true)
const loadError = ref(false)
const saving = ref(false)
const saveResult = ref<'idle' | 'success' | 'error'>('idle')
const generating = ref(false)
const generateError = ref('')

// ── Resume readiness ──────────────────────────────────────────────────────────
const resumeQuality = ref<ResumeQualityReport | null>(null)

const packet = ref<ApplicationPacket>({
  target_job_title: '',
  target_company: '',
  job_description: '',
  resume_markdown: '',
  cover_letter_draft: '',
  tailored_summary: '',
  skills_emphasis: [],
  fit_summary: '',
  talking_points: [],
  checklist: [],
  status: 'not_started',
  notes: '',
  updated_at: null,
})

const APPLICATION_STATUSES = [
  { value: 'not_started',        label: 'Not Started',        color: 'bg-gray-100 text-gray-600' },
  { value: 'ready',              label: 'Ready',              color: 'bg-blue-100 text-blue-700' },
  { value: 'submitted_manually', label: 'Submitted Manually', color: 'bg-amber-100 text-amber-700' },
  { value: 'interviewing',       label: 'Interviewing',       color: 'bg-purple-100 text-purple-700' },
  { value: 'rejected',           label: 'Rejected',           color: 'bg-red-100 text-red-600' },
  { value: 'offer',              label: 'Offer',              color: 'bg-emerald-100 text-emerald-700' },
]

const statusColor = computed(() =>
  APPLICATION_STATUSES.find(s => s.value === packet.value.status)?.color ?? 'bg-gray-100 text-gray-600'
)
const statusLabel = computed(() =>
  APPLICATION_STATUSES.find(s => s.value === packet.value.status)?.label ?? packet.value.status
)

// ── Load ──────────────────────────────────────────────────────────────────────
async function load() {
  loading.value = true
  loadError.value = false
  try {
    packet.value = await api.getApplicationPacket()
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
  try {
    resumeQuality.value = await api.getResumeQuality()
  } catch {
    // non-critical
  }
}

onMounted(load)

// ── Save ──────────────────────────────────────────────────────────────────────
async function save() {
  saving.value = true
  saveResult.value = 'idle'
  try {
    const updates: ApplicationPacketUpdate = {
      target_job_title:  packet.value.target_job_title,
      target_company:    packet.value.target_company,
      job_description:   packet.value.job_description,
      cover_letter_draft: packet.value.cover_letter_draft,
      talking_points:    packet.value.talking_points,
      checklist:         packet.value.checklist,
      status:            packet.value.status,
      notes:             packet.value.notes,
    }
    packet.value = await api.updateApplicationPacket(updates)
    saveResult.value = 'success'
    setTimeout(() => { saveResult.value = 'idle' }, 3000)
  } catch {
    saveResult.value = 'error'
  } finally {
    saving.value = false
  }
}

// ── Generate ──────────────────────────────────────────────────────────────────
async function generate() {
  generating.value = true
  generateError.value = ''
  try {
    await save()
    packet.value = await api.generateApplicationPacket()
  } catch {
    generateError.value = 'Generation failed — is the backend running?'
  } finally {
    generating.value = false
  }
}

// ── Checklist ─────────────────────────────────────────────────────────────────
function toggleChecklist(item: ChecklistItem) {
  item.done = !item.done
}

const completedCount = computed(() => packet.value.checklist.filter(i => i.done).length)
const totalCount     = computed(() => packet.value.checklist.length)
const checklistProgress = computed(() =>
  totalCount.value > 0 ? Math.round((completedCount.value / totalCount.value) * 100) : 0
)

// ── Copy helpers ──────────────────────────────────────────────────────────────
const copiedCover  = ref(false)
async function copyCoverLetter() {
  try {
    await navigator.clipboard.writeText(packet.value.cover_letter_draft)
    copiedCover.value = true
    setTimeout(() => { copiedCover.value = false }, 2500)
  } catch {}
}

const copiedResume = ref(false)
async function copyResume() {
  try {
    await navigator.clipboard.writeText(packet.value.resume_markdown)
    copiedResume.value = true
    setTimeout(() => { copiedResume.value = false }, 2500)
  } catch {}
}

const copiedTailored = ref(false)
async function copyTailored() {
  try {
    await navigator.clipboard.writeText(packet.value.tailored_summary)
    copiedTailored.value = true
    setTimeout(() => { copiedTailored.value = false }, 2500)
  } catch {}
}

// ── Download cover letter ─────────────────────────────────────────────────────
function downloadCoverLetter() {
  if (!packet.value.cover_letter_draft) return
  const blob = new Blob([packet.value.cover_letter_draft], { type: 'text/plain' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = 'cover-letter.txt'
  a.click()
  URL.revokeObjectURL(url)
}

function formatDate(iso: string | null) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Application Packet"
      subtitle="Prepare your materials for manual submission"
    />

    <div v-if="loading" class="flex-1 flex items-center justify-center p-8">
      <LoadingSpinner label="Loading Application Packet…" />
    </div>

    <div v-else-if="loadError" class="flex-1 p-6 max-w-3xl mx-auto w-full">
      <AppCard>
        <ErrorState
          message="Could not reach the backend. Make sure uvicorn is running on port 8000."
          :show-retry="true"
          @retry="load"
        />
      </AppCard>
    </div>

    <template v-else>

      <!-- Safety notice -->
      <div class="px-6 pt-4">
        <div class="flex items-start gap-3 rounded-xl bg-emerald-50 border border-emerald-100 px-4 py-3 max-w-5xl mx-auto">
          <svg class="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
          <p class="text-sm text-emerald-700">
            <strong>Prepared for manual submission.</strong>
            DobryBot never sends or applies automatically. Use this packet to prepare — then submit yourself.
          </p>
        </div>
      </div>

      <div class="flex-1 p-6 max-w-5xl mx-auto w-full space-y-5">

        <!-- ── Resume Readiness ───────────────────────────────────────────── -->
        <div v-if="resumeQuality" class="rounded-xl border px-4 py-3 flex items-center gap-4" :class="{
          'bg-emerald-50 border-emerald-100': resumeQuality.completeness_score >= 80,
          'bg-blue-50 border-blue-100':       resumeQuality.completeness_score >= 60 && resumeQuality.completeness_score < 80,
          'bg-amber-50 border-amber-100':     resumeQuality.completeness_score >= 40 && resumeQuality.completeness_score < 60,
          'bg-gray-50 border-gray-200':       resumeQuality.completeness_score < 40,
        }">
          <div class="flex-shrink-0">
            <div class="h-10 w-10 rounded-full flex items-center justify-center font-bold text-sm" :class="{
              'bg-emerald-100 text-emerald-700': resumeQuality.completeness_score >= 80,
              'bg-blue-100 text-blue-700':       resumeQuality.completeness_score >= 60 && resumeQuality.completeness_score < 80,
              'bg-amber-100 text-amber-700':     resumeQuality.completeness_score >= 40 && resumeQuality.completeness_score < 60,
              'bg-gray-100 text-gray-500':       resumeQuality.completeness_score < 40,
            }">{{ resumeQuality.completeness_score }}%</div>
          </div>
          <div class="flex-1">
            <p class="text-sm font-semibold text-gray-900">
              Resume readiness:
              <span :class="{
                'text-emerald-600': resumeQuality.completeness_score >= 80,
                'text-blue-600':    resumeQuality.completeness_score >= 60 && resumeQuality.completeness_score < 80,
                'text-amber-600':   resumeQuality.completeness_score >= 40 && resumeQuality.completeness_score < 60,
                'text-gray-500':    resumeQuality.completeness_score < 40,
              }">
                {{ resumeQuality.completeness_score >= 80 ? 'Excellent' : resumeQuality.completeness_score >= 60 ? 'Good' : resumeQuality.completeness_score >= 40 ? 'Fair' : 'Incomplete' }}
              </span>
            </p>
            <p v-if="resumeQuality.missing_sections.length > 0" class="text-xs text-gray-500 mt-0.5">
              Missing: {{ resumeQuality.missing_sections.slice(0, 4).join(', ') }}{{ resumeQuality.missing_sections.length > 4 ? ` +${resumeQuality.missing_sections.length - 4} more` : '' }}
            </p>
            <p v-else class="text-xs text-emerald-600 mt-0.5">All key sections complete</p>
          </div>
          <NuxtLink
            to="/resume"
            class="flex-shrink-0 inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition"
          >
            <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125" />
            </svg>
            Edit Resume
          </NuxtLink>
        </div>

        <!-- ── Target + Status row ───────────────────────────────────────── -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">

          <!-- Target job + job description -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100">
              <h3 class="text-sm font-semibold text-gray-900">Target Role</h3>
            </div>
            <div class="px-5 py-4 space-y-3">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Job Title</label>
                <input
                  v-model="packet.target_job_title"
                  type="text"
                  placeholder="e.g. Senior Backend Engineer"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Company</label>
                <input
                  v-model="packet.target_company"
                  type="text"
                  placeholder="e.g. Acme Corp"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">
                  Job Description
                  <span class="ml-1 text-gray-400 font-normal">Paste from job posting</span>
                </label>
                <textarea
                  v-model="packet.job_description"
                  rows="6"
                  placeholder="Paste the job description here. Used locally to tailor your summary, skills emphasis, and cover letter — not sent anywhere."
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition resize-none leading-relaxed"
                />
                <p class="text-[10px] text-gray-400 mt-1">Used locally to tailor materials. Never sent externally.</p>
              </div>
            </div>
          </AppCard>

          <!-- Application Status -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100">
              <h3 class="text-sm font-semibold text-gray-900">Application Status</h3>
            </div>
            <div class="px-5 py-4 space-y-3">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-xs px-2.5 py-1 rounded-full font-semibold" :class="statusColor">{{ statusLabel }}</span>
                <span v-if="packet.updated_at" class="text-xs text-gray-400">{{ formatDate(packet.updated_at) }}</span>
              </div>
              <div class="grid grid-cols-2 gap-1.5">
                <button
                  v-for="s in APPLICATION_STATUSES"
                  :key="s.value"
                  class="rounded-lg border px-3 py-1.5 text-xs font-medium transition text-left"
                  :class="packet.status === s.value
                    ? 'border-blue-300 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
                  @click="packet.status = s.value"
                >
                  {{ s.label }}
                </button>
              </div>
            </div>
          </AppCard>
        </div>

        <!-- ── Action bar ─────────────────────────────────────────────────── -->
        <div class="flex items-center gap-3 flex-wrap">
          <button
            :disabled="generating"
            class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition shadow-sm"
            @click="generate"
          >
            <svg v-if="generating" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
            <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            {{ generating ? 'Generating…' : 'Generate Packet (Local)' }}
          </button>
          <button
            :disabled="saving"
            class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60 transition"
            @click="save"
          >
            <svg v-if="saving" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
            <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
            </svg>
            {{ saving ? 'Saving…' : 'Save' }}
          </button>
          <transition name="fade">
            <span v-if="saveResult === 'success'" class="text-sm text-emerald-600 font-medium">Saved</span>
            <span v-else-if="saveResult === 'error'" class="text-sm text-red-500">Could not save</span>
          </transition>
          <span v-if="generateError" class="text-sm text-red-500">{{ generateError }}</span>
          <span class="ml-auto text-xs text-gray-400">No external AI · No auto-submit · Local only</span>
        </div>

        <!-- ── Tailored for this role (shown after generation) ─────────────── -->
        <template v-if="packet.tailored_summary || packet.skills_emphasis.length > 0 || packet.fit_summary">
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h3 class="text-sm font-semibold text-gray-900">Tailored for This Role</h3>
                <p class="text-xs text-gray-500 mt-0.5">Generated locally from your profile and job description</p>
              </div>
              <span class="rounded-full bg-blue-50 border border-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700">Local only</span>
            </div>
            <div class="px-5 py-4 space-y-5">

              <!-- Tailored Summary -->
              <div v-if="packet.tailored_summary">
                <div class="flex items-center justify-between mb-2">
                  <p class="text-xs font-semibold text-gray-700 uppercase tracking-wide">Tailored Summary</p>
                  <button
                    class="inline-flex items-center gap-1 rounded-lg border border-gray-200 px-2 py-1 text-[10px] font-medium text-gray-500 hover:bg-gray-50 transition"
                    @click="copyTailored"
                  >
                    <svg v-if="copiedTailored" class="h-3 w-3 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                    <svg v-else class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                    </svg>
                    {{ copiedTailored ? 'Copied!' : 'Copy' }}
                  </button>
                </div>
                <p class="text-sm text-gray-700 leading-relaxed bg-blue-50 rounded-lg px-4 py-3 border border-blue-100">{{ packet.tailored_summary }}</p>
              </div>

              <!-- Skills Emphasis -->
              <div v-if="packet.skills_emphasis.length > 0">
                <p class="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Relevant Skills</p>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="skill in packet.skills_emphasis"
                    :key="skill"
                    class="rounded-full bg-emerald-50 border border-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-700"
                  >{{ skill }}</span>
                </div>
              </div>

              <!-- Fit Summary -->
              <div v-if="packet.fit_summary">
                <p class="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Why You Fit</p>
                <p class="text-sm text-gray-700 leading-relaxed bg-gray-50 rounded-lg px-4 py-3 border border-gray-100">{{ packet.fit_summary }}</p>
              </div>

            </div>
          </AppCard>
        </template>

        <!-- Empty state for tailored section (before first generate) -->
        <div v-else class="rounded-xl border border-dashed border-gray-200 bg-gray-50 px-4 py-5 text-center">
          <svg class="mx-auto h-8 w-8 text-gray-200 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          <p class="text-sm font-medium text-gray-500">No tailored materials yet</p>
          <p class="text-xs text-gray-400 mt-1">
            Paste a job description above, then click "Generate Packet" to get a tailored summary, skills emphasis, and fit analysis.
          </p>
        </div>

        <!-- ── Two-column: Cover Letter + Right panel ─────────────────────── -->
        <div class="grid grid-cols-1 xl:grid-cols-2 gap-5 items-start">

          <!-- Cover Letter -->
          <AppCard>
            <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-semibold text-gray-900">Cover Letter Draft</h3>
              <div class="flex items-center gap-1.5">
                <button
                  :disabled="!packet.cover_letter_draft"
                  class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition"
                  @click="downloadCoverLetter"
                >
                  <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                  </svg>
                  .txt
                </button>
                <button
                  :disabled="!packet.cover_letter_draft"
                  class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition"
                  @click="copyCoverLetter"
                >
                  <svg v-if="copiedCover" class="h-3.5 w-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <svg v-else class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                  </svg>
                  {{ copiedCover ? 'Copied!' : 'Copy' }}
                </button>
              </div>
            </div>
            <div class="px-5 py-4">
              <div v-if="!packet.cover_letter_draft" class="text-center py-8">
                <svg class="mx-auto h-8 w-8 text-gray-200 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <p class="text-sm text-gray-400">No cover letter yet.</p>
                <p class="text-xs text-gray-400 mt-1">Click "Generate Packet" to create one from your profile.</p>
              </div>
              <textarea
                v-else
                v-model="packet.cover_letter_draft"
                rows="16"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition resize-none leading-relaxed"
              />
              <p class="text-xs text-gray-400 mt-2">Edit freely. Generated locally — not sent anywhere.</p>
            </div>
          </AppCard>

          <!-- Right column: Resume + Talking Points -->
          <div class="space-y-5">

            <!-- Resume draft -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
                <h3 class="text-sm font-semibold text-gray-900">Resume Draft</h3>
                <button
                  :disabled="!packet.resume_markdown"
                  class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition"
                  @click="copyResume"
                >
                  <svg v-if="copiedResume" class="h-3.5 w-3.5 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <svg v-else class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
                  </svg>
                  {{ copiedResume ? 'Copied!' : 'Copy' }}
                </button>
              </div>
              <div class="px-5 py-4">
                <div v-if="!packet.resume_markdown" class="text-center py-5">
                  <p class="text-sm text-gray-400">Resume draft appears here after generating.</p>
                  <p class="text-xs text-gray-400 mt-1">Build your resume in Resume Studio first, then generate.</p>
                </div>
                <div v-else class="max-h-56 overflow-y-auto rounded-lg border border-gray-100 bg-gray-50 px-3 py-3">
                  <pre class="text-xs text-gray-700 font-mono whitespace-pre-wrap leading-relaxed">{{ packet.resume_markdown }}</pre>
                </div>
              </div>
            </AppCard>

            <!-- Talking points -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100">
                <h3 class="text-sm font-semibold text-gray-900">Interview Talking Points</h3>
                <p class="text-xs text-gray-500 mt-0.5">Generated from your profile and the target role</p>
              </div>
              <div class="px-5 py-4">
                <div v-if="packet.talking_points.length === 0" class="text-center py-5">
                  <p class="text-sm text-gray-400">Talking points appear after generating the packet.</p>
                </div>
                <ul v-else class="space-y-2">
                  <li
                    v-for="(pt, i) in packet.talking_points"
                    :key="i"
                    class="flex items-start gap-2 text-sm text-gray-700"
                  >
                    <span class="flex-shrink-0 mt-0.5 h-5 w-5 flex items-center justify-center rounded-full bg-blue-100 text-blue-700 text-xs font-bold">{{ i + 1 }}</span>
                    <span>{{ pt }}</span>
                  </li>
                </ul>
              </div>
            </AppCard>

          </div>
        </div>

        <!-- ── Manual Application Checklist ───────────────────────────────── -->
        <AppCard>
          <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h3 class="text-sm font-semibold text-gray-900">Manual Application Checklist</h3>
              <p class="text-xs text-gray-500 mt-0.5">Tick off each step before submitting manually</p>
            </div>
            <div v-if="packet.checklist.length > 0" class="text-right">
              <span class="text-sm font-semibold" :class="checklistProgress === 100 ? 'text-emerald-600' : 'text-gray-700'">
                {{ completedCount }}/{{ totalCount }}
              </span>
              <div class="h-1 w-20 bg-gray-100 rounded-full mt-1 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="checklistProgress === 100 ? 'bg-emerald-500' : 'bg-blue-500'"
                  :style="{ width: `${checklistProgress}%` }"
                />
              </div>
            </div>
          </div>
          <div class="divide-y divide-gray-50">
            <div v-if="packet.checklist.length === 0" class="px-5 py-6 text-center">
              <svg class="mx-auto h-8 w-8 text-gray-200 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-sm text-gray-400">Generate the packet to get a pre-filled submission checklist.</p>
            </div>
            <div
              v-for="(item, i) in packet.checklist"
              :key="i"
              class="flex items-start gap-3 px-5 py-3 cursor-pointer hover:bg-gray-50 transition"
              @click="toggleChecklist(item)"
            >
              <div
                class="flex-shrink-0 mt-0.5 h-4 w-4 rounded border-2 flex items-center justify-center transition-colors"
                :class="item.done ? 'border-emerald-500 bg-emerald-500' : 'border-gray-300'"
              >
                <svg v-if="item.done" class="h-2.5 w-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <span class="text-sm transition-colors" :class="item.done ? 'text-gray-400 line-through' : 'text-gray-700'">{{ item.text }}</span>
            </div>
          </div>
        </AppCard>

        <!-- ── Notes ──────────────────────────────────────────────────────── -->
        <AppCard>
          <div class="px-5 py-3.5 border-b border-gray-100">
            <h3 class="text-sm font-semibold text-gray-900">Notes</h3>
            <p class="text-xs text-gray-500 mt-0.5">Personal notes about this application — stored locally only</p>
          </div>
          <div class="px-5 py-4">
            <textarea
              v-model="packet.notes"
              rows="4"
              placeholder="Recruiter name, application portal URL, who referred you, specific questions to ask at interview, follow-up dates…"
              class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-800 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition resize-none leading-relaxed"
            />
          </div>
        </AppCard>

        <!-- ── Privacy footer ─────────────────────────────────────────────── -->
        <div class="rounded-xl border border-gray-100 bg-gray-50 px-4 py-3 space-y-1.5">
          <p class="text-xs font-semibold text-gray-500">Data &amp; Safety</p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-1">
            <div class="flex items-center gap-2 text-xs text-gray-500">
              <svg class="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              Stored locally in <code class="bg-gray-100 px-1 rounded font-mono text-[10px]">data/application_packet.json</code>
            </div>
            <div class="flex items-center gap-2 text-xs text-gray-500">
              <svg class="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              All content generated by local rule-based template only
            </div>
            <div class="flex items-center gap-2 text-xs text-gray-400">
              <svg class="h-3.5 w-3.5 text-gray-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              Never submitted automatically
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
    </template>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
