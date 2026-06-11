<template>
  <div class="flex-1 overflow-y-auto">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-slate-950/80 backdrop-blur border-b border-slate-800 px-8 py-4">
      <h1 class="text-xl font-bold text-slate-100">Safety Center</h1>
      <p class="text-xs text-slate-500 mt-0.5">How DobryBot protects you from unintended actions</p>
    </div>

    <div class="px-8 py-8 space-y-8 max-w-3xl mx-auto">
      <!-- Primary safety statement -->
      <div class="rounded-2xl bg-gradient-to-br from-emerald-950/80 to-slate-900 border border-emerald-800/50 p-8 text-center">
        <div class="w-16 h-16 rounded-full bg-emerald-900/50 flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z" clip-rule="evenodd" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-emerald-300">DobryBot never sends or applies automatically.</h2>
        <p class="mt-3 text-slate-400 text-sm leading-relaxed max-w-md mx-auto">
          Every outreach message and job application requires explicit human review and approval before anything leaves your machine. There are no hidden send paths.
        </p>
      </div>

      <!-- Safety rules grid -->
      <div>
        <h3 class="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Safety Rules</h3>
        <div class="space-y-3">
          <div
            v-for="rule in safetyRules"
            :key="rule.title"
            class="flex items-start gap-4 p-4 bg-slate-800 border border-slate-700 rounded-xl"
          >
            <div class="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-900/50 flex items-center justify-center">
              <svg class="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-slate-200">{{ rule.title }}</h4>
              <p class="text-sm text-slate-500 mt-0.5 leading-relaxed">{{ rule.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- What Approve means -->
      <div>
        <h3 class="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">What "Approve" Really Means</h3>
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
          <div class="flex items-start gap-3">
            <span class="flex-shrink-0 mt-0.5 w-5 h-5 rounded-full bg-emerald-900/50 text-emerald-400 flex items-center justify-center text-xs font-bold">✓</span>
            <p class="text-sm text-slate-300">
              <strong class="text-slate-200">Approve</strong> saves a human-approved flag in the local database. The draft is marked ready for your manual delivery.
            </p>
          </div>
          <div class="flex items-start gap-3">
            <span class="flex-shrink-0 mt-0.5 w-5 h-5 rounded-full bg-red-900/50 text-red-400 flex items-center justify-center text-xs">✕</span>
            <p class="text-sm text-slate-300">
              <strong class="text-slate-200">Approve does NOT send</strong> any email, LinkedIn message, or job application. There is no send path in this API.
            </p>
          </div>
          <div class="flex items-start gap-3">
            <span class="flex-shrink-0 mt-0.5 w-5 h-5 rounded-full bg-amber-900/50 text-amber-400 flex items-center justify-center text-xs font-bold">!</span>
            <p class="text-sm text-slate-300">
              <strong class="text-slate-200">Quality Guard is always enforced.</strong> Approving a draft that has not passed Quality Guard returns an error — there is no force-approve option.
            </p>
          </div>
        </div>
      </div>

      <!-- API safety -->
      <div>
        <h3 class="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">API Safety Guarantees</h3>
        <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-700">
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500">Endpoint</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500">Exists?</th>
                <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500">Notes</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-700/40">
              <tr v-for="ep in endpoints" :key="ep.path" class="hover:bg-slate-700/20">
                <td class="px-5 py-3 font-mono text-xs text-slate-400">{{ ep.path }}</td>
                <td class="px-5 py-3">
                  <span :class="ep.exists ? 'text-emerald-400' : 'text-red-400'" class="text-xs font-semibold">
                    {{ ep.exists ? 'Yes' : 'No — never' }}
                  </span>
                </td>
                <td class="px-5 py-3 text-xs text-slate-500">{{ ep.note }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

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
  { path: 'POST /api/drafts/{id}/approve', exists: true, note: 'Marks approved locally. Quality Guard enforced. Does not send.' },
  { path: 'POST /api/drafts/{id}/skip', exists: true, note: 'Removes from queue. Optional reason logged.' },
  { path: 'POST /api/drafts/{id}/needs-research', exists: true, note: 'Flags for additional research.' },
  { path: 'POST /send', exists: false, note: 'Will never exist. Sending is a human action.' },
  { path: 'POST /send-approved', exists: false, note: 'Will never exist. No batch send path.' },
  { path: 'POST /apply', exists: false, note: 'Will never exist. LinkedIn applying is human-only.' },
  { path: 'POST /force-approve', exists: false, note: 'Will never exist. Quality Guard cannot be bypassed.' },
]
</script>
