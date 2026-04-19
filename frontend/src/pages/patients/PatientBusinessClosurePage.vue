<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import PatientMedicationClosurePanel from '../../components/medication/PatientMedicationClosurePanel.vue'
import PatientAttachmentPanel from '../../components/patient/PatientAttachmentPanel.vue'
import { getBusinessClosureSummary, getPatientCase } from '../../services/api'
import type { BusinessClosureSummary, PatientCase } from '../../services/types'

const route = useRoute()
const loading = ref(false)
const errorMessage = ref('')
const patient = ref<PatientCase | null>(null)
const closure = ref<BusinessClosureSummary | null>(null)

const patientId = computed(() => {
  const value = route.params.patientId ?? route.query.patientId
  return Array.isArray(value) ? value[0] ?? '' : String(value ?? '')
})

async function reload() {
  if (!patientId.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const nextPatient = await getPatientCase(patientId.value)
    patient.value = nextPatient
    closure.value = await getBusinessClosureSummary(patientId.value, nextPatient.careAdvice)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load patient business closure.'
  } finally {
    loading.value = false
  }
}

watch(patientId, () => {
  void reload()
})

onMounted(() => {
  void reload()
})
</script>

<template>
  <section class="workspace-page patient-business-closure-page">
    <header class="card page-header">
      <div>
        <p class="eyebrow">Patient business closure</p>
        <h2>Attachments / Medication / Assessment</h2>
        <p>
          Close the first-round chronic-care loop: attachment upload and view, drug permission control,
          current medication records, and backend adequacy assessment.
        </p>
      </div>
      <button class="secondary-button" type="button" :disabled="loading || !patientId" @click="reload">
        {{ loading ? 'Refreshing...' : 'Refresh closure' }}
      </button>
    </header>

    <section v-if="!patientId" class="card empty-card">
      Open this workspace with a patient ID, for example: <strong>?patientId=PID1001</strong>
    </section>

    <template v-else>
      <p v-if="errorMessage" class="card error-card">{{ errorMessage }}</p>

      <section class="card patient-summary-card">
        <div>
          <p class="eyebrow">Current patient</p>
          <h3>{{ patient?.name || patientId }}</h3>
          <p>{{ patient?.primaryDisease || '--' }} / {{ patient?.riskLevel || '--' }} / {{ patient?.dataSupport || '--' }}</p>
        </div>
        <div class="summary-metrics">
          <p><span>Attachments</span><strong>{{ closure?.attachmentCount ?? '--' }}</strong></p>
          <p><span>Current meds</span><strong>{{ closure?.currentMedicationCount ?? '--' }}</strong></p>
          <p><span>Controlled meds</span><strong>{{ closure?.controlledMedicationCount ?? '--' }}</strong></p>
          <p><span>Review</span><strong>{{ closure?.needsPharmacistReview ? 'Needed' : 'No' }}</strong></p>
        </div>
      </section>

      <section class="module-grid">
        <article class="card">
          <PatientAttachmentPanel :patient-id="patientId" title="Electronic Archive / Attachments" />
        </article>
        <article class="card">
          <PatientMedicationClosurePanel :patient-id="patientId" :model-advice="patient?.careAdvice || []" />
        </article>
      </section>
    </template>
  </section>
</template>

<style scoped>
.patient-business-closure-page {
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

.empty-card,
.error-card {
  text-align: center;
}

.error-card {
  color: #991b1b;
}

.patient-summary-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.patient-summary-card h3,
.patient-summary-card p {
  margin: 0;
}

.summary-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(100px, 1fr));
  gap: 12px;
}

.summary-metrics p {
  display: grid;
  gap: 4px;
  border-left: 1px solid rgba(148, 163, 184, 0.28);
  padding-left: 12px;
}

.summary-metrics span {
  color: #64748b;
  font-size: 12px;
}

.summary-metrics strong {
  color: #0f172a;
  font-size: 20px;
}

.module-grid {
  display: grid;
  gap: 16px;
}

@media (max-width: 960px) {
  .patient-summary-card,
  .summary-metrics {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>
