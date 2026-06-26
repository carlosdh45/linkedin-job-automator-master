<script setup lang="ts">
interface MockProspect {
  id: string
  name: string
  title: string
  company: string
  industry: string
  signalCount: number
  painPoints: number
  score: number
  scoreLabel: string
  angle: string
  status: string
}

const mockProspects: MockProspect[] = [
  {
    id: '1', name: 'Alex Rivera', title: 'VP of Engineering', company: 'Meridian Labs',
    industry: 'DevTools', signalCount: 4, painPoints: 2, score: 89, scoreLabel: 'hot',
    angle: 'Deployment automation — they posted 3 DevOps roles last month', status: 'researched',
  },
  {
    id: '2', name: 'Morgan Chen', title: 'CTO', company: 'Vantage Capital',
    industry: 'FinTech', signalCount: 3, painPoints: 3, score: 82, scoreLabel: 'hot',
    angle: 'Compliance reporting — multiple pain point mentions in recent job postings', status: 'identified',
  },
  {
    id: '3', name: 'Jamie Okafor', title: 'Head of Platform', company: 'Stratos Engineering',
    industry: 'Infrastructure', signalCount: 2, painPoints: 2, score: 74, scoreLabel: 'warm',
    angle: 'Tech debt reduction — leadership change 6 weeks ago signals new priorities', status: 'identified',
  },
  {
    id: '4', name: 'Sam Torres', title: 'VP Product', company: 'Nexus Health',
    industry: 'HealthTech', signalCount: 2, painPoints: 1, score: 68, scoreLabel: 'warm',
    angle: 'HIPAA audit prep — annual audit cycle approaching based on company age', status: 'researched',
  },
  {
    id: '5', name: 'Drew Kim', title: 'Director of Engineering', company: 'Prism Analytics',
    industry: 'Data / Analytics', signalCount: 1, painPoints: 1, score: 55, scoreLabel: 'cold',
    angle: 'Data pipeline reliability — mentioned in engineering blog post', status: 'identified',
  },
]

const activeFilter = ref('all')

const filters = [
  { value: 'all', label: 'All' },
  { value: 'hot', label: 'Hot' },
  { value: 'warm', label: 'Warm' },
  { value: 'cold', label: 'Cold' },
]

const filtered = computed(() =>
  activeFilter.value === 'all'
    ? mockProspects
    : mockProspects.filter(p => p.scoreLabel === activeFilter.value)
)

const scoreLabelColor: Record<string, string> = {
  hot: 'bg-rose-50 text-rose-700 ring-rose-100',
  warm: 'bg-amber-50 text-amber-700 ring-amber-100',
  cold: 'bg-gray-100 text-gray-600 ring-gray-200',
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Prospects"
      :subtitle="`${filtered.length} of ${mockProspects.length} decision makers`"
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
            ? 'bg-violet-50 text-violet-700 border-violet-200'
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
                <th>Prospect</th>
                <th class="hidden md:table-cell">Company</th>
                <th class="hidden lg:table-cell">Signals / Pain Pts</th>
                <th class="text-right">Score</th>
                <th>Signal</th>
                <th class="hidden xl:table-cell">Recommended Angle</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in filtered" :key="p.id">
                <td>
                  <div class="font-medium text-gray-900">{{ p.name }}</div>
                  <div class="text-xs text-gray-400">{{ p.title }}</div>
                </td>
                <td class="hidden md:table-cell">
                  <div class="text-gray-700">{{ p.company }}</div>
                  <div class="text-xs text-gray-400">{{ p.industry }}</div>
                </td>
                <td class="hidden lg:table-cell">
                  <div class="flex items-center gap-2">
                    <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-100">
                      <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                      </svg>
                      {{ p.signalCount }}
                    </span>
                    <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-rose-50 text-rose-600 ring-1 ring-inset ring-rose-100">
                      {{ p.painPoints }} pain
                    </span>
                  </div>
                </td>
                <td class="text-right font-semibold tabular-nums text-violet-600">{{ p.score }}</td>
                <td>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset"
                    :class="scoreLabelColor[p.scoreLabel] ?? 'bg-gray-100 text-gray-600 ring-gray-200'"
                  >
                    {{ p.scoreLabel }}
                  </span>
                </td>
                <td class="hidden xl:table-cell text-xs text-gray-500 max-w-sm truncate">{{ p.angle }}</td>
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
          <p class="text-sm font-medium text-gray-700">Phase 2: Live Prospect Intelligence</p>
          <p class="text-xs text-gray-500 mt-0.5">In Phase 2, this page connects to real prospect data — decision maker research, signal history, pain point detection, and AI-suggested outreach angles. All outreach drafts still route through the Review Queue.</p>
        </div>
      </div>
    </div>
  </div>
</template>
