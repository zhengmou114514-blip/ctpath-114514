<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { ContactLogCreatePayload, DoctorUser, FlowBoardRow, FollowupTaskRow } from '../services/types'
import FollowupWorklistBoard from '../components/FollowupWorklistBoard.vue'
import MobileFollowupTodayBoard from '../components/MobileFollowupTodayBoard.vue'

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

const isMobile = ref(false)
let mediaQuery: MediaQueryList | null = null

function updateMobileState() {
  if (typeof window === 'undefined') return
  isMobile.value = window.matchMedia('(max-width: 720px)').matches
}

onMounted(() => {
  if (typeof window === 'undefined') return
  mediaQuery = window.matchMedia('(max-width: 720px)')
  updateMobileState()
  mediaQuery.addEventListener('change', updateMobileState)
})

onBeforeUnmount(() => {
  mediaQuery?.removeEventListener('change', updateMobileState)
})
</script>

<template>
  <section class="role-page-stack">
    <MobileFollowupTodayBoard
      v-if="isMobile"
      :loading="props.loading"
      :followup-items="props.followupItems"
      :selected-patient-id="props.selectedPatientId"
      :saving-contact-log="props.savingContactLog"
      @open-patient="emit('open-patient', $event)"
      @open-archive="emit('open-archive', $event)"
      @submit-contact-log="emit('submit-contact-log', $event.patientId, $event.payload)"
    />

    <FollowupWorklistBoard
      v-else
      :loading="props.loading"
      :followup-items="props.followupItems"
      :flow-board-items="props.flowBoardItems"
      :selected-patient-id="props.selectedPatientId"
      :saving-contact-log="props.savingContactLog"
      @open-patient="emit('open-patient', $event)"
      @open-archive="emit('open-archive', $event)"
      @complete-task="emit('complete-task', $event)"
      @close-task="emit('close-task', $event)"
      @submit-contact-log="emit('submit-contact-log', $event.patientId, $event.payload)"
    />
  </section>
</template>