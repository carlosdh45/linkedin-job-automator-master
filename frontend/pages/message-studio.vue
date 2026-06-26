<script setup lang="ts">
import type { BDOutreachDraft } from '~/types'

type MessageType = 'email' | 'linkedin' | 'intro_request'
type ToneType = 'warm' | 'direct' | 'executive' | 'technical'

const api = useApi()

const activeTab = ref<'compose' | 'drafts'>('compose')
const selectedType = ref<MessageType>('email')
const selectedTone = ref<ToneType>('warm')
const isGenerating = ref(false)
const generatedDraft = ref<string | null>(null)
const generatedSubject = ref<string | null>(null)
const generateError = ref<string | null>(null)

const draftContext = ref({
  company: 'Meridian Labs',
  contact: 'Alex Rivera',
  role: 'VP of Engineering',
  painPoint: 'Manual deployment pipeline slowing release velocity',
  angle: 'CI/CD automation and engineering efficiency',
})

const { data: savedDrafts, pending: draftsPending } = await useAsyncData<BDOutreachDraft[]>(
  'bd-outreach-drafts',
  () => api.getBDSignals().then(() => [] as BDOutreachDraft[]),
  { default: () => [] }
)

const messageTypes: { value: MessageType; label: string }[] = [
  { value: 'email', label: 'Email' },
  { value: 'linkedin', label: 'LinkedIn Message' },
  { value: 'intro_request', label: 'Intro Request' },
]

const tones: { value: ToneType; label: string; description: string }[] = [
  { value: 'warm', label: 'Warm', description: 'Conversational, relationship-first' },
  { value: 'direct', label: 'Direct', description: 'Clear, no-fluff, executive-ready' },
  { value: 'executive', label: 'Executive', description: 'C-suite register, strategic framing' },
  { value: 'technical', label: 'Technical', description: 'Peer-to-peer, credibility-led' },
]

const displayDraft = computed(() => generatedDraft.value ?? '')

async function generateDraft() {
  generateError.value = null
  isGenerating.value = true
  try {
    const result = await api.generateBDDraft({
      company_name: draftContext.value.company,
      contact_name: draftContext.value.contact,
      contact_role: draftContext.value.role,
      pain_point: draftContext.value.painPoint,
      angle: draftContext.value.angle,
      message_type: selectedType.value,
      tone: selectedTone.value,
    })
    generatedDraft.value = result.draft
    generatedSubject.value = result.subject ?? null
  } catch {
    generateError.value = 'Could not generate draft — make sure the backend is running.'
  } finally {
    isGenerating.value = false
  }
}

const statusColor: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600',
  review: 'bg-amber-50 text-amber-700',
  approved: 'bg-emerald-50 text-emerald-700',
}
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader
      title="Message Studio"
      subtitle="Compose and review personalized BD outreach — all drafts require explicit approval"
    >
      <template #actions>
        <span class="inline-flex items-center gap-1.5 rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-1.5 text-xs font-medium text-emerald-700">
          Drafts only — never auto-sends
        </span>
      </template>
    </PageHeader>

    <div class="flex-1 p-6 max-w-6xl w-full mx-auto space-y-4">
      <!-- Tab switcher -->
      <div class="flex gap-1 border-b border-gray-200">
        <button
          v-for="tab in [{ key: 'compose', label: 'Compose' }, { key: 'drafts', label: 'Saved Drafts' }]"
          :key="tab.key"
          class="px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px"
          :class="activeTab === tab.key
            ? 'border-blue-600 text-blue-700'
            : 'border-transparent text-gray-500 hover:text-gray-700'"
          @click="activeTab = tab.key as 'compose' | 'drafts'"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Compose tab -->
      <template v-if="activeTab === 'compose'">
        <div class="grid grid-cols-1 xl:grid-cols-5 gap-6">
          <!-- Left: context inputs (2/5) -->
          <div class="xl:col-span-2 space-y-4">
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100">
                <h2 class="text-sm font-semibold text-gray-900">Message Context</h2>
                <p class="text-xs text-gray-400 mt-0.5">Context drives personalization</p>
              </div>
              <div class="px-5 py-4 space-y-4">
                <!-- Message type -->
                <div>
                  <label class="block text-xs font-semibold text-gray-700 mb-1.5">Message Type</label>
                  <div class="flex gap-1">
                    <button
                      v-for="t in messageTypes"
                      :key="t.value"
                      class="flex-1 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors border"
                      :class="selectedType === t.value
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'"
                      @click="selectedType = t.value"
                    >
                      {{ t.label }}
                    </button>
                  </div>
                </div>

                <!-- Tone -->
                <div>
                  <label class="block text-xs font-semibold text-gray-700 mb-1.5">Tone</label>
                  <div class="grid grid-cols-2 gap-1">
                    <button
                      v-for="t in tones"
                      :key="t.value"
                      class="rounded-lg px-2 py-1.5 text-left transition-colors border"
                      :class="selectedTone === t.value
                        ? 'bg-violet-50 border-violet-200'
                        : 'bg-white border-gray-200 hover:bg-gray-50'"
                      @click="selectedTone = t.value"
                    >
                      <div class="text-xs font-medium" :class="selectedTone === t.value ? 'text-violet-700' : 'text-gray-700'">{{ t.label }}</div>
                      <div class="text-[10px] text-gray-400 mt-0.5">{{ t.description }}</div>
                    </button>
                  </div>
                </div>

                <!-- Context fields -->
                <div>
                  <label class="block text-xs font-semibold text-gray-700 mb-1">Company</label>
                  <input v-model="draftContext.company" type="text" class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400" />
                </div>
                <div>
                  <label class="block text-xs font-semibold text-gray-700 mb-1">Contact Name</label>
                  <input v-model="draftContext.contact" type="text" class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400" />
                </div>
                <div>
                  <label class="block text-xs font-semibold text-gray-700 mb-1">Pain Point</label>
                  <textarea v-model="draftContext.painPoint" rows="2" class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none" />
                </div>
                <div>
                  <label class="block text-xs font-semibold text-gray-700 mb-1">Angle / Value Prop</label>
                  <textarea v-model="draftContext.angle" rows="2" class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none" />
                </div>

                <button
                  class="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="isGenerating || !draftContext.company || !draftContext.contact"
                  @click="generateDraft"
                >
                  {{ isGenerating ? 'Generating…' : 'Generate Draft' }}
                </button>

                <div v-if="generateError" class="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-xs text-red-700">
                  {{ generateError }}
                </div>
              </div>
            </AppCard>
          </div>

          <!-- Right: draft preview (3/5) -->
          <div class="xl:col-span-3 space-y-4">
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100">
                <h2 class="text-sm font-semibold text-gray-900">Draft Preview</h2>
                <p class="text-xs text-gray-400 mt-0.5">Rule-based local template — no AI, no external calls</p>
              </div>

              <div v-if="!displayDraft" class="px-5 py-12 text-center text-sm text-gray-400">
                Fill in context and click "Generate Draft" to create a local template draft.
              </div>
              <div v-else class="px-5 py-4">
                <div v-if="generatedSubject" class="mb-3 text-xs font-medium text-gray-500 border-b border-gray-100 pb-2">
                  {{ generatedSubject }}
                </div>
                <pre class="whitespace-pre-wrap font-sans text-sm text-gray-700 leading-relaxed">{{ displayDraft }}</pre>
              </div>
            </AppCard>

            <!-- Safety notice -->
            <div class="flex items-start gap-3 rounded-xl bg-emerald-50 border border-emerald-100 px-4 py-3">
              <svg class="h-4 w-4 text-emerald-600 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
              <div>
                <p class="text-sm font-medium text-emerald-800">Human-in-the-loop — always</p>
                <p class="text-xs text-emerald-700 mt-0.5">Drafts are generated locally using rule-based templates. No AI calls. No external APIs. DobryBot does not send or post anything automatically. All outreach requires your explicit approval.</p>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Saved drafts tab -->
      <template v-else>
        <AppCard>
          <div class="px-5 py-4 text-center text-sm text-gray-400">
            Saved draft tracking connects in Phase 10 when outreach drafts are persisted through the Review Queue.
          </div>
        </AppCard>
      </template>
    </div>
  </div>
</template>
