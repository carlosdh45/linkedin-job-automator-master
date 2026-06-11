<script setup lang="ts">
import { statJobTotal, statJobScored, statLeadTotal, statLeadScored } from '~/types'

const api = useApi()
const showSeedConfirm = ref(false)

const { data: brief, pending, error, refresh } = await useAsyncData('dashboard', () => api.getDailyBrief())

const today = computed(() =>
  brief.value?.date
    ? new Date(brief.value.date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
    : new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
)

const stats = computed(() => brief.value?.stats ?? {})
const jobTotal = computed(() => statJobTotal(stats.value))
const jobScored = computed(() => statJobScored(stats.value))
const leadTotal = computed(() => statLeadTotal(stats.value))
const leadScored = computed(() => statLeadScored(stats.value))
const outreachGenerated = computed(() => stats.value.outreach_generated ?? 0)
const reviewPending = computed(() => brief.value?.pending_drafts.total ?? 0)
const approvable = computed(() => brief.value?.pending_drafts.approvable.length ?? 0)

async function seedDemo() {
  try {
    await api.seedDemo()
    await refresh()
  } catch {
    // non-critical
  }
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader title="Dashboard" :subtitle="today">
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
      <!-- Safety banner -->
      <div class="flex items-center gap-3 rounded-xl bg-emerald-50 border border-emerald-100 px-4 py-3">
        <svg class="h-4 w-4 text-emerald-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
        <span class="text-sm text-emerald-700 font-medium">All actions require explicit human approval — DobryBot never sends or applies automatically.</span>
      </div>

      <LoadingSpinner v-if="pending" label="Loading dashboard…" />

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
            title="Jobs Tracked"
            :value="jobTotal"
            :sub="`${jobScored} scored / ready`"
            variant="blue"
            icon="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z"
          />
          <StatCard
            title="Leads"
            :value="leadTotal"
            :sub="`${leadScored} scored`"
            variant="violet"
            icon="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
          />
          <StatCard
            title="Outreach Drafts"
            :value="outreachGenerated"
            :sub="`${reviewPending} pending review`"
            variant="green"
            icon="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
          />
          <StatCard
            title="Review Queue"
            :value="reviewPending"
            :sub="reviewPending === 1 ? '1 draft awaiting review' : `${approvable} approvable`"
            variant="amber"
            icon="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
          />
        </div>

        <!-- Content grid -->
        <div class="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <!-- Top Jobs + Leads (2/3 width) -->
          <div class="xl:col-span-2 space-y-6">
            <!-- Top Jobs -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
                <h2 class="text-sm font-semibold text-gray-900">Top Jobs</h2>
                <NuxtLink to="/jobs" class="text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors">View all →</NuxtLink>
              </div>
              <div v-if="!brief.top_jobs.length" class="py-10 text-center text-sm text-gray-400">
                No high-priority jobs yet.
              </div>
              <table v-else class="app-table">
                <thead>
                  <tr>
                    <th>Role / Company</th>
                    <th class="hidden sm:table-cell">Location</th>
                    <th class="text-right">Score</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="job in brief.top_jobs.slice(0, 6)" :key="job.id">
                    <td>
                      <div class="font-medium text-gray-900 truncate max-w-xs">{{ job.title }}</div>
                      <div class="text-xs text-gray-400 truncate max-w-xs">{{ job.company }}</div>
                    </td>
                    <td class="hidden sm:table-cell text-gray-500">{{ job.location || '—' }}</td>
                    <td class="text-right font-semibold tabular-nums text-blue-600">{{ job.job_score }}</td>
                    <td><StatusBadge :status="job.score_label || job.status" /></td>
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
                No high-priority leads yet.
              </div>
              <table v-else class="app-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th class="hidden sm:table-cell">Industry</th>
                    <th class="text-right">Score</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="lead in brief.top_leads.slice(0, 6)" :key="lead.id">
                    <td>
                      <div class="font-medium text-gray-900 truncate max-w-xs">{{ lead.company }}</div>
                      <div class="text-xs text-gray-400 truncate max-w-xs">{{ lead.domain }}</div>
                    </td>
                    <td class="hidden sm:table-cell text-gray-500">{{ lead.industry || '—' }}</td>
                    <td class="text-right font-semibold tabular-nums text-violet-600">{{ lead.lead_score }}</td>
                    <td><StatusBadge :status="lead.score_label || lead.status" /></td>
                  </tr>
                </tbody>
              </table>
            </AppCard>
          </div>

          <!-- Sidebar: Actions + Queue summary (1/3 width) -->
          <div class="space-y-6">
            <!-- Recommended Actions -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100">
                <h2 class="text-sm font-semibold text-gray-900">Recommended Actions</h2>
              </div>
              <div class="px-5 py-4">
                <p v-if="!brief.recommended_actions.length" class="text-sm text-gray-400">No actions suggested.</p>
                <ol v-else class="space-y-3">
                  <li v-for="(action, i) in brief.recommended_actions" :key="i" class="flex items-start gap-3">
                    <span class="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-blue-50 text-xs font-semibold text-blue-600 mt-0.5">
                      {{ i + 1 }}
                    </span>
                    <span class="text-sm text-gray-700 leading-snug">{{ action }}</span>
                  </li>
                </ol>
              </div>
            </AppCard>

            <!-- Review Queue summary -->
            <AppCard v-if="brief.pending_drafts.total > 0">
              <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
                <h2 class="text-sm font-semibold text-gray-900">Review Queue</h2>
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
                  <span class="text-gray-500">Total</span>
                  <span class="font-semibold text-gray-900">{{ brief.pending_drafts.total }}</span>
                </div>
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
