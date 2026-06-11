<script setup lang="ts">
const api = useApi()
const reviewCount = useReviewCount()
const route = useRoute()

const health = ref<'checking' | 'ok' | 'error'>('checking')

const navItems = computed(() => [
  {
    to: '/',
    label: 'Dashboard',
    icon: 'M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25',
  },
  {
    to: '/daily-brief',
    label: 'Daily Brief',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
  },
  {
    to: '/jobs',
    label: 'Jobs',
    icon: 'M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z',
  },
  {
    to: '/leads',
    label: 'Leads',
    icon: 'M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z',
  },
  {
    to: '/review-queue',
    label: 'Review Queue',
    icon: 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z',
    badge: reviewCount.value,
  },
  {
    to: '/safety',
    label: 'Safety Center',
    icon: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
  },
  {
    to: '/settings',
    label: 'Settings',
    icon: 'M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28zM15 12a3 3 0 11-6 0 3 3 0 016 0z',
  },
])

function isActive(to: string) {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}

onMounted(async () => {
  try {
    const h = await api.getHealth()
    health.value = h.status === 'ok' ? 'ok' : 'error'
  } catch {
    health.value = 'error'
  }
  try {
    const q = await api.getReviewQueue()
    reviewCount.value = q.total
  } catch {
    // non-critical
  }
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-gray-50">
    <!-- Sidebar -->
    <aside class="w-60 flex-shrink-0 flex flex-col bg-white border-r border-gray-200">
      <!-- Brand -->
      <div class="flex items-center gap-3 px-4 h-14 border-b border-gray-100">
        <div class="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-white font-bold text-xs flex-shrink-0 shadow-sm select-none">
          D
        </div>
        <div class="min-w-0">
          <div class="text-sm font-semibold text-gray-900 leading-none truncate">DobryBot</div>
          <div class="text-xs text-gray-400 mt-0.5 truncate">CorosDev Internal</div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 overflow-y-auto px-2 py-3">
        <div class="space-y-0.5">
          <NuxtLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="group flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-100"
            :class="isActive(item.to)
              ? 'bg-blue-50 text-blue-700'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'"
          >
            <svg
              class="h-4 w-4 flex-shrink-0"
              :class="isActive(item.to) ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
            </svg>
            <span class="flex-1 truncate">{{ item.label }}</span>
            <span
              v-if="item.badge && item.badge > 0"
              class="ml-auto flex h-5 min-w-[1.25rem] items-center justify-center rounded-full px-1 text-[11px] font-semibold tabular-nums"
              :class="isActive(item.to) ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'"
            >
              {{ item.badge }}
            </span>
          </NuxtLink>
        </div>
      </nav>

      <!-- Footer -->
      <div class="border-t border-gray-100 px-3 py-3 space-y-2.5">
        <div class="flex items-center gap-2">
          <div
            class="h-1.5 w-1.5 rounded-full flex-shrink-0"
            :class="{
              'bg-emerald-500': health === 'ok',
              'bg-red-400':     health === 'error',
              'bg-amber-400 animate-pulse': health === 'checking',
            }"
          />
          <span class="text-xs text-gray-400">
            <template v-if="health === 'ok'">Backend connected</template>
            <template v-else-if="health === 'error'">Backend offline</template>
            <template v-else>Connecting…</template>
          </span>
        </div>
        <div class="rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-2">
          <p class="text-xs text-emerald-700 font-medium leading-snug">
            Never sends or applies automatically
          </p>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <slot />
    </div>
  </div>
</template>
