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

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Daily Brief"
      :subtitle="brief?.date ?? ''"
    >
      <template #actions>
        <button
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
          :disabled="pending"
          @click="() => refresh()"
        >
          <svg class="h-3.5 w-3.5" :class="{ 'animate-spin': pending }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Refresh
        </button>
      </template>
    </PageHeader>

    <div class="flex-1 p-6 space-y-6 max-w-5xl w-full mx-auto">
      <LoadingSpinner v-if="pending" label="Loading brief…" />

      <template v-else-if="error">
        <AppCard>
          <ErrorState
            message="Could not reach the backend."
            :show-retry="true"
            @retry="() => refresh()"
          />
        </AppCard>
      </template>

      <template v-else-if="brief">
        <!-- Stats row -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-white border border-gray-200 rounded-xl shadow-card px-5 py-4 text-center">
            <p class="text-2xl font-bold text-blue-600 tabular-nums">{{ jobTotal }}</p>
            <p class="text-xs text-gray-500 mt-1 font-medium">Jobs</p>
          </div>
          <div class="bg-white border border-gray-200 rounded-xl shadow-card px-5 py-4 text-center">
            <p class="text-2xl font-bold text-violet-600 tabular-nums">{{ leadTotal }}</p>
            <p class="text-xs text-gray-500 mt-1 font-medium">Leads</p>
          </div>
          <div class="bg-white border border-gray-200 rounded-xl shadow-card px-5 py-4 text-center">
            <p class="text-2xl font-bold text-emerald-600 tabular-nums">{{ outreachGenerated }}</p>
            <p class="text-xs text-gray-500 mt-1 font-medium">Drafts</p>
          </div>
          <div class="bg-white border border-gray-200 rounded-xl shadow-card px-5 py-4 text-center">
            <p class="text-2xl font-bold text-amber-600 tabular-nums">{{ reviewPending }}</p>
            <p class="text-xs text-gray-500 mt-1 font-medium">Pending Review</p>
          </div>
        </div>

        <!-- Recommended Actions -->
        <AppCard>
          <div class="px-5 py-3.5 border-b border-gray-100">
            <h2 class="text-sm font-semibold text-gray-900">Recommended Actions</h2>
          </div>
          <div class="px-5 py-4">
            <p v-if="!brief.recommended_actions.length" class="text-sm text-gray-400">No actions suggested today.</p>
            <ol v-else class="space-y-3">
              <li v-for="(action, i) in brief.recommended_actions" :key="i" class="flex items-start gap-3">
                <span class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-50 text-xs font-semibold text-blue-600 mt-0.5">
                  {{ i + 1 }}
                </span>
                <span class="text-sm text-gray-700 leading-relaxed pt-0.5">{{ action }}</span>
              </li>
            </ol>
          </div>
        </AppCard>

        <!-- Approvable Drafts -->
        <AppCard v-if="brief.pending_drafts.approvable.length > 0">
          <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 class="text-sm font-semibold text-gray-900">Approvable Drafts</h2>
              <p class="text-xs text-gray-500 mt-0.5">Passed Quality Guard — ready for your review.</p>
            </div>
            <NuxtLink to="/review-queue" class="text-xs text-emerald-600 hover:text-emerald-700 font-medium transition-colors">
              Review →
            </NuxtLink>
          </div>
          <table class="app-table">
            <thead>
              <tr>
                <th>Subject / Company</th>
                <th class="hidden sm:table-cell">Type</th>
                <th>Quality</th>
                <th class="text-right hidden sm:table-cell">Personalization</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="draft in brief.pending_drafts.approvable.slice(0, 5)" :key="draft.id">
                <td>
                  <div class="font-medium text-gray-900 truncate max-w-xs">{{ draft.subject }}</div>
                  <div class="text-xs text-gray-400 truncate max-w-xs">{{ draft.company }}</div>
                </td>
                <td class="hidden sm:table-cell text-gray-500">{{ draft.outreach_type }}</td>
                <td><StatusBadge :status="draft.quality_status || 'pending'" /></td>
                <td class="text-right hidden sm:table-cell">
                  <span class="font-semibold tabular-nums text-emerald-600">{{ draft.personalization_score }}</span>
                  <span class="text-gray-400 text-xs">/100</span>
                </td>
              </tr>
            </tbody>
          </table>
        </AppCard>

        <!-- Blocked Drafts -->
        <AppCard v-if="brief.pending_drafts.blocked.length > 0">
          <div class="px-5 py-3.5 border-b border-red-100 bg-red-50">
            <h2 class="text-sm font-semibold text-red-800">Quality-Blocked Drafts</h2>
            <p class="text-xs text-red-600 mt-0.5">Did not pass Quality Guard — edit or regenerate before approving.</p>
          </div>
          <table class="app-table">
            <thead>
              <tr>
                <th>Subject / Company</th>
                <th>Quality</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="draft in brief.pending_drafts.blocked.slice(0, 5)" :key="draft.id">
                <td>
                  <div class="font-medium text-gray-900 truncate max-w-xs">{{ draft.subject }}</div>
                  <div class="text-xs text-gray-400">{{ draft.company }}</div>
                </td>
                <td><StatusBadge :status="draft.quality_status || 'pending'" /></td>
              </tr>
            </tbody>
          </table>
        </AppCard>

        <!-- Top Jobs -->
        <AppCard>
          <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-gray-900">Top Jobs</h2>
            <NuxtLink to="/jobs" class="text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors">View all →</NuxtLink>
          </div>
          <div v-if="!brief.top_jobs.length" class="py-10 text-center text-sm text-gray-400">
            No scored jobs yet. Run <code class="text-gray-600 bg-gray-100 px-1 rounded text-xs">--discover-jobs</code>.
          </div>
          <table v-else class="app-table">
            <thead>
              <tr>
                <th>Role</th>
                <th>Company</th>
                <th class="text-right">Score</th>
                <th>Label</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in brief.top_jobs" :key="job.id">
                <td class="font-medium text-gray-900 truncate max-w-xs">{{ job.title }}</td>
                <td class="text-gray-500 truncate max-w-xs">{{ job.company }}</td>
                <td class="text-right font-semibold tabular-nums text-blue-600">{{ job.job_score }}</td>
                <td><StatusBadge :status="job.score_label || '—'" /></td>
              </tr>
            </tbody>
          </table>
        </AppCard>

        <!-- Top Leads -->
        <AppCard>
          <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-gray-900">Top Leads</h2>
            <NuxtLink to="/leads" class="text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors">View all →</NuxtLink>
          </div>
          <div v-if="!brief.top_leads.length" class="py-10 text-center text-sm text-gray-400">
            No scored leads yet. Run <code class="text-gray-600 bg-gray-100 px-1 rounded text-xs">--discover-leads</code>.
          </div>
          <table v-else class="app-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Industry</th>
                <th class="text-right">Score</th>
                <th>Label</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lead in brief.top_leads" :key="lead.id">
                <td class="font-medium text-gray-900 truncate max-w-xs">{{ lead.company }}</td>
                <td class="text-gray-500">{{ lead.industry || '—' }}</td>
                <td class="text-right font-semibold tabular-nums text-violet-600">{{ lead.lead_score }}</td>
                <td><StatusBadge :status="lead.score_label || '—'" /></td>
              </tr>
            </tbody>
          </table>
        </AppCard>
      </template>
    </div>
  </div>
</template>
