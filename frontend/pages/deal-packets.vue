<script setup lang="ts">
interface MockDealPacket {
  id: string
  company: string
  contact: string | null
  contactRole: string | null
  engagementType: string
  painPoints: string[]
  status: string
  talkingPoints: number
  hasOutreachDraft: boolean
  checklistTotal: number
  checklistDone: number
  updatedAt: string
}

const mockPackets: MockDealPacket[] = [
  {
    id: '1', company: 'Meridian Labs', contact: 'Alex Rivera', contactRole: 'VP of Engineering',
    engagementType: 'New Business',
    painPoints: ['Manual deployment pipeline', 'Slow release cycles'],
    status: 'draft', talkingPoints: 4, hasOutreachDraft: true,
    checklistTotal: 6, checklistDone: 2, updatedAt: '2026-06-24',
  },
  {
    id: '2', company: 'Vantage Capital', contact: 'Morgan Chen', contactRole: 'CTO',
    engagementType: 'New Business',
    painPoints: ['Compliance reporting overhead', 'Manual audit prep'],
    status: 'review', talkingPoints: 5, hasOutreachDraft: true,
    checklistTotal: 5, checklistDone: 4, updatedAt: '2026-06-23',
  },
  {
    id: '3', company: 'Stratos Engineering', contact: null, contactRole: null,
    engagementType: 'New Business',
    painPoints: ['Developer onboarding velocity'],
    status: 'draft', talkingPoints: 3, hasOutreachDraft: false,
    checklistTotal: 5, checklistDone: 1, updatedAt: '2026-06-20',
  },
]

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

const filtered = computed(() =>
  activeStatus.value === 'all'
    ? mockPackets
    : mockPackets.filter(p => p.status === activeStatus.value)
)
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Deal Packets"
      :subtitle="`${mockPackets.length} deal packets — comprehensive BD briefings for each engagement`"
    >
      <template #actions>
        <span class="inline-flex items-center gap-1.5 rounded-lg bg-blue-50 border border-blue-100 px-3 py-1.5 text-xs font-medium text-blue-700">
          Placeholder data
        </span>
      </template>
    </PageHeader>

    <div class="flex-1 p-6 space-y-4 max-w-5xl w-full mx-auto">
      <!-- Context note about Deal Packet concept -->
      <div class="flex items-start gap-3 rounded-xl bg-violet-50 border border-violet-100 px-4 py-3">
        <svg class="h-4 w-4 text-violet-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
        </svg>
        <div>
          <p class="text-sm font-medium text-violet-800">Deal Packet = Application Packet, reframed for BD</p>
          <p class="text-xs text-violet-700 mt-0.5">A Deal Packet bundles company context, pain points, value proposition, talking points, and outreach drafts into one briefing. All outreach drafts inside a Deal Packet go through the Review Queue before use.</p>
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

      <!-- Packet cards -->
      <div class="space-y-3">
        <AppCard
          v-for="pkt in filtered"
          :key="pkt.id"
        >
          <div class="px-5 py-4">
            <div class="flex items-start justify-between gap-4">
              <!-- Left -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <h3 class="text-sm font-semibold text-gray-900">{{ pkt.company }}</h3>
                  <span
                    class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold"
                    :class="statusConfig[pkt.status]?.color ?? 'bg-gray-100 text-gray-600'"
                  >
                    {{ statusConfig[pkt.status]?.label ?? pkt.status }}
                  </span>
                  <span class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-500">
                    {{ pkt.engagementType }}
                  </span>
                </div>
                <p v-if="pkt.contact" class="text-xs text-gray-500 mt-0.5">
                  {{ pkt.contact }} · {{ pkt.contactRole }}
                </p>

                <!-- Pain points -->
                <div class="flex flex-wrap gap-1 mt-2">
                  <span
                    v-for="pp in pkt.painPoints"
                    :key="pp"
                    class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium bg-rose-50 text-rose-600 ring-1 ring-inset ring-rose-100"
                  >
                    {{ pp }}
                  </span>
                </div>

                <!-- Metadata row -->
                <div class="flex items-center gap-4 mt-3 text-xs text-gray-500">
                  <span>{{ pkt.talkingPoints }} talking points</span>
                  <span class="text-gray-300">·</span>
                  <span>
                    Checklist {{ pkt.checklistDone }}/{{ pkt.checklistTotal }}
                  </span>
                  <span class="text-gray-300">·</span>
                  <span
                    :class="pkt.hasOutreachDraft ? 'text-emerald-600' : 'text-gray-400'"
                  >
                    {{ pkt.hasOutreachDraft ? 'Outreach draft ready' : 'No draft yet' }}
                  </span>
                </div>
              </div>

              <!-- Right: checklist progress + date -->
              <div class="flex-shrink-0 text-right">
                <div class="text-xs text-gray-400">Updated {{ pkt.updatedAt }}</div>
                <!-- Checklist progress bar -->
                <div class="mt-2 w-20">
                  <div class="flex items-center justify-between text-[10px] text-gray-400 mb-1">
                    <span>{{ pkt.checklistDone }}/{{ pkt.checklistTotal }}</span>
                    <span>{{ Math.round((pkt.checklistDone / pkt.checklistTotal) * 100) }}%</span>
                  </div>
                  <div class="h-1.5 w-full rounded-full bg-gray-100">
                    <div
                      class="h-1.5 rounded-full bg-emerald-500 transition-all"
                      :style="{ width: `${(pkt.checklistDone / pkt.checklistTotal) * 100}%` }"
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

      <!-- Phase notice -->
      <div class="flex items-start gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3">
        <svg class="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
        </svg>
        <div>
          <p class="text-sm font-medium text-gray-700">Phase 2: Deal Packet Generation</p>
          <p class="text-xs text-gray-500 mt-0.5">In Phase 2, Deal Packets are generated from Company + Prospect + Signal context automatically. The existing Application Packet endpoint migrates to <code class="font-mono">/api/deal-packets</code> with BD-specific fields. Human review stays mandatory.</p>
        </div>
      </div>
    </div>
  </div>
</template>
