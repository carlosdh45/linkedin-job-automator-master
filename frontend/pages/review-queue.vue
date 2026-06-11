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
      notify('success', `Draft approved. Not sent — ready for manual delivery.`)
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
    notify('success', 'Draft skipped.')
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
    notify('success', 'Draft flagged for research.')
    await refresh()
  } catch {
    notify('error', 'Could not flag draft.')
  } finally {
    processingId.value = null
  }
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      :title="`Review Queue`"
      :subtitle="`${drafts.length} draft${drafts.length !== 1 ? 's' : ''} pending review`"
    >
      <template #actions>
        <button
          class="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
          :disabled="pending"
          @click="() => refresh()"
        >
          <svg class="h-3.5 w-3.5" :class="{ 'animate-spin': pending }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Refresh
        </button>
      </template>
    </PageHeader>

    <!-- Toast notifications -->
    <div class="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
      <Transition v-for="n in notifications" :key="n.id" name="toast">
        <div
          class="pointer-events-auto px-4 py-3 rounded-xl border shadow-card-md text-sm font-medium max-w-sm"
          :class="n.type === 'success'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : 'bg-red-50 border-red-200 text-red-800'"
        >
          {{ n.message }}
        </div>
      </Transition>
    </div>

    <div class="flex-1 p-6 space-y-5 max-w-3xl w-full mx-auto">
      <!-- Safety reminder -->
      <div class="flex items-start gap-3 px-4 py-3 bg-blue-50 border border-blue-100 rounded-xl">
        <svg class="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
        </svg>
        <p class="text-sm text-blue-700">
          <strong>Approve</strong> marks a draft as human-approved for your records — it does <strong>not</strong> send anything.
          DobryBot never sends emails or applies to jobs automatically.
        </p>
      </div>

      <LoadingSpinner v-if="pending" label="Loading queue…" />

      <template v-else-if="error">
        <AppCard>
          <ErrorState message="Could not load review queue." :show-retry="true" @retry="() => refresh()" />
        </AppCard>
      </template>

      <template v-else>
        <!-- Empty state -->
        <AppCard v-if="!drafts.length">
          <EmptyState title="Queue is empty" message="No drafts are pending review. Run the CLI to generate outreach.">
            <template #icon>
              <svg class="h-6 w-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </template>
          </EmptyState>
        </AppCard>

        <!-- Draft cards -->
        <div v-else class="space-y-4">
          <div
            v-for="draft in drafts"
            :key="draft.id"
            class="bg-white border border-gray-200 rounded-xl shadow-card overflow-hidden transition-opacity"
            :class="{ 'opacity-50 pointer-events-none': processingId === draft.id }"
          >
            <!-- Card header -->
            <div class="px-5 py-4 border-b border-gray-100">
              <div class="flex items-center gap-2 flex-wrap mb-1.5">
                <span class="text-xs font-semibold uppercase tracking-wider text-gray-400">{{ draft.outreach_type }}</span>
                <span class="text-gray-200">·</span>
                <span class="text-xs text-gray-400">ID {{ draft.id }}</span>
                <StatusBadge :status="draft.quality_status || 'pending'" />
              </div>
              <h3 class="text-base font-semibold text-gray-900 truncate">{{ draft.subject }}</h3>
              <p class="text-xs text-gray-500 mt-0.5">
                {{ draft.company }}
                <template v-if="draft.to_name"> · To: {{ draft.to_name }}</template>
                <template v-if="draft.to_role"> ({{ draft.to_role }})</template>
              </p>
            </div>

            <!-- Quality scores -->
            <div class="px-5 py-3 border-b border-gray-100 flex items-center gap-6 flex-wrap bg-gray-50/50">
              <div class="flex items-center gap-2">
                <span class="text-xs text-gray-500">Personalization</span>
                <span class="text-sm font-bold tabular-nums"
                  :class="draft.personalization_score >= 75 ? 'text-emerald-600' : draft.personalization_score >= 50 ? 'text-amber-600' : 'text-red-500'">
                  {{ draft.personalization_score }}<span class="text-gray-300 font-normal text-xs">/100</span>
                </span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-gray-500">Spam Risk</span>
                <span class="text-sm font-bold tabular-nums"
                  :class="draft.spam_risk_score <= 35 ? 'text-emerald-600' : draft.spam_risk_score <= 60 ? 'text-amber-600' : 'text-red-500'">
                  {{ draft.spam_risk_score }}<span class="text-gray-300 font-normal text-xs">/100</span>
                </span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-gray-500">AI-sounding</span>
                <span class="text-sm font-bold tabular-nums"
                  :class="draft.ai_sounding_score <= 40 ? 'text-emerald-600' : draft.ai_sounding_score <= 65 ? 'text-amber-600' : 'text-red-500'">
                  {{ draft.ai_sounding_score }}<span class="text-gray-300 font-normal text-xs">/100</span>
                </span>
              </div>
              <div v-if="draft.quality_reasons?.length" class="text-xs text-amber-600 truncate max-w-xs">
                ⚠ {{ draft.quality_reasons.join('; ') }}
              </div>
            </div>

            <!-- Draft body preview -->
            <div class="px-5 py-4 border-b border-gray-100">
              <p class="text-sm text-gray-600 leading-relaxed whitespace-pre-line" :class="{ 'line-clamp-5': !expanded.has(draft.id) }">
                {{ draft.body }}
              </p>
              <button
                v-if="draft.body.length > 300"
                class="mt-2 text-xs text-blue-600 hover:text-blue-700 transition-colors font-medium"
                @click="toggleExpanded(draft.id)"
              >
                {{ expanded.has(draft.id) ? 'Show less' : 'Show full draft' }}
              </button>
            </div>

            <!-- Actions — NO send, NO apply -->
            <div class="px-5 py-4 flex items-center gap-3 flex-wrap bg-gray-50/30">
              <!-- Approve (not send) -->
              <button
                :disabled="draft.quality_status !== 'passed'"
                :title="draft.quality_status !== 'passed' ? 'Quality Guard not passed — cannot approve' : 'Mark as approved (does not send)'"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                :class="draft.quality_status === 'passed'
                  ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
                @click="draft.quality_status === 'passed' && openApprove(draft)"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                Approve Draft
                <span class="text-xs opacity-75 font-normal">(not send)</span>
              </button>

              <!-- Skip -->
              <button
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
                @click="openSkip(draft)"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
                Skip
              </button>

              <!-- Needs Research -->
              <button
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-sky-50 border border-sky-200 text-sky-700 hover:bg-sky-100 transition-colors"
                @click="openResearch(draft)"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
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
      :message="`The draft will be marked as skipped and removed from the queue.\n\nDraft: ${skipDialog.draft?.subject}`"
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
