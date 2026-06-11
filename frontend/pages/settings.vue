<template>
  <div class="flex-1 overflow-y-auto">
    <!-- Header -->
    <div class="sticky top-0 z-10 bg-slate-950/80 backdrop-blur border-b border-slate-800 px-8 py-4">
      <h1 class="text-xl font-bold text-slate-100">Settings</h1>
      <p class="text-xs text-slate-500 mt-0.5">Configuration and profile — coming soon</p>
    </div>

    <div class="px-8 py-8 space-y-6 max-w-2xl mx-auto">
      <!-- Placeholder card -->
      <div class="bg-slate-800 border border-slate-700 rounded-xl p-8 text-center">
        <div class="w-12 h-12 rounded-xl bg-slate-700 flex items-center justify-center mx-auto mb-4">
          <svg class="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28zM15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <h2 class="text-lg font-semibold text-slate-200">Settings coming in a future phase</h2>
        <p class="mt-2 text-sm text-slate-500 leading-relaxed max-w-sm mx-auto">
          Profile, config.yaml editing, quality thresholds, and notification settings will be added here.
        </p>
      </div>

      <!-- API connection info -->
      <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
        <div class="px-5 py-4 border-b border-slate-700">
          <h3 class="text-sm font-semibold text-slate-200">API Connection</h3>
        </div>
        <div class="px-5 py-4 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-400">Backend URL</span>
            <code class="text-xs text-slate-300 bg-slate-700 px-2 py-1 rounded">{{ apiBase }}</code>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-400">Health status</span>
            <div class="flex items-center gap-2">
              <div
                :class="{
                  'bg-emerald-400': health === 'ok',
                  'bg-red-400': health === 'error',
                  'bg-amber-400 animate-pulse': health === 'checking',
                }"
                class="w-2 h-2 rounded-full"
              />
              <span class="text-xs text-slate-400">
                <template v-if="health === 'ok'">Connected</template>
                <template v-else-if="health === 'error'">Offline — start uvicorn</template>
                <template v-else>Checking…</template>
              </span>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-400">Override env var</span>
            <code class="text-xs text-slate-500 bg-slate-700 px-2 py-1 rounded">NUXT_PUBLIC_API_BASE</code>
          </div>
        </div>
      </div>

      <!-- Config files note -->
      <div class="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
        <div class="px-5 py-4 border-b border-slate-700">
          <h3 class="text-sm font-semibold text-slate-200">CLI Configuration</h3>
        </div>
        <div class="px-5 py-4 space-y-3 text-sm text-slate-400">
          <p>The CLI reads configuration from <code class="text-slate-300 bg-slate-700 px-1.5 py-0.5 rounded text-xs">config.yaml</code> in the project root.</p>
          <p>A safe example is available at <code class="text-slate-300 bg-slate-700 px-1.5 py-0.5 rounded text-xs">config.example.yaml</code>.</p>
          <p class="text-amber-400/80 text-xs">⚠ Never commit <code class="bg-slate-700 px-1 rounded">config.yaml</code>, <code class="bg-slate-700 px-1 rounded">profile.yaml</code>, or <code class="bg-slate-700 px-1 rounded">.env</code> to version control.</p>
        </div>
      </div>
    </div>
  </div>
</template>

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
</script>
