<script setup lang="ts">
interface MockCompany {
  id: string
  name: string
  domain: string
  industry: string
  size: string
  painPoints: string[]
  signals: number
  score: number
  scoreLabel: string
  status: string
  icpMatch: boolean
}

const mockCompanies: MockCompany[] = [
  {
    id: '1', name: 'Meridian Labs', domain: 'meridianlabs.io', industry: 'DevTools / SaaS',
    size: '50–200', painPoints: ['Manual deployment pipeline', 'Slow release cycles'],
    signals: 4, score: 89, scoreLabel: 'hot', status: 'researched', icpMatch: true,
  },
  {
    id: '2', name: 'Vantage Capital', domain: 'vantagecap.com', industry: 'FinTech',
    size: '200–500', painPoints: ['Compliance reporting overhead', 'Data reconciliation delays', 'Manual audit prep'],
    signals: 3, score: 82, scoreLabel: 'hot', status: 'qualified', icpMatch: true,
  },
  {
    id: '3', name: 'Stratos Engineering', domain: 'stratos.build', industry: 'Infrastructure',
    size: '100–300', painPoints: ['Developer onboarding velocity', 'Tech debt accumulation'],
    signals: 2, score: 74, scoreLabel: 'warm', status: 'researched', icpMatch: true,
  },
  {
    id: '4', name: 'Nexus Health', domain: 'nexushealth.co', industry: 'HealthTech',
    size: '50–150', painPoints: ['HIPAA audit prep', 'Legacy system integrations'],
    signals: 2, score: 68, scoreLabel: 'warm', status: 'identified', icpMatch: true,
  },
  {
    id: '5', name: 'Prism Analytics', domain: 'prismanalytics.io', industry: 'Data / Analytics',
    size: '20–80', painPoints: ['Data pipeline reliability'],
    signals: 1, score: 55, scoreLabel: 'cold', status: 'identified', icpMatch: false,
  },
  {
    id: '6', name: 'Cascade Retail', domain: 'cascaderetail.com', industry: 'E-commerce',
    size: '500+', painPoints: ['Inventory sync delays', 'Cart abandonment analytics'],
    signals: 1, score: 48, scoreLabel: 'cold', status: 'identified', icpMatch: false,
  },
]

const activeFilter = ref('all')

const filters = [
  { value: 'all', label: 'All' },
  { value: 'icp', label: 'ICP Match' },
  { value: 'hot', label: 'Hot' },
  { value: 'warm', label: 'Warm' },
]

const filtered = computed(() => {
  if (activeFilter.value === 'all') return mockCompanies
  if (activeFilter.value === 'icp') return mockCompanies.filter(c => c.icpMatch)
  return mockCompanies.filter(c => c.scoreLabel === activeFilter.value)
})

const scoreLabelColor: Record<string, string> = {
  hot: 'bg-rose-50 text-rose-700 ring-rose-100',
  warm: 'bg-amber-50 text-amber-700 ring-amber-100',
  cold: 'bg-gray-100 text-gray-600 ring-gray-200',
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Companies"
      :subtitle="`${filtered.length} of ${mockCompanies.length} target companies`"
    >
      <template #actions>
        <span class="inline-flex items-center gap-1.5 rounded-lg bg-blue-50 border border-blue-100 px-3 py-1.5 text-xs font-medium text-blue-700">
          Placeholder data — Phase 2 connects real intelligence
        </span>
      </template>
    </PageHeader>

    <div class="flex-1 p-6 space-y-4 max-w-6xl w-full mx-auto">
      <!-- Filter tabs -->
      <div class="flex gap-1.5 flex-wrap">
        <button
          v-for="f in filters"
          :key="f.value"
          class="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors border"
          :class="activeFilter === f.value
            ? 'bg-blue-50 text-blue-700 border-blue-200'
            : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:text-gray-900'"
          @click="activeFilter = f.value"
        >
          {{ f.label }}
        </button>
      </div>

      <AppCard>
        <div class="overflow-x-auto">
          <table class="app-table">
            <thead>
              <tr>
                <th>Company</th>
                <th class="hidden md:table-cell">Industry</th>
                <th class="hidden sm:table-cell">Size</th>
                <th>Pain Points</th>
                <th class="hidden lg:table-cell text-center">Signals</th>
                <th class="text-right">Score</th>
                <th>Signal</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="co in filtered" :key="co.id">
                <td>
                  <div class="flex items-center gap-2">
                    <div>
                      <div class="font-medium text-gray-900">{{ co.name }}</div>
                      <div class="text-xs text-gray-400">{{ co.domain }}</div>
                    </div>
                    <span
                      v-if="co.icpMatch"
                      class="hidden lg:inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-semibold bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-100"
                    >
                      ICP
                    </span>
                  </div>
                </td>
                <td class="hidden md:table-cell text-gray-500">{{ co.industry }}</td>
                <td class="hidden sm:table-cell text-gray-500">{{ co.size }}</td>
                <td>
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="pp in co.painPoints.slice(0, 2)"
                      :key="pp"
                      class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium bg-rose-50 text-rose-600 ring-1 ring-inset ring-rose-100"
                    >
                      {{ pp }}
                    </span>
                    <span
                      v-if="co.painPoints.length > 2"
                      class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium bg-gray-100 text-gray-500"
                    >
                      +{{ co.painPoints.length - 2 }}
                    </span>
                  </div>
                </td>
                <td class="hidden lg:table-cell text-center">
                  <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-100">
                    <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                    {{ co.signals }}
                  </span>
                </td>
                <td class="text-right font-semibold tabular-nums text-blue-600">{{ co.score }}</td>
                <td>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset"
                    :class="scoreLabelColor[co.scoreLabel] ?? 'bg-gray-100 text-gray-600 ring-gray-200'"
                  >
                    {{ co.scoreLabel }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </AppCard>

      <!-- Phase notice -->
      <div class="flex items-start gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3">
        <svg class="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
        </svg>
        <div>
          <p class="text-sm font-medium text-gray-700">Phase 2: Live Company Intelligence</p>
          <p class="text-xs text-gray-500 mt-0.5">In Phase 2, companies connect to real signal data — hiring patterns, funding events, leadership changes, tech stack detection, and automated pain point analysis. ICP scoring becomes dynamic based on your configured criteria.</p>
        </div>
      </div>
    </div>
  </div>
</template>
