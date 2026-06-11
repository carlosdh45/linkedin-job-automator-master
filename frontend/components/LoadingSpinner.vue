<script setup lang="ts">
defineProps<{ label?: string }>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 gap-3">
    <div class="h-8 w-8 animate-spin rounded-full border-2 border-gray-200 border-t-blue-600" />
    <p v-if="label" class="text-sm text-gray-500">{{ label }}</p>
  </div>
</template>
