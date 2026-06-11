<script setup lang="ts">
import type { ResumeProfile, ResumeExperienceItem } from '~/types'

const props = defineProps<{
  form: Omit<ResumeProfile, 'updated_at'>
  loadingQuality?: boolean
}>()

// Compute quality metrics locally (real-time, no API call needed)
const completionScore = computed(() => {
  let pts = 0
  if (props.form.headline)                   pts += 15
  if (props.form.professional_summary)       pts += 15
  if (props.form.email)                      pts += 10
  if (props.form.skills.length > 0)          pts += 15
  if (props.form.experience_items.length > 0) pts += 20
  if (props.form.education_items.length > 0)  pts += 10
  if (props.form.linkedin_url)               pts += 10
  return Math.min(pts, 100)
})

const completionLabel = computed(() => {
  const s = completionScore.value
  if (s >= 80) return 'Excellent'
  if (s >= 60) return 'Good'
  if (s >= 40) return 'Fair'
  return 'Getting started'
})

const completionColor = computed(() => {
  const s = completionScore.value
  if (s >= 80) return 'text-emerald-600'
  if (s >= 60) return 'text-blue-600'
  if (s >= 40) return 'text-amber-600'
  return 'text-gray-400'
})

const completionBarColor = computed(() => {
  const s = completionScore.value
  if (s >= 80) return 'bg-emerald-500'
  if (s >= 60) return 'bg-blue-500'
  if (s >= 40) return 'bg-amber-500'
  return 'bg-gray-300'
})

const atsChecks = computed(() => {
  const exp = props.form.experience_items as ResumeExperienceItem[]
  const hasBullets = exp.length > 0 && exp.some(e => e.bullets.length > 0)
  return [
    { label: 'Professional headline',        passed: Boolean(props.form.headline) },
    { label: 'Email + phone present',        passed: Boolean(props.form.email && props.form.phone) },
    { label: 'Skills section present',       passed: props.form.skills.length > 0 },
    { label: '5 or more skills listed',      passed: props.form.skills.length >= 5 },
    { label: 'Work experience included',     passed: exp.length > 0 },
    { label: 'Bullets in experience roles',  passed: hasBullets },
    { label: 'Education section present',    passed: props.form.education_items.length > 0 },
    { label: 'LinkedIn profile linked',      passed: Boolean(props.form.linkedin_url) },
  ]
})

const atsScore = computed(() => atsChecks.value.filter(c => c.passed).length)
const atsTotal = computed(() => atsChecks.value.length)

const missingFields = computed(() => {
  const m: string[] = []
  if (!props.form.headline)                    m.push('Headline')
  if (!props.form.professional_summary)        m.push('Summary')
  if (!props.form.email)                       m.push('Email')
  if (props.form.skills.length === 0)          m.push('Skills')
  if (props.form.experience_items.length === 0) m.push('Experience')
  if (props.form.education_items.length === 0)  m.push('Education')
  if (!props.form.linkedin_url)                m.push('LinkedIn URL')
  return m
})

const atsLabel = computed(() => {
  const s = atsScore.value
  const t = atsTotal.value
  if (s === t) return 'ATS Ready'
  if (s >= t * 0.75) return 'Good'
  if (s >= t * 0.5) return 'Needs work'
  return 'Incomplete'
})
</script>

<template>
  <div class="space-y-4">

    <!-- Completeness card -->
    <AppCard>
      <div class="px-5 py-3.5 border-b border-gray-100">
        <h3 class="text-sm font-semibold text-gray-900">Profile Completeness</h3>
      </div>
      <div class="px-5 py-4 space-y-3">
        <div class="flex items-center justify-between mb-1">
          <span class="text-2xl font-bold text-gray-900">{{ completionScore }}%</span>
          <span class="text-sm font-semibold px-2.5 py-1 rounded-full" :class="{
            'bg-emerald-100 text-emerald-700': completionScore >= 80,
            'bg-blue-100 text-blue-700':       completionScore >= 60 && completionScore < 80,
            'bg-amber-100 text-amber-700':     completionScore >= 40 && completionScore < 60,
            'bg-gray-100 text-gray-500':       completionScore < 40,
          }">{{ completionLabel }}</span>
        </div>
        <div class="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="completionBarColor"
            :style="{ width: `${completionScore}%` }"
          />
        </div>

        <!-- Missing fields -->
        <div v-if="missingFields.length > 0" class="pt-1 space-y-1">
          <p class="text-xs font-medium text-gray-500">Missing</p>
          <div class="flex flex-wrap gap-1">
            <span
              v-for="f in missingFields"
              :key="f"
              class="rounded-full bg-red-50 border border-red-100 px-2 py-0.5 text-xs text-red-600"
            >{{ f }}</span>
          </div>
        </div>
        <div v-else class="flex items-center gap-1.5 pt-1 text-xs text-emerald-600 font-medium">
          <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
          All key sections filled
        </div>
      </div>
    </AppCard>

    <!-- ATS Readiness card -->
    <AppCard>
      <div class="px-5 py-3.5 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-sm font-semibold text-gray-900">ATS Readiness</h3>
        <span class="text-xs font-semibold rounded-full px-2.5 py-0.5" :class="{
          'bg-emerald-100 text-emerald-700': atsScore === atsTotal,
          'bg-blue-100 text-blue-700':       atsScore >= atsTotal * 0.75 && atsScore < atsTotal,
          'bg-amber-100 text-amber-700':     atsScore >= atsTotal * 0.5 && atsScore < atsTotal * 0.75,
          'bg-red-100 text-red-600':         atsScore < atsTotal * 0.5,
        }">{{ atsScore }}/{{ atsTotal }} · {{ atsLabel }}</span>
      </div>
      <div class="px-5 py-3 space-y-1.5">
        <div
          v-for="check in atsChecks"
          :key="check.label"
          class="flex items-center gap-2.5"
        >
          <svg
            v-if="check.passed"
            class="h-3.5 w-3.5 text-emerald-500 flex-shrink-0"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
          <svg
            v-else
            class="h-3.5 w-3.5 text-gray-300 flex-shrink-0"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <span class="text-xs" :class="check.passed ? 'text-gray-700' : 'text-gray-400'">
            {{ check.label }}
          </span>
        </div>
      </div>
    </AppCard>

  </div>
</template>
