<script setup lang="ts">
const api = useApi()

const profileEmail = ref('')
const loadingProfile = ref(true)

onMounted(async () => {
  try {
    const p = await api.getProfile()
    profileEmail.value = p.email
  } catch {
    // non-critical
  } finally {
    loadingProfile.value = false
  }
})
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader title="Account" subtitle="Account management and authentication" />

    <div class="flex-1 p-6 space-y-6 max-w-2xl w-full mx-auto">
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
            <p class="text-sm font-medium text-gray-900">CorosDev Internal Build</p>
            <p class="text-xs text-gray-400 mt-0.5">
              <template v-if="loadingProfile">Loading…</template>
              <template v-else-if="profileEmail">{{ profileEmail }}</template>
              <template v-else>No email set — add one on the Profile page</template>
            </p>
          </div>
          <span class="flex-shrink-0 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">Dev mode</span>
        </div>
      </AppCard>

      <!-- Auth status -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Authentication</h3>
          <p class="text-xs text-gray-500 mt-0.5">Single-user local auth is available via the API.</p>
        </div>
        <div class="px-5 py-4 space-y-3.5">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-700">Register Account</p>
              <p class="text-xs text-gray-400">POST /api/auth/register</p>
            </div>
            <code class="text-xs bg-gray-100 px-2 py-1 rounded-md font-mono text-gray-600">Available</code>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-700">Login</p>
              <p class="text-xs text-gray-400">POST /api/auth/login — returns Bearer token</p>
            </div>
            <code class="text-xs bg-gray-100 px-2 py-1 rounded-md font-mono text-gray-600">Available</code>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-700">Session UI</p>
              <p class="text-xs text-gray-400">Login form and session persistence in the dashboard</p>
            </div>
            <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full font-medium">Phase 4</span>
          </div>
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-700">Multi-user support</p>
              <p class="text-xs text-gray-400">Per-user profiles, separate data stores</p>
            </div>
            <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full font-medium">Phase 4</span>
          </div>
        </div>
      </AppCard>

      <!-- Auth API quick reference -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Auth API Quick Reference</h3>
        </div>
        <div class="px-5 py-4 space-y-2 font-mono text-xs text-gray-600">
          <div class="flex items-center gap-2">
            <span class="text-emerald-600 font-semibold w-12 flex-shrink-0">POST</span>
            <span>/api/auth/register</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-emerald-600 font-semibold w-12 flex-shrink-0">POST</span>
            <span>/api/auth/login</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-blue-600 font-semibold w-12 flex-shrink-0">GET</span>
            <span>/api/auth/me</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-emerald-600 font-semibold w-12 flex-shrink-0">POST</span>
            <span>/api/auth/logout</span>
          </div>
        </div>
      </AppCard>

      <!-- Safety note -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Data &amp; Privacy</h3>
        </div>
        <div class="px-5 py-4 space-y-2.5">
          <div class="flex items-start gap-2.5 text-sm text-gray-600">
            <svg class="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            All account data is stored locally — no cloud sync
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
            <svg class="h-4 w-4 text-gray-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            No external auth provider (Google, LinkedIn, etc.) in this phase
          </div>
          <div class="mt-3 flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-100 px-3 py-2.5">
            <svg class="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <p class="text-xs text-amber-700">
              This is a development build. Never commit <code class="bg-amber-100 px-1 rounded font-mono">data/account.json</code> or <code class="bg-amber-100 px-1 rounded font-mono">.env</code> to version control.
            </p>
          </div>
        </div>
      </AppCard>
    </div>
  </div>
</template>
