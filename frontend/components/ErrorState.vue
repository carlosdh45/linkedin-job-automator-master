<script setup lang="ts">
defineProps<{
  message?: string
  showRetry?: boolean
}>()

const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 text-center px-4">
    <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-red-50">
      <svg class="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
    </div>
    <h3 class="text-sm font-semibold text-gray-900">Something went wrong</h3>
    <p v-if="message" class="mt-1 text-sm text-gray-500 max-w-xs">{{ message }}</p>
    <button
      v-if="showRetry"
      class="mt-4 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
      @click="emit('retry')"
    >
      Try again
    </button>
  </div>
</template>
