<script setup lang="ts">
import type { BDCompany } from '~/types'

const api = useApi()

const { data: companies, pending, error } = await useAsyncData<BDCompany[]>(
  'bd-companies',
  () => api.getBDCompanies(),
  { default: () => [] }
)

const activeFilter = ref('all')

const filters = [
  { value: 'all', label: 'All' },
  { value: 'icp', label: 'ICP Match' },
  { value: 'hot', label: 'Hot' },
  { value: 'warm', label: 'Warm' },
]

const filtered = computed(() => {
  const list = companies.value ?? []
  if (activeFilter.value === 'all') return list
  if (activeFilter.value === 'icp') return list.filter(c => c.icp_match)
  return list.filter(c => c.score_label === activeFilter.value)
})

const scoreLabelColor: Record<string, string> = {
  hot: 'bg-rose-50 text-rose-700 ring-rose-100',
  warm: 'bg-amber-50 text-amber-700 ring-amber-100',
  cold: 'bg-gray-100 text-gray-600 ring-gray-200',
  disqualified: 'bg-gray-100 text-gray-400 ring-gray-200',
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Companies"
      :subtitle="pending ? 'Loading…' : `${filtered.length} of ${(companies ?? []).length} target accounts — scored by pain points, signals, and ICP fit`"
    />

    <div class="flex-1 p-6 space-y-4 max-w-6xl w-full mx-auto">
      <!-- Error state -->
      <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Could not load companies — make sure the backend is running.
      </div>

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

      <!-- Loading skeleton -->
      <AppCard v-if="pending">
        <div class="px-6 py-8 text-center text-sm text-gray-400 animate-pulse">Loading companies…</div>
      </AppCard>

      <!-- Table -->
      <AppCard v-else>
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
                      <div class="text-xs text-gray-400">{{ co.domain ?? '—' }}</div>
                    </div>
                    <span
                      v-if="co.icp_match"
                      class="hidden lg:inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-semibold bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-100"
                    >
                      ICP
                    </span>
                  </div>
                </td>
                <td class="hidden md:table-cell text-gray-500">{{ co.industry ?? '—' }}</td>
                <td class="hidden sm:table-cell text-gray-500">{{ co.size_estimate ?? '—' }}</td>
                <td>
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="pp in co.pain_points.slice(0, 2)"
                      :key="pp"
                      class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium bg-rose-50 text-rose-600 ring-1 ring-inset ring-rose-100"
                    >
                      {{ pp }}
                    </span>
                    <span
                      v-if="co.pain_points.length > 2"
                      class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium bg-gray-100 text-gray-500"
                    >
                      +{{ co.pain_points.length - 2 }}
                    </span>
                  </div>
                </td>
                <td class="hidden lg:table-cell text-center">
                  <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-100">
                    <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                    {{ co.tech_signals.length }}
                  </span>
                </td>
                <td class="text-right font-semibold tabular-nums text-blue-600">{{ co.opportunity_score }}</td>
                <td>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset"
                    :class="scoreLabelColor[co.score_label] ?? 'bg-gray-100 text-gray-600 ring-gray-200'"
                  >
                    {{ co.score_label }}
                  </span>
                </td>
              </tr>
              <tr v-if="!filtered.length && !pending">
                <td colspan="7" class="py-12 text-center">
                  <p class="text-sm text-gray-400 font-medium">No companies match this filter.</p>
                  <p class="text-xs text-gray-300 mt-1">Load demo data from the Command Center or switch to "All" to see every account.</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </AppCard>
    </div>
  </div>
</template>
