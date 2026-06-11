<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  type?: 'button' | 'submit' | 'reset'
}>()
</script>

<template>
  <button
    :type="type ?? 'button'"
    :disabled="disabled || loading"
    class="inline-flex items-center gap-2 font-medium rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed"
    :class="[
      size === 'sm' ? 'px-3 py-1.5 text-xs' : size === 'lg' ? 'px-5 py-2.5 text-sm' : 'px-4 py-2 text-sm',
      variant === 'primary' || !variant
        ? 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500'
        : variant === 'secondary'
        ? 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus-visible:ring-gray-400'
        : variant === 'ghost'
        ? 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 focus-visible:ring-gray-400'
        : variant === 'danger'
        ? 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500'
        : variant === 'success'
        ? 'bg-emerald-600 text-white hover:bg-emerald-700 focus-visible:ring-emerald-500'
        : '',
    ]"
  >
    <svg v-if="loading" class="animate-spin h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" fill="none">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <slot />
  </button>
</template>
