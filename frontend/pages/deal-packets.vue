<script setup lang="ts">
import type { BDDealPacket } from '~/types'

const api = useApi()

const { data: packets, pending, error } = await useAsyncData<BDDealPacket[]>(
  'bd-deal-packets',
  () => api.getBDDealPackets(),
  { default: () => [] }
)

const statusConfig: Record<string, { label: string; color: string }> = {
  draft: { label: 'Draft', color: 'bg-gray-100 text-gray-600' },
  review: { label: 'In Review', color: 'bg-amber-50 text-amber-700' },
  approved: { label: 'Approved', color: 'bg-emerald-50 text-emerald-700' },
  executed: { label: 'Executed', color: 'bg-blue-50 text-blue-700' },
}

const activeStatus = ref('all')

const statusFilters = [
  { value: 'all', label: 'All' },
  { value: 'draft', label: 'Draft' },
  { value: 'review', label: 'In Review' },
  { value: 'approved', label: 'Approved' },
]

const filtered = computed(() => {
  const list = packets.value ?? []
  return activeStatus.value === 'all'
    ? list
    : list.filter(p => p.status === activeStatus.value)
})

function checklist_done(pkt: BDDealPacket): number {
  return pkt.checklist.filter(c => c.done).length
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Deal Packets"
      :subtitle="pending ? 'Loading…' : `${(packets ?? []).length} deal packets — comprehensive BD briefings for each engagement`"
    />

    <div class="flex-1 p-6 space-y-4 max-w-5xl w-full mx-auto">
      <!-- Error -->
      <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Could not load deal packets — make sure the backend is running.
      </div>

      <!-- Context note -->
      <div class="flex items-start gap-3 rounded-xl bg-violet-50 border border-violet-100 px-4 py-3">
        <svg class="h-4 w-4 text-violet-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
        </svg>
        <div>
          <p class="text-sm font-medium text-violet-800">Deal Packet = Comprehensive BD Briefing</p>
          <p class="text-xs text-violet-700 mt-0.5">Each packet bundles company context, pain points, value proposition, talking points, and an outreach draft. All outreach drafts are prepared for manual review — DobryBot does not send automatically.</p>
        </div>
      </div>

      <!-- Status filters -->
      <div class="flex gap-1.5 flex-wrap">
        <button
          v-for="f in statusFilters"
          :key="f.value"
          class="inline-flex items-center rounded-lg px-3 py-1.5 text-xs font-medium transition-colors border"
          :class="activeStatus === f.value
            ? 'bg-violet-50 text-violet-700 border-violet-200'
            : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
          @click="activeStatus = f.value"
        >
          {{ f.label }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="pending" class="py-12 text-center text-sm text-gray-400 animate-pulse">Loading deal packets…</div>

      <!-- Packet cards -->
      <div v-else class="space-y-3">
        <AppCard
          v-for="pkt in filtered"
          :key="pkt.id"
        >
          <div class="px-5 py-4">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <h3 class="text-sm font-semibold text-gray-900">{{ pkt.company_name }}</h3>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold"
                    :class="statusConfig[pkt.status]?.color ?? 'bg-gray-100 text-gray-600'"
                  >
                    {{ statusConfig[pkt.status]?.label ?? pkt.status }}
                  </span>
                  <span v-if="pkt.engagement_type" class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-500">
                    {{ pkt.engagement_type }}
                  </span>
                </div>
                <p v-if="pkt.contact_name" class="text-xs text-gray-500 mt-0.5">
                  {{ pkt.contact_name }}{{ pkt.contact_role ? ` · ${pkt.contact_role}` : '' }}
                </p>

                <div class="flex flex-wrap gap-1 mt-2">
                  <span
                    v-for="pp in pkt.pain_points"
                    :key="pp"
                    class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium bg-rose-50 text-rose-600 ring-1 ring-inset ring-rose-100"
                  >
                    {{ pp }}
                  </span>
                </div>

                <div class="flex items-center gap-4 mt-3 text-xs text-gray-500">
                  <span>{{ pkt.talking_points.length }} talking points</span>
                  <span class="text-gray-300">·</span>
                  <span>Checklist {{ checklist_done(pkt) }}/{{ pkt.checklist.length }}</span>
                  <span class="text-gray-300">·</span>
                  <span :class="pkt.outreach_draft ? 'text-emerald-600' : 'text-gray-400'">
                    {{ pkt.outreach_draft ? 'Outreach draft ready' : 'No draft yet' }}
                  </span>
                </div>
              </div>

              <div class="flex-shrink-0 text-right">
                <div class="text-xs text-gray-400">{{ pkt.updated_at ? pkt.updated_at.slice(0, 10) : pkt.created_at.slice(0, 10) }}</div>
                <div v-if="pkt.checklist.length" class="mt-2 w-20">
                  <div class="flex items-center justify-between text-[10px] text-gray-400 mb-1">
                    <span>{{ checklist_done(pkt) }}/{{ pkt.checklist.length }}</span>
                    <span>{{ Math.round((checklist_done(pkt) / pkt.checklist.length) * 100) }}%</span>
                  </div>
                  <div class="h-1.5 w-full rounded-full bg-gray-100">
                    <div
                      class="h-1.5 rounded-full bg-emerald-500 transition-all"
                      :style="{ width: `${(checklist_done(pkt) / pkt.checklist.length) * 100}%` }"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </AppCard>

        <div v-if="!filtered.length" class="py-16 text-center">
          <p class="text-sm text-gray-400">No deal packets match the current filter.</p>
        </div>
      </div>
    </div>
  </div>
</template>
