<script setup lang="ts">
import type { BDOpportunity, BDOpportunityRecalculateResult } from '~/types'

const api = useApi()

const { data: opportunities, pending, error, refresh } = await useAsyncData<BDOpportunity[]>(
  'bd-opportunities',
  () => api.getBDOpportunities(),
  { default: () => [] }
)

const activeStage = ref('all')
const activeScore = ref('all')
const recalculating = ref<string | null>(null)
const lastRecalc = ref<BDOpportunityRecalculateResult | null>(null)

const stageFilters = [
  { value: 'all', label: 'All Stages' },
  { value: 'identified', label: 'Identified' },
  { value: 'researched', label: 'Researched' },
  { value: 'qualified', label: 'Qualified' },
  { value: 'engaged', label: 'Engaged' },
]

const scoreFilters = [
  { value: 'all', label: 'All Scores' },
  { value: 'hot', label: 'Hot' },
  { value: 'warm', label: 'Warm' },
]

const filtered = computed(() => {
  let list = opportunities.value ?? []
  if (activeStage.value !== 'all') list = list.filter(o => o.stage === activeStage.value)
  if (activeScore.value !== 'all') list = list.filter(o => o.score_label === activeScore.value)
  return list
})

const scoreLabelColor: Record<string, string> = {
  hot: 'bg-rose-50 text-rose-700 ring-rose-100',
  warm: 'bg-amber-50 text-amber-700 ring-amber-100',
  cold: 'bg-gray-100 text-gray-600 ring-gray-200',
  disqualified: 'bg-gray-100 text-gray-400 ring-gray-200',
}

const stageColor: Record<string, string> = {
  identified: 'bg-gray-100 text-gray-600',
  researched: 'bg-blue-50 text-blue-700',
  qualified: 'bg-violet-50 text-violet-700',
  engaged: 'bg-amber-50 text-amber-700',
  deal_packet: 'bg-orange-50 text-orange-700',
  active: 'bg-emerald-50 text-emerald-700',
}

function scoreChangeColor(change: number | null): string {
  if (change === null) return 'text-gray-400'
  if (change > 0) return 'text-emerald-600'
  if (change < 0) return 'text-red-500'
  return 'text-gray-400'
}

function formatScoreChange(change: number | null): string {
  if (change === null) return ''
  return change >= 0 ? `+${change}` : String(change)
}

async function recalculate(opp: BDOpportunity) {
  recalculating.value = opp.id
  lastRecalc.value = null
  try {
    const result = await api.recalculateBDOpportunity(opp.id)
    lastRecalc.value = result
    await refresh()
  } catch {
    // non-critical
  } finally {
    recalculating.value = null
  }
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Opportunities"
      :subtitle="pending ? 'Loading…' : `${filtered.length} qualified opportunities tracked`"
    />

    <div class="flex-1 p-6 space-y-4 max-w-6xl w-full mx-auto">
      <!-- Error -->
      <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Could not load opportunities — make sure the backend is running.
      </div>

      <!-- Last recalc result -->
      <div
        v-if="lastRecalc"
        class="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 flex items-start gap-3"
      >
        <svg class="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-blue-900">
            Score recalculated: {{ lastRecalc.previous_score }} → {{ lastRecalc.new_score }}
            <span :class="scoreChangeColor(lastRecalc.score_change)" class="font-semibold ml-1">
              ({{ formatScoreChange(lastRecalc.score_change) }})
            </span>
          </p>
          <p class="text-xs text-blue-700 mt-0.5 leading-snug">{{ lastRecalc.score_reason }}</p>
          <p v-if="lastRecalc.signal_contribution > 0" class="text-xs text-blue-600 mt-1">
            Signal contribution: +{{ lastRecalc.signal_contribution }} pts
          </p>
        </div>
        <button class="text-blue-400 hover:text-blue-600" @click="lastRecalc = null">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="f in stageFilters"
          :key="f.value"
          class="inline-flex items-center rounded-lg px-3 py-1.5 text-xs font-medium transition-colors border"
          :class="activeStage === f.value
            ? 'bg-blue-50 text-blue-700 border-blue-200'
            : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
          @click="activeStage = f.value"
        >
          {{ f.label }}
        </button>
        <span class="w-px bg-gray-200 mx-1" />
        <button
          v-for="f in scoreFilters"
          :key="f.value"
          class="inline-flex items-center rounded-lg px-3 py-1.5 text-xs font-medium transition-colors border"
          :class="activeScore === f.value
            ? 'bg-violet-50 text-violet-700 border-violet-200'
            : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
          @click="activeScore = f.value"
        >
          {{ f.label }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="pending" class="py-12 text-center text-sm text-gray-400 animate-pulse">Loading opportunities…</div>

      <!-- Opportunity cards -->
      <div v-else class="space-y-3">
        <AppCard
          v-for="opp in filtered"
          :key="opp.id"
        >
          <div class="px-5 py-4">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <h3 class="text-sm font-semibold text-gray-900">{{ opp.company_name }}</h3>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset"
                    :class="scoreLabelColor[opp.score_label] ?? 'bg-gray-100 text-gray-600 ring-gray-200'"
                  >
                    {{ opp.score_label }}
                  </span>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                    :class="stageColor[opp.stage] ?? 'bg-gray-100 text-gray-600'"
                  >
                    {{ opp.stage }}
                  </span>
                </div>
                <p v-if="opp.contact_name" class="text-xs text-gray-500 mt-0.5">{{ opp.contact_name }}</p>
                <p v-else class="text-xs text-gray-400 mt-0.5 italic">Contact not yet identified</p>

                <div class="flex flex-wrap gap-1 mt-2">
                  <span
                    v-for="pp in opp.pain_points"
                    :key="pp"
                    class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium bg-rose-50 text-rose-600 ring-1 ring-inset ring-rose-100"
                  >
                    {{ pp }}
                  </span>
                </div>
              </div>

              <div class="flex-shrink-0 text-right">
                <div class="text-2xl font-bold tabular-nums text-blue-600">{{ opp.score }}</div>
                <div class="text-[10px] text-gray-400">opp score</div>
                <!-- Score change indicator -->
                <div
                  v-if="opp.score_change !== null && opp.score_change !== undefined"
                  class="text-[10px] font-semibold tabular-nums mt-0.5"
                  :class="scoreChangeColor(opp.score_change)"
                >
                  {{ formatScoreChange(opp.score_change) }}
                </div>
              </div>
            </div>

            <!-- Recommended action -->
            <div v-if="opp.recommended_action" class="mt-3 flex items-start gap-2 rounded-lg bg-blue-50 border border-blue-100 px-3 py-2">
              <svg class="h-3.5 w-3.5 text-blue-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-xs text-blue-700">{{ opp.recommended_action }}</p>
            </div>

            <!-- Score reason (shown after recalculation) -->
            <div v-if="opp.score_reason" class="mt-2 flex items-start gap-2 rounded-lg bg-gray-50 border border-gray-100 px-3 py-2">
              <svg class="h-3.5 w-3.5 text-gray-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
              </svg>
              <div class="flex-1 min-w-0">
                <p class="text-xs text-gray-600 leading-snug">{{ opp.score_reason }}</p>
                <p v-if="opp.signal_contribution > 0" class="text-[11px] text-indigo-600 mt-0.5 font-medium">
                  Signal contribution: +{{ opp.signal_contribution }} pts
                </p>
              </div>
            </div>

            <!-- Recalculate button -->
            <div class="mt-3 flex items-center justify-end">
              <button
                class="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors disabled:opacity-50"
                :disabled="recalculating === opp.id"
                @click="recalculate(opp)"
              >
                <span v-if="recalculating === opp.id" class="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                <svg v-else class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
                </svg>
                Recalculate Score
              </button>
            </div>
          </div>
        </AppCard>

        <div v-if="!filtered.length" class="py-16 text-center">
          <p class="text-sm text-gray-400">No opportunities match the current filter.</p>
        </div>
      </div>
    </div>
  </div>
</template>
