<script setup lang="ts">
import BasePatientAttachmentPanel from '../patient/PatientAttachmentPanel.vue'

const props = defineProps<{
  patientId: string
  title?: string
}>()
</script>

<template>
  <BasePatientAttachmentPanel
    :patient-id="props.patientId"
    :title="props.title || '档案附件区（患者照片/证件/单据）'"
  />
</template>
