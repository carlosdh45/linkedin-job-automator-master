<script setup lang="ts">
defineProps<{
  variant?: 'default' | 'blue' | 'green' | 'amber' | 'red' | 'violet' | 'sky' | 'orange'
}>()
</script>

<template>
  <span
    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset"
    :class="
      variant === 'blue'   ? 'bg-blue-50 text-blue-700 ring-blue-200' :
      variant === 'green'  ? 'bg-emerald-50 text-emerald-700 ring-emerald-200' :
      variant === 'amber'  ? 'bg-amber-50 text-amber-700 ring-amber-200' :
      variant === 'red'    ? 'bg-red-50 text-red-700 ring-red-200' :
      variant === 'violet' ? 'bg-violet-50 text-violet-700 ring-violet-200' :
      variant === 'sky'    ? 'bg-sky-50 text-sky-700 ring-sky-200' :
      variant === 'orange' ? 'bg-orange-50 text-orange-700 ring-orange-200' :
                             'bg-gray-100 text-gray-600 ring-gray-200'
    "
  >
    <slot />
  </span>
</template>
