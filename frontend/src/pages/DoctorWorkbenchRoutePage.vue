<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useWorkspaceContext } from '../composables/workspaceContext'
import DoctorDashboardPage from './DoctorDashboardPage.vue'

const workspace = useWorkspaceContext()
const router = useRouter()

async function handleOpenPatientDetail(patientId: string) {
  const loaded = await workspace.openPatient(patientId, 'doctor')
  if (loaded) {
    void router.push({ name: 'patient-overview', params: { patientId } })
  }
}

function handleDoctorOpenArchive(payload: { patientId: string; focus?: 'overview' | 'events' }) {
  void workspace.openArchiveInNewTab(payload.patientId, payload.focus ?? 'overview')
}

function handleDoctorOpenFollowup(payload: { patientId: string; section?: 'tasks' | 'contacts' | 'flow' }) {
  void workspace.openFollowupModule(payload.patientId, payload.section ?? 'tasks')
}

async function handleDoctorOpenModel(patientId: string) {
  await workspace.openPatient(patientId, 'doctor')
  workspace.selectSection('insights')
  void router.push({ name: 'patient-risk', params: { patientId } })
}
</script>

<template>
  <DoctorDashboardPage
    :all-patients="workspace.allPatients"
    :patients="workspace.visiblePendingPatients"
    :selected-patient="workspace.selectedPatient"
    :loading-patients="workspace.loadingPatients"
    :loading-patient="workspace.loadingPatient"
    :loading-action="workspace.loadingWorkbenchAction"
    :no-permission="workspace.doctorNoPermission"
    :search-text="workspace.workspaceSearchText"
    :risk-filter="workspace.workspaceRiskFilter"
    :risk-options="workspace.riskOptions"
    @update:search-text="workspace.workspaceSearchText = $event"
    @update:risk-filter="workspace.workspaceRiskFilter = $event"
    @open="workspace.openPatient($event, 'doctor')"
    @open-detail="handleOpenPatientDetail"
    @open-archive="handleDoctorOpenArchive"
    @open-followup="handleDoctorOpenFollowup"
    @open-model="handleDoctorOpenModel"
    @workflow-action="workspace.updateDoctorWorkbenchStatus($event.patientId, $event.action)"
  />
</template>
