<template>
  <span :class="cls" class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{ status: string }>()

const MAP: Record<string, string> = {
  // quality
  passed: 'bg-emerald-900/60 text-emerald-300 border border-emerald-800/60',
  failed: 'bg-red-900/60 text-red-300 border border-red-800/60',
  pending: 'bg-slate-700 text-slate-400 border border-slate-600',
  // job / lead status
  discovered: 'bg-slate-700 text-slate-400 border border-slate-600',
  scored: 'bg-blue-900/60 text-blue-300 border border-blue-800/60',
  draft_ready: 'bg-violet-900/60 text-violet-300 border border-violet-800/60',
  approved: 'bg-emerald-900/60 text-emerald-300 border border-emerald-800/60',
  skipped: 'bg-slate-700 text-slate-500 border border-slate-600',
  sent: 'bg-teal-900/60 text-teal-300 border border-teal-800/60',
  needs_review: 'bg-amber-900/60 text-amber-300 border border-amber-800/60',
  needs_research: 'bg-sky-900/60 text-sky-300 border border-sky-800/60',
  // score labels
  high_priority: 'bg-orange-900/60 text-orange-300 border border-orange-800/60',
  good_fit: 'bg-blue-900/60 text-blue-300 border border-blue-800/60',
  low_priority: 'bg-slate-700 text-slate-500 border border-slate-600',
  poor_fit: 'bg-slate-700 text-slate-500 border border-slate-600',
}

const cls = computed(() => MAP[props.status?.toLowerCase()] ?? 'bg-slate-700 text-slate-400 border border-slate-600')
const label = computed(() => (props.status || '—').replace(/_/g, ' '))
</script>
