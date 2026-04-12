<script setup lang="ts">
import type { DoctorUser, HealthResponse } from '../services/types'
import { sectionLabel } from '../config/workspaceMenu'
import type { AppSection } from '../types/workspace'

defineProps<{
  doctor: DoctorUser
  section: AppSection
  health: HealthResponse | null
}>()

function roleLabel(role: DoctorUser['role']) {
  if (role === 'archivist') return 'Archivist'
  if (role === 'nurse') return 'Nurse'
  return 'Doctor'
}
</script>

<template>
  <section class="workspace-topbar card">
    <div class="workspace-topbar-main">
      <p class="eyebrow">Clinical Workspace</p>
      <strong class="page-title">{{ sectionLabel(section) }}</strong>
      <small class="page-subtitle">{{ doctor.department }} / {{ roleLabel(doctor.role) }}</small>
    </div>

    <div class="workspace-topbar-status">
      <span class="workspace-status-pill">Status: {{ health?.status ?? 'unknown' }}</span>
      <span class="workspace-status-pill">Runtime: {{ health?.mode ?? 'unknown' }}</span>
      <span class="workspace-status-pill">Model: {{ health?.model_available ? 'Available' : 'Unavailable' }}</span>
    </div>
  </section>
</template>
