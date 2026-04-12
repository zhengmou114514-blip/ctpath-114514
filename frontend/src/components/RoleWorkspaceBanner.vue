<script setup lang="ts">
import { computed } from 'vue'
import type { DoctorUser } from '../services/types'
import { sectionLabel } from '../config/workspaceMenu'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  doctor: DoctorUser
  section: AppSection
  patientCount: number
  followupCount: number
}>()

const bannerConfig = computed(() => {
  if (props.doctor.role === 'nurse') {
    return {
      eyebrow: 'Nurse Workbench',
      title: 'Follow-up and Coordination Console',
      description: 'Track follow-up tasks, contact outcomes, and patient flow with clear status transitions.',
    }
  }

  if (props.doctor.role === 'archivist') {
    return {
      eyebrow: 'Archive Workbench',
      title: 'Archive and Data Quality Console',
      description: 'Focus on archive completeness, record consistency, and governance-quality traceability.',
    }
  }

  return {
    eyebrow: 'Doctor Workbench',
    title: 'Chronic Disease Diagnostic Workstation',
    description: 'Combine disease trajectory, model evidence, and care suggestions for outpatient decisions.',
  }
})
</script>

<template>
  <section class="role-banner card">
    <div>
      <p class="eyebrow">{{ bannerConfig.eyebrow }}</p>
      <h2 class="page-title">{{ bannerConfig.title }}</h2>
      <p class="role-banner-copy page-description">{{ bannerConfig.description }}</p>
    </div>

    <div class="role-banner-chips">
      <article class="role-banner-chip">
        <span>Current Module</span>
        <strong>{{ sectionLabel(props.section) }}</strong>
      </article>
      <article class="role-banner-chip">
        <span>Total Patients</span>
        <strong>{{ props.patientCount }}</strong>
      </article>
      <article class="role-banner-chip">
        <span>Follow-up Tasks</span>
        <strong>{{ props.followupCount }}</strong>
      </article>
    </div>
  </section>
</template>
