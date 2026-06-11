<template>
  <div class="flex flex-col items-center justify-center py-16 gap-3">
    <div class="w-8 h-8 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
    <p v-if="label" class="text-sm text-slate-500">{{ label }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label?: string }>()
</script>
