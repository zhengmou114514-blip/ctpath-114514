<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PatientAttachmentPanel from '../../components/patient/PatientAttachmentPanel.vue'

const route = useRoute()

const patientId = computed(() => {
  const value = route.params.patientId ?? route.query.patientId
  return Array.isArray(value) ? value[0] ?? '' : String(value ?? '')
})
</script>

<template>
  <section class="workspace-page patient-attachments-page">
    <header class="card page-header">
      <div>
        <p class="eyebrow">Patient archive</p>
        <h2>Electronic Archive / Attachments</h2>
        <p>
          Manage patient photos, ID cards, insurance cards, referral notes, exam reports and informed consent files.
        </p>
      </div>
    </header>

    <section v-if="!patientId" class="card empty-card">
      Please open this workspace with a patient ID.
    </section>
    <section v-else class="card">
      <PatientAttachmentPanel :patient-id="patientId" />
    </section>
  </section>
</template>

<style scoped>
.patient-attachments-page {
  display: grid;
  gap: 16px;
}

.eyebrow {
  margin: 0 0 4px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.empty-card {
  color: #64748b;
  text-align: center;
}
</style>
