<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useWorkspaceContext } from '../composables/workspaceContext'
import PatientArchivePage from './PatientArchivePage.vue'

const workspace = useWorkspaceContext()
const router = useRouter()

async function handleOpenPatientSubpage(patientId: string, routeName: string) {
  const loaded = await workspace.openPatient(patientId, 'archive')
  if (loaded) {
    void router.push({ name: routeName, params: { patientId } })
  }
}

function handleOpenFollowup(payload: { patientId?: string; section?: 'tasks' | 'contacts' | 'flow' }) {
  void workspace.openFollowupModule(payload.patientId || workspace.selectedPatientId || undefined, payload.section ?? 'tasks')
}

function handlePrintArchive(patientId?: string) {
  const targetPatientId = patientId || workspace.selectedPatientId || workspace.allPatients[0]?.patientId
  if (!targetPatientId) return
  void router.push({ name: 'patient-archive-print', params: { patientId: targetPatientId } })
}
</script>

<template>
  <PatientArchivePage
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
    :doctor-role="workspace.currentDoctor?.role"
    :no-permission="workspace.archiveNoPermission"
    :model-unavailable="workspace.modelUnavailable"
    @open="handleOpenPatientSubpage($event, 'patient-overview')"
    @open-profile="handleOpenPatientSubpage($event, 'patient-profile')"
    @open-attachments="handleOpenPatientSubpage($event, 'patient-attachments')"
    @create="workspace.openCreateModule"
    @import="workspace.openImportModule"
    @export="handlePrintArchive"
    @prev-page="workspace.prevArchivePage"
    @next-page="workspace.nextArchivePage"
    @submit-archive="workspace.submitArchive"
    @submit-event="workspace.submitEvent"
    @submit-import="workspace.submitImport"
    @prepare-new="workspace.openCreateModule"
    @back="workspace.backToArchiveList"
    @open-followup="handleOpenFollowup"
  />
</template>
