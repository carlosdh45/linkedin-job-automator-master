<script setup lang="ts">
import type { ProfileUpdate } from '~/types'

const api = useApi()

const { data: profile, pending, error, refresh } = await useAsyncData('profile', () => api.getProfile())

const form = reactive({
  full_name: '',
  email: '',
  target_roles_text: '',
  seniority: '',
  preferred_locations_text: '',
  remote_preference: '',
  salary_expectation: '',
  linkedin_url: '',
  portfolio_url: '',
  github_url: '',
  key_skills_text: '',
  industries_text: '',
})

function populateForm() {
  if (!profile.value) return
  form.full_name = profile.value.full_name
  form.email = profile.value.email
  form.target_roles_text = profile.value.target_roles.join(', ')
  form.seniority = profile.value.seniority
  form.preferred_locations_text = profile.value.preferred_locations.join(', ')
  form.remote_preference = profile.value.remote_preference
  form.salary_expectation = profile.value.salary_expectation
  form.linkedin_url = profile.value.linkedin_url
  form.portfolio_url = profile.value.portfolio_url
  form.github_url = profile.value.github_url
  form.key_skills_text = profile.value.key_skills.join(', ')
  form.industries_text = profile.value.industries_of_interest.join(', ')
}

watch(profile, populateForm, { immediate: true })

const saving = ref(false)
const saveResult = ref<'idle' | 'success' | 'error'>('idle')

function splitList(text: string): string[] {
  return text.split(',').map(s => s.trim()).filter(Boolean)
}

// ── Completion score ─────────────────────────────────────────────────────────
const completionScore = computed(() => {
  if (!profile.value) return 0
  let pts = 0
  if (profile.value.full_name) pts += 10
  if (profile.value.email) pts += 10
  if (profile.value.target_roles.length > 0) pts += 15
  if (profile.value.key_skills.length > 0) pts += 15
  if (profile.value.seniority) pts += 10
  if (profile.value.remote_preference) pts += 10
  if (profile.value.preferred_locations.length > 0) pts += 10
  if (profile.value.linkedin_url) pts += 10
  if (profile.value.industries_of_interest.length > 0) pts += 10
  return Math.min(pts, 100)
})

const completionLabel = computed(() => {
  const s = completionScore.value
  if (s >= 80) return 'Profile is strong'
  if (s >= 60) return 'Looking good'
  if (s >= 40) return 'Getting there'
  return 'Just getting started'
})

const completionBarColor = computed(() => {
  const s = completionScore.value
  if (s >= 80) return 'bg-emerald-500'
  if (s >= 60) return 'bg-blue-500'
  if (s >= 40) return 'bg-amber-500'
  return 'bg-gray-300'
})

const missingFields = computed(() => {
  if (!profile.value) return []
  const m: { label: string; hint: string }[] = []
  if (!profile.value.full_name) m.push({ label: 'Full Name', hint: 'Required for personalised outreach' })
  if (!profile.value.email) m.push({ label: 'Email', hint: 'Contact details for your profile' })
  if (profile.value.target_roles.length === 0) m.push({ label: 'Target Roles', hint: 'Helps DobryBot score job matches' })
  if (profile.value.key_skills.length === 0) m.push({ label: 'Skills', hint: 'Used for opportunity scoring and matching' })
  if (!profile.value.seniority) m.push({ label: 'Seniority', hint: 'Filters roles by level' })
  if (!profile.value.linkedin_url) m.push({ label: 'LinkedIn URL', hint: 'Enables better outreach context' })
  if (profile.value.industries_of_interest.length === 0) m.push({ label: 'Industries', hint: 'Focuses lead scoring' })
  return m
})

// Parse target roles and skills from current form text for chip display
const targetRoleChips = computed(() => splitList(form.target_roles_text))
const skillChips = computed(() => splitList(form.key_skills_text))
const industryChips = computed(() => splitList(form.industries_text))

async function save() {
  saving.value = true
  saveResult.value = 'idle'
  try {
    const updates: ProfileUpdate = {
      full_name: form.full_name,
      email: form.email,
      target_roles: splitList(form.target_roles_text),
      seniority: form.seniority,
      preferred_locations: splitList(form.preferred_locations_text),
      remote_preference: form.remote_preference,
      salary_expectation: form.salary_expectation,
      linkedin_url: form.linkedin_url,
      portfolio_url: form.portfolio_url,
      github_url: form.github_url,
      key_skills: splitList(form.key_skills_text),
      industries_of_interest: splitList(form.industries_text),
    }
    await api.updateProfile(updates)
    await refresh()
    saveResult.value = 'success'
    setTimeout(() => { saveResult.value = 'idle' }, 3000)
  } catch {
    saveResult.value = 'error'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Profile Intelligence"
      subtitle="Your profile powers opportunity scoring — a stronger profile means better matches."
    />

    <div class="flex-1 p-6 space-y-6 max-w-2xl w-full mx-auto">
      <LoadingSpinner v-if="pending" label="Loading profile…" />

      <template v-else-if="error">
        <AppCard>
          <ErrorState
            message="Could not reach the backend. Make sure uvicorn is running on port 8000."
            :show-retry="true"
            @retry="() => refresh()"
          />
        </AppCard>
      </template>

      <template v-else>
        <!-- ── Profile Intelligence Score ───────────────────────────────── -->
        <AppCard>
          <div class="px-5 py-4 space-y-3">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-semibold text-gray-900">Profile Score</p>
                <p class="text-xs text-gray-500 mt-0.5">{{ completionLabel }}</p>
              </div>
              <div class="text-right">
                <span class="text-2xl font-bold tabular-nums" :class="{
                  'text-emerald-600': completionScore >= 80,
                  'text-blue-600': completionScore >= 60 && completionScore < 80,
                  'text-amber-500': completionScore >= 40 && completionScore < 60,
                  'text-gray-400': completionScore < 40,
                }">{{ completionScore }}</span>
                <span class="text-sm text-gray-400">/100</span>
              </div>
            </div>
            <div class="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="completionBarColor"
                :style="{ width: `${completionScore}%` }"
              />
            </div>
            <!-- Explanation -->
            <div class="rounded-lg bg-blue-50 border border-blue-100 px-3 py-2.5">
              <p class="text-xs text-blue-700">
                <strong>How this helps:</strong> A complete profile allows DobryBot to rank jobs, score leads, and
                personalise outreach with accurate context — entirely locally, never shared externally.
              </p>
            </div>
          </div>
        </AppCard>

        <!-- ── Missing Fields Checklist ─────────────────────────────────── -->
        <AppCard v-if="missingFields.length > 0">
          <div class="px-5 py-3.5 border-b border-gray-100">
            <h3 class="text-sm font-semibold text-gray-900">Complete your profile</h3>
            <p class="text-xs text-gray-500 mt-0.5">{{ missingFields.length }} field{{ missingFields.length === 1 ? '' : 's' }} missing</p>
          </div>
          <div class="px-5 py-3 divide-y divide-gray-50">
            <div
              v-for="f in missingFields"
              :key="f.label"
              class="flex items-start gap-3 py-2.5"
            >
              <div class="h-4 w-4 rounded-full border-2 border-gray-300 flex-shrink-0 mt-0.5" />
              <div>
                <p class="text-sm font-medium text-gray-700">{{ f.label }}</p>
                <p class="text-xs text-gray-400">{{ f.hint }}</p>
              </div>
            </div>
          </div>
        </AppCard>

        <AppCard v-else>
          <div class="px-5 py-4 flex items-center gap-3">
            <svg class="h-5 w-5 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p class="text-sm font-semibold text-gray-900">Profile complete</p>
              <p class="text-xs text-gray-500">All key fields are filled. DobryBot will score opportunities with full context.</p>
            </div>
          </div>
        </AppCard>

        <!-- Info banner -->
        <div class="flex items-start gap-3 rounded-xl bg-blue-50 border border-blue-100 px-4 py-3">
          <svg class="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="text-sm text-blue-700">
            All profile data is stored <strong>locally</strong> in <code class="bg-blue-100 px-1 rounded font-mono text-xs">data/profile.json</code> — never sent to any external service.
          </span>
        </div>

        <!-- ── Identity ───────────────────────────────────────────────────── -->
        <AppCard>
          <div class="px-5 py-3.5 border-b border-gray-100">
            <h3 class="text-sm font-semibold text-gray-900">Identity</h3>
          </div>
          <div class="px-5 py-4 space-y-4">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Full Name</label>
                <input
                  v-model="form.full_name"
                  type="text"
                  placeholder="Jane Smith"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Email</label>
                <input
                  v-model="form.email"
                  type="email"
                  placeholder="jane@example.com"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                />
              </div>
            </div>
          </div>
        </AppCard>

        <!-- ── Career Preferences ─────────────────────────────────────────── -->
        <AppCard>
          <div class="px-5 py-3.5 border-b border-gray-100">
            <h3 class="text-sm font-semibold text-gray-900">Opportunity Fit Settings</h3>
            <p class="text-xs text-gray-500 mt-0.5">These settings directly influence how DobryBot scores jobs and leads.</p>
          </div>
          <div class="px-5 py-4 space-y-4">
            <!-- Target roles with chip preview -->
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Target Roles</label>
              <input
                v-model="form.target_roles_text"
                type="text"
                placeholder="Backend Engineer, Staff Engineer, Engineering Manager"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
              />
              <div v-if="targetRoleChips.length > 0" class="flex flex-wrap gap-1.5 mt-2">
                <span
                  v-for="role in targetRoleChips"
                  :key="role"
                  class="rounded-full bg-blue-50 border border-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700"
                >{{ role }}</span>
              </div>
              <p class="text-xs text-gray-400 mt-1">Comma-separated. Chips update as you type.</p>
            </div>

            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Seniority Level</label>
                <select
                  v-model="form.seniority"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                >
                  <option value="">— Select —</option>
                  <option value="junior">Junior</option>
                  <option value="mid">Mid-level</option>
                  <option value="senior">Senior</option>
                  <option value="staff">Staff</option>
                  <option value="principal">Principal</option>
                  <option value="lead">Lead</option>
                  <option value="manager">Manager</option>
                  <option value="director">Director</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Remote Preference</label>
                <select
                  v-model="form.remote_preference"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                >
                  <option value="">— Select —</option>
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="onsite">Onsite</option>
                  <option value="flexible">Flexible</option>
                </select>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Preferred Locations</label>
                <input
                  v-model="form.preferred_locations_text"
                  type="text"
                  placeholder="London, Remote, Berlin"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                />
                <p class="text-xs text-gray-400 mt-1">Comma-separated</p>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Salary Expectation</label>
                <input
                  v-model="form.salary_expectation"
                  type="text"
                  placeholder="£80,000 – £100,000"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                />
              </div>
            </div>
          </div>
        </AppCard>

        <!-- ── Skills & Industries ─────────────────────────────────────────── -->
        <AppCard>
          <div class="px-5 py-3.5 border-b border-gray-100">
            <h3 class="text-sm font-semibold text-gray-900">Skills &amp; Industries</h3>
            <p class="text-xs text-gray-500 mt-0.5">Used by the scoring engine to match you to relevant opportunities.</p>
          </div>
          <div class="px-5 py-4 space-y-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Key Skills</label>
              <input
                v-model="form.key_skills_text"
                type="text"
                placeholder="Python, FastAPI, PostgreSQL, TypeScript, Vue"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
              />
              <div v-if="skillChips.length > 0" class="flex flex-wrap gap-1.5 mt-2">
                <span
                  v-for="skill in skillChips"
                  :key="skill"
                  class="rounded-full bg-gray-100 border border-gray-200 px-2.5 py-0.5 text-xs font-medium text-gray-600"
                >{{ skill }}</span>
              </div>
              <p class="text-xs text-gray-400 mt-1">Comma-separated. Chips update as you type.</p>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">Industries of Interest</label>
              <input
                v-model="form.industries_text"
                type="text"
                placeholder="SaaS, Fintech, Developer Tools, AI"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
              />
              <div v-if="industryChips.length > 0" class="flex flex-wrap gap-1.5 mt-2">
                <span
                  v-for="ind in industryChips"
                  :key="ind"
                  class="rounded-full bg-purple-50 border border-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-600"
                >{{ ind }}</span>
              </div>
              <p class="text-xs text-gray-400 mt-1">Comma-separated.</p>
            </div>
          </div>
        </AppCard>

        <!-- ── Online Presence ─────────────────────────────────────────────── -->
        <AppCard>
          <div class="px-5 py-3.5 border-b border-gray-100">
            <h3 class="text-sm font-semibold text-gray-900">Online Presence</h3>
          </div>
          <div class="px-5 py-4 space-y-4">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">LinkedIn URL</label>
              <input
                v-model="form.linkedin_url"
                type="url"
                placeholder="https://linkedin.com/in/yourname"
                class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
              />
            </div>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">Portfolio URL</label>
                <input
                  v-model="form.portfolio_url"
                  type="url"
                  placeholder="https://yoursite.com"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-600 mb-1">GitHub URL</label>
                <input
                  v-model="form.github_url"
                  type="url"
                  placeholder="https://github.com/yourname"
                  class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 transition"
                />
              </div>
            </div>
          </div>
        </AppCard>

        <!-- ── Save ───────────────────────────────────────────────────────── -->
        <div class="flex items-center justify-between pb-2">
          <transition name="fade">
            <div v-if="saveResult === 'success'" class="flex items-center gap-1.5 text-sm text-emerald-600">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Profile saved
            </div>
            <div v-else-if="saveResult === 'error'" class="flex items-center gap-1.5 text-sm text-red-500">
              <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              Could not save — is the backend running?
            </div>
          </transition>
          <button
            :disabled="saving"
            class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition-colors shadow-sm"
            @click="save"
          >
            <svg v-if="saving" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
            {{ saving ? 'Saving…' : 'Save Profile' }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
