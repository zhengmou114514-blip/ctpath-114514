<script setup lang="ts">
import FollowupPage from './FollowupPage.vue'
import type { ContactLogCreatePayload, DoctorUser, FlowBoardRow, FollowupTaskRow } from '../services/types'

const props = defineProps<{
  loading: boolean
  followupItems: FollowupTaskRow[]
  flowBoardItems: FlowBoardRow[]
  selectedPatientId?: string
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
  <FollowupPage
    :loading="props.loading"
    :followup-items="props.followupItems"
    :flow-board-items="props.flowBoardItems"
    :selected-patient-id="props.selectedPatientId"
    :saving-contact-log="props.savingContactLog"
    :doctor-role="props.doctorRole"
    @open-patient="emit('open-patient', $event)"
    @open-archive="emit('open-archive', $event)"
    @complete-task="emit('complete-task', $event)"
    @close-task="emit('close-task', $event)"
    @submit-contact-log="(patientId, payload) => emit('submit-contact-log', patientId, payload)"
  />
</template>

