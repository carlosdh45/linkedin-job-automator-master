<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/75 backdrop-blur-sm" @click="close" />
        <div class="relative w-full max-w-md bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl">
          <div class="p-6">
            <div class="flex items-start gap-4">
              <div :class="iconWrap" class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" :d="iconPath" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-base font-semibold text-slate-100">{{ title }}</h3>
                <p class="mt-1.5 text-sm text-slate-400 leading-relaxed whitespace-pre-line">{{ message }}</p>
                <div v-if="hasInput" class="mt-3">
                  <textarea
                    v-model="inputVal"
                    :placeholder="inputPlaceholder || 'Optional note…'"
                    rows="2"
                    class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  />
                </div>
              </div>
            </div>
          </div>
          <div class="px-6 pb-6 flex justify-end gap-3">
            <button
              type="button"
              class="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
              @click="close"
            >
              {{ cancelLabel || 'Cancel' }}
            </button>
            <button
              type="button"
              :class="confirmCls"
              class="px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors"
              @click="onConfirm"
            >
              {{ confirmLabel || 'Confirm' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title: string
    message: string
    confirmLabel?: string
    cancelLabel?: string
    variant?: 'success' | 'warning' | 'info' | 'danger'
    hasInput?: boolean
    inputPlaceholder?: string
  }>(),
  { variant: 'info', hasInput: false }
)

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  confirm: [inputValue: string]
}>()

const inputVal = ref('')

const iconWrap = computed(() => ({
  'bg-emerald-900/50 text-emerald-400': props.variant === 'success',
  'bg-amber-900/50 text-amber-400': props.variant === 'warning',
  'bg-blue-900/50 text-blue-400': props.variant === 'info',
  'bg-red-900/50 text-red-400': props.variant === 'danger',
}))

const iconPath = computed(() => {
  if (props.variant === 'success') return 'M4.5 12.75l6 6 9-13.5'
  if (props.variant === 'warning') return 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z'
  if (props.variant === 'danger') return 'M6 18L18 6M6 6l12 12'
  return 'M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z'
})

const confirmCls = computed(() => ({
  'bg-emerald-600 hover:bg-emerald-500': props.variant === 'success',
  'bg-amber-600 hover:bg-amber-500': props.variant === 'warning',
  'bg-blue-600 hover:bg-blue-500': props.variant === 'info',
  'bg-red-600 hover:bg-red-500': props.variant === 'danger',
}))

function close() {
  emit('update:modelValue', false)
}

function onConfirm() {
  emit('confirm', inputVal.value)
  emit('update:modelValue', false)
  inputVal.value = ''
}
</script>

<style scoped>
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.15s ease;
}
.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}
</style>
