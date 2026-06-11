<script setup lang="ts">
const safetyRules = [
  {
    title: 'No automatic email sending',
    description: 'The API has no /send endpoint. Emails can never be sent by the bot without explicit human action outside this system.',
  },
  {
    title: 'No automatic job applying',
    description: 'LinkedIn application and job submission paths are permanently removed. There is no apply-on-behalf feature.',
  },
  {
    title: 'No direct LinkedIn submission',
    description: 'DobryBot does not submit anything to LinkedIn automatically. LinkedIn actions must be performed by you, manually.',
  },
  {
    title: 'Quality Guard is mandatory',
    description: 'Drafts must pass Quality Guard checks (personalization, spam risk, AI-sounding score) before they can be approved. There is no bypass.',
  },
  {
    title: 'Human approval required',
    description: 'Every draft in the Review Queue must be explicitly approved or skipped by a human. No automatic bulk actions.',
  },
  {
    title: 'All risky actions are logged',
    description: 'Approvals, skips, and research flags are recorded with timestamps in the local database for full audit traceability.',
  },
]

const endpoints = [
  { path: 'POST /api/drafts/{id}/approve', exists: true,  note: 'Marks approved locally. Quality Guard enforced. Does not send.' },
  { path: 'POST /api/drafts/{id}/skip',    exists: true,  note: 'Removes from queue. Optional reason logged.' },
  { path: 'POST /api/drafts/{id}/needs-research', exists: true, note: 'Flags for additional research.' },
  { path: 'POST /send',         exists: false, note: 'Will never exist. Sending is a human action.' },
  { path: 'POST /send-approved', exists: false, note: 'Will never exist. No batch send path.' },
  { path: 'POST /apply',        exists: false, note: 'Will never exist. LinkedIn applying is human-only.' },
  { path: 'POST /force-approve', exists: false, note: 'Will never exist. Quality Guard cannot be bypassed.' },
]
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader title="Safety Center" subtitle="How DobryBot protects you from unintended actions" />

    <div class="flex-1 p-6 space-y-8 max-w-3xl w-full mx-auto">
      <!-- Primary statement -->
      <div class="rounded-2xl bg-gradient-to-br from-emerald-50 to-white border border-emerald-200 p-8 text-center shadow-card">
        <div class="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100 mx-auto mb-4">
          <svg class="h-7 w-7 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z" clip-rule="evenodd" />
          </svg>
        </div>
        <h2 class="text-xl font-bold text-gray-900">DobryBot never sends or applies automatically.</h2>
        <p class="mt-3 text-sm text-gray-600 leading-relaxed max-w-md mx-auto">
          Every outreach message and job application requires explicit human review and approval before anything leaves your machine. There are no hidden send paths.
        </p>
      </div>

      <!-- Safety Rules -->
      <div>
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Safety Rules</h3>
        <div class="space-y-2">
          <div
            v-for="rule in safetyRules"
            :key="rule.title"
            class="flex items-start gap-4 p-4 bg-white border border-gray-200 rounded-xl shadow-card"
          >
            <div class="flex-shrink-0 flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50">
              <svg class="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-gray-900">{{ rule.title }}</h4>
              <p class="text-sm text-gray-500 mt-0.5 leading-relaxed">{{ rule.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- What Approve means -->
      <div>
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">What "Approve" Really Means</h3>
        <AppCard>
          <div class="px-5 py-4 space-y-4">
            <div class="flex items-start gap-3">
              <span class="flex-shrink-0 mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 text-xs font-bold ring-1 ring-inset ring-emerald-200">✓</span>
              <p class="text-sm text-gray-700">
                <strong class="text-gray-900">Approve</strong> saves a human-approved flag in the local database. The draft is marked ready for your manual delivery.
              </p>
            </div>
            <div class="flex items-start gap-3">
              <span class="flex-shrink-0 mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-red-50 text-red-600 text-xs font-bold ring-1 ring-inset ring-red-200">✕</span>
              <p class="text-sm text-gray-700">
                <strong class="text-gray-900">Approve does NOT send</strong> any email, LinkedIn message, or job application. There is no send path in this API.
              </p>
            </div>
            <div class="flex items-start gap-3">
              <span class="flex-shrink-0 mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-amber-50 text-amber-600 text-xs font-bold ring-1 ring-inset ring-amber-200">!</span>
              <p class="text-sm text-gray-700">
                <strong class="text-gray-900">Quality Guard is always enforced.</strong> Approving a draft that has not passed Quality Guard returns an error — there is no force-approve option.
              </p>
            </div>
          </div>
        </AppCard>
      </div>

      <!-- API Safety Guarantees -->
      <div>
        <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">API Safety Guarantees</h3>
        <AppCard>
          <table class="app-table">
            <thead>
              <tr>
                <th>Endpoint</th>
                <th>Exists?</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ep in endpoints" :key="ep.path">
                <td class="font-mono text-xs text-gray-600">{{ ep.path }}</td>
                <td>
                  <span class="text-xs font-semibold" :class="ep.exists ? 'text-emerald-600' : 'text-red-500'">
                    {{ ep.exists ? 'Yes' : 'No — never' }}
                  </span>
                </td>
                <td class="text-xs text-gray-500">{{ ep.note }}</td>
              </tr>
            </tbody>
          </table>
        </AppCard>
      </div>
    </div>
  </div>
</template>
