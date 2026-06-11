<template>
  <div class="p-6 space-y-3">
    <div v-for="i in 4" :key="i" class="animate-pulse h-4 bg-gray-100 rounded-full" :class="[i === 1 ? 'w-3/4' : i === 2 ? 'w-1/2' : i === 3 ? 'w-5/6' : 'w-2/3']" />
  </div>
</template>
