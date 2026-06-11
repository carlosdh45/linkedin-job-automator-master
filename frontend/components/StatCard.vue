<template>
  <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 flex items-start gap-4">
    <div
      v-if="icon"
      :class="iconBg"
      class="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
    >
      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" :d="icon" />
      </svg>
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider truncate">{{ title }}</p>
      <p class="mt-1 text-3xl font-bold text-slate-100 tabular-nums">{{ value }}</p>
      <p v-if="sub" class="mt-1 text-xs text-slate-500 truncate">{{ sub }}</p>
    </div>
  </div>
</template>

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

const iconBg = computed(() => ({
  'bg-blue-900/50 text-blue-400': props.variant === 'blue',
  'bg-emerald-900/50 text-emerald-400': props.variant === 'green',
  'bg-violet-900/50 text-violet-400': props.variant === 'violet',
  'bg-amber-900/50 text-amber-400': props.variant === 'amber',
  'bg-rose-900/50 text-rose-400': props.variant === 'rose',
}))
</script>
