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
  'bg-emerald-100 text-emerald-600': props.variant === 'success',
  'bg-amber-100 text-amber-600':     props.variant === 'warning',
  'bg-blue-100 text-blue-600':       props.variant === 'info',
  'bg-red-100 text-red-600':         props.variant === 'danger',
}))

const iconPath = computed(() => {
  if (props.variant === 'success') return 'M4.5 12.75l6 6 9-13.5'
  if (props.variant === 'warning') return 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z'
  if (props.variant === 'danger')  return 'M6 18L18 6M6 6l12 12'
  return 'M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z'
})

const confirmBtnCls = computed(() => ({
  'bg-emerald-600 hover:bg-emerald-700 focus-visible:ring-emerald-500': props.variant === 'success',
  'bg-amber-600 hover:bg-amber-700 focus-visible:ring-amber-500':       props.variant === 'warning',
  'bg-blue-600 hover:bg-blue-700 focus-visible:ring-blue-500':           props.variant === 'info',
  'bg-red-600 hover:bg-red-700 focus-visible:ring-red-500':             props.variant === 'danger',
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

<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="close" />
        <div class="relative w-full max-w-md bg-white rounded-2xl border border-gray-200 shadow-dialog overflow-hidden">
          <div class="p-6">
            <div class="flex items-start gap-4">
              <div class="flex-shrink-0 flex h-10 w-10 items-center justify-center rounded-xl" :class="iconWrap">
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" :d="iconPath" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-base font-semibold text-gray-900">{{ title }}</h3>
                <p class="mt-1.5 text-sm text-gray-600 leading-relaxed whitespace-pre-line">{{ message }}</p>
                <textarea
                  v-if="hasInput"
                  v-model="inputVal"
                  :placeholder="inputPlaceholder || 'Optional note…'"
                  rows="2"
                  class="mt-3 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 resize-none"
                />
              </div>
            </div>
          </div>
          <div class="flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 border-t border-gray-200">
            <button
              type="button"
              class="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-1 transition-colors"
              @click="close"
            >
              {{ cancelLabel || 'Cancel' }}
            </button>
            <button
              type="button"
              class="rounded-lg px-4 py-2 text-sm font-medium text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 transition-colors"
              :class="confirmBtnCls"
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
