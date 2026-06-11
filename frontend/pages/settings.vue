<script setup lang="ts">
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

const placeholderSections = [
  { label: 'Profile', description: 'Name, title, bio, and target roles' },
  { label: 'Quality Thresholds', description: 'Personalization and spam score cutoffs' },
  { label: 'Resume / CV', description: 'Upload and manage your resume for context' },
  { label: 'Notifications', description: 'Alerts for queue items and pipeline events' },
]
</script>

<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <PageHeader title="Settings" subtitle="Configuration and profile — coming soon" />

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

      <!-- Coming-soon sections -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Future Settings</h3>
          <p class="text-xs text-gray-500 mt-0.5">These sections are planned for a future phase.</p>
        </div>
        <div class="divide-y divide-gray-100">
          <div
            v-for="section in placeholderSections"
            :key="section.label"
            class="px-5 py-4 flex items-center justify-between"
          >
            <div>
              <p class="text-sm font-medium text-gray-700">{{ section.label }}</p>
              <p class="text-xs text-gray-400 mt-0.5">{{ section.description }}</p>
            </div>
            <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full font-medium">Coming soon</span>
          </div>
        </div>
      </AppCard>

      <!-- Auth placeholder -->
      <AppCard>
        <div class="px-5 py-3.5 border-b border-gray-100">
          <h3 class="text-sm font-semibold text-gray-900">Account</h3>
          <p class="text-xs text-gray-500 mt-0.5">Authentication is not yet implemented.</p>
        </div>
        <div class="px-5 py-4 flex items-center gap-4">
          <div class="h-10 w-10 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
            <svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-700">CorosDev Internal</p>
            <p class="text-xs text-gray-400">carlos@corosdev.com · Auth coming in a future phase</p>
          </div>
          <span class="ml-auto text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full font-medium flex-shrink-0">Placeholder</span>
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
