<template>
  <div class="flex-1 overflow-y-auto">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-slate-950/80 backdrop-blur border-b border-slate-800 px-8 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-100">Review Queue</h1>
        <p class="text-xs text-slate-500 mt-0.5">{{ drafts.length }} draft{{ drafts.length !== 1 ? 's' : '' }} pending review</p>
      </div>
      <button
        class="px-3 py-1.5 text-xs font-medium text-slate-400 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
        @click="() => refresh()"
      >
        Refresh
      </button>
    </div>

    <!-- Toast notifications -->
    <div class="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
      <Transition
        v-for="n in notifications"
        :key="n.id"
        name="toast"
      >
        <div
          :class="n.type === 'success' ? 'bg-emerald-800 border-emerald-700 text-emerald-100' : 'bg-red-900 border-red-800 text-red-100'"
          class="pointer-events-auto px-4 py-3 rounded-xl border shadow-xl text-sm font-medium max-w-sm"
        >
          {{ n.message }}
        </div>
      </Transition>
    </div>

    <div class="px-8 py-6 space-y-4 max-w-4xl mx-auto">
      <!-- Safety reminder -->
      <div class="flex items-start gap-3 px-4 py-3 bg-blue-950/30 border border-blue-900/40 rounded-xl">
        <svg class="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
        </svg>
        <p class="text-sm text-blue-300">
          <strong>Approve</strong> marks a draft as human-approved for your records — it does <strong>not</strong> send anything.
          DobryBot never sends emails or applies to jobs automatically.
        </p>
      </div>

      <LoadingSpinner v-if="pending" label="Loading queue…" />

      <template v-else-if="error">
        <div class="rounded-xl border border-red-900/50 bg-red-950/30 p-6 text-center">
          <p class="text-red-400 font-medium">Could not load review queue.</p>
          <button class="mt-4 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-sm text-slate-200 rounded-lg" @click="() => refresh()">Retry</button>
        </div>
      </template>

      <template v-else>
        <div v-if="drafts.length === 0" class="rounded-xl border border-slate-800 bg-slate-800/50 p-16 text-center">
          <div class="w-12 h-12 rounded-full bg-emerald-900/40 flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
          <p class="text-slate-300 font-semibold">Queue is empty</p>
          <p class="text-sm text-slate-500 mt-1">No drafts are pending review. Run the CLI to generate outreach.</p>
        </div>

        <div v-else class="space-y-4">
          <div
            v-for="draft in drafts"
            :key="draft.id"
            class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden"
            :class="{ 'opacity-50 pointer-events-none': processingId === draft.id }"
          >
            <!-- Card header -->
            <div class="px-5 py-4 border-b border-slate-700 flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">{{ draft.outreach_type }}</span>
                  <span class="text-slate-700">·</span>
                  <span class="text-xs text-slate-500">ID {{ draft.id }}</span>
                  <StatusBadge :status="draft.quality_status || 'pending'" />
                </div>
                <h3 class="mt-1.5 text-base font-semibold text-slate-100 truncate">
                  {{ draft.subject }}
                </h3>
                <p class="text-xs text-slate-500 mt-0.5">
                  {{ draft.company }}
                  <template v-if="draft.to_name"> · To: {{ draft.to_name }}</template>
                  <template v-if="draft.to_role"> ({{ draft.to_role }})</template>
                </p>
              </div>
            </div>

            <!-- Quality scores -->
            <div class="px-5 py-3 border-b border-slate-700/50 flex items-center gap-6 flex-wrap">
              <div class="flex items-center gap-2">
                <span class="text-xs text-slate-500">Personalization</span>
                <span :class="draft.personalization_score >= 75 ? 'text-emerald-400' : draft.personalization_score >= 50 ? 'text-amber-400' : 'text-red-400'" class="text-sm font-bold tabular-nums">
                  {{ draft.personalization_score }}<span class="text-slate-600 font-normal">/100</span>
                </span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-slate-500">Spam Risk</span>
                <span :class="draft.spam_risk_score <= 35 ? 'text-emerald-400' : draft.spam_risk_score <= 60 ? 'text-amber-400' : 'text-red-400'" class="text-sm font-bold tabular-nums">
                  {{ draft.spam_risk_score }}<span class="text-slate-600 font-normal">/100</span>
                </span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-slate-500">AI-sounding</span>
                <span :class="draft.ai_sounding_score <= 40 ? 'text-emerald-400' : draft.ai_sounding_score <= 65 ? 'text-amber-400' : 'text-red-400'" class="text-sm font-bold tabular-nums">
                  {{ draft.ai_sounding_score }}<span class="text-slate-600 font-normal">/100</span>
                </span>
              </div>
              <div v-if="draft.quality_reasons && draft.quality_reasons.length > 0" class="text-xs text-slate-500 truncate max-w-xs">
                ⚠ {{ draft.quality_reasons.join('; ') }}
              </div>
            </div>

            <!-- Draft body preview -->
            <div class="px-5 py-4 border-b border-slate-700/50">
              <p class="text-sm text-slate-400 leading-relaxed whitespace-pre-line line-clamp-5">{{ draft.body }}</p>
              <button
                v-if="draft.body.length > 300"
                class="mt-2 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                @click="toggleExpanded(draft.id)"
              >
                {{ expanded.has(draft.id) ? 'Show less' : 'Show full draft' }}
              </button>
              <div v-if="expanded.has(draft.id)" class="mt-3 pt-3 border-t border-slate-700/50">
                <p class="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{{ draft.body }}</p>
              </div>
            </div>

            <!-- Actions — NO send, NO apply -->
            <div class="px-5 py-4 flex items-center gap-3 flex-wrap">
              <!-- Approve (not send) -->
              <button
                :disabled="draft.quality_status !== 'passed'"
                :title="draft.quality_status !== 'passed' ? 'Quality Guard not passed — cannot approve' : 'Mark as approved (not sent)'"
                :class="draft.quality_status === 'passed' ? 'bg-emerald-700 hover:bg-emerald-600 text-white' : 'bg-slate-700 text-slate-500 cursor-not-allowed'"
                class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                @click="draft.quality_status === 'passed' && openApprove(draft)"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                Approve Draft
                <span class="text-xs opacity-70 font-normal">(not send)</span>
              </button>

              <!-- Skip -->
              <button
                class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
                @click="openSkip(draft)"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
                Skip
              </button>

              <!-- Needs Research -->
              <button
                class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-sky-900/40 hover:bg-sky-900/60 text-sky-400 border border-sky-800/50 transition-colors"
                @click="openResearch(draft)"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
                Needs Research
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Approve confirmation -->
    <ConfirmDialog
      v-model="approveDialog.open"
      title="Approve this draft?"
      :message="`Approving marks the draft as human-reviewed and ready.\n\nThis does NOT send anything. You must manually send the message after approving.\n\nDraft: ${approveDialog.draft?.subject}`"
      confirm-label="Approve (does not send)"
      variant="success"
      @confirm="doApprove"
    />

    <!-- Skip confirmation -->
    <ConfirmDialog
      v-model="skipDialog.open"
      title="Skip this draft?"
      :message="`The draft will be marked as skipped and removed from the review queue.\n\nDraft: ${skipDialog.draft?.subject}`"
      confirm-label="Skip Draft"
      variant="warning"
      has-input
      input-placeholder="Reason for skipping (optional)"
      @confirm="doSkip"
    />

    <!-- Needs Research confirmation -->
    <ConfirmDialog
      v-model="researchDialog.open"
      title="Flag for research?"
      :message="`This draft will be flagged as needing additional research before it can be reviewed.\n\nDraft: ${researchDialog.draft?.subject}`"
      confirm-label="Flag for Research"
      variant="info"
      has-input
      input-placeholder="Research note (optional)"
      @confirm="doResearch"
    />
  </div>
</template>

<script setup lang="ts">
import type { Draft } from '~/types'

const api = useApi()
const reviewCount = useReviewCount()

const expanded = ref(new Set<number>())
const processingId = ref<number | null>(null)

type NotifType = { id: number; type: 'success' | 'error'; message: string }
const notifications = ref<NotifType[]>([])

const approveDialog = reactive({ open: false, draft: null as Draft | null })
const skipDialog = reactive({ open: false, draft: null as Draft | null })
const researchDialog = reactive({ open: false, draft: null as Draft | null })

const { data, pending, error, refresh } = await useAsyncData('review-queue', () => api.getReviewQueue())

const drafts = computed<Draft[]>(() => data.value?.drafts ?? [])

watch(() => data.value?.total, (total) => {
  if (total !== undefined) reviewCount.value = total
}, { immediate: true })

function toggleExpanded(id: number) {
  if (expanded.value.has(id)) expanded.value.delete(id)
  else expanded.value.add(id)
}

function notify(type: 'success' | 'error', message: string) {
  const id = Date.now()
  notifications.value.push({ id, type, message })
  setTimeout(() => {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }, 4500)
}

function openApprove(draft: Draft) { approveDialog.draft = draft; approveDialog.open = true }
function openSkip(draft: Draft) { skipDialog.draft = draft; skipDialog.open = true }
function openResearch(draft: Draft) { researchDialog.draft = draft; researchDialog.open = true }

async function doApprove() {
  const draft = approveDialog.draft
  if (!draft) return
  processingId.value = draft.id
  try {
    const result = await api.approveDraft(draft.id)
    if (result.approved) {
      notify('success', `Draft "${draft.subject}" approved. Not sent — ready for manual delivery.`)
      await refresh()
    } else {
      notify('error', result.reason || 'Approval blocked by Quality Guard.')
    }
  } catch (e: unknown) {
    const msg = (e as { data?: { detail?: string } })?.data?.detail || 'Approval failed — Quality Guard may have blocked it.'
    notify('error', msg)
  } finally {
    processingId.value = null
  }
}

async function doSkip(reason: string) {
  const draft = skipDialog.draft
  if (!draft) return
  processingId.value = draft.id
  try {
    await api.skipDraft(draft.id, reason || undefined)
    notify('success', `Draft skipped.`)
    await refresh()
  } catch {
    notify('error', 'Could not skip draft.')
  } finally {
    processingId.value = null
  }
}

async function doResearch(note: string) {
  const draft = researchDialog.draft
  if (!draft) return
  processingId.value = draft.id
  try {
    await api.markNeedsResearch(draft.id, note || undefined)
    notify('success', `Draft flagged for research.`)
    await refresh()
  } catch {
    notify('error', 'Could not flag draft.')
  } finally {
    processingId.value = null
  }
}
</script>

<style scoped>
.line-clamp-5 {
  display: -webkit-box;
  -webkit-line-clamp: 5;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(1rem);
}
</style>
