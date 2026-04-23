<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '../components/AppSidebar.vue'
import PatientContextBar from '../components/PatientContextBar.vue'
import WorkspaceTopbar from '../components/WorkspaceTopbar.vue'
import type { DoctorUser, HealthResponse, PatientCase } from '../services/types'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  doctor: DoctorUser
  activeSection: AppSection
  health: HealthResponse | null
  patientCount: number
  followupCount: number
  selectedPatient: PatientCase | null
  errorMessage: string
  successMessage: string
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'select', section: AppSection): void
  (e: 'logout'): void
  (e: 'open-archive', payload: { patientId: string; focus?: 'overview' | 'events' }): void
  (e: 'open-followup', payload: { patientId: string; section?: 'tasks' | 'contacts' | 'flow' }): void
  (e: 'back-to-list'): void
}>()

const route = useRoute()
const showError = ref(false)
const showSuccess = ref(false)

const patientContextSections = new Set<AppSection>([
  'doctor',
  'archive',
  'emr',
  'tasks',
  'contacts',
  'flow',
  'coordination',
])

const showPatientContext = computed(() => {
  if (!props.selectedPatient) return false
  if (route.name === 'patient-detail') return false
  return patientContextSections.has(props.activeSection)
})

watch(
  () => props.errorMessage,
  (next) => {
    if (!next) return
    showError.value = true
    window.setTimeout(() => {
      showError.value = false
    }, 5000)
  }
)

watch(
  () => props.successMessage,
  (next) => {
    if (!next) return
    showSuccess.value = true
    window.setTimeout(() => {
      showSuccess.value = false
    }, 3200)
  }
)
</script>

<template>
  <div class="medical-workbench-shell" :class="`app-role-${doctor.role}`">
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
      <WorkspaceTopbar :doctor="doctor" :section="activeSection" :health="health" :loading="loading" />

      <transition name="slide-fade">
        <div v-if="showError && errorMessage" class="status-banner status-banner-error" role="alert">
          <strong>系统提示</strong>
          <span>{{ errorMessage }}</span>
          <button type="button" @click="showError = false">关闭</button>
        </div>
      </transition>

      <transition name="slide-fade">
        <div v-if="showSuccess && successMessage" class="status-banner status-banner-success" role="status">
          <strong>操作成功</strong>
          <span>{{ successMessage }}</span>
          <button type="button" @click="showSuccess = false">关闭</button>
        </div>
      </transition>

      <PatientContextBar
        v-if="showPatientContext && selectedPatient"
        :patient="selectedPatient"
        @open-archive="emit('open-archive', $event)"
        @open-followup="emit('open-followup', $event)"
        @back-to-list="emit('back-to-list')"
      />

      <section class="workspace-content-region">
        <slot name="workspace" />
      </section>

      <slot v-if="$slots['bottom-panel']" name="bottom-panel" />
    </main>
  </div>
</template>
