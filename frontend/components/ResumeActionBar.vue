<script setup lang="ts">
import type { ResumeTone } from '~/types'

const props = defineProps<{
  saving: boolean
  generating: boolean
  saveResult: 'idle' | 'success' | 'error'
  copied: boolean
  copiedPlain: boolean
  hasPreview: boolean
  tone: ResumeTone
}>()

const emit = defineEmits<{
  save: []
  regenerate: []
  'copy-markdown': []
  'copy-plain': []
  print: []
  'update:tone': [value: ResumeTone]
}>()

const TONES: { value: ResumeTone; label: string; hint: string }[] = [
  { value: 'professional', label: 'Professional', hint: 'Balanced, standard format' },
  { value: 'executive',    label: 'Executive',    hint: 'Outcome-focused, concise scope' },
  { value: 'technical',    label: 'Technical',    hint: 'Tech detail, fuller context' },
  { value: 'concise',      label: 'Concise',      hint: 'Trimmed bullets, brief summary' },
]
</script>

<template>
  <div class="px-6 pt-4 pb-2">
    <div class="max-w-[1600px] mx-auto flex flex-wrap items-center gap-3">

      <!-- Save -->
      <button
        :disabled="saving"
        class="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-semibold text-white hover:bg-gray-800 disabled:opacity-60 transition shadow-sm"
        @click="emit('save')"
      >
        <svg v-if="saving" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
        <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.593 3.322c1.1.128 1.907 1.077 1.907 2.185V21L12 17.25 4.5 21V5.507c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0z" />
        </svg>
        {{ saving ? 'Saving…' : 'Save' }}
      </button>

      <!-- Regenerate -->
      <button
        :disabled="generating"
        class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 transition shadow-sm"
        @click="emit('regenerate')"
      >
        <svg v-if="generating" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
        <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
        </svg>
        {{ generating ? 'Generating…' : 'Regenerate Draft' }}
      </button>

      <!-- Divider -->
      <div class="h-6 w-px bg-gray-200" />

      <!-- Copy Markdown -->
      <button
        :disabled="!hasPreview"
        class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition"
        @click="emit('copy-markdown')"
      >
        <svg v-if="copied" class="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184" />
        </svg>
        {{ copied ? 'Copied!' : 'Copy Markdown' }}
      </button>

      <!-- Copy Plain Text -->
      <button
        :disabled="!hasPreview"
        class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition"
        @click="emit('copy-plain')"
      >
        <svg v-if="copiedPlain" class="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        {{ copiedPlain ? 'Copied!' : 'Copy Plain Text' }}
      </button>

      <!-- Print -->
      <button
        :disabled="!hasPreview"
        class="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition"
        @click="emit('print')"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0021 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 00-1.913-.247M6.34 18H5.25A2.25 2.25 0 013 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 011.913-.247m10.5 0a48.536 48.536 0 00-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18 10.5h.008v.008H18V10.5zm-3 0h.008v.008H15V10.5z" />
        </svg>
        Print
      </button>

      <!-- Export PDF placeholder -->
      <button
        disabled
        title="PDF export coming in a future phase"
        class="inline-flex items-center gap-2 rounded-lg border border-dashed border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-400 cursor-not-allowed"
      >
        <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
        Export PDF
        <span class="rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-400">Soon</span>
      </button>

      <!-- Spacer -->
      <div class="flex-1" />

      <!-- Tone selector -->
      <div class="flex items-center gap-2">
        <span class="text-xs font-medium text-gray-500">Tone:</span>
        <div class="flex gap-0.5 p-0.5 bg-gray-100 rounded-lg">
          <button
            v-for="t in TONES"
            :key="t.value"
            :title="t.hint"
            class="px-2.5 py-1 rounded-md text-xs font-medium transition-colors"
            :class="tone === t.value
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'"
            @click="emit('update:tone', t.value)"
          >
            {{ t.label }}
          </button>
        </div>
      </div>

      <!-- Save feedback -->
      <transition name="fade">
        <span v-if="saveResult === 'success'" class="text-sm text-emerald-600 font-medium">Saved</span>
        <span v-else-if="saveResult === 'error'" class="text-sm text-red-500">Could not save</span>
      </transition>

    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
