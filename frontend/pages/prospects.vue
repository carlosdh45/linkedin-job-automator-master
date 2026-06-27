<script setup lang="ts">
import type { BDProspect } from '~/types'

const api = useApi()

const { data: prospects, pending, error } = await useAsyncData<BDProspect[]>(
  'bd-prospects',
  () => api.getBDProspects(),
  { default: () => [] }
)

const activeFilter = ref('all')

const filters = [
  { value: 'all', label: 'All' },
  { value: 'hot', label: 'Hot' },
  { value: 'warm', label: 'Warm' },
  { value: 'cold', label: 'Cold' },
]

const filtered = computed(() => {
  const list = prospects.value ?? []
  return activeFilter.value === 'all'
    ? list
    : list.filter(p => p.score_label === activeFilter.value)
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
      title="Prospects"
      :subtitle="pending ? 'Loading…' : `${filtered.length} of ${(prospects ?? []).length} decision-makers — scored by signal strength, seniority, and recommended outreach angle`"
    />

    <div class="flex-1 p-6 space-y-4 max-w-6xl w-full mx-auto">
      <!-- Error state -->
      <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Could not load prospects — make sure the backend is running.
      </div>

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

      <AppCard v-if="pending">
        <div class="px-6 py-8 text-center text-sm text-gray-400 animate-pulse">Loading prospects…</div>
      </AppCard>

      <AppCard v-else>
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
                  <div class="text-xs text-gray-400">{{ p.title ?? '—' }}</div>
                </td>
                <td class="hidden md:table-cell">
                  <div class="text-gray-700">{{ p.company_name }}</div>
                  <div class="text-xs text-gray-400">{{ p.seniority ?? '' }}</div>
                </td>
                <td class="hidden lg:table-cell">
                  <div class="flex items-center gap-2">
                    <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-100">
                      <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                      </svg>
                      {{ p.signal_count }}
                    </span>
                    <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-rose-50 text-rose-600 ring-1 ring-inset ring-rose-100">
                      {{ p.pain_point_count }} pain
                    </span>
                  </div>
                </td>
                <td class="text-right font-semibold tabular-nums text-violet-600">{{ p.opportunity_score }}</td>
                <td>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset"
                    :class="scoreLabelColor[p.score_label] ?? 'bg-gray-100 text-gray-600 ring-gray-200'"
                  >
                    {{ p.score_label }}
                  </span>
                </td>
                <td class="hidden xl:table-cell text-xs text-gray-500 max-w-sm truncate">
                  {{ p.recommended_angle ?? '—' }}
                </td>
              </tr>
              <tr v-if="!filtered.length && !pending">
                <td colspan="6" class="py-12 text-center">
                  <p class="text-sm text-gray-400 font-medium">No prospects match this filter.</p>
                  <p class="text-xs text-gray-300 mt-1">Load demo data from the Command Center or switch to "All" to see every prospect.</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </AppCard>
    </div>
  </div>
</template>
