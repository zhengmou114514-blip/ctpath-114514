<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import {
  createPatientMedication,
  getDrugCatalog,
  getDrugPermissions,
  getPatientMedicationAssessment,
  getPatientMedications,
  restoreAuthSession,
  updatePatientMedication,
} from '../../services/api'
import type {
  DrugCatalogRecord,
  DrugPermissionRecord,
  MedicationAdequacyAssessment,
  PatientMedicationRecord,
  PatientMedicationReviewStatus,
  PatientMedicationStatus,
  PatientMedicationUpsertRequest,
} from '../../services/types'

const props = withDefaults(defineProps<{
  patientId: string
  modelAdvice?: string[]
}>(), {
  modelAdvice: () => [],
})

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const medications = ref<PatientMedicationRecord[]>([])
const drugs = ref<DrugCatalogRecord[]>([])
const permissions = ref<DrugPermissionRecord[]>([])
const assessment = ref<MedicationAdequacyAssessment | null>(null)
const editingMedicationId = ref('')

const form = reactive<PatientMedicationUpsertRequest>({
  medication_id: '',
  patient_id: '',
  drug_id: '',
  drug_name_snapshot: '',
  dosage: '',
  frequency: '',
  route: 'po',
  start_date: '',
  end_date: '',
  status: 'active',
  review_status: 'pending',
  note: '',
})

const currentRole = computed(() => restoreAuthSession()?.doctor.role ?? 'doctor')
const currentPermission = computed(() => permissions.value.find((item) => item.role === currentRole.value) ?? null)
const selectedDrug = computed(() => drugs.value.find((item) => item.drug_id === form.drug_id) ?? null)
const activeMedications = computed(() => medications.value.filter((item) => item.status === 'active'))
const controlledMedicationCount = computed(() => {
  const drugById = new Map(drugs.value.map((item) => [item.drug_id, item]))
  return medications.value.filter((item) => drugById.get(item.drug_id)?.is_controlled).length
})
const canEditMedication = computed(() => Boolean(currentPermission.value?.allow_prescribe))

function resetForm() {
  const today = new Date()
  const defaultEnd = new Date(today)
  defaultEnd.setDate(today.getDate() + 30)
  editingMedicationId.value = ''
  form.medication_id = ''
  form.patient_id = props.patientId
  form.drug_id = drugs.value[0]?.drug_id ?? ''
  form.drug_name_snapshot = drugs.value[0]?.generic_name ?? ''
  form.dosage = ''
  form.frequency = ''
  form.route = 'po'
  form.start_date = today.toISOString().slice(0, 10)
  form.end_date = defaultEnd.toISOString().slice(0, 10)
  form.status = 'active'
  form.review_status = 'pending'
  form.note = ''
}

function openMedication(record: PatientMedicationRecord) {
  editingMedicationId.value = record.medication_id
  form.medication_id = record.medication_id
  form.patient_id = record.patient_id
  form.drug_id = record.drug_id
  form.drug_name_snapshot = record.drug_name_snapshot
  form.dosage = record.dosage
  form.frequency = record.frequency
  form.route = record.route
  form.start_date = record.start_date
  form.end_date = record.end_date
  form.status = record.status
  form.review_status = record.review_status
  form.note = record.note
}

async function reload() {
  if (!props.patientId) return
  loading.value = true
  errorMessage.value = ''
  try {
    const [nextDrugs, nextPermissions, nextMedications, nextAssessment] = await Promise.all([
      getDrugCatalog(),
      getDrugPermissions(),
      getPatientMedications(props.patientId),
      getPatientMedicationAssessment(props.patientId, { modelAdvice: props.modelAdvice }),
    ])
    drugs.value = nextDrugs
    permissions.value = nextPermissions
    medications.value = nextMedications
    assessment.value = nextAssessment
    if (!editingMedicationId.value) resetForm()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load medication closure data.'
  } finally {
    loading.value = false
  }
}

async function saveMedication() {
  if (!props.patientId || !canEditMedication.value) return
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const drug = selectedDrug.value
    const payload: PatientMedicationUpsertRequest = {
      ...form,
      patient_id: props.patientId,
      medication_id: editingMedicationId.value || form.medication_id || `med-${Date.now()}`,
      end_date: form.end_date || form.start_date,
      drug_name_snapshot: drug
        ? [drug.generic_name, drug.brand_name ? `(${drug.brand_name})` : ''].filter(Boolean).join(' ')
        : form.drug_name_snapshot,
    }

    if (editingMedicationId.value) {
      await updatePatientMedication(props.patientId, editingMedicationId.value, payload)
      successMessage.value = 'Current medication updated. Audit is recorded by backend.'
    } else {
      await createPatientMedication(props.patientId, payload)
      successMessage.value = 'Current medication created. Audit is recorded by backend.'
    }
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to save current medication.'
  } finally {
    saving.value = false
  }
}

function statusText(value: PatientMedicationStatus): string {
  return value === 'active' ? 'Active' : value === 'paused' ? 'Paused' : 'Stopped'
}

function reviewText(value: PatientMedicationReviewStatus): string {
  return value === 'not_required' ? 'Not required' : `${value.charAt(0).toUpperCase()}${value.slice(1)}`
}

watch(
  () => props.patientId,
  () => {
    editingMedicationId.value = ''
    void reload()
  },
  { immediate: true }
)

watch(selectedDrug, (drug) => {
  if (!drug || editingMedicationId.value) return
  form.drug_name_snapshot = drug.generic_name
})
</script>

<template>
  <section class="medication-closure-panel">
    <header class="panel-header">
      <div>
        <p class="eyebrow">Medication closure</p>
        <h3>Current Medication / Adequacy Assessment</h3>
        <p class="subtle">
          The page displays backend rule results only; duplicate, baseline and pharmacist-review judgments stay in the service layer.
        </p>
      </div>
      <button class="secondary-button" type="button" :disabled="loading" @click="reload">
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <section class="summary-grid">
      <article class="metric-card">
        <span>Current role</span>
        <strong>{{ currentRole }}</strong>
      </article>
      <article class="metric-card">
        <span>Active medications</span>
        <strong>{{ activeMedications.length }}</strong>
      </article>
      <article class="metric-card">
        <span>Controlled meds</span>
        <strong>{{ controlledMedicationCount }}</strong>
      </article>
      <article class="metric-card">
        <span>Pharmacist review</span>
        <strong>{{ assessment?.needsPharmacistReview ? 'Needed' : 'No' }}</strong>
      </article>
    </section>

    <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>
    <p v-else-if="successMessage" class="message success">{{ successMessage }}</p>

    <section class="closure-layout">
      <article class="list-card">
        <div class="card-head">
          <h4>Current Medication List</h4>
          <span>{{ medications.length }} records</span>
        </div>

        <p v-if="loading" class="empty-state">Loading medications...</p>
        <p v-else-if="!medications.length" class="empty-state">No current medication records.</p>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Drug</th>
                <th>Usage</th>
                <th>Status</th>
                <th>Review</th>
                <th>Prescriber</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in medications"
                :key="item.medication_id"
                :class="{ active: item.medication_id === editingMedicationId }"
                @click="openMedication(item)"
              >
                <td>
                  <strong>{{ item.drug_name_snapshot }}</strong>
                  <p>{{ item.start_date }} - {{ item.end_date || 'ongoing' }}</p>
                </td>
                <td>{{ item.dosage }} / {{ item.frequency }} / {{ item.route }}</td>
                <td>{{ statusText(item.status) }}</td>
                <td>{{ reviewText(item.review_status) }}</td>
                <td>{{ item.prescribed_by || '--' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="editor-card">
        <div class="card-head">
          <h4>{{ editingMedicationId ? 'Edit Medication' : 'Add Medication' }}</h4>
          <span>{{ canEditMedication ? 'Editable' : 'View only' }}</span>
        </div>

        <p v-if="!canEditMedication" class="message warning">
          Current role can view medication data but cannot prescribe or edit. Backend permissions remain authoritative.
        </p>

        <div class="form-grid">
          <label class="field wide">
            <span>Drug</span>
            <select v-model="form.drug_id" :disabled="!canEditMedication">
              <option v-for="drug in drugs" :key="drug.drug_id" :value="drug.drug_id">
                {{ drug.generic_name }} / {{ drug.specification }}{{ drug.is_controlled ? ' / Controlled' : '' }}
              </option>
            </select>
          </label>
          <label class="field">
            <span>Dosage</span>
            <input v-model="form.dosage" :disabled="!canEditMedication" type="text" placeholder="500 mg" />
          </label>
          <label class="field">
            <span>Frequency</span>
            <input v-model="form.frequency" :disabled="!canEditMedication" type="text" placeholder="bid" />
          </label>
          <label class="field">
            <span>Route</span>
            <input v-model="form.route" :disabled="!canEditMedication" type="text" placeholder="po" />
          </label>
          <label class="field">
            <span>Start date</span>
            <input v-model="form.start_date" :disabled="!canEditMedication" type="date" />
          </label>
          <label class="field">
            <span>End date</span>
            <input v-model="form.end_date" :disabled="!canEditMedication" type="date" />
          </label>
          <label class="field">
            <span>Status</span>
            <select v-model="form.status" :disabled="!canEditMedication">
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="stopped">Stopped</option>
            </select>
          </label>
          <label class="field">
            <span>Review status</span>
            <select v-model="form.review_status" :disabled="!canEditMedication">
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="not_required">Not required</option>
            </select>
          </label>
          <label class="field wide">
            <span>Note</span>
            <textarea v-model="form.note" :disabled="!canEditMedication" rows="3" />
          </label>
        </div>

        <div class="actions">
          <button class="secondary-button" type="button" @click="resetForm">New</button>
          <button class="primary-button" type="button" :disabled="saving || !canEditMedication" @click="saveMedication">
            {{ saving ? 'Saving...' : editingMedicationId ? 'Save changes' : 'Create medication' }}
          </button>
        </div>
      </article>
    </section>

    <section class="assessment-card">
      <div class="card-head">
        <h4>Backend Assessment Result</h4>
        <span>{{ assessment?.source || '--' }}</span>
      </div>

      <div v-if="assessment" class="assessment-grid">
        <p><span>Duplicate medication</span><strong>{{ assessment.hasDuplicateMedication ? 'Warning' : 'Clear' }}</strong></p>
        <p><span>Baseline therapy</span><strong>{{ assessment.coversBaselineTherapy ? 'Covered' : 'Needs review' }}</strong></p>
        <p><span>Model advice alignment</span><strong>{{ assessment.alignsWithModelAdvice ? 'Aligned' : 'Review' }}</strong></p>
        <p><span>Pharmacist review</span><strong>{{ assessment.needsPharmacistReview ? 'Suggested' : 'Not required' }}</strong></p>
      </div>

      <ul v-if="assessment?.notes.length" class="note-list">
        <li v-for="note in assessment.notes" :key="note">{{ note }}</li>
      </ul>
    </section>
  </section>
</template>

<style scoped>
.medication-closure-panel {
  display: grid;
  gap: 16px;
}

.panel-header,
.card-head,
.actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-header h3,
.panel-header p,
.card-head h4,
.message {
  margin: 0;
}

.eyebrow {
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.subtle,
.metric-card span,
.field span,
.card-head span,
.assessment-grid span {
  color: #64748b;
  font-size: 12px;
}

.summary-grid,
.closure-layout,
.form-grid,
.assessment-grid {
  display: grid;
  gap: 12px;
}

.summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.closure-layout {
  grid-template-columns: minmax(0, 1.2fr) minmax(360px, 0.8fr);
  align-items: start;
}

.metric-card,
.list-card,
.editor-card,
.assessment-card {
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 14px;
  background: #fff;
  padding: 14px;
}

.metric-card {
  display: grid;
  gap: 4px;
}

.metric-card strong {
  color: #0f172a;
  font-size: 22px;
  text-transform: capitalize;
}

.message {
  border-radius: 10px;
  padding: 10px 12px;
}

.message.error {
  border-left: 4px solid #dc2626;
  background: #fef2f2;
  color: #991b1b;
}

.message.success {
  border-left: 4px solid #16a34a;
  background: #f0fdf4;
  color: #166534;
}

.message.warning {
  background: #fff7ed;
  color: #9a3412;
}

.table-wrap {
  margin-top: 12px;
  overflow: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  padding: 10px;
  text-align: left;
  vertical-align: top;
}

tbody tr {
  cursor: pointer;
}

tbody tr.active {
  background: rgba(37, 99, 235, 0.08);
}

td p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 12px;
}

.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 12px;
}

.field {
  display: grid;
  gap: 6px;
}

.field.wide {
  grid-column: 1 / -1;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.42);
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
}

.actions {
  margin-top: 12px;
  justify-content: flex-end;
}

.empty-state {
  margin: 12px 0 0;
  border: 1px dashed rgba(148, 163, 184, 0.42);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
  color: #64748b;
}

.assessment-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 12px;
}

.assessment-grid p {
  display: grid;
  gap: 4px;
  margin: 0;
}

.note-list {
  margin: 12px 0 0;
  color: #334155;
}

@media (max-width: 1120px) {
  .summary-grid,
  .closure-layout,
  .assessment-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
