<script setup lang="ts">
import AppSidebar from '../components/AppSidebar.vue'
import RoleWorkspaceBanner from '../components/RoleWorkspaceBanner.vue'
import WorkspaceTopbar from '../components/WorkspaceTopbar.vue'
import type { DoctorUser, HealthResponse } from '../services/types'
import type { AppSection } from '../types/workspace'

defineProps<{
  doctor: DoctorUser
  activeSection: AppSection
  health: HealthResponse | null
  patientCount: number
  followupCount: number
  errorMessage: string
  successMessage: string
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'select', section: AppSection): void
  (e: 'logout'): void
}>()
</script>

<template>
  <div class="app-shell" :class="`app-role-${doctor.role}`">
    <AppSidebar
      :active-section="activeSection"
      :doctor="doctor"
      :health="health"
      :patient-count="patientCount"
      :followup-count="followupCount"
      @select="emit('select', $event)"
      @logout="emit('logout')"
    />

    <main class="main-shell">
      <p v-if="loading" class="workspace-status-pill">Loading workspace data...</p>
      <p v-if="errorMessage" class="error-banner">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success-banner">{{ successMessage }}</p>

      <WorkspaceTopbar :doctor="doctor" :section="activeSection" :health="health" />
      <RoleWorkspaceBanner
        :doctor="doctor"
        :section="activeSection"
        :patient-count="patientCount"
        :followup-count="followupCount"
      />

      <slot />
    </main>
  </div>
</template>

