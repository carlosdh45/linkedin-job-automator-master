<script setup lang="ts">
interface MockOpportunity {
  id: string
  company: string
  contact: string | null
  contactRole: string | null
  score: number
  scoreLabel: string
  stage: string
  painPoints: string[]
  action: string
  signals: number
}

const mockOpportunities: MockOpportunity[] = [
  {
    id: '1', company: 'Meridian Labs', contact: 'Alex Rivera', contactRole: 'VP of Engineering',
    score: 89, scoreLabel: 'hot', stage: 'researched',
    painPoints: ['Manual deployment pipeline', 'Slow release cycles'],
    action: 'Reach out via mutual connection — Morgan at Acme introduced us', signals: 4,
  },
  {
    id: '2', company: 'Vantage Capital', contact: 'Morgan Chen', contactRole: 'CTO',
    score: 82, scoreLabel: 'hot', stage: 'qualified',
    painPoints: ['Compliance reporting overhead', 'Manual audit prep'],
    action: 'New CTO 6 weeks in — send intro + compliance angle deck', signals: 3,
  },
  {
    id: '3', company: 'Stratos Engineering', contact: 'Jamie Okafor', contactRole: 'Head of Platform',
    score: 74, scoreLabel: 'warm', stage: 'researched',
    painPoints: ['Developer onboarding velocity', 'Tech debt accumulation'],
    action: 'Follow up on tech change signal — Jenkins → GitHub Actions migration', signals: 2,
  },
  {
    id: '4', company: 'Nexus Health', contact: 'Sam Torres', contactRole: 'VP Product',
    score: 68, scoreLabel: 'warm', stage: 'identified',
    painPoints: ['HIPAA audit prep'],
    action: 'First touch — connect on LinkedIn with healthcare compliance angle', signals: 2,
  },
  {
    id: '5', company: 'Prism Analytics', contact: null, contactRole: null,
    score: 55, scoreLabel: 'cold', stage: 'identified',
    painPoints: ['Data pipeline reliability'],
    action: 'Identify right contact — likely VP Engineering or CTO', signals: 1,
  },
]

const stageOrder = ['identified', 'researched', 'qualified', 'engaged', 'deal_packet', 'active', 'won', 'lost']
const activeStage = ref('all')
const activeScore = ref('all')

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
  let list = mockOpportunities
  if (activeStage.value !== 'all') list = list.filter(o => o.stage === activeStage.value)
  if (activeScore.value !== 'all') list = list.filter(o => o.scoreLabel === activeScore.value)
  return list
})

const scoreLabelColor: Record<string, string> = {
  hot: 'bg-rose-50 text-rose-700 ring-rose-100',
  warm: 'bg-amber-50 text-amber-700 ring-amber-100',
  cold: 'bg-gray-100 text-gray-600 ring-gray-200',
}

const stageColor: Record<string, string> = {
  identified: 'bg-gray-100 text-gray-600',
  researched: 'bg-blue-50 text-blue-700',
  qualified: 'bg-violet-50 text-violet-700',
  engaged: 'bg-amber-50 text-amber-700',
  deal_packet: 'bg-orange-50 text-orange-700',
  active: 'bg-emerald-50 text-emerald-700',
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Opportunities"
      :subtitle="`${filtered.length} qualified opportunities tracked`"
    >
      <template #actions>
        <span class="inline-flex items-center gap-1.5 rounded-lg bg-blue-50 border border-blue-100 px-3 py-1.5 text-xs font-medium text-blue-700">
          Placeholder data
        </span>
      </template>
    </PageHeader>

    <div class="flex-1 p-6 space-y-4 max-w-6xl w-full mx-auto">
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

      <!-- Opportunity cards -->
      <div class="space-y-3">
        <AppCard
          v-for="opp in filtered"
          :key="opp.id"
        >
          <div class="px-5 py-4">
            <div class="flex items-start justify-between gap-4">
              <!-- Left: company + contact + pain points -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <h3 class="text-sm font-semibold text-gray-900">{{ opp.company }}</h3>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset"
                    :class="scoreLabelColor[opp.scoreLabel] ?? 'bg-gray-100 text-gray-600 ring-gray-200'"
                  >
                    {{ opp.scoreLabel }}
                  </span>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                    :class="stageColor[opp.stage] ?? 'bg-gray-100 text-gray-600'"
                  >
                    {{ opp.stage }}
                  </span>
                </div>
                <p v-if="opp.contact" class="text-xs text-gray-500 mt-0.5">
                  {{ opp.contact }} · {{ opp.contactRole }}
                </p>
                <p v-else class="text-xs text-gray-400 mt-0.5 italic">Contact not yet identified</p>

                <!-- Pain points -->
                <div class="flex flex-wrap gap-1 mt-2">
                  <span
                    v-for="pp in opp.painPoints"
                    :key="pp"
                    class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium bg-rose-50 text-rose-600 ring-1 ring-inset ring-rose-100"
                  >
                    {{ pp }}
                  </span>
                </div>
              </div>

              <!-- Right: score + signals -->
              <div class="flex-shrink-0 text-right">
                <div class="text-2xl font-bold tabular-nums text-blue-600">{{ opp.score }}</div>
                <div class="text-[10px] text-gray-400">opp score</div>
                <div class="mt-1 flex items-center justify-end gap-1 text-xs text-gray-500">
                  <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                  </svg>
                  {{ opp.signals }} signals
                </div>
              </div>
            </div>

            <!-- Recommended action -->
            <div class="mt-3 flex items-start gap-2 rounded-lg bg-blue-50 border border-blue-100 px-3 py-2">
              <svg class="h-3.5 w-3.5 text-blue-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-xs text-blue-700">{{ opp.action }}</p>
            </div>
          </div>
        </AppCard>

        <div v-if="!filtered.length" class="py-16 text-center">
          <p class="text-sm text-gray-400">No opportunities match the current filter.</p>
        </div>
      </div>

      <!-- Phase notice -->
      <div class="flex items-start gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3">
        <svg class="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
        </svg>
        <div>
          <p class="text-sm font-medium text-gray-700">Phase 2: Dynamic Opportunity Scoring</p>
          <p class="text-xs text-gray-500 mt-0.5">Scores will be computed automatically from ICP fit, signal strength, pain point count, decision maker access, and timing indicators. Recommended actions will be AI-generated and reviewed locally before display.</p>
        </div>
      </div>
    </div>
  </div>
</template>
