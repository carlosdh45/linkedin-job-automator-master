<template>
  <div class="flex-1 overflow-y-auto">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-slate-950/80 backdrop-blur border-b border-slate-800 px-8 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-100">Daily Brief</h1>
        <p v-if="brief" class="text-xs text-slate-500 mt-0.5">{{ brief.date }}</p>
      </div>
      <button
        class="px-3 py-1.5 text-xs font-medium text-slate-400 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
        @click="() => refresh()"
      >
        Refresh
      </button>
    </div>

    <div class="px-8 py-6 space-y-6 max-w-5xl mx-auto">
      <LoadingSpinner v-if="pending" label="Loading brief…" />

      <template v-else-if="error">
        <div class="rounded-xl border border-red-900/50 bg-red-950/30 p-6 text-center">
          <p class="text-red-400 font-medium">Could not reach the backend.</p>
          <button class="mt-4 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-sm text-slate-200 rounded-lg" @click="() => refresh()">
            Retry
          </button>
        </div>
      </template>

      <template v-else-if="brief">
        <!-- Stats row -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center">
            <p class="text-2xl font-bold text-blue-400 tabular-nums">{{ jobTotal }}</p>
            <p class="text-xs text-slate-500 mt-1">Jobs</p>
          </div>
          <div class="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center">
            <p class="text-2xl font-bold text-violet-400 tabular-nums">{{ leadTotal }}</p>
            <p class="text-xs text-slate-500 mt-1">Leads</p>
          </div>
          <div class="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center">
            <p class="text-2xl font-bold text-emerald-400 tabular-nums">{{ outreachGenerated }}</p>
            <p class="text-xs text-slate-500 mt-1">Drafts</p>
          </div>
          <div class="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center">
            <p class="text-2xl font-bold text-amber-400 tabular-nums">{{ reviewPending }}</p>
            <p class="text-xs text-slate-500 mt-1">Pending Review</p>
          </div>
        </div>

        <!-- Recommended actions -->
        <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-700">
            <h2 class="text-sm font-semibold text-slate-200">Recommended Actions</h2>
          </div>
          <ul class="px-5 py-4 space-y-3">
            <li
              v-for="(action, i) in brief.recommended_actions"
              :key="i"
              class="flex items-start gap-3"
            >
              <span class="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600/20 text-blue-400 flex items-center justify-center text-xs font-bold">
                {{ i + 1 }}
              </span>
              <span class="text-sm text-slate-300 leading-relaxed pt-0.5">{{ action }}</span>
            </li>
          </ul>
        </div>

        <!-- Approvable drafts -->
        <div v-if="brief.pending_drafts.approvable.length > 0" class="bg-slate-800 border border-emerald-900/40 rounded-xl overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-700 flex items-center justify-between">
            <div>
              <h2 class="text-sm font-semibold text-slate-200">Approvable Drafts</h2>
              <p class="text-xs text-slate-500 mt-0.5">These have passed Quality Guard and are ready for your review.</p>
            </div>
            <NuxtLink to="/review-queue" class="text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
              Review →
            </NuxtLink>
          </div>
          <ul class="divide-y divide-slate-700/50">
            <li
              v-for="draft in brief.pending_drafts.approvable.slice(0, 5)"
              :key="draft.id"
              class="px-5 py-3 flex items-center gap-4"
            >
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-slate-200 truncate">{{ draft.subject }}</p>
                <p class="text-xs text-slate-500 mt-0.5">{{ draft.company }} · {{ draft.outreach_type }}</p>
              </div>
              <div class="flex-shrink-0 flex items-center gap-2">
                <StatusBadge :status="draft.quality_status || 'pending'" />
                <span class="text-xs text-slate-500">P:{{ draft.personalization_score }}</span>
              </div>
            </li>
          </ul>
        </div>

        <!-- Blocked drafts -->
        <div v-if="brief.pending_drafts.blocked.length > 0" class="bg-slate-800 border border-red-900/30 rounded-xl overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-700">
            <h2 class="text-sm font-semibold text-slate-200">Quality-Blocked Drafts</h2>
            <p class="text-xs text-slate-500 mt-0.5">These did not pass Quality Guard. Edit or regenerate before approving.</p>
          </div>
          <ul class="divide-y divide-slate-700/50">
            <li
              v-for="draft in brief.pending_drafts.blocked.slice(0, 5)"
              :key="draft.id"
              class="px-5 py-3 flex items-center gap-4"
            >
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-slate-300 truncate">{{ draft.subject }}</p>
                <p class="text-xs text-slate-500 mt-0.5">{{ draft.company }}</p>
              </div>
              <StatusBadge :status="draft.quality_status || 'pending'" />
            </li>
          </ul>
        </div>

        <!-- Top Jobs -->
        <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-700 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-slate-200">Top Jobs</h2>
            <NuxtLink to="/jobs" class="text-xs text-blue-400 hover:text-blue-300">View all →</NuxtLink>
          </div>
          <div v-if="brief.top_jobs.length === 0" class="px-5 py-8 text-center text-sm text-slate-500">
            No scored jobs yet. Run <code class="text-slate-400">--discover-jobs</code>.
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-slate-700/50">
                  <th class="px-5 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Role</th>
                  <th class="px-5 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Company</th>
                  <th class="px-5 py-2.5 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Score</th>
                  <th class="px-5 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Label</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-700/30">
                <tr
                  v-for="job in brief.top_jobs"
                  :key="job.id"
                  class="hover:bg-slate-700/20 transition-colors"
                >
                  <td class="px-5 py-3 text-slate-200 font-medium truncate max-w-xs">{{ job.title }}</td>
                  <td class="px-5 py-3 text-slate-400 truncate max-w-xs">{{ job.company }}</td>
                  <td class="px-5 py-3 text-right text-blue-400 font-semibold tabular-nums">{{ job.job_score }}</td>
                  <td class="px-5 py-3"><StatusBadge :status="job.score_label || '—'" /></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Top Leads -->
        <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-700 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-slate-200">Top Leads</h2>
            <NuxtLink to="/leads" class="text-xs text-blue-400 hover:text-blue-300">View all →</NuxtLink>
          </div>
          <div v-if="brief.top_leads.length === 0" class="px-5 py-8 text-center text-sm text-slate-500">
            No scored leads yet. Run <code class="text-slate-400">--discover-leads</code>.
          </div>
          <div v-else class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-slate-700/50">
                  <th class="px-5 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Company</th>
                  <th class="px-5 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Industry</th>
                  <th class="px-5 py-2.5 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Score</th>
                  <th class="px-5 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Label</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-700/30">
                <tr
                  v-for="lead in brief.top_leads"
                  :key="lead.id"
                  class="hover:bg-slate-700/20 transition-colors"
                >
                  <td class="px-5 py-3 text-slate-200 font-medium truncate max-w-xs">{{ lead.company }}</td>
                  <td class="px-5 py-3 text-slate-400">{{ lead.industry || '—' }}</td>
                  <td class="px-5 py-3 text-right text-violet-400 font-semibold tabular-nums">{{ lead.lead_score }}</td>
                  <td class="px-5 py-3"><StatusBadge :status="lead.score_label || '—'" /></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { statJobTotal, statLeadTotal } from '~/types'

const api = useApi()
const { data: brief, pending, error, refresh } = await useAsyncData('daily-brief', () => api.getDailyBrief())

const stats = computed(() => brief.value?.stats ?? {})
const jobTotal = computed(() => statJobTotal(stats.value))
const leadTotal = computed(() => statLeadTotal(stats.value))
const outreachGenerated = computed(() => stats.value.outreach_generated ?? 0)
const reviewPending = computed(() => stats.value.outreach_pending_review ?? 0)
</script>
