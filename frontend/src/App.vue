<script setup lang="ts">
import { onMounted } from 'vue'
import LoginScreen from './components/LoginScreen.vue'
import { useWorkspaceController } from './composables/useWorkspaceController'
import AppShell from './layouts/AppShell.vue'
import DoctorDashboardPage from './pages/DoctorDashboardPage.vue'
import FollowupWorkbenchPage from './pages/FollowupWorkbenchPage.vue'
import GovernancePage from './pages/GovernancePage.vue'
import PatientArchivePage from './pages/PatientArchivePage.vue'

const workspace = useWorkspaceController()

onMounted(async () => {
  await workspace.initialize()
})
</script>

<template>
  <LoginScreen
    v-if="!workspace.currentDoctor"
    :username="workspace.username"
    :password="workspace.password"
    :login-error="workspace.loginError"
    :loading-login="workspace.loadingLogin"
    :health="workspace.health"
    :register-mode="workspace.registerMode"
    :register-form="workspace.registerForm"
    :register-error="workspace.registerError"
    :loading-register="workspace.loadingRegister"
    @update:username="workspace.username = $event"
    @update:password="workspace.password = $event"
    @submit-login="workspace.submitLogin"
    @toggle-register="workspace.toggleRegister"
    @submit-register="workspace.submitRegister"
  />

  <AppShell
    v-else
    :doctor="workspace.currentDoctor"
    :active-section="workspace.section"
    :health="workspace.health"
    :patient-count="workspace.allPatients.length"
    :followup-count="workspace.followupItems.length"
    :error-message="workspace.permissionHint || workspace.screenError"
    :success-message="workspace.archiveSuccess"
    :loading="workspace.globalLoading"
    @select="workspace.selectSection"
    @logout="workspace.logout"
  >
    <DoctorDashboardPage
      v-if="workspace.section === 'doctor'"
      :all-patients="workspace.allPatients"
      :patients="workspace.visiblePendingPatients"
      :selected-patient="workspace.selectedPatient"
      :patient-quadruples="workspace.patientQuadruples"
      :prediction-result="workspace.predictionResult"
      :loading-patients="workspace.loadingPatients"
      :loading-patient="workspace.loadingPatient"
      :loading-predict="workspace.loadingPredict"
      :loading-open-archive="workspace.loadingOpenArchive"
      :loading-open-followup="workspace.loadingOpenFollowup"
      :loading-encounter-status="workspace.loadingEncounterStatus"
      :loading-create-task="workspace.loadingCreateTask"
      :model-unavailable="workspace.modelUnavailable"
      :no-permission="workspace.doctorNoPermission"
      :search-text="workspace.workspaceSearchText"
      :risk-filter="workspace.workspaceRiskFilter"
      :risk-options="workspace.riskOptions"
      @update:search-text="workspace.workspaceSearchText = $event"
      @update:risk-filter="workspace.workspaceRiskFilter = $event"
      @open="workspace.openPatient($event, 'doctor')"
      @open-archive="workspace.openArchiveInNewTab"
      @open-followup="workspace.openFollowupModule"
      @update-encounter-status="workspace.applyEncounterStatus"
      @create-outpatient-task="workspace.registerOutpatientTask"
      @predict="workspace.runPrediction"
    />

    <PatientArchivePage
      v-else-if="workspace.section === 'archive' || workspace.section === 'data-quality'"
      :mode="workspace.archiveMode"
      :all-patients="workspace.allPatients"
      :patients="workspace.archivePagedPatients"
      :loading-patients="workspace.loadingPatients"
      :current-page="workspace.archivePage"
      :total-pages="workspace.archiveTotalPages"
      :patient-count="workspace.allPatients.length"
      :patient-form="workspace.patientForm"
      :selected-patient-id="workspace.selectedPatientId"
      :event-form="workspace.eventForm"
      :relation-options="workspace.relationOptions"
      :saving-patient="workspace.savingPatient"
      :saving-event="workspace.savingEvent"
      :timeline-items="workspace.selectedPatient?.timeline ?? []"
      :selected-patient="workspace.selectedPatient"
      :focus-section="workspace.archiveFocusSection"
      :importing-archive="workspace.importingArchive"
      :import-result-text="workspace.importResultText"
      :doctor-role="workspace.currentDoctor.role"
      :no-permission="workspace.archiveNoPermission"
      :model-unavailable="workspace.modelUnavailable"
      @open="workspace.openPatient($event, 'archive')"
      @create="workspace.openCreateModule"
      @import="workspace.openImportModule"
      @export="workspace.handleExportPatients"
      @prev-page="workspace.prevArchivePage"
      @next-page="workspace.nextArchivePage"
      @submit-archive="workspace.submitArchive"
      @submit-event="workspace.submitEvent"
      @submit-import="workspace.submitImport"
      @prepare-new="workspace.openCreateModule"
      @back="workspace.backToArchiveList"
    />

    <GovernancePage
      v-else-if="workspace.section === 'governance' || workspace.section === 'insights'"
      :doctor-role="workspace.currentDoctor.role"
      :health="workspace.health"
      :maintenance="workspace.maintenanceOverview"
      :governance-modules="workspace.governanceModules"
      :model-metrics="workspace.modelMetrics"
      :loading-governance="workspace.loadingGovernance"
      :loading-maintenance="workspace.loadingMaintenance"
      :loading-metrics="workspace.loadingModelMetrics"
      @refresh="workspace.refreshGovernanceWorkspace"
    />

    <FollowupWorkbenchPage
      v-else-if="workspace.section === 'tasks' || workspace.section === 'contacts' || workspace.section === 'flow'"
      :loading="workspace.loadingBoards"
      :loading-task-action="workspace.loadingTaskStatus || workspace.loadingEncounterStatus"
      :followup-items="workspace.followupItems"
      :flow-board-items="workspace.flowBoardItems"
      :selected-patient-id="workspace.followupFocusPatientId"
      :saving-contact-log="workspace.savingContactLog"
      :doctor-role="workspace.currentDoctor.role"
      :no-permission="workspace.followupNoPermission"
      :model-unavailable="workspace.modelUnavailable"
      @open-patient="workspace.openPatient($event, 'doctor')"
      @open-archive="workspace.openArchiveInNewTab"
      @complete-task="workspace.changeOutpatientTaskStatus($event.patientId, $event.taskId, workspace.taskStatusCompleted)"
      @close-task="workspace.changeOutpatientTaskStatus($event.patientId, $event.taskId, workspace.taskStatusClosed)"
      @submit-contact-log="workspace.submitContactLog"
    />

    <section v-else class="empty-state-card">
      <h3>Module unavailable</h3>
      <p>You do not have permission to access this module. Please choose an available workspace from the left menu.</p>
    </section>
  </AppShell>
</template>

