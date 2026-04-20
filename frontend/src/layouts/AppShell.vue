<script setup lang="ts">
import { ref, watch } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import PatientContextBar from '../components/PatientContextBar.vue'
import RoleWorkspaceBanner from '../components/RoleWorkspaceBanner.vue'
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

const showError = ref(false)
const showSuccess = ref(false)

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
          <strong>操作未完成</strong>
          <span>{{ errorMessage }}</span>
          <button type="button" @click="showError = false">关闭</button>
        </div>
      </transition>

      <transition name="slide-fade">
        <div v-if="showSuccess && successMessage" class="status-banner status-banner-success" role="status">
          <strong>已保存</strong>
          <span>{{ successMessage }}</span>
          <button type="button" @click="showSuccess = false">关闭</button>
        </div>
      </transition>

      <RoleWorkspaceBanner
        :doctor="doctor"
        :section="activeSection"
        :patient-count="patientCount"
        :followup-count="followupCount"
      />

      <PatientContextBar
        v-if="selectedPatient"
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

<style scoped>
.medical-workbench-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 256px minmax(0, 1fr);
  background: var(--ws-bg);
}

.main-shell {
  min-width: 0;
  display: grid;
  grid-template-rows: auto;
  align-content: start;
  gap: 24px;
  padding: 24px;
  background: var(--ws-bg);
}

.workspace-content-region {
  min-width: 0;
}

.status-banner {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid;
  background: #fff;
  font-size: 14px;
}

.status-banner strong {
  font-size: 14px;
}

.status-banner span {
  min-width: 0;
  color: var(--ws-text);
}

.status-banner button {
  border: 0;
  background: transparent;
  color: inherit;
  font-size: 12px;
  font-weight: 700;
}

.status-banner-error {
  border-color: var(--ws-danger-border);
  color: var(--ws-danger);
  background: var(--ws-danger-soft);
}

.status-banner-success {
  border-color: var(--ws-success-border);
  color: var(--ws-success);
  background: var(--ws-success-soft);
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 1080px) {
  .medical-workbench-shell {
    grid-template-columns: 1fr;
  }

  .main-shell {
    padding: 16px;
  }
}
</style>
