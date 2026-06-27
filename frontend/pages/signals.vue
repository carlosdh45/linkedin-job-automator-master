<script setup lang="ts">
import type { BDSignal, BDSignalEvaluationResult, BDCompany } from '~/types'

const api = useApi()

const { data: signals, pending, error, refresh } = await useAsyncData<BDSignal[]>(
  'bd-signals',
  () => api.getBDSignals(),
  { default: () => [] }
)

const { data: companies } = await useAsyncData<BDCompany[]>(
  'bd-companies-signals',
  () => api.getBDCompanies(),
  { default: () => [] }
)

// ── Add Signal form ──────────────────────────────────────────────────────────
const showAddForm = ref(false)
const isSavingSignal = ref(false)
const saveError = ref<string | null>(null)

const newSignal = reactive({
  company_name: '',
  signal_type: 'hiring',
  summary: '',
  source: '',
  relevance_score: 70,
  detected_at: new Date().toISOString().slice(0, 10),
})

const signalTypes = [
  { value: 'hiring', label: 'Hiring Signal' },
  { value: 'funding', label: 'Funding' },
  { value: 'leadership_change', label: 'Leadership Change' },
  { value: 'tech_change', label: 'Tech Change' },
  { value: 'pain_point', label: 'Pain Point' },
  { value: 'growth', label: 'Growth Signal' },
  { value: 'competitive', label: 'Competitive' },
  { value: 'expansion', label: 'Expansion' },
  { value: 'partnership', label: 'Partnership' },
  { value: 'compliance_pressure', label: 'Compliance Pressure' },
  { value: 'market_event', label: 'Market Event' },
  { value: 'other', label: 'Other' },
]

function resetForm() {
  newSignal.company_name = ''
  newSignal.signal_type = 'hiring'
  newSignal.summary = ''
  newSignal.source = ''
  newSignal.relevance_score = 70
  newSignal.detected_at = new Date().toISOString().slice(0, 10)
  saveError.value = null
}

async function saveSignal() {
  if (!newSignal.company_name.trim() || !newSignal.summary.trim()) {
    saveError.value = 'Company name and description are required.'
    return
  }
  isSavingSignal.value = true
  saveError.value = null
  try {
    await api.createBDSignal({
      company_name: newSignal.company_name.trim(),
      signal_type: newSignal.signal_type,
      summary: newSignal.summary.trim(),
      source: newSignal.source.trim() || undefined,
      relevance_score: newSignal.relevance_score,
      detected_at: newSignal.detected_at || undefined,
    })
    showAddForm.value = false
    resetForm()
    await refresh()
  } catch {
    saveError.value = 'Could not save signal — make sure the backend is running.'
  } finally {
    isSavingSignal.value = false
  }
}

const signalTypeConfig: Record<string, { label: string; color: string; icon: string }> = {
  hiring: {
    label: 'Hiring Signal',
    color: 'bg-blue-50 text-blue-700 ring-blue-100',
    icon: 'M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0',
  },
  funding: {
    label: 'Funding',
    color: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
    icon: 'M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  leadership_change: {
    label: 'Leadership Change',
    color: 'bg-violet-50 text-violet-700 ring-violet-100',
    icon: 'M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z',
  },
  tech_change: {
    label: 'Tech Change',
    color: 'bg-indigo-50 text-indigo-700 ring-indigo-100',
    icon: 'M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5',
  },
  competitive: {
    label: 'Competitive',
    color: 'bg-orange-50 text-orange-700 ring-orange-100',
    icon: 'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z',
  },
  pain_point: {
    label: 'Pain Point',
    color: 'bg-rose-50 text-rose-700 ring-rose-100',
    icon: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
  },
  growth: {
    label: 'Growth Signal',
    color: 'bg-teal-50 text-teal-700 ring-teal-100',
    icon: 'M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941',
  },
  other: {
    label: 'Signal',
    color: 'bg-gray-100 text-gray-600 ring-gray-200',
    icon: 'M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z',
  },
}

const strengthConfig: Record<string, { label: string; color: string }> = {
  critical: { label: 'Critical', color: 'bg-red-50 text-red-700 ring-red-200' },
  high:     { label: 'High',     color: 'bg-orange-50 text-orange-700 ring-orange-200' },
  medium:   { label: 'Medium',   color: 'bg-amber-50 text-amber-700 ring-amber-200' },
  low:      { label: 'Low',      color: 'bg-gray-100 text-gray-500 ring-gray-200' },
}

const activeType = ref<string>('all')
const showReviewed = ref(true)
const evaluating = ref<string | null>(null)
const lastResult = ref<BDSignalEvaluationResult | null>(null)

const typeFilters = [
  { value: 'all', label: 'All Types' },
  { value: 'hiring', label: 'Hiring' },
  { value: 'pain_point', label: 'Pain Point' },
  { value: 'leadership_change', label: 'Leadership' },
  { value: 'funding', label: 'Funding' },
  { value: 'tech_change', label: 'Tech Change' },
  { value: 'competitive', label: 'Competitive' },
]

const filtered = computed(() => {
  let list = signals.value ?? []
  if (!showReviewed.value) list = list.filter(s => !s.reviewed)
  if (activeType.value !== 'all') list = list.filter(s => s.signal_type === activeType.value)
  return list
})

const evaluatedCount = computed(() => (signals.value ?? []).filter(s => s.evaluated).length)

async function evaluateSignal(signal: BDSignal) {
  evaluating.value = signal.id
  lastResult.value = null
  try {
    const result = await api.evaluateBDSignal(signal.id)
    lastResult.value = result
    await refresh()
  } catch {
    // non-critical
  } finally {
    evaluating.value = null
  }
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Signals"
      :subtitle="pending ? 'Loading…' : `${filtered.length} buying signals — ${evaluatedCount} evaluated · Hiring, leadership changes, pain points, and more`"
    >
      <template #actions>
        <button
          class="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors"
          :class="!showReviewed
            ? 'bg-blue-50 text-blue-700 border-blue-200'
            : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
          @click="showReviewed = !showReviewed"
        >
          {{ showReviewed ? 'Show unreviewed only' : 'Show all' }}
        </button>
        <button
          class="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 transition-colors"
          @click="showAddForm = !showAddForm; if (!showAddForm) resetForm()"
        >
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Add Signal
        </button>
      </template>
    </PageHeader>

    <div class="flex-1 p-6 space-y-4 max-w-5xl w-full mx-auto">
      <!-- Add Signal form (inline panel) -->
      <AppCard v-if="showAddForm">
        <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
          <h3 class="text-sm font-semibold text-gray-900">Log a Market Signal</h3>
          <p class="text-xs text-gray-400">Saved locally — no external APIs called</p>
        </div>
        <div class="px-5 py-4 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Company name -->
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Company Name <span class="text-red-500">*</span></label>
              <input
                v-model="newSignal.company_name"
                list="company-names-list"
                type="text"
                placeholder="e.g. Meridian Labs"
                class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
              <datalist id="company-names-list">
                <option v-for="co in (companies ?? [])" :key="co.id" :value="co.name" />
              </datalist>
            </div>
            <!-- Signal type -->
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Signal Type <span class="text-red-500">*</span></label>
              <select
                v-model="newSignal.signal_type"
                class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
              >
                <option v-for="st in signalTypes" :key="st.value" :value="st.value">{{ st.label }}</option>
              </select>
            </div>
          </div>

          <!-- Description / summary -->
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Description <span class="text-red-500">*</span></label>
            <textarea
              v-model="newSignal.summary"
              rows="3"
              placeholder="Describe what you observed — the more context, the better the evaluation."
              class="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
            />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Source -->
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Source</label>
              <input
                v-model="newSignal.source"
                type="text"
                placeholder="e.g. LinkedIn, Job board"
                class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
            </div>
            <!-- Relevance score -->
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">
                Relevance Score: <span class="text-blue-600 font-bold">{{ newSignal.relevance_score }}</span>
              </label>
              <input
                v-model.number="newSignal.relevance_score"
                type="range"
                min="1"
                max="100"
                class="w-full accent-blue-600"
              />
              <div class="flex justify-between text-[10px] text-gray-400 mt-0.5">
                <span>Low (1)</span><span>High (100)</span>
              </div>
            </div>
            <!-- Date -->
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Observed Date</label>
              <input
                v-model="newSignal.detected_at"
                type="date"
                class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
            </div>
          </div>

          <!-- Save / cancel -->
          <div class="flex items-center gap-3 pt-1">
            <button
              class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:opacity-50"
              :disabled="isSavingSignal"
              @click="saveSignal"
            >
              {{ isSavingSignal ? 'Saving…' : 'Save Signal' }}
            </button>
            <button
              class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
              @click="showAddForm = false; resetForm()"
            >
              Cancel
            </button>
            <span v-if="saveError" class="text-xs text-red-600">{{ saveError }}</span>
          </div>
        </div>
      </AppCard>

      <!-- Error -->
      <div v-if="error" class="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Could not load signals — make sure the backend is running.
      </div>

      <!-- Last evaluation result toast -->
      <div
        v-if="lastResult"
        class="rounded-xl border border-violet-200 bg-violet-50 px-4 py-3 flex items-start gap-3"
      >
        <svg class="h-4 w-4 text-violet-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
        </svg>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-violet-900">Signal evaluated — strength: {{ lastResult.signal_strength }}</p>
          <p class="text-xs text-violet-700 mt-0.5 leading-snug">{{ lastResult.recommended_action }}</p>
          <p v-if="lastResult.recommendation_created" class="text-xs text-violet-600 mt-1 font-medium">
            Recommendation created for your review queue.
          </p>
        </div>
        <button class="text-violet-400 hover:text-violet-600" @click="lastResult = null">
          <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Type filters -->
      <div class="flex gap-1.5 flex-wrap">
        <button
          v-for="f in typeFilters"
          :key="f.value"
          class="inline-flex items-center rounded-lg px-3 py-1.5 text-xs font-medium transition-colors border"
          :class="activeType === f.value
            ? 'bg-violet-50 text-violet-700 border-violet-200'
            : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:text-gray-900'"
          @click="activeType = f.value"
        >
          {{ f.label }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="pending" class="py-12 text-center text-sm text-gray-400 animate-pulse">Loading signals…</div>

      <!-- Signal cards -->
      <div v-else class="space-y-3">
        <AppCard
          v-for="signal in filtered"
          :key="signal.id"
        >
          <div class="px-5 py-4 flex items-start gap-4">
            <span
              class="mt-0.5 inline-flex flex-shrink-0 rounded-lg px-2.5 py-1 text-xs font-semibold ring-1 ring-inset"
              :class="signalTypeConfig[signal.signal_type]?.color ?? 'bg-gray-100 text-gray-600 ring-gray-200'"
            >
              {{ signalTypeConfig[signal.signal_type]?.label ?? signal.signal_type }}
            </span>

            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <div>
                  <p class="text-sm font-semibold text-gray-900">{{ signal.company_name }}</p>
                  <p class="text-sm text-gray-600 mt-0.5 leading-snug">{{ signal.summary }}</p>
                </div>
                <div class="flex-shrink-0 text-right">
                  <div class="text-lg font-bold tabular-nums text-blue-600">{{ signal.relevance_score }}</div>
                  <div class="text-[10px] text-gray-400">relevance</div>
                </div>
              </div>

              <div class="flex items-center gap-3 mt-2 flex-wrap">
                <span class="text-xs text-gray-400">{{ signal.source ?? 'Unknown source' }}</span>
                <span class="text-xs text-gray-300">·</span>
                <span class="text-xs text-gray-400">{{ signal.detected_at }}</span>

                <!-- Evaluated badge -->
                <template v-if="signal.evaluated">
                  <span class="text-xs text-gray-300">·</span>
                  <span class="inline-flex items-center gap-1 text-xs text-violet-600">
                    <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                    </svg>
                    Evaluated
                  </span>
                  <!-- Strength badge -->
                  <span
                    v-if="signal.signal_strength && signal.signal_strength !== 'medium'"
                    class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset"
                    :class="strengthConfig[signal.signal_strength]?.color ?? 'bg-gray-100 text-gray-500 ring-gray-200'"
                  >
                    {{ strengthConfig[signal.signal_strength]?.label ?? signal.signal_strength }}
                  </span>
                </template>

                <span v-if="signal.reviewed" class="inline-flex items-center gap-1 text-xs text-emerald-600">
                  <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  Reviewed
                </span>
              </div>
            </div>

            <!-- Evaluate button -->
            <button
              class="flex-shrink-0 inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors"
              :class="signal.evaluated
                ? 'border-violet-200 bg-violet-50 text-violet-600 hover:bg-violet-100'
                : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
              :disabled="evaluating === signal.id"
              @click="evaluateSignal(signal)"
            >
              <span v-if="evaluating === signal.id" class="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
              <svg v-else class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
              {{ signal.evaluated ? 'Re-evaluate' : 'Evaluate' }}
            </button>
          </div>
        </AppCard>

        <div v-if="!filtered.length" class="py-16 text-center">
          <p class="text-sm text-gray-400 font-medium">No signals match the current filter.</p>
          <p class="text-xs text-gray-300 mt-1">Try "All Types" or load demo data from the Command Center to see example signals.</p>
        </div>
      </div>
    </div>
  </div>
</template>
