<template>
  <div class="flex-1 overflow-y-auto">
    <!-- Page header -->
    <div class="sticky top-0 z-10 bg-slate-950/80 backdrop-blur border-b border-slate-800 px-8 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-100">Dashboard</h1>
        <p class="text-xs text-slate-500 mt-0.5">{{ today }}</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          class="px-3 py-1.5 text-xs font-medium text-slate-400 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
          @click="() => refresh()"
        >
          Refresh
        </button>
        <button
          class="px-3 py-1.5 text-xs font-medium text-blue-400 bg-blue-900/30 hover:bg-blue-900/50 border border-blue-800/50 rounded-lg transition-colors"
          @click="showSeedConfirm = true"
        >
          Load Demo Data
        </button>
      </div>
    </div>

    <div class="px-8 py-6 space-y-6 max-w-7xl mx-auto">
      <!-- Safety banner -->
      <div class="flex items-center gap-3 px-4 py-3 bg-emerald-950/40 border border-emerald-900/50 rounded-xl">
        <svg class="w-4 h-4 text-emerald-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 1a4.5 4.5 0 00-4.5 4.5V9H5a2 2 0 00-2 2v6a2 2 0 002 2h10a2 2 0 002-2v-6a2 2 0 00-2-2h-.5V5.5A4.5 4.5 0 0010 1zm3 8V5.5a3 3 0 10-6 0V9h6z" clip-rule="evenodd" />
        </svg>
        <p class="text-sm font-medium text-emerald-400">
          DobryBot never sends or applies automatically. Every action requires human approval.
        </p>
      </div>

      <!-- Loading / error states -->
      <LoadingSpinner v-if="pending" label="Loading dashboard…" />

      <template v-else-if="error">
        <div class="rounded-xl border border-red-900/50 bg-red-950/30 p-6 text-center">
          <p class="text-red-400 font-medium">Could not reach the backend.</p>
          <p class="text-sm text-slate-500 mt-1">Make sure <code class="text-slate-400">uvicorn backend.main:app --reload --port 8000</code> is running.</p>
          <button class="mt-4 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-sm text-slate-200 rounded-lg transition-colors" @click="() => refresh()">
            Retry
          </button>
        </div>
      </template>

      <template v-else-if="brief">
        <!-- Stats cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
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
            :sub="`${outreachSent} sent by you`"
            variant="green"
            icon="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
          />
          <StatCard
            title="Review Queue"
            :value="reviewPending"
            :sub="reviewPending === 1 ? 'draft awaiting review' : 'drafts awaiting review'"
            variant="amber"
            icon="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
          />
        </div>

        <!-- Recommended actions + top opportunities -->
        <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <!-- Top Jobs -->
          <div class="xl:col-span-1 bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <div class="px-5 py-4 border-b border-slate-700 flex items-center justify-between">
              <h2 class="text-sm font-semibold text-slate-200">Top Jobs</h2>
              <NuxtLink to="/jobs" class="text-xs text-blue-400 hover:text-blue-300 transition-colors">View all →</NuxtLink>
            </div>
            <div v-if="brief.top_jobs.length === 0" class="px-5 py-8 text-center text-sm text-slate-500">
              No high-priority jobs found.
            </div>
            <ul v-else class="divide-y divide-slate-700/50">
              <li
                v-for="job in brief.top_jobs.slice(0, 6)"
                :key="job.id"
                class="px-5 py-3 flex items-center gap-3 hover:bg-slate-700/30 transition-colors"
              >
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-slate-200 truncate">{{ job.title }}</p>
                  <p class="text-xs text-slate-500 truncate">{{ job.company }}</p>
                </div>
                <div class="flex-shrink-0 flex items-center gap-2">
                  <span class="text-xs font-semibold text-blue-400 tabular-nums">{{ job.job_score }}</span>
                  <StatusBadge :status="job.score_label || job.status" />
                </div>
              </li>
            </ul>
          </div>

          <!-- Top Leads -->
          <div class="xl:col-span-1 bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            <div class="px-5 py-4 border-b border-slate-700 flex items-center justify-between">
              <h2 class="text-sm font-semibold text-slate-200">Top Leads</h2>
              <NuxtLink to="/leads" class="text-xs text-blue-400 hover:text-blue-300 transition-colors">View all →</NuxtLink>
            </div>
            <div v-if="brief.top_leads.length === 0" class="px-5 py-8 text-center text-sm text-slate-500">
              No high-priority leads found.
            </div>
            <ul v-else class="divide-y divide-slate-700/50">
              <li
                v-for="lead in brief.top_leads.slice(0, 6)"
                :key="lead.id"
                class="px-5 py-3 flex items-center gap-3 hover:bg-slate-700/30 transition-colors"
              >
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-slate-200 truncate">{{ lead.company }}</p>
                  <p class="text-xs text-slate-500 truncate">{{ lead.industry || lead.domain }}</p>
                </div>
                <div class="flex-shrink-0 flex items-center gap-2">
                  <span class="text-xs font-semibold text-violet-400 tabular-nums">{{ lead.lead_score }}</span>
                  <StatusBadge :status="lead.score_label || lead.status" />
                </div>
              </li>
            </ul>
          </div>

          <!-- Recommended actions + review queue summary -->
          <div class="xl:col-span-1 space-y-4">
            <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
              <div class="px-5 py-4 border-b border-slate-700">
                <h2 class="text-sm font-semibold text-slate-200">Recommended Actions</h2>
              </div>
              <ul class="px-5 py-3 space-y-2">
                <li
                  v-for="(action, i) in brief.recommended_actions"
                  :key="i"
                  class="flex items-start gap-2.5 text-sm text-slate-300"
                >
                  <span class="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full bg-blue-900/40 text-blue-400 flex items-center justify-center text-xs font-bold">{{ i + 1 }}</span>
                  <span class="leading-relaxed">{{ action }}</span>
                </li>
              </ul>
            </div>

            <!-- Review queue summary -->
            <div
              v-if="brief.pending_drafts.total > 0"
              class="bg-slate-800 border border-amber-900/40 rounded-xl overflow-hidden"
            >
              <div class="px-5 py-4 border-b border-slate-700 flex items-center justify-between">
                <h2 class="text-sm font-semibold text-slate-200">Review Queue</h2>
                <NuxtLink to="/review-queue" class="text-xs text-amber-400 hover:text-amber-300 transition-colors">Open →</NuxtLink>
              </div>
              <div class="px-5 py-4 space-y-2">
                <div class="flex justify-between text-sm">
                  <span class="text-slate-400">Total pending</span>
                  <span class="font-semibold text-slate-200">{{ brief.pending_drafts.total }}</span>
                </div>
                <div class="flex justify-between text-sm">
                  <span class="text-emerald-400">Approvable</span>
                  <span class="font-semibold text-emerald-300">{{ brief.pending_drafts.approvable.length }}</span>
                </div>
                <div v-if="brief.pending_drafts.blocked.length > 0" class="flex justify-between text-sm">
                  <span class="text-red-400">Quality blocked</span>
                  <span class="font-semibold text-red-300">{{ brief.pending_drafts.blocked.length }}</span>
                </div>
              </div>
            </div>
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

<script setup lang="ts">
import { statJobTotal, statJobScored, statLeadTotal, statLeadScored } from '~/types'

const api = useApi()
const showSeedConfirm = ref(false)

const { data: brief, pending, error, refresh } = await useAsyncData('dashboard', () => api.getDailyBrief())

const today = computed(() => brief.value?.date ?? new Date().toDateString())

const stats = computed(() => brief.value?.stats ?? {})
const jobTotal = computed(() => statJobTotal(stats.value))
const jobScored = computed(() => statJobScored(stats.value))
const leadTotal = computed(() => statLeadTotal(stats.value))
const leadScored = computed(() => statLeadScored(stats.value))
const outreachGenerated = computed(() => stats.value.outreach_generated ?? 0)
const outreachSent = computed(() => stats.value.outreach_sent ?? 0)
const reviewPending = computed(() => stats.value.outreach_pending_review ?? 0)

async function seedDemo() {
  try {
    await api.seedDemo()
    await refresh()
  } catch {
    // non-critical
  }
}
</script>
