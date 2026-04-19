<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
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

const reviewLabel = computed(() => (closure.value?.needsPharmacistReview ? 'Pharmacist review suggested' : 'No pharmacist review flag'))
const permissionLabel = computed(() => {
  const permission = closure.value?.drugPermission
  if (!permission) return 'No role permission loaded'
  return [
    permission.allow_view ? 'view' : '',
    permission.allow_prescribe ? 'prescribe' : '',
    permission.allow_review ? 'review' : '',
    permission.allow_execute ? 'execute' : '',
    permission.allow_controlled_drug ? 'controlled-drug' : '',
  ].filter(Boolean).join(' / ') || 'view only'
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
        <p class="eyebrow">Business closure summary</p>
        <h2>Patient Attachment / Medication Closure</h2>
        <p>
          This page only summarizes the first-round closure status. Full attachment operations stay in
          Patient Detail / Electronic Archive, while drug catalog and permission configuration stay in Medication Management.
        </p>
      </div>
      <button class="secondary-button" type="button" :disabled="loading || !patientId" @click="reload">
        {{ loading ? 'Refreshing...' : 'Refresh summary' }}
      </button>
    </header>

    <section v-if="!patientId" class="card empty-card">
      Open this summary with a patient ID, for example: <strong>?patientId=PID1001</strong>
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
          <p><span>Assessment</span><strong>{{ reviewLabel }}</strong></p>
        </div>
      </section>

      <section class="closure-grid">
        <article class="card closure-card">
          <p class="eyebrow">Electronic archive</p>
          <h3>Attachment status</h3>
          <p>
            Attachment upload, preview and audit are handled by Patient Detail / Electronic Archive.
            This summary only reports the current attachment count.
          </p>
          <strong>{{ closure?.attachmentCount ?? 0 }} attachment records</strong>
        </article>

        <article class="card closure-card">
          <p class="eyebrow">Medication closure</p>
          <h3>Medication assessment</h3>
          <p>
            Duplicate medication, baseline therapy, pharmacist-review and model-advice alignment are
            returned by the backend assessment service. This page does not reimplement those rules.
          </p>
          <ul>
            <li>Active medications: {{ closure?.activeMedicationCount ?? 0 }}</li>
            <li>Controlled medications: {{ closure?.controlledMedicationCount ?? 0 }}</li>
            <li>Permission scope: {{ permissionLabel }}</li>
          </ul>
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
.patient-summary-card p,
.closure-card h3,
.closure-card p {
  margin: 0;
}

.summary-metrics,
.closure-grid {
  display: grid;
  gap: 12px;
}

.summary-metrics {
  grid-template-columns: repeat(4, minmax(120px, 1fr));
}

.summary-metrics p {
  display: grid;
  gap: 4px;
  border-left: 1px solid rgba(148, 163, 184, 0.28);
  padding-left: 12px;
}

.summary-metrics span,
.closure-card p,
.closure-card li {
  color: #64748b;
  font-size: 12px;
}

.summary-metrics strong {
  color: #0f172a;
  font-size: 18px;
}

.closure-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.closure-card {
  display: grid;
  gap: 10px;
}

.closure-card strong {
  color: #0f172a;
}

.closure-card ul {
  margin: 0;
  padding-left: 18px;
}

@media (max-width: 960px) {
  .patient-summary-card,
  .summary-metrics,
  .closure-grid {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>
