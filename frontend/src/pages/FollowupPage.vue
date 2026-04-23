<script setup lang="ts">
import type { ContactLogCreatePayload, DoctorUser, FlowBoardRow, FollowupTaskRow, PatientCase } from '../services/types'
import FollowupWorklistBoard from '../components/FollowupWorklistBoard.vue'

const props = defineProps<{
  loading: boolean
  loadingTaskAction: boolean
  followupItems: FollowupTaskRow[]
  flowBoardItems: FlowBoardRow[]
  selectedPatientId?: string
  selectedPatient?: PatientCase | null
  savingContactLog: boolean
  doctorRole?: DoctorUser['role']
}>()

const emit = defineEmits<{
  (e: 'open-patient', patientId: string): void
  (e: 'open-archive', patientId: string): void
  (e: 'complete-task', payload: { patientId: string; taskId: string }): void
  (e: 'close-task', payload: { patientId: string; taskId: string }): void
  (e: 'submit-contact-log', patientId: string, payload: ContactLogCreatePayload): void
}>()
</script>

<template>
  <section class="role-page-stack">
    <FollowupWorklistBoard
      :loading="props.loading"
      :loading-task-action="props.loadingTaskAction"
      :followup-items="props.followupItems"
      :flow-board-items="props.flowBoardItems"
      :selected-patient-id="props.selectedPatientId"
      :selected-patient="props.selectedPatient"
      :saving-contact-log="props.savingContactLog"
      @open-patient="emit('open-patient', $event)"
      @open-archive="emit('open-archive', $event)"
      @complete-task="emit('complete-task', $event)"
      @close-task="emit('close-task', $event)"
      @submit-contact-log="emit('submit-contact-log', $event.patientId, $event.payload)"
    />
  </section>
</template>
