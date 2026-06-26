<script setup lang="ts">
interface PipelineStage {
  slug: string
  label: string
  color: string
  textColor: string
  bgColor: string
  count: number
  value: string | null
  deals: MockDeal[]
}

interface MockDeal {
  id: string
  company: string
  contact: string | null
  score: number
  scoreLabel: string
  lastAction: string
  daysInStage: number
}

const stages: PipelineStage[] = [
  {
    slug: 'identified',
    label: 'Identified',
    color: 'border-gray-300',
    textColor: 'text-gray-700',
    bgColor: 'bg-gray-50',
    count: 0,
    value: null,
    deals: [],
  },
  {
    slug: 'researched',
    label: 'Researched',
    color: 'border-blue-300',
    textColor: 'text-blue-700',
    bgColor: 'bg-blue-50',
    count: 2,
    value: null,
    deals: [
      { id: 'r1', company: 'Meridian Labs', contact: 'Alex Rivera', score: 89, scoreLabel: 'hot', lastAction: 'Signal detected: 3 DevOps hires', daysInStage: 4 },
      { id: 'r2', company: 'Stratos Engineering', contact: 'Jamie Okafor', score: 74, scoreLabel: 'warm', lastAction: 'Tech change signal reviewed', daysInStage: 8 },
    ],
  },
  {
    slug: 'qualified',
    label: 'Qualified',
    color: 'border-violet-300',
    textColor: 'text-violet-700',
    bgColor: 'bg-violet-50',
    count: 1,
    value: null,
    deals: [
      { id: 'q1', company: 'Vantage Capital', contact: 'Morgan Chen', score: 82, scoreLabel: 'hot', lastAction: 'Deal packet created', daysInStage: 2 },
    ],
  },
  {
    slug: 'engaged',
    label: 'Engaged',
    color: 'border-amber-300',
    textColor: 'text-amber-700',
    bgColor: 'bg-amber-50',
    count: 0,
    value: null,
    deals: [],
  },
  {
    slug: 'active',
    label: 'Active',
    color: 'border-emerald-300',
    textColor: 'text-emerald-700',
    bgColor: 'bg-emerald-50',
    count: 0,
    value: null,
    deals: [],
  },
]

const viewMode = ref<'kanban' | 'list'>('kanban')

const totalDeals = computed(() => stages.reduce((n, s) => n + s.count, 0))

const scoreLabelColor: Record<string, string> = {
  hot: 'bg-rose-50 text-rose-700',
  warm: 'bg-amber-50 text-amber-700',
  cold: 'bg-gray-100 text-gray-500',
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Pipeline"
      :subtitle="`${totalDeals} deals across ${stages.length} stages`"
    >
      <template #actions>
        <div class="flex gap-1 rounded-lg border border-gray-200 bg-white p-0.5">
          <button
            class="rounded-md px-3 py-1 text-xs font-medium transition-colors"
            :class="viewMode === 'kanban' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-700'"
            @click="viewMode = 'kanban'"
          >
            Kanban
          </button>
          <button
            class="rounded-md px-3 py-1 text-xs font-medium transition-colors"
            :class="viewMode === 'list' ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-700'"
            @click="viewMode = 'list'"
          >
            List
          </button>
        </div>
        <span class="inline-flex items-center gap-1.5 rounded-lg bg-blue-50 border border-blue-100 px-3 py-1.5 text-xs font-medium text-blue-700">
          Placeholder data
        </span>
      </template>
    </PageHeader>

    <div class="flex-1 p-6 max-w-full mx-auto space-y-4">
      <!-- Stage summary row -->
      <div class="grid grid-cols-5 gap-3">
        <div
          v-for="stage in stages"
          :key="stage.slug"
          class="rounded-xl border px-4 py-3 text-center"
          :class="[stage.bgColor, stage.color]"
        >
          <div class="text-2xl font-bold tabular-nums" :class="stage.textColor">{{ stage.count }}</div>
          <div class="text-xs font-medium mt-0.5" :class="stage.textColor">{{ stage.label }}</div>
        </div>
      </div>

      <!-- Kanban view -->
      <template v-if="viewMode === 'kanban'">
        <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
          <div
            v-for="stage in stages"
            :key="stage.slug"
            class="flex flex-col gap-2"
          >
            <!-- Stage header -->
            <div class="flex items-center gap-2 px-1">
              <span
                class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold"
                :class="[stage.bgColor, stage.textColor]"
              >
                {{ stage.label }}
              </span>
              <span class="text-xs text-gray-400">{{ stage.count }}</span>
            </div>

            <!-- Deal cards -->
            <div
              v-for="deal in stage.deals"
              :key="deal.id"
              class="rounded-xl border border-gray-200 bg-white px-4 py-3 space-y-2"
            >
              <div class="flex items-start justify-between gap-1">
                <p class="text-sm font-semibold text-gray-900 leading-tight">{{ deal.company }}</p>
                <span
                  class="inline-flex flex-shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
                  :class="scoreLabelColor[deal.scoreLabel] ?? 'bg-gray-100 text-gray-500'"
                >
                  {{ deal.scoreLabel }}
                </span>
              </div>
              <p v-if="deal.contact" class="text-xs text-gray-500">{{ deal.contact }}</p>
              <p class="text-xs text-gray-400 leading-snug">{{ deal.lastAction }}</p>
              <div class="flex items-center justify-between text-xs text-gray-400">
                <span>{{ deal.daysInStage }}d in stage</span>
                <span class="font-semibold text-blue-600">{{ deal.score }}</span>
              </div>
            </div>

            <!-- Empty column -->
            <div
              v-if="stage.deals.length === 0"
              class="rounded-xl border border-dashed border-gray-200 px-4 py-6 text-center"
            >
              <p class="text-xs text-gray-400">No deals yet</p>
            </div>
          </div>
        </div>
      </template>

      <!-- List view -->
      <template v-else>
        <AppCard>
          <div class="overflow-x-auto">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Contact</th>
                  <th>Stage</th>
                  <th class="text-right">Score</th>
                  <th>Signal</th>
                  <th class="hidden lg:table-cell">Last Action</th>
                  <th class="text-right hidden md:table-cell">Days in Stage</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="stage in stages" :key="stage.slug">
                  <tr v-for="deal in stage.deals" :key="deal.id">
                    <td>
                      <div class="font-medium text-gray-900">{{ deal.company }}</div>
                    </td>
                    <td class="text-gray-500">{{ deal.contact || '—' }}</td>
                    <td>
                      <span
                        class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium"
                        :class="[stage.bgColor, stage.textColor]"
                      >
                        {{ stage.label }}
                      </span>
                    </td>
                    <td class="text-right font-semibold tabular-nums text-blue-600">{{ deal.score }}</td>
                    <td>
                      <span
                        class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold"
                        :class="scoreLabelColor[deal.scoreLabel] ?? 'bg-gray-100 text-gray-500'"
                      >
                        {{ deal.scoreLabel }}
                      </span>
                    </td>
                    <td class="hidden lg:table-cell text-xs text-gray-500 max-w-xs truncate">{{ deal.lastAction }}</td>
                    <td class="text-right hidden md:table-cell text-gray-500">{{ deal.daysInStage }}d</td>
                  </tr>
                </template>
                <tr v-if="totalDeals === 0">
                  <td colspan="7" class="py-10 text-center text-sm text-gray-400">No deals in pipeline yet.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </AppCard>
      </template>

      <!-- Phase notice -->
      <div class="flex items-start gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3">
        <svg class="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
        </svg>
        <div>
          <p class="text-sm font-medium text-gray-700">Phase 3: Live Pipeline Tracking</p>
          <p class="text-xs text-gray-500 mt-0.5">In Phase 3, pipeline connects to real opportunity records — stage transitions are logged, velocity is tracked, and the Command Center snapshot updates automatically. Drag-and-drop stage movement is planned for Phase 4.</p>
        </div>
      </div>
    </div>
  </div>
</template>
