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
  DrugPermissionRole,
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

const currentRole = computed<DrugPermissionRole>(() => {
  const role = restoreAuthSession()?.doctor.role
  if (role === 'doctor' || role === 'nurse' || role === 'archivist') return role
  return 'doctor'
})
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
  const firstDrug = drugs.value[0]

  editingMedicationId.value = ''
  form.medication_id = ''
  form.patient_id = props.patientId
  form.drug_id = firstDrug?.drug_id ?? ''
  form.drug_name_snapshot = firstDrug?.generic_name ?? ''
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

function statusTagType(value: PatientMedicationStatus) {
  if (value === 'active') return 'success'
  if (value === 'paused') return 'warning'
  return 'info'
}

function assessmentTagType(value: boolean, positiveIsGood = true) {
  if (positiveIsGood) return value ? 'success' : 'warning'
  return value ? 'warning' : 'success'
}

function rowClass({ row }: { row: PatientMedicationRecord }) {
  return row.medication_id === editingMedicationId.value ? 'selected-row' : ''
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
    <el-card shadow="never" class="module-card">
      <template #header>
        <div class="module-header">
          <div>
            <p class="eyebrow">Medication closure</p>
            <h3>Current Medication / Adequacy Assessment</h3>
            <p class="subtle">
              This panel displays backend rule results only. Duplicate, baseline and pharmacist-review judgments are not reimplemented here.
            </p>
          </div>
          <el-button :loading="loading" @click="reload">Refresh</el-button>
        </div>
      </template>

      <el-row :gutter="12" class="summary-row">
        <el-col :xs="24" :sm="6">
          <el-statistic title="Current role" :value="currentRole" />
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-statistic title="Active medications" :value="activeMedications.length" />
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-statistic title="Controlled meds" :value="controlledMedicationCount" />
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-statistic title="Pharmacist review" :value="assessment?.needsPharmacistReview ? 'Needed' : 'No'" />
        </el-col>
      </el-row>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        class="module-alert"
      />
      <el-alert
        v-else-if="successMessage"
        :title="successMessage"
        type="success"
        show-icon
        :closable="false"
        class="module-alert"
      />
    </el-card>

    <section class="medication-grid">
      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <div>
              <h4>Current Medication List</h4>
              <span>{{ medications.length }} records</span>
            </div>
          </div>
        </template>

        <el-table
          v-loading="loading"
          :data="medications"
          :row-class-name="rowClass"
          border
          stripe
          empty-text="No current medication records."
          @row-click="openMedication"
        >
          <el-table-column label="Drug" min-width="220">
            <template #default="{ row }">
              <strong>{{ row.drug_name_snapshot }}</strong>
              <p class="table-subtitle">{{ row.start_date }} - {{ row.end_date || 'ongoing' }}</p>
            </template>
          </el-table-column>
          <el-table-column label="Usage" min-width="180">
            <template #default="{ row }">{{ row.dosage }} / {{ row.frequency }} / {{ row.route }}</template>
          </el-table-column>
          <el-table-column label="Status" width="110">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" effect="light">{{ statusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Review" width="130">
            <template #default="{ row }">{{ reviewText(row.review_status) }}</template>
          </el-table-column>
          <el-table-column prop="prescribed_by" label="Prescriber" min-width="130" />
        </el-table>
      </el-card>

      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <div>
              <h4>{{ editingMedicationId ? 'Edit Medication' : 'Add Medication' }}</h4>
              <span>{{ canEditMedication ? 'Editable by current role' : 'View only for current role' }}</span>
            </div>
            <el-tag :type="canEditMedication ? 'success' : 'info'">{{ canEditMedication ? 'Editable' : 'View only' }}</el-tag>
          </div>
        </template>

        <el-alert
          v-if="!canEditMedication"
          title="Current role can view medication data but cannot prescribe or edit. Backend permissions remain authoritative."
          type="warning"
          show-icon
          :closable="false"
          class="module-alert"
        />

        <el-form label-position="top" class="editor-form">
          <el-form-item label="Drug">
            <el-select v-model="form.drug_id" :disabled="!canEditMedication" class="full-width" filterable>
              <el-option
                v-for="drug in drugs"
                :key="drug.drug_id"
                :label="`${drug.generic_name} / ${drug.specification}${drug.is_controlled ? ' / Controlled' : ''}`"
                :value="drug.drug_id"
              />
            </el-select>
          </el-form-item>

          <el-row :gutter="12">
            <el-col :xs="24" :md="12">
              <el-form-item label="Dosage">
                <el-input v-model="form.dosage" :disabled="!canEditMedication" placeholder="500 mg" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Frequency">
                <el-input v-model="form.frequency" :disabled="!canEditMedication" placeholder="bid" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Route">
                <el-input v-model="form.route" :disabled="!canEditMedication" placeholder="po" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Status">
                <el-select v-model="form.status" :disabled="!canEditMedication" class="full-width">
                  <el-option label="Active" value="active" />
                  <el-option label="Paused" value="paused" />
                  <el-option label="Stopped" value="stopped" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Start date">
                <el-date-picker v-model="form.start_date" :disabled="!canEditMedication" value-format="YYYY-MM-DD" class="full-width" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="End date">
                <el-date-picker v-model="form.end_date" :disabled="!canEditMedication" value-format="YYYY-MM-DD" class="full-width" />
              </el-form-item>
            </el-col>
            <el-col :xs="24">
              <el-form-item label="Review status">
                <el-select v-model="form.review_status" :disabled="!canEditMedication" class="full-width">
                  <el-option label="Pending" value="pending" />
                  <el-option label="Approved" value="approved" />
                  <el-option label="Rejected" value="rejected" />
                  <el-option label="Not required" value="not_required" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24">
              <el-form-item label="Note">
                <el-input v-model="form.note" :disabled="!canEditMedication" type="textarea" :rows="3" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <div class="editor-actions">
          <el-button @click="resetForm">New</el-button>
          <el-button type="primary" :loading="saving" :disabled="!canEditMedication" @click="saveMedication">
            {{ editingMedicationId ? 'Save changes' : 'Create medication' }}
          </el-button>
        </div>
      </el-card>
    </section>

    <el-card shadow="never" class="module-card">
      <template #header>
        <div class="section-header">
          <div>
            <h4>用药充分性评估结果</h4>
            <span>{{ assessment?.source || '规则评估' }}</span>
          </div>
        </div>
      </template>

      <el-row v-if="assessment" :gutter="12" class="assessment-row">
        <el-col :xs="24" :sm="6">
          <el-tag :type="assessmentTagType(assessment.hasDuplicateMedication, false)" effect="light">
            重复用药：{{ assessment.hasDuplicateMedication ? '需关注' : '未发现' }}
          </el-tag>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-tag :type="assessmentTagType(assessment.coversBaselineTherapy)" effect="light">
            基础治疗：{{ assessment.coversBaselineTherapy ? '已覆盖' : '需复核' }}
          </el-tag>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-tag :type="assessmentTagType(assessment.alignsWithModelAdvice)" effect="light">
            建议匹配：{{ assessment.alignsWithModelAdvice ? '匹配' : '需复核' }}
          </el-tag>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-tag :type="assessmentTagType(assessment.needsPharmacistReview, false)" effect="light">
            药师复核：{{ assessment.needsPharmacistReview ? '建议复核' : '无需复核' }}
          </el-tag>
        </el-col>
      </el-row>

      <el-empty v-else description="暂无用药评估结果。" />

      <ul v-if="assessment?.notes.length" class="note-list">
        <li v-for="note in assessment.notes" :key="note">{{ note }}</li>
      </ul>
    </el-card>
  </section>
</template>

<style scoped>
.medication-closure-panel {
  display: grid;
  gap: 16px;
}

.module-card {
  border-radius: 12px;
}

.module-header,
.section-header,
.editor-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.module-header h3,
.module-header p,
.section-header h4,
.section-header span,
.table-subtitle {
  margin: 0;
}

.eyebrow {
  margin: 0 0 4px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.subtle,
.section-header span,
.table-subtitle {
  color: #64748b;
  font-size: 12px;
}

.summary-row,
.module-alert,
.editor-form,
.assessment-row {
  margin-top: 14px;
}

.medication-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(360px, 0.8fr);
  gap: 16px;
  align-items: start;
}

.full-width {
  width: 100%;
}

.editor-actions {
  justify-content: flex-end;
}

.note-list {
  margin: 14px 0 0;
  color: #334155;
  line-height: 1.8;
}

:deep(.selected-row) {
  --el-table-tr-bg-color: #eff6ff;
}

@media (max-width: 1180px) {
  .medication-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .module-header,
  .section-header {
    display: grid;
  }
}
</style>
