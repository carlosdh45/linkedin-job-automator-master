<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    title: string
    value: string | number
    sub?: string
    icon?: string
    variant?: 'blue' | 'green' | 'violet' | 'amber' | 'rose'
  }>(),
  { variant: 'blue' }
)

const iconClasses = computed(() => ({
  blue:   { wrap: 'bg-blue-50 ring-blue-100',    icon: 'text-blue-600' },
  green:  { wrap: 'bg-emerald-50 ring-emerald-100', icon: 'text-emerald-600' },
  violet: { wrap: 'bg-violet-50 ring-violet-100', icon: 'text-violet-600' },
  amber:  { wrap: 'bg-amber-50 ring-amber-100',  icon: 'text-amber-600' },
  rose:   { wrap: 'bg-rose-50 ring-rose-100',    icon: 'text-rose-600' },
}[props.variant] ?? { wrap: 'bg-blue-50 ring-blue-100', icon: 'text-blue-600' }))
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-xl shadow-card px-5 py-4 flex items-start gap-4">
    <div
      v-if="icon"
      class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg ring-1"
      :class="iconClasses.wrap"
    >
      <svg class="h-5 w-5" :class="iconClasses.icon" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" :d="icon" />
      </svg>
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-xs font-semibold uppercase tracking-wider text-gray-500 truncate">{{ title }}</p>
      <p class="mt-1 text-2xl font-bold text-gray-900 tabular-nums">{{ value }}</p>
      <p v-if="sub" class="mt-0.5 text-xs text-gray-400 truncate">{{ sub }}</p>
    </div>
  </div>
</template>
