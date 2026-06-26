<script setup lang="ts">
type MessageType = 'email' | 'linkedin' | 'intro_request'
type ToneType = 'warm' | 'direct' | 'executive' | 'technical'

interface DraftContext {
  company: string
  contact: string
  role: string
  painPoint: string
  angle: string
}

const activeTab = ref<'compose' | 'drafts'>('compose')
const selectedType = ref<MessageType>('email')
const selectedTone = ref<ToneType>('warm')
const draftContext = ref<DraftContext>({
  company: 'Meridian Labs',
  contact: 'Alex Rivera',
  role: 'VP of Engineering',
  painPoint: 'Manual deployment pipeline slowing release velocity',
  angle: 'CI/CD automation and engineering efficiency',
})

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

const mockDraft = computed(() => {
  const { company, contact, painPoint, angle } = draftContext.value
  if (selectedType.value === 'email') {
    return `Subject: Solving the ${painPoint.toLowerCase()} at ${company}

Hi ${contact.split(' ')[0]},

I came across ${company}'s engineering blog and noticed you're working through some challenges with ${painPoint.toLowerCase()}.

At CorosDev, we've helped teams like yours reduce deployment cycle time by 60–80% without disrupting existing workflows — typically in 6–8 weeks.

Would a 20-minute call to share what's working for similar teams be worth your time?

Best,
[Your name]`
  }
  if (selectedType.value === 'linkedin') {
    return `Hi ${contact.split(' ')[0]}, I saw your team is scaling fast at ${company} — impressive growth. We've been helping engineering orgs tackle ${painPoint.toLowerCase()} and I thought there might be a relevant angle for your roadmap. Would love to share what we've seen work. Open to a quick chat?`
  }
  return `Hi [Mutual connection],

Could you introduce me to ${contact} at ${company}? I've been following their engineering work and think there's a strong alignment around ${angle}. I'm not looking to pitch — just a conversation to see if it makes sense to explore further.

Happy to make it easy for you with a quick intro draft if helpful.

Thanks!`
})

const mockSavedDrafts = [
  {
    id: '1', company: 'Vantage Capital', contact: 'Morgan Chen',
    type: 'email', status: 'review', score: 84, updatedAt: '2026-06-24',
  },
  {
    id: '2', company: 'Meridian Labs', contact: 'Alex Rivera',
    type: 'linkedin', status: 'draft', score: 71, updatedAt: '2026-06-22',
  },
]

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
        <span class="inline-flex items-center gap-1.5 rounded-lg bg-blue-50 border border-blue-100 px-3 py-1.5 text-xs font-medium text-blue-700">
          Placeholder UI
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
                  <input
                    v-model="draftContext.company"
                    type="text"
                    class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
                  />
                </div>
                <div>
                  <label class="block text-xs font-semibold text-gray-700 mb-1">Contact Name</label>
                  <input
                    v-model="draftContext.contact"
                    type="text"
                    class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
                  />
                </div>
                <div>
                  <label class="block text-xs font-semibold text-gray-700 mb-1">Pain Point</label>
                  <textarea
                    v-model="draftContext.painPoint"
                    rows="2"
                    class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
                  />
                </div>
                <div>
                  <label class="block text-xs font-semibold text-gray-700 mb-1">Angle / Value Prop</label>
                  <textarea
                    v-model="draftContext.angle"
                    rows="2"
                    class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
                  />
                </div>

                <button
                  class="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
                  disabled
                  title="Draft generation connects in Phase 2"
                >
                  Generate Draft — Phase 2
                </button>
              </div>
            </AppCard>
          </div>

          <!-- Right: draft preview (3/5) -->
          <div class="xl:col-span-3 space-y-4">
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h2 class="text-sm font-semibold text-gray-900">Draft Preview</h2>
                  <p class="text-xs text-gray-400 mt-0.5">Sample draft — AI generation connects in Phase 2</p>
                </div>
                <button
                  class="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  disabled
                  title="Send to Review Queue connects in Phase 2"
                >
                  Send to Review Queue
                </button>
              </div>
              <div class="px-5 py-4">
                <pre class="whitespace-pre-wrap font-sans text-sm text-gray-700 leading-relaxed">{{ mockDraft }}</pre>
              </div>
            </AppCard>

            <!-- Quality indicators (placeholder) -->
            <AppCard>
              <div class="px-5 py-3.5 border-b border-gray-100">
                <h2 class="text-sm font-semibold text-gray-900">Quality Indicators</h2>
              </div>
              <div class="px-5 py-4 grid grid-cols-3 gap-4">
                <div class="text-center">
                  <div class="text-2xl font-bold text-emerald-600">—</div>
                  <div class="text-xs text-gray-500 mt-0.5">Personalization</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold text-emerald-600">—</div>
                  <div class="text-xs text-gray-500 mt-0.5">Spam Risk</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold text-emerald-600">—</div>
                  <div class="text-xs text-gray-500 mt-0.5">AI Detection</div>
                </div>
              </div>
              <div class="px-5 pb-4 text-xs text-gray-400 text-center">
                Quality scoring activates when draft generation is connected in Phase 2
              </div>
            </AppCard>
          </div>
        </div>
      </template>

      <!-- Saved drafts tab -->
      <template v-else>
        <AppCard>
          <div class="overflow-x-auto">
            <table class="app-table">
              <thead>
                <tr>
                  <th>Company / Contact</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th class="text-right">Score</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in mockSavedDrafts" :key="d.id">
                  <td>
                    <div class="font-medium text-gray-900">{{ d.company }}</div>
                    <div class="text-xs text-gray-400">{{ d.contact }}</div>
                  </td>
                  <td class="text-gray-500 capitalize">{{ d.type.replace('_', ' ') }}</td>
                  <td>
                    <span
                      class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold"
                      :class="statusColor[d.status] ?? 'bg-gray-100 text-gray-600'"
                    >
                      {{ d.status }}
                    </span>
                  </td>
                  <td class="text-right font-semibold tabular-nums text-violet-600">{{ d.score }}</td>
                  <td class="text-gray-500">{{ d.updatedAt }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </AppCard>
      </template>
    </div>
  </div>
</template>
