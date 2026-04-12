<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import PatientWorkstationBottomPanel from '../components/patient-workstation/PatientWorkstationBottomPanel.vue'
import PatientWorkstationHeaderBar from '../components/patient-workstation/PatientWorkstationHeaderBar.vue'
import PatientWorkstationLeftPanel from '../components/patient-workstation/PatientWorkstationLeftPanel.vue'
import PatientWorkstationMiddlePanel from '../components/patient-workstation/PatientWorkstationMiddlePanel.vue'
import PatientWorkstationRightPanel from '../components/patient-workstation/PatientWorkstationRightPanel.vue'
import {
  createPatientOutpatientTask,
  getPatientCase,
  getPatientQuadruples,
  healthCheck,
  predictPatient,
  updatePatientEncounterStatus,
} from '../services/api'
import type { HealthResponse, PatientCase, PatientQuadruple, PredictResponse } from '../services/types'
import { useAuditTrailStore } from '../stores/auditTrailStore'

const props = defineProps<{
  patientId: string
}>()

const emit = defineEmits<{
  (e: 'back'): void
}>()

const patient = ref<PatientCase | null>(null)
const quadruples = ref<PatientQuadruple[]>([])
const prediction = ref<PredictResponse | null>(null)
const health = ref<HealthResponse | null>(null)

const loadingPatient = ref(false)
const loadingHealth = ref(false)
const loadingPredict = ref(false)
const loadingAction = ref(false)

const screenError = ref('')
const predictError = ref('')
const actionMessage = ref('')
const lastUpdatedAt = ref('')
const isWatched = ref(false)
const auditTrail = useAuditTrailStore()

const hasPatient = computed(() => Boolean(patient.value))
const loading = computed(() => loadingPatient.value || loadingHealth.value)

const degradedReasons = computed(() => {
  const reasons: string[] = []
  if (health.value?.mode === 'demo') {
    reasons.push('System is running in demo mode. Data may be placeholder data.')
  }
  if (patient.value?.dataSupport === 'low') {
    reasons.push('Current data support is low. Please verify key structured events before final decisions.')
  }
  if (prediction.value?.mode === 'similar-case') {
    reasons.push('Prediction currently uses similar-case fallback instead of direct model scoring.')
  }
  if (predictError.value) {
    reasons.push('Latest prediction failed. Current advice may rely on historical results only.')
  }
  return reasons
})

function riskPriority(level: string): 'high' | 'medium' | 'low' {
  const normalized = level.toLowerCase()
  if (normalized.includes('high')) return 'high'
  if (normalized.includes('medium')) return 'medium'
  return 'low'
}

async function loadHealth() {
  loadingHealth.value = true
  try {
    health.value = await healthCheck()
  } catch {
    health.value = null
  } finally {
    loadingHealth.value = false
  }
}

async function loadPatientDetail(id: string) {
  if (!id) return
  loadingPatient.value = true
  screenError.value = ''
  actionMessage.value = ''
  predictError.value = ''

  try {
    const [patientRes, quadruplesRes] = await Promise.all([getPatientCase(id), getPatientQuadruples(id)])
    patient.value = patientRes
    quadruples.value = quadruplesRes
    prediction.value = null
    lastUpdatedAt.value = new Date().toISOString()
    auditTrail.addAuditLog({
      action: 'view_patient_detail',
      target: { type: 'patient', id: patientRes.patientId, label: patientRes.name },
      result: 'success',
      detail: 'Opened patient detail workstation.',
    })
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : 'Failed to load patient detail.'
    patient.value = null
    quadruples.value = []
    prediction.value = null
    auditTrail.addAuditLog({
      action: 'view_patient_detail',
      target: { type: 'patient', id },
      result: 'failed',
      detail: error instanceof Error ? error.message : 'Failed to load patient detail.',
    })
  } finally {
    loadingPatient.value = false
  }
}

async function refreshPrediction() {
  if (!patient.value) return
  loadingPredict.value = true
  predictError.value = ''
  actionMessage.value = ''

  try {
    prediction.value = await predictPatient({
      patientId: patient.value.patientId,
      asOfTime: patient.value.lastVisit,
      topk: 3,
    })
    lastUpdatedAt.value = prediction.value.generatedAt
    auditTrail.addAuditLog({
      action: 'trigger_prediction',
      target: { type: 'patient', id: patient.value.patientId, label: patient.value.name },
      result: prediction.value.mode === 'model' ? 'success' : 'degraded',
      detail: `Prediction completed via ${prediction.value.mode}/${prediction.value.strategy}.`,
    })
    auditTrail.addAuditLog({
      action: 'generate_advice',
      target: { type: 'patient', id: patient.value.patientId, label: patient.value.name },
      result: prediction.value.advice.length ? (prediction.value.mode === 'model' ? 'success' : 'degraded') : 'failed',
      detail: `Advice count: ${prediction.value.advice.length}.`,
    })
  } catch (error) {
    predictError.value = error instanceof Error ? error.message : 'Prediction failed.'
    auditTrail.addAuditLog({
      action: 'trigger_prediction',
      target: { type: 'patient', id: patient.value.patientId, label: patient.value.name },
      result: 'failed',
      detail: error instanceof Error ? error.message : 'Prediction failed.',
    })
    auditTrail.addAuditLog({
      action: 'generate_advice',
      target: { type: 'patient', id: patient.value.patientId, label: patient.value.name },
      result: 'failed',
      detail: 'Advice generation failed because prediction failed.',
    })
  } finally {
    loadingPredict.value = false
  }
}

async function createFollowupTask(title?: string) {
  if (!patient.value) return
  loadingAction.value = true
  actionMessage.value = ''

  try {
    const dueDate = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10)
    const updated = await createPatientOutpatientTask(patient.value.patientId, {
      category: 'recheck',
      title: title || 'Clinical follow-up task',
      owner: patient.value.caseManager || 'Follow-up Nurse',
      dueDate,
      priority: riskPriority(patient.value.riskLevel),
      note: title ? `Copied from advice card: ${title}` : 'Generated from patient workstation quick action.',
      status: 'Pending',
      source: 'workspace',
    })
    patient.value = updated
    actionMessage.value = title ? 'Advice copied to follow-up plan.' : 'Follow-up task created.'
    lastUpdatedAt.value = new Date().toISOString()
    auditTrail.addAuditLog({
      action: 'create_followup_task',
      target: { type: 'followup_task', id: patient.value.patientId, label: title || 'Clinical follow-up task' },
      result: 'success',
      detail: title ? `Created follow-up task from advice: ${title}` : 'Created follow-up task from quick action.',
    })
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : 'Failed to create follow-up task.'
    auditTrail.addAuditLog({
      action: 'create_followup_task',
      target: { type: 'followup_task', id: patient.value.patientId, label: title || 'Clinical follow-up task' },
      result: 'failed',
      detail: error instanceof Error ? error.message : 'Failed to create follow-up task.',
    })
  } finally {
    loadingAction.value = false
  }
}

async function markForReview() {
  if (!patient.value) return
  loadingAction.value = true
  actionMessage.value = ''

  try {
    const updated = await updatePatientEncounterStatus(patient.value.patientId, {
      status: 'pending_review',
    })
    patient.value = updated
    actionMessage.value = 'Case has been marked for review.'
    lastUpdatedAt.value = new Date().toISOString()
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : 'Failed to update review status.'
  } finally {
    loadingAction.value = false
  }
}

function toggleWatch() {
  isWatched.value = !isWatched.value
  actionMessage.value = isWatched.value ? 'Patient added to watchlist.' : 'Patient removed from watchlist.'
}

function copySuggestionToFollowup(actionTitle: string) {
  void createFollowupTask(actionTitle)
}

watch(
  () => props.patientId,
  (id) => {
    void Promise.all([loadHealth(), loadPatientDetail(id)])
  },
  { immediate: true }
)
</script>

<template>
  <section class="patient-workstation-page">
    <div class="page-head">
      <button class="secondary-button" @click="emit('back')">Back to Patient List</button>
      <p v-if="actionMessage" class="workstation-tip">{{ actionMessage }}</p>
    </div>

    <div v-if="loading" class="state-card loading">Loading patient workstation...</div>

    <div v-else-if="screenError" class="state-card error">
      <strong>Failed to load patient detail</strong>
      <p>{{ screenError }}</p>
      <button class="secondary-button" @click="loadPatientDetail(props.patientId)">Retry</button>
    </div>

    <div v-else-if="!hasPatient" class="state-card empty">Patient not found.</div>

    <template v-else>
      <PatientWorkstationHeaderBar
        :patient="patient!"
        :data-mode="health?.mode ?? 'unknown'"
        :last-updated-at="lastUpdatedAt || patient!.lastVisit"
        :degraded-reasons="degradedReasons"
      />

      <div v-if="degradedReasons.length" class="state-card degraded">
        <strong>Degraded Mode Notice</strong>
        <ul>
          <li v-for="reason in degradedReasons" :key="reason">{{ reason }}</li>
        </ul>
      </div>

      <section class="workstation-grid">
        <PatientWorkstationLeftPanel :patient="patient!" />
        <PatientWorkstationMiddlePanel :timeline="patient!.timeline" :quadruples="quadruples" />
        <PatientWorkstationRightPanel
          :patient="patient!"
          :prediction-result="prediction"
          :loading-predict="loadingPredict"
          :predict-error="predictError"
          :loading-action="loadingAction"
          :watched="isWatched"
          @refresh-predict="refreshPrediction"
          @create-followup="createFollowupTask"
          @toggle-watch="toggleWatch"
          @mark-review="markForReview"
          @copy-to-followup="copySuggestionToFollowup"
        />
      </section>

      <PatientWorkstationBottomPanel :patient="patient!" />
    </template>
  </section>
</template>

<style scoped>
.patient-workstation-page {
  display: grid;
  gap: 12px;
}

.page-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.workstation-tip {
  margin: 0;
  color: var(--ws-text-muted, #617385);
  font-size: 0.86rem;
}

.state-card {
  border-radius: 10px;
  border: 1px solid var(--ws-border, #cfd9e5);
  background: #fff;
  padding: 14px;
}

.state-card.loading {
  color: var(--ws-text-muted, #617385);
}

.state-card.error {
  border-color: #efc2c5;
  background: #fff0f2;
  color: #a4383f;
  display: grid;
  gap: 8px;
}

.state-card.error p {
  margin: 0;
}

.state-card.empty {
  color: var(--ws-text-muted, #617385);
}

.state-card.degraded {
  border-color: #efdbb2;
  background: #fff8ec;
  color: #8a5a12;
}

.state-card.degraded strong {
  display: block;
  margin-bottom: 6px;
}

.state-card.degraded ul {
  margin: 0;
  padding-left: 18px;
}

.workstation-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 360px;
  gap: 12px;
  align-items: start;
}

@media (max-width: 1420px) {
  .workstation-grid {
    grid-template-columns: 1fr;
  }
}
</style>
