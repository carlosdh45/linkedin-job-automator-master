<script setup lang="ts">
const props = defineProps<{ status: string }>()

const MAP: Record<string, string> = {
  passed:          'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200',
  failed:          'bg-red-50 text-red-700 ring-1 ring-inset ring-red-200',
  pending:         'bg-gray-100 text-gray-600 ring-1 ring-inset ring-gray-200',
  discovered:      'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-200',
  scored:          'bg-violet-50 text-violet-700 ring-1 ring-inset ring-violet-200',
  draft_ready:     'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200',
  approved:        'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200',
  skipped:         'bg-gray-100 text-gray-500 ring-1 ring-inset ring-gray-200',
  sent:            'bg-teal-50 text-teal-700 ring-1 ring-inset ring-teal-200',
  needs_review:    'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200',
  needs_research:  'bg-sky-50 text-sky-700 ring-1 ring-inset ring-sky-200',
  high_priority:   'bg-orange-50 text-orange-700 ring-1 ring-inset ring-orange-200',
  good_fit:        'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-200',
  low_priority:    'bg-gray-100 text-gray-500 ring-1 ring-inset ring-gray-200',
  poor_fit:        'bg-gray-100 text-gray-400 ring-1 ring-inset ring-gray-200',
}

const cls = computed(() => MAP[props.status?.toLowerCase()] ?? 'bg-gray-100 text-gray-600 ring-1 ring-inset ring-gray-200')
const label = computed(() => (props.status || '—').replace(/_/g, ' '))
</script>

<template>
  <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap" :class="cls">
    {{ label }}
  </span>
</template>
