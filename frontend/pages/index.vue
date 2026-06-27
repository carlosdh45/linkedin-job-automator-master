<script setup lang="ts">
import { statJobTotal, statJobScored, statLeadTotal, statLeadScored } from '~/types'
import type { BDCompany, BDRecommendation } from '~/types'

const api = useApi()
const showSeedConfirm = ref(false)
const refreshingRecs = ref(false)
const dismissing = ref<string | null>(null)

const { data: brief, pending, error, refresh } = await useAsyncData('dashboard', () => api.getDailyBrief())
const { data: bdStats, refresh: refreshBD } = await useAsyncData('bd-dashboard', () => api.getBDDashboard(), {
  default: () => null,
})
const { data: bdCompanies } = await useAsyncData<BDCompany[]>('bd-companies-dash', () => api.getBDCompanies(), {
  default: () => [],
})
const { data: recommendations, refresh: refreshRecs } = await useAsyncData<BDRecommendation[]>(
  'bd-recommendations-dash',
  () => api.getBDRecommendations({ status: 'new', limit: 10 }),
  { default: () => [] }
)

const today = computed(() =>
  brief.value?.date
    ? new Date(brief.value.date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
    : new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
)

const stats = computed(() => brief.value?.stats ?? {})
const opportunityTotal = computed(() => statJobTotal(stats.value))
const opportunityQualified = computed(() => statJobScored(stats.value))
const prospectTotal = computed(() => statLeadTotal(stats.value))
const prospectSignaled = computed(() => statLeadScored(stats.value))
const draftsGenerated = computed(() => stats.value.outreach_generated ?? 0)
const reviewPending = computed(() => brief.value?.pending_drafts.total ?? 0)
const approvable = computed(() => brief.value?.pending_drafts.approvable.length ?? 0)

// BD real data
const bdQualifiedOpps = computed(() => bdStats.value?.qualified_opportunities ?? 0)
const bdHighSignalProspects = computed(() => bdStats.value?.high_signal_prospects ?? 0)
const bdDraftsForReview = computed(() => bdStats.value?.drafts_for_review ?? 0)
const bdRecommendedActions = computed(() => bdStats.value?.recommended_actions ?? [])
const bdPipelineSnapshot = computed(() => bdStats.value?.pipeline_snapshot ?? [])

const companiesWithPainPoints = computed(() =>
  (bdCompanies.value ?? []).filter(c => c.pain_points.length > 0).slice(0, 6)
)
const hasRealBDData = computed(() =>
  (bdCompanies.value?.length ?? 0) > 0 || bdQualifiedOpps.value > 0
)

const stageColorMap: Record<string, string> = {
  identified: 'bg-gray-100 text-gray-600',
  researched: 'bg-blue-50 text-blue-700',
  qualified: 'bg-violet-50 text-violet-700',
  outreach_ready: 'bg-indigo-50 text-indigo-700',
  in_conversation: 'bg-amber-50 text-amber-700',
  proposal: 'bg-orange-50 text-orange-700',
  engaged: 'bg-amber-50 text-amber-700',
  deal_packet: 'bg-orange-50 text-orange-700',
  active: 'bg-emerald-50 text-emerald-700',
  won: 'bg-emerald-100 text-emerald-800',
  lost: 'bg-red-50 text-red-600',
}

const stageLabel: Record<string, string> = {
  identified: 'Identified',
  researched: 'Researched',
  qualified: 'Qualified',
  outreach_ready: 'Outreach Ready',
  in_conversation: 'In Conversation',
  proposal: 'Proposal',
  engaged: 'Engaged',
  deal_packet: 'Deal Packet',
  active: 'Active',
  won: 'Won',
  lost: 'Lost',
}

const priorityConfig: Record<string, { label: string; color: string }> = {
  critical: { label: 'Critical', color: 'bg-red-50 text-red-700 ring-red-200' },
  high:     { label: 'High',     color: 'bg-orange-50 text-orange-700 ring-orange-200' },
  medium:   { label: 'Medium',   color: 'bg-amber-50 text-amber-700 ring-amber-200' },
  low:      { label: 'Low',      color: 'bg-gray-100 text-gray-500 ring-gray-200' },
}

const topRecommendations = computed(() =>
  (recommendations.value ?? []).filter(r => r.status === 'new').slice(0, 5)
)

async function seedDemo() {
  try {
    await api.seedDemo()
    await refresh()
    await refreshBD()
  } catch {
    // non-critical
  }
}

async function runRefresh() {
  refreshingRecs.value = true
  try {
    await api.refreshBDRecommendations()
    await Promise.all([refreshBD(), refreshRecs()])
  } catch {
    // non-critical
  } finally {
    refreshingRecs.value = false
  }
}

async function dismissRec(id: string) {
  dismissing.value = id
  try {
    await api.dismissBDRecommendation(id)
    await refreshRecs()
  } catch {
    // non-critical
  } finally {
    dismissing.value = null
  }
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader title="Command Center" :subtitle="today">
      <template #actions>
        <button
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          @click="showSeedConfirm = true"
        >
          Load Demo Data
        </button>
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

    <div class="flex-1 p-6 space-y-6 max-w-7xl w-full mx-auto">
      <!-- Hero value prop + safety strip -->
      <div class="rounded-xl border border-gray-200 bg-white px-5 py-4 flex items-start justify-between gap-6">
        <div>
          <p class="text-base font-semibold text-gray-900 leading-snug">Less noise. More qualified opportunities.</p>
          <p class="text-sm text-gray-500 mt-1 leading-relaxed">DobryBot surfaces buying signals, scores your ICP, and prepares deal intelligence for human-led outreach — so you reach the right prospect with the right context before you ever say hello.</p>
        </div>
        <div class="hidden xl:flex flex-col items-end gap-2 flex-shrink-0 text-right">
          <span class="inline-flex items-center gap-1.5 text-xs text-gray-400"><span class="h-1.5 w-1.5 rounded-full bg-emerald-400 flex-shrink-0"></span>100% local — no external APIs</span>
          <span class="inline-flex items-center gap-1.5 text-xs text-gray-400"><span class="h-1.5 w-1.5 rounded-full bg-emerald-400 flex-shrink-0"></span>No AI calls — rule-based scoring</span>
          <span class="inline-flex items-center gap-1.5 text-xs text-gray-400"><span class="h-1.5 w-1.5 rounded-full bg-emerald-400 flex-shrink-0"></span>Human approval required — never auto-sends</span>
        </div>
      </div>

      <LoadingSpinner v-if="pending" label="Loading command center…" />

      <template v-else-if="error">
        <AppCard>
          <ErrorState
            message="Could not reach the backend. Make sure uvicorn is running on port 8000."
            :show-retry="true"
            @retry="() => refresh()"
          />
        </AppCard>
      </template>

      <template v-else-if="brief">
        <!-- Stats -->
        <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard
            title="Qualified Opportunities"
            :value="bdQualifiedOpps || opportunityQualified"
            :sub="bdQualifiedOpps ? 'BD pipeline' : `${opportunityTotal} tracked total`"
            variant="blue"
            icon="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.562.562 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
          />
          <StatCard
            title="High Signal Prospects"
            :value="bdHighSignalProspects || prospectSignaled"
            :sub="bdHighSignalProspects ? 'BD prospects' : `${prospectTotal} prospects total`"
            variant="violet"
            icon="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
          />
          <StatCard
            title="BD Drafts"
            :value="bdDraftsForReview || draftsGenerated"
            :sub="bdDraftsForReview ? 'pending manual review' : `${reviewPending} pending review`"
            variant="green"
            icon="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
          />
          <StatCard
            title="Awaiting Review"
            :value="reviewPending + bdDraftsForReview"
            :sub="bdDraftsForReview ? `${bdDraftsForReview} BD · ${reviewPending} job` : (reviewPending === 1 ? '1 draft needs your approval' : `${approvable} approvable now`)"
            variant="amber"
            icon="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
          />
        </div>

        <!-- Main content grid: 2/3 + 1/3 -->
        <div class="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <!-- Left col (2/3) -->
          <div class="xl:col-span-2 space-y-6">

            <!-- Qualified Opportunities -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h2 class="text-sm font-semibold text-gray-900">Qualified Opportunities</h2>
                  <p class="text-xs text-gray-400 mt-0.5">Highest-scoring deals ready to engage</p>
                </div>
                <NuxtLink to="/opportunities" class="text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors">View all →</NuxtLink>
              </div>
              <div v-if="!brief.top_jobs.length" class="py-10 text-center">
                <p class="text-sm text-gray-400">No qualified opportunities yet.</p>
                <p class="text-xs text-gray-300 mt-1">Load demo data to see the full workflow, or add companies and prospects via the BD pages.</p>
              </div>
              <table v-else class="app-table">
                <thead>
                  <tr>
                    <th>Company / Role</th>
                    <th class="hidden sm:table-cell">Location</th>
                    <th class="text-right">Score</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="job in brief.top_jobs.slice(0, 6)" :key="job.id">
                    <td>
                      <div class="font-medium text-gray-900 truncate max-w-xs">{{ job.company }}</div>
                      <div class="text-xs text-gray-400 truncate max-w-xs">{{ job.title }}</div>
                    </td>
                    <td class="hidden sm:table-cell text-gray-500">{{ job.location || '—' }}</td>
                    <td class="text-right font-semibold tabular-nums text-blue-600">{{ job.job_score }}</td>
                    <td><StatusBadge :status="job.score_label || job.status" /></td>
                  </tr>
                </tbody>
              </table>
            </AppCard>

            <!-- High Signal Prospects -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h2 class="text-sm font-semibold text-gray-900">High Signal Prospects</h2>
                  <p class="text-xs text-gray-400 mt-0.5">Contacts with the strongest buying signals</p>
                </div>
                <NuxtLink to="/prospects" class="text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors">View all →</NuxtLink>
              </div>
              <div v-if="!brief.top_leads.length" class="py-10 text-center">
                <p class="text-sm text-gray-400">No high signal prospects yet.</p>
                <p class="text-xs text-gray-300 mt-1">Add prospects under Intelligence → Prospects, or load demo data to explore the workflow.</p>
              </div>
              <table v-else class="app-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th class="hidden md:table-cell">Industry</th>
                    <th class="text-right">Score</th>
                    <th>Signal</th>
                    <th class="hidden lg:table-cell text-center">Pain Points</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="lead in brief.top_leads.slice(0, 6)" :key="lead.id">
                    <td>
                      <div class="font-medium text-gray-900 truncate max-w-xs">{{ lead.company }}</div>
                      <div class="text-xs text-gray-400 truncate max-w-xs">{{ lead.contact_name || lead.domain }}</div>
                    </td>
                    <td class="hidden md:table-cell text-gray-500">{{ lead.industry || '—' }}</td>
                    <td class="text-right font-semibold tabular-nums text-violet-600">{{ lead.lead_score }}</td>
                    <td><StatusBadge :status="lead.score_label || lead.status" /></td>
                    <td class="text-center hidden lg:table-cell">
                      <span
                        v-if="lead.pain_points?.length"
                        class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-rose-50 text-rose-600 ring-1 ring-inset ring-rose-100"
                      >
                        {{ lead.pain_points.length }}
                      </span>
                      <span v-else class="text-gray-300 text-xs">—</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </AppCard>

            <!-- Companies with Pain Points -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h2 class="text-sm font-semibold text-gray-900">Companies with Pain Points</h2>
                  <p class="text-xs text-gray-400 mt-0.5">Target companies with detected operational pain — best outreach candidates</p>
                </div>
                <NuxtLink to="/companies" class="text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors">View all →</NuxtLink>
              </div>
              <div v-if="!companiesWithPainPoints.length" class="px-5 py-8 text-center">
                <p class="text-sm text-gray-400">No companies with detected pain points yet.</p>
                <p class="text-xs text-gray-300 mt-1">Load demo data or add companies with tagged pain points to surface them here.</p>
              </div>
              <table v-else class="app-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th class="hidden md:table-cell">Industry</th>
                    <th>Top Pain Points</th>
                    <th class="text-right">Score</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="co in companiesWithPainPoints" :key="co.id">
                    <td>
                      <div class="font-medium text-gray-900">{{ co.name }}</div>
                    </td>
                    <td class="hidden md:table-cell text-gray-500">{{ co.industry || '—' }}</td>
                    <td>
                      <div class="flex flex-wrap gap-1">
                        <span
                          v-for="pp in co.pain_points.slice(0, 3)"
                          :key="pp"
                          class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium bg-rose-50 text-rose-600 ring-1 ring-inset ring-rose-100"
                        >
                          {{ pp }}
                        </span>
                      </div>
                    </td>
                    <td class="text-right font-semibold tabular-nums text-blue-600">{{ co.opportunity_score }}</td>
                  </tr>
                </tbody>
              </table>
            </AppCard>
          </div>

          <!-- Right col (1/3) -->
          <div class="space-y-6">

            <!-- Recommended Actions (BD-first if available) -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100">
                <h2 class="text-sm font-semibold text-gray-900">Recommended Next Actions</h2>
                <p class="text-xs text-gray-400 mt-0.5">Highest-priority moves for today</p>
              </div>
              <div class="px-5 py-4">
                <template v-if="bdRecommendedActions.length">
                  <ol class="space-y-3">
                    <li v-for="(action, i) in bdRecommendedActions" :key="i" class="flex items-start gap-3">
                      <span class="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-violet-50 text-xs font-semibold text-violet-600 mt-0.5">
                        {{ i + 1 }}
                      </span>
                      <span class="text-sm text-gray-700 leading-snug">{{ action }}</span>
                    </li>
                  </ol>
                </template>
                <template v-else-if="brief.recommended_actions.length">
                  <ol class="space-y-3">
                    <li v-for="(action, i) in brief.recommended_actions" :key="i" class="flex items-start gap-3">
                      <span class="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-blue-50 text-xs font-semibold text-blue-600 mt-0.5">
                        {{ i + 1 }}
                      </span>
                      <span class="text-sm text-gray-700 leading-snug">{{ action }}</span>
                    </li>
                  </ol>
                </template>
                <p v-else class="text-sm text-gray-400">No actions suggested yet — load demo data or add companies and prospects to get started.</p>
              </div>
            </AppCard>

            <!-- Drafts for Review -->
            <AppCard v-if="brief.pending_drafts.total > 0">
              <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
                <h2 class="text-sm font-semibold text-gray-900">Drafts for Review</h2>
                <NuxtLink to="/review-queue" class="text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors">Open →</NuxtLink>
              </div>
              <div class="px-5 py-4 space-y-2.5">
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-600">Approvable</span>
                  <span class="font-semibold text-emerald-600">{{ brief.pending_drafts.approvable.length }}</span>
                </div>
                <div v-if="brief.pending_drafts.blocked.length > 0" class="flex items-center justify-between text-sm">
                  <span class="text-gray-600">Quality blocked</span>
                  <span class="font-semibold text-red-500">{{ brief.pending_drafts.blocked.length }}</span>
                </div>
                <div class="flex items-center justify-between text-sm border-t border-gray-100 pt-2.5">
                  <span class="text-gray-500">Total pending</span>
                  <span class="font-semibold text-gray-900">{{ brief.pending_drafts.total }}</span>
                </div>
              </div>
            </AppCard>

            <!-- Pipeline Snapshot (real BD data) -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
                <h2 class="text-sm font-semibold text-gray-900">Pipeline Snapshot</h2>
                <NuxtLink to="/pipeline" class="text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors">View →</NuxtLink>
              </div>
              <div class="px-5 py-4 space-y-2">
                <template v-if="bdPipelineSnapshot.length">
                  <div
                    v-for="stage in bdPipelineSnapshot"
                    :key="stage.stage"
                    class="flex items-center justify-between"
                  >
                    <span class="text-sm text-gray-600">{{ stageLabel[stage.stage] ?? stage.stage }}</span>
                    <span
                      class="inline-flex h-6 min-w-[1.5rem] items-center justify-center rounded-full px-2 text-xs font-semibold tabular-nums"
                      :class="stageColorMap[stage.stage] ?? 'bg-gray-100 text-gray-600'"
                    >
                      {{ stage.count }}
                    </span>
                  </div>
                </template>
                <p v-else class="text-sm text-gray-400">No active deals in pipeline yet.</p>
                <p class="text-xs text-gray-400 pt-1 border-t border-gray-100">
                  Advance opportunities through stages on the <NuxtLink to="/pipeline" class="text-blue-600 hover:underline">Pipeline page</NuxtLink>
                </p>
              </div>
            </AppCard>

            <!-- Signal Intelligence Recommendations -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h2 class="text-sm font-semibold text-gray-900">Signal Intelligence</h2>
                  <p class="text-xs text-gray-400 mt-0.5">ICP-aware recommendations — local scoring, no AI calls</p>
                </div>
                <button
                  class="inline-flex items-center gap-1 rounded-lg border border-gray-200 bg-white px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
                  :disabled="refreshingRecs"
                  @click="runRefresh"
                >
                  <span v-if="refreshingRecs" class="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  <svg v-else class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                  </svg>
                  Refresh
                </button>
              </div>

              <!-- Intelligence summary counts -->
              <div v-if="bdStats" class="px-5 py-3 border-b border-gray-50 flex gap-4">
                <div class="text-center">
                  <p class="text-lg font-bold text-violet-600 tabular-nums">{{ bdStats.signal_recommendations }}</p>
                  <p class="text-[10px] text-gray-400">new recs</p>
                </div>
                <div class="text-center">
                  <p class="text-lg font-bold text-amber-600 tabular-nums">{{ bdStats.companies_needing_research }}</p>
                  <p class="text-[10px] text-gray-400">need research</p>
                </div>
                <div class="text-center">
                  <p class="text-lg font-bold text-emerald-600 tabular-nums">{{ bdStats.prospects_ready_for_review }}</p>
                  <p class="text-[10px] text-gray-400">ready for review</p>
                </div>
              </div>

              <div class="px-5 py-4 space-y-3">
                <template v-if="topRecommendations.length">
                  <div
                    v-for="rec in topRecommendations"
                    :key="rec.id"
                    class="flex items-start gap-2.5 rounded-lg border border-gray-100 bg-gray-50 px-3 py-2.5"
                  >
                    <span
                      class="mt-0.5 inline-flex flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset"
                      :class="priorityConfig[rec.priority]?.color ?? 'bg-gray-100 text-gray-500 ring-gray-200'"
                    >
                      {{ priorityConfig[rec.priority]?.label ?? rec.priority }}
                    </span>
                    <div class="flex-1 min-w-0">
                      <p class="text-xs font-medium text-gray-900 truncate">{{ rec.entity_name }}</p>
                      <p class="text-[11px] text-gray-500 leading-snug mt-0.5">{{ rec.recommended_action }}</p>
                    </div>
                    <button
                      class="flex-shrink-0 text-gray-300 hover:text-gray-500 transition-colors"
                      :disabled="dismissing === rec.id"
                      @click="dismissRec(rec.id)"
                    >
                      <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </template>
                <p v-else class="text-sm text-gray-400">
                  No new recommendations.
                  <button class="text-blue-600 hover:underline ml-1" @click="runRefresh">Run signal refresh</button>
                  to evaluate signals and surface opportunities.
                </p>
                <p class="text-[11px] text-gray-400 border-t border-gray-100 pt-2">
                  Recommendations require your explicit action — DobryBot never reaches out automatically.
                </p>
              </div>
            </AppCard>

          </div>
        </div>
      </template>
    </div>

    <!-- Seed confirmation -->
    <ConfirmDialog
      v-model="showSeedConfirm"
      title="Load Demo Data?"
      message="This will seed safe demo records (fake .test domains, no real companies or emails) into the database. Use it to explore the dashboard without a real config.yaml."
      confirm-label="Seed Demo Data"
      variant="info"
      @confirm="seedDemo"
    />
  </div>
</template>
