<script setup lang="ts">
import type { BDPipelineResponse, BDPipelineStage } from '~/types'

const api = useApi()

const { data: pipeline, pending, error } = await useAsyncData<BDPipelineResponse>(
  'bd-pipeline',
  () => api.getBDPipeline(),
  { default: () => ({ stages: [], total_active: 0 }) }
)

const viewMode = ref<'kanban' | 'list'>('kanban')

const stages = computed(() => pipeline.value?.stages ?? [])
const totalDeals = computed(() => pipeline.value?.total_active ?? 0)

const stageColorMap: Record<string, { bg: string; text: string; border: string }> = {
  gray:   { bg: 'bg-gray-50',    text: 'text-gray-700',   border: 'border-gray-300' },
  blue:   { bg: 'bg-blue-50',    text: 'text-blue-700',   border: 'border-blue-300' },
  violet: { bg: 'bg-violet-50',  text: 'text-violet-700', border: 'border-violet-300' },
  amber:  { bg: 'bg-amber-50',   text: 'text-amber-700',  border: 'border-amber-300' },
  orange: { bg: 'bg-orange-50',  text: 'text-orange-700', border: 'border-orange-300' },
  green:  { bg: 'bg-emerald-50', text: 'text-emerald-700',border: 'border-emerald-300' },
}

function stageColors(stage: BDPipelineStage) {
  return stageColorMap[stage.color] ?? stageColorMap.gray
}

const scoreLabelColor: Record<string, string> = {
  hot: 'bg-rose-50 text-rose-700',
  warm: 'bg-amber-50 text-amber-700',
  cold: 'bg-gray-100 text-gray-500',
  disqualified: 'bg-gray-100 text-gray-400',
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Pipeline"
      :subtitle="pending ? 'Loading…' : `${totalDeals} deals across ${stages.length} stages`"
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
      </template>
    </PageHeader>

    <div class="flex-1 p-6 max-w-full mx-auto space-y-4">
      <!-- Error -->
      <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Could not load pipeline — make sure the backend is running.
      </div>

      <!-- Loading -->
      <div v-if="pending" class="py-12 text-center text-sm text-gray-400 animate-pulse">Loading pipeline…</div>

      <template v-else>
        <!-- Stage summary row -->
        <div class="grid grid-cols-3 md:grid-cols-6 gap-3">
          <div
            v-for="stage in stages"
            :key="stage.slug"
            class="rounded-xl border px-4 py-3 text-center"
            :class="[stageColors(stage).bg, stageColors(stage).border]"
          >
            <div class="text-2xl font-bold tabular-nums" :class="stageColors(stage).text">{{ stage.count }}</div>
            <div class="text-xs font-medium mt-0.5" :class="stageColors(stage).text">{{ stage.label }}</div>
          </div>
        </div>

        <!-- Kanban view -->
        <template v-if="viewMode === 'kanban'">
          <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
            <div
              v-for="stage in stages"
              :key="stage.slug"
              class="flex flex-col gap-2"
            >
              <div class="flex items-center gap-2 px-1">
                <span
                  class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold"
                  :class="[stageColors(stage).bg, stageColors(stage).text]"
                >
                  {{ stage.label }}
                </span>
                <span class="text-xs text-gray-400">{{ stage.count }}</span>
              </div>

              <div
                v-for="deal in stage.deals"
                :key="deal.id"
                class="rounded-xl border border-gray-200 bg-white px-4 py-3 space-y-2"
              >
                <div class="flex items-start justify-between gap-1">
                  <p class="text-sm font-semibold text-gray-900 leading-tight">{{ deal.company }}</p>
                  <span
                    class="inline-flex flex-shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
                    :class="scoreLabelColor[deal.score_label] ?? 'bg-gray-100 text-gray-500'"
                  >
                    {{ deal.score_label }}
                  </span>
                </div>
                <p v-if="deal.contact" class="text-xs text-gray-500">{{ deal.contact }}</p>
                <p class="text-xs text-gray-400 leading-snug line-clamp-2">{{ deal.last_action }}</p>
                <div class="flex items-center justify-end text-xs">
                  <span class="font-semibold text-blue-600">{{ deal.score }}</span>
                </div>
              </div>

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
                          :class="[stageColors(stage).bg, stageColors(stage).text]"
                        >
                          {{ stage.label }}
                        </span>
                      </td>
                      <td class="text-right font-semibold tabular-nums text-blue-600">{{ deal.score }}</td>
                      <td>
                        <span
                          class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold"
                          :class="scoreLabelColor[deal.score_label] ?? 'bg-gray-100 text-gray-500'"
                        >
                          {{ deal.score_label }}
                        </span>
                      </td>
                      <td class="hidden lg:table-cell text-xs text-gray-500 max-w-xs truncate">{{ deal.last_action }}</td>
                    </tr>
                  </template>
                  <tr v-if="totalDeals === 0">
                    <td colspan="6" class="py-10 text-center text-sm text-gray-400">No deals in pipeline yet — seed demo data to get started.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </AppCard>
        </template>
      </template>
    </div>
  </div>
</template>
