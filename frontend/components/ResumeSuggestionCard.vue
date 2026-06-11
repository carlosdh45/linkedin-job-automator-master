<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div class="flex items-start gap-3 rounded-lg border border-dashed border-gray-200 bg-gray-50 px-3 py-2.5 opacity-60">
    <svg class="h-4 w-4 text-gray-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
    </svg>
    <div class="flex-1 min-w-0">
      <p class="text-xs font-medium text-gray-600">{{ title }}</p>
      <p v-if="description" class="text-[10px] text-gray-400 mt-0.5">{{ description }}</p>
    </div>
    <span class="flex-shrink-0 rounded-full bg-gray-200 px-1.5 py-0.5 text-[10px] font-medium text-gray-500">Soon</span>
  </div>
</template>
