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
  { value: 'all',        label: 'All',        count: allLeads.value.length },
  { value: 'scored',     label: 'Scored',     count: statusCounts.value.scored || 0 },
  { value: 'draft_ready', label: 'Draft Ready', count: statusCounts.value.draft_ready || 0 },
  { value: 'approved',   label: 'Approved',   count: statusCounts.value.approved || 0 },
  { value: 'skipped',    label: 'Skipped',    count: statusCounts.value.skipped || 0 },
])

const filteredLeads = computed(() => {
  if (activeFilter.value === 'all') return allLeads.value
  return allLeads.value.filter(l => l.status === activeFilter.value)
})
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Leads"
      :subtitle="`${filteredLeads.length} of ${allLeads.length} leads`"
    >
      <template #actions>
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
          <span
            v-if="f.count > 0"
            class="rounded-full px-1.5 py-0.5 text-[10px] font-semibold tabular-nums"
            :class="activeFilter === f.value ? 'bg-violet-100 text-violet-700' : 'bg-gray-100 text-gray-500'"
          >
            {{ f.count }}
          </span>
        </button>
      </div>

      <LoadingSpinner v-if="pending" label="Loading leads…" />

      <template v-else-if="error">
        <AppCard>
          <ErrorState message="Could not load leads." :show-retry="true" @retry="() => refresh()" />
        </AppCard>
      </template>

      <template v-else>
        <AppCard v-if="!filteredLeads.length">
          <EmptyState
            title="No leads found"
            :message="activeFilter === 'all' ? 'Run python main.py --discover-leads to find new leads.' : 'No leads match this filter.'"
          />
        </AppCard>

        <AppCard v-else>
          <div class="overflow-x-auto">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th class="hidden md:table-cell">Contact</th>
                  <th class="hidden lg:table-cell">Industry</th>
                  <th class="text-right">Score</th>
                  <th>Label</th>
                  <th>Status</th>
                  <th class="text-center hidden lg:table-cell">Pain Points</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="lead in filteredLeads" :key="lead.id">
                  <td>
                    <div class="font-medium text-gray-900 truncate max-w-xs">{{ lead.company }}</div>
                    <div class="text-xs text-gray-400 mt-0.5 truncate">{{ lead.domain }}</div>
                  </td>
                  <td class="hidden md:table-cell">
                    <div class="text-gray-700 truncate max-w-xs">{{ lead.contact_name || '—' }}</div>
                    <div class="text-xs text-gray-400 truncate max-w-xs">{{ lead.contact_role || '' }}</div>
                  </td>
                  <td class="hidden lg:table-cell text-gray-500">{{ lead.industry || '—' }}</td>
                  <td class="text-right">
                    <span class="font-semibold tabular-nums text-violet-600">{{ lead.lead_score }}</span>
                  </td>
                  <td>
                    <StatusBadge v-if="lead.score_label" :status="lead.score_label" />
                    <span v-else class="text-gray-300 text-xs">—</span>
                  </td>
                  <td><StatusBadge :status="lead.status" /></td>
                  <td class="text-center hidden lg:table-cell">
                    <span
                      v-if="lead.pain_points?.length"
                      class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 ring-1 ring-inset ring-gray-200"
                    >
                      {{ lead.pain_points.length }}
                    </span>
                    <span v-else class="text-gray-300 text-xs">—</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </AppCard>
      </template>
    </div>
  </div>
</template>
