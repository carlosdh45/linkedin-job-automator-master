<script setup lang="ts">
const api = useApi()

const profileEmail = ref('')
const profileName = ref('')
const loadingProfile = ref(true)
const authStatus = ref<'active' | 'error' | 'checking'>('checking')

onMounted(async () => {
  try {
    const p = await api.getProfile()
    profileEmail.value = p.email
    profileName.value = p.full_name
  } catch {
    // non-critical
  } finally {
    loadingProfile.value = false
  }

  try {
    const h = await api.getHealth()
    authStatus.value = h.status === 'ok' ? 'active' : 'error'
  } catch {
    authStatus.value = 'error'
  }
})

type FeatureRow = { label: string; detail: string; status: 'ready' | 'dev' | 'upcoming' }

const featureRows: FeatureRow[] = [
  { label: 'Local profile storage', detail: 'data/profile.json — excluded from git', status: 'ready' },
  { label: 'CV upload (local)', detail: 'Stored in uploads/ — excluded from git', status: 'ready' },
  { label: 'Resume Studio', detail: 'Structured profile + local draft generation', status: 'ready' },
  { label: 'Auth API (register / login / logout)', detail: 'POST /api/auth/register · POST /api/auth/login', status: 'ready' },
  { label: 'Password hashing', detail: 'PBKDF2-HMAC-SHA256 · 260,000 iterations', status: 'ready' },
  { label: 'Quality Guard enforcement', detail: 'Drafts must pass before any action is allowed', status: 'ready' },
  { label: 'Session UI (login form)', detail: 'Persistent login sessions in the dashboard', status: 'dev' },
  { label: 'PDF export', detail: 'Export resume as a formatted PDF', status: 'upcoming' },
  { label: 'AI resume parsing', detail: 'Extract structured data from uploaded CV', status: 'upcoming' },
  { label: 'Multi-user support', detail: 'Per-user isolated data stores', status: 'upcoming' },
  { label: 'External auth provider', detail: 'Google or GitHub OAuth', status: 'upcoming' },
  { label: 'Production deployment', detail: 'Cloud-hosted with persistent auth', status: 'upcoming' },
]
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader title="Account" subtitle="Authentication, privacy, and system status" />

    <div class="flex-1 p-6 space-y-6 max-w-2xl w-full mx-auto">

      <!-- Dev build warning -->
      <div class="flex items-start gap-3 rounded-xl bg-amber-50 border border-amber-200 px-4 py-3.5">
        <svg class="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
        <div>
          <p class="text-sm font-semibold text-amber-800">Development Build</p>
          <p class="text-xs text-amber-700 mt-0.5">
            This is a local development instance. Never commit <code class="bg-amber-100 px-1 rounded font-mono text-[10px]">data/account.json</code>,
            <code class="bg-amber-100 px-1 rounded font-mono text-[10px]">.env</code>, or any uploaded files to version control.
            Sessions are in-memory only and reset on server restart.
          </p>
        </div>
      </div>

      <!-- Current identity card -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Current Session</h3>
        </div>
        <div class="px-5 py-4 flex items-center gap-4">
          <div class="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
            <svg class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold text-gray-900">
              <template v-if="loadingProfile">Loading…</template>
              <template v-else-if="profileName">{{ profileName }}</template>
              <template v-else>CorosDev Internal Build</template>
            </p>
            <p class="text-xs text-gray-400 mt-0.5">
              <template v-if="loadingProfile">…</template>
              <template v-else-if="profileEmail">{{ profileEmail }}</template>
              <template v-else>No email set — add one on the Profile page</template>
            </p>
          </div>
          <span class="flex-shrink-0 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">Dev mode</span>
        </div>
      </AppCard>

      <!-- Auth status -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 class="text-sm font-semibold text-gray-900">Authentication</h3>
            <p class="text-xs text-gray-500 mt-0.5">Single-user local auth — API available, UI in next phase</p>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="h-2 w-2 rounded-full flex-shrink-0" :class="{
              'bg-emerald-500': authStatus === 'active',
              'bg-red-400': authStatus === 'error',
              'bg-amber-400 animate-pulse': authStatus === 'checking',
            }" />
            <span class="text-xs font-medium" :class="{
              'text-emerald-600': authStatus === 'active',
              'text-red-500': authStatus === 'error',
              'text-amber-500': authStatus === 'checking',
            }">
              <template v-if="authStatus === 'active'">Backend online</template>
              <template v-else-if="authStatus === 'error'">Backend offline</template>
              <template v-else>Checking…</template>
            </span>
          </div>
        </div>
        <div class="px-5 py-4 space-y-3.5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-700">Register Account</p>
              <p class="text-xs text-gray-400 font-mono">POST /api/auth/register</p>
            </div>
            <span class="text-xs bg-emerald-50 text-emerald-700 border border-emerald-100 px-2 py-0.5 rounded-full font-medium">Available</span>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-700">Login — returns Bearer token</p>
              <p class="text-xs text-gray-400 font-mono">POST /api/auth/login</p>
            </div>
            <span class="text-xs bg-emerald-50 text-emerald-700 border border-emerald-100 px-2 py-0.5 rounded-full font-medium">Available</span>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-700">Session UI &amp; Login Form</p>
              <p class="text-xs text-gray-400">Persistent login sessions in the dashboard</p>
            </div>
            <span class="text-xs bg-blue-50 text-blue-600 border border-blue-100 px-2 py-0.5 rounded-full font-medium">Phase 5</span>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-700">Multi-user support</p>
              <p class="text-xs text-gray-400">Per-user isolated profiles and data stores</p>
            </div>
            <span class="text-xs bg-blue-50 text-blue-600 border border-blue-100 px-2 py-0.5 rounded-full font-medium">Phase 5</span>
          </div>
        </div>
      </AppCard>

      <!-- Auth API quick reference -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Auth API Reference</h3>
        </div>
        <div class="px-5 py-4 space-y-2 font-mono text-xs text-gray-600 bg-gray-50/50">
          <div v-for="(row, i) in [
            { method: 'POST', path: '/api/auth/register', note: 'email + password + full_name' },
            { method: 'POST', path: '/api/auth/login', note: 'returns token' },
            { method: 'GET',  path: '/api/auth/me', note: 'Bearer token required' },
            { method: 'POST', path: '/api/auth/logout', note: 'invalidates token' },
          ]" :key="i" class="flex items-center gap-3">
            <span class="font-semibold w-10 flex-shrink-0" :class="row.method === 'GET' ? 'text-blue-600' : 'text-emerald-600'">{{ row.method }}</span>
            <span class="flex-1 text-gray-700">{{ row.path }}</span>
            <span class="text-gray-400 text-[10px]">{{ row.note }}</span>
          </div>
        </div>
      </AppCard>

      <!-- Production readiness table -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Feature Status</h3>
          <p class="text-xs text-gray-500 mt-0.5">What is production-ready vs development-only vs upcoming</p>
        </div>
        <div class="divide-y divide-gray-50">
          <div
            v-for="row in featureRows"
            :key="row.label"
            class="flex items-start gap-3 px-5 py-3"
          >
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-800">{{ row.label }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ row.detail }}</p>
            </div>
            <span
              class="flex-shrink-0 text-xs px-2 py-0.5 rounded-full font-medium border"
              :class="{
                'bg-emerald-50 text-emerald-700 border-emerald-100': row.status === 'ready',
                'bg-amber-50 text-amber-600 border-amber-100': row.status === 'dev',
                'bg-gray-50 text-gray-400 border-gray-100': row.status === 'upcoming',
              }"
            >
              <template v-if="row.status === 'ready'">Production-ready</template>
              <template v-else-if="row.status === 'dev'">Dev only</template>
              <template v-else>Upcoming</template>
            </span>
          </div>
        </div>
      </AppCard>

      <!-- Data & Privacy -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Data &amp; Privacy Summary</h3>
        </div>
        <div class="px-5 py-4 space-y-2.5">
          <div class="flex items-start gap-2.5 text-sm text-gray-600">
            <svg class="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            All profile, resume, and account data stored locally — no cloud sync
          </div>
          <div class="flex items-start gap-2.5 text-sm text-gray-600">
            <svg class="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            Passwords hashed with PBKDF2-HMAC-SHA256 (260,000 iterations)
          </div>
          <div class="flex items-start gap-2.5 text-sm text-gray-600">
            <svg class="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            Sessions are in-memory only — reset on server restart
          </div>
          <div class="flex items-start gap-2.5 text-sm text-gray-600">
            <svg class="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            DobryBot never sends or applies automatically — Quality Guard enforced on all actions
          </div>
          <div class="flex items-start gap-2.5 text-sm text-gray-600">
            <svg class="h-4 w-4 text-gray-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            No external auth provider, AI API, or cloud service in this phase
          </div>
        </div>
      </AppCard>

    </div>
  </div>
</template>
