<script setup lang="ts">
import type { BDICPConfig } from '~/types'

const config = useRuntimeConfig()
const apiBase = config.public.apiBase as string
const api = useApi()

const health = ref<'checking' | 'ok' | 'error'>('checking')

onMounted(async () => {
  try {
    const h = await api.getHealth()
    health.value = h.status === 'ok' ? 'ok' : 'error'
  } catch {
    health.value = 'error'
  }
})

const { data: icpConfig, refresh: refreshICP } = await useAsyncData<BDICPConfig>(
  'icp-config',
  () => api.getICPConfig(),
  { default: () => ({
    target_industries: [],
    company_size_min: null,
    company_size_max: null,
    target_roles: [],
    pain_point_priorities: [],
    signal_priorities: [],
    scoring_weights: { icp_match: 30, pain_points: 20, signals: 20, seniority: 15, urgency: 10, existing_relationship: 5 },
    updated_at: '',
  }) }
)

const icpForm = reactive({
  target_industries: '',
  target_roles: '',
  pain_point_priorities: '',
  company_size_min: '',
  company_size_max: '',
})

const isSavingICP = ref(false)
const icpSaveSuccess = ref(false)
const icpSaveError = ref<string | null>(null)

watch(icpConfig, (cfg) => {
  if (!cfg) return
  icpForm.target_industries = cfg.target_industries.join(', ')
  icpForm.target_roles = cfg.target_roles.join(', ')
  icpForm.pain_point_priorities = cfg.pain_point_priorities.join(', ')
  icpForm.company_size_min = cfg.company_size_min != null ? String(cfg.company_size_min) : ''
  icpForm.company_size_max = cfg.company_size_max != null ? String(cfg.company_size_max) : ''
}, { immediate: true })

function parseList(s: string): string[] {
  return s.split(',').map(x => x.trim()).filter(Boolean)
}

async function saveICP() {
  icpSaveError.value = null
  icpSaveSuccess.value = false
  isSavingICP.value = true
  try {
    await api.updateICPConfig({
      target_industries: parseList(icpForm.target_industries),
      target_roles: parseList(icpForm.target_roles),
      pain_point_priorities: parseList(icpForm.pain_point_priorities),
      company_size_min: icpForm.company_size_min ? Number(icpForm.company_size_min) : null,
      company_size_max: icpForm.company_size_max ? Number(icpForm.company_size_max) : null,
    })
    icpSaveSuccess.value = true
    await refreshICP()
  } catch {
    icpSaveError.value = 'Could not save ICP config — make sure the backend is running.'
  } finally {
    isSavingICP.value = false
  }
}

const scoringWeightKeys = computed(() =>
  Object.entries(icpConfig.value?.scoring_weights ?? {})
)
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader title="Settings" subtitle="ICP scoring criteria and system configuration — controls local opportunity scoring and outreach quality" />

    <div class="flex-1 p-6 space-y-6 max-w-2xl w-full mx-auto">
      <!-- API Connection -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">API Connection</h3>
        </div>
        <div class="px-5 py-4 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">Backend URL</span>
            <code class="text-xs text-gray-700 bg-gray-100 px-2 py-1 rounded-md font-mono">{{ apiBase }}</code>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">Health status</span>
            <div class="flex items-center gap-2">
              <div
                class="h-2 w-2 rounded-full"
                :class="{
                  'bg-emerald-500': health === 'ok',
                  'bg-red-400':     health === 'error',
                  'bg-amber-400 animate-pulse': health === 'checking',
                }"
              />
              <span class="text-xs text-gray-500">
                <template v-if="health === 'ok'">Connected</template>
                <template v-else-if="health === 'error'">Offline — start uvicorn</template>
                <template v-else>Checking…</template>
              </span>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-600">Override env var</span>
            <code class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-md font-mono">NUXT_PUBLIC_API_BASE</code>
          </div>
        </div>
      </AppCard>

      <!-- ICP Configuration -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">ICP Configuration</h3>
          <p class="text-xs text-gray-500 mt-0.5">Ideal Customer Profile — defines who you're targeting. Drives local opportunity scoring and signal prioritization. No external calls. Stored in <code class="bg-gray-100 px-1 rounded text-xs font-mono">data/bd_icp_config.json</code>.</p>
        </div>
        <div class="px-5 py-4 space-y-5">
          <!-- Target industries -->
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Target Industries</label>
            <input
              v-model="icpForm.target_industries"
              type="text"
              placeholder="e.g. SaaS, FinTech, HealthTech"
              class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
            <p class="text-xs text-gray-400 mt-1">Comma-separated list</p>
          </div>

          <!-- Target roles -->
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Target Roles</label>
            <input
              v-model="icpForm.target_roles"
              type="text"
              placeholder="e.g. VP Engineering, CTO, Head of Product"
              class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
            <p class="text-xs text-gray-400 mt-1">Comma-separated list</p>
          </div>

          <!-- Pain point priorities -->
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Pain Point Priorities</label>
            <input
              v-model="icpForm.pain_point_priorities"
              type="text"
              placeholder="e.g. deployment velocity, compliance overhead, data reconciliation"
              class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
            <p class="text-xs text-gray-400 mt-1">Comma-separated — used for filtering and prioritization</p>
          </div>

          <!-- Company size -->
          <div class="flex gap-4">
            <div class="flex-1">
              <label class="block text-xs font-semibold text-gray-700 mb-1">Min Company Size</label>
              <input
                v-model="icpForm.company_size_min"
                type="number"
                placeholder="e.g. 50"
                class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
            </div>
            <div class="flex-1">
              <label class="block text-xs font-semibold text-gray-700 mb-1">Max Company Size</label>
              <input
                v-model="icpForm.company_size_max"
                type="number"
                placeholder="e.g. 5000"
                class="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
            </div>
          </div>

          <!-- Scoring weights (read-only display) -->
          <div v-if="scoringWeightKeys.length">
            <label class="block text-xs font-semibold text-gray-700 mb-2">Current Scoring Weights</label>
            <div class="grid grid-cols-2 gap-2">
              <div
                v-for="[key, val] in scoringWeightKeys"
                :key="key"
                class="flex items-center justify-between rounded-lg bg-gray-50 border border-gray-100 px-3 py-2"
              >
                <span class="text-xs text-gray-600 capitalize">{{ key.replace(/_/g, ' ') }}</span>
                <span class="text-xs font-semibold text-gray-800 tabular-nums">{{ val }} pts</span>
              </div>
            </div>
            <p class="text-xs text-gray-400 mt-2">Weights are stored in ICP config and applied during local scoring.</p>
          </div>

          <div class="flex items-center gap-3 pt-1">
            <button
              class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="isSavingICP"
              @click="saveICP"
            >
              {{ isSavingICP ? 'Saving…' : 'Save ICP Config' }}
            </button>
            <span v-if="icpSaveSuccess" class="text-xs text-emerald-600 font-medium">Saved — affects local scoring</span>
            <span v-if="icpSaveError" class="text-xs text-red-600">{{ icpSaveError }}</span>
          </div>

          <div class="flex items-start gap-2 rounded-lg bg-blue-50 border border-blue-100 px-3 py-2.5">
            <svg class="h-3.5 w-3.5 text-blue-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
            </svg>
            <p class="text-xs text-blue-700">ICP criteria are used only for local scoring — no external APIs are called. Changes apply immediately to new scoring calculations.</p>
          </div>
        </div>
      </AppCard>

      <!-- Account -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">User</h3>
          <p class="text-xs text-gray-500 mt-0.5">Currently running as a local single-user instance.</p>
        </div>
        <div class="px-5 py-4 flex items-center gap-4">
          <div class="h-10 w-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0">
            <svg class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-700">CorosDev Internal</p>
            <p class="text-xs text-gray-400">Local instance — all data is stored on your machine</p>
          </div>
          <span class="ml-auto text-xs text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full font-medium flex-shrink-0">Local</span>
        </div>
      </AppCard>

      <!-- CLI Configuration -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">CLI Configuration</h3>
        </div>
        <div class="px-5 py-4 space-y-3 text-sm text-gray-600">
          <p>The CLI reads configuration from <code class="text-gray-700 bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">config.yaml</code> in the project root.</p>
          <p>A safe example is available at <code class="text-gray-700 bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">config.example.yaml</code>.</p>
          <div class="flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-100 px-3 py-2.5 mt-1">
            <svg class="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <p class="text-xs text-amber-700">Never commit <code class="bg-amber-100 px-1 rounded font-mono">config.yaml</code>, <code class="bg-amber-100 px-1 rounded font-mono">profile.yaml</code>, or <code class="bg-amber-100 px-1 rounded font-mono">.env</code> to version control.</p>
          </div>
        </div>
      </AppCard>
    </div>
  </div>
</template>
