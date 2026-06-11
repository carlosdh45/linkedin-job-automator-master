<template>
  <div class="flex-1 overflow-y-auto">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-slate-950/80 backdrop-blur border-b border-slate-800 px-8 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-100">Leads</h1>
        <p class="text-xs text-slate-500 mt-0.5">{{ filteredLeads.length }} of {{ allLeads.length }} leads</p>
      </div>
      <button
        class="px-3 py-1.5 text-xs font-medium text-slate-400 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
        @click="() => refresh()"
      >
        Refresh
      </button>
    </div>

    <div class="px-8 py-6 space-y-4 max-w-6xl mx-auto">
      <!-- Filter tabs -->
      <div class="flex gap-2 flex-wrap">
        <button
          v-for="f in filters"
          :key="f.value"
          :class="[
            'px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors',
            activeFilter === f.value
              ? 'bg-violet-600/20 text-violet-400 border-violet-700/50'
              : 'text-slate-400 bg-slate-800 border-slate-700 hover:bg-slate-700 hover:text-slate-200',
          ]"
          @click="activeFilter = f.value"
        >
          {{ f.label }}
          <span v-if="f.count > 0" class="ml-1.5 opacity-70">{{ f.count }}</span>
        </button>
      </div>

      <LoadingSpinner v-if="pending" label="Loading leads…" />

      <template v-else-if="error">
        <div class="rounded-xl border border-red-900/50 bg-red-950/30 p-6 text-center">
          <p class="text-red-400 font-medium">Could not load leads.</p>
          <button class="mt-4 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-sm text-slate-200 rounded-lg" @click="() => refresh()">Retry</button>
        </div>
      </template>

      <template v-else>
        <div v-if="filteredLeads.length === 0" class="rounded-xl border border-slate-800 bg-slate-800/50 p-12 text-center">
          <p class="text-slate-400 font-medium">No leads found for this filter.</p>
          <p class="text-sm text-slate-600 mt-1">Run <code class="text-slate-500">python main.py --discover-leads</code> to find new leads.</p>
        </div>

        <div v-else class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-slate-700">
                  <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Company</th>
                  <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider hidden md:table-cell">Contact</th>
                  <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider hidden lg:table-cell">Industry</th>
                  <th class="px-5 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Score</th>
                  <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Label</th>
                  <th class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                  <th class="px-5 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider hidden lg:table-cell">Pain Points</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-700/40">
                <tr
                  v-for="lead in filteredLeads"
                  :key="lead.id"
                  class="hover:bg-slate-700/20 transition-colors"
                >
                  <td class="px-5 py-3.5">
                    <p class="font-medium text-slate-200 truncate max-w-xs">{{ lead.company }}</p>
                    <p class="text-xs text-slate-500 mt-0.5 truncate">{{ lead.domain }}</p>
                  </td>
                  <td class="px-5 py-3.5 hidden md:table-cell">
                    <p class="text-slate-300 truncate max-w-xs">{{ lead.contact_name || '—' }}</p>
                    <p class="text-xs text-slate-500 truncate max-w-xs">{{ lead.contact_role || '' }}</p>
                  </td>
                  <td class="px-5 py-3.5 text-slate-400 hidden lg:table-cell">{{ lead.industry || '—' }}</td>
                  <td class="px-5 py-3.5 text-right">
                    <span class="font-semibold text-violet-400 tabular-nums">{{ lead.lead_score }}</span>
                  </td>
                  <td class="px-5 py-3.5">
                    <StatusBadge v-if="lead.score_label" :status="lead.score_label" />
                    <span v-else class="text-slate-600">—</span>
                  </td>
                  <td class="px-5 py-3.5">
                    <StatusBadge :status="lead.status" />
                  </td>
                  <td class="px-5 py-3.5 text-center hidden lg:table-cell">
                    <span
                      v-if="lead.pain_points && lead.pain_points.length > 0"
                      class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-400 border border-slate-600"
                    >
                      {{ lead.pain_points.length }}
                    </span>
                    <span v-else class="text-slate-600">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Lead } from '~/types'

const api = useApi()
const activeFilter = ref('all')

const { data, pending, error, refresh } = await useAsyncData('leads', () => api.getLeads())

const allLeads = computed<Lead[]>(() => data.value?.leads ?? [])

const statusCounts = computed(() => {
  const counts: Record<string, number> = {}
  for (const lead of allLeads.value) {
    counts[lead.status] = (counts[lead.status] || 0) + 1
  }
  return counts
})

const filters = computed(() => [
  { value: 'all', label: 'All', count: allLeads.value.length },
  { value: 'scored', label: 'Scored', count: statusCounts.value.scored || 0 },
  { value: 'draft_ready', label: 'Draft Ready', count: statusCounts.value.draft_ready || 0 },
  { value: 'approved', label: 'Approved', count: statusCounts.value.approved || 0 },
  { value: 'skipped', label: 'Skipped', count: statusCounts.value.skipped || 0 },
])

const filteredLeads = computed(() => {
  if (activeFilter.value === 'all') return allLeads.value
  return allLeads.value.filter(l => l.status === activeFilter.value)
})
</script>
