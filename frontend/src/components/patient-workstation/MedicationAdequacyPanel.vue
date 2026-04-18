<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  createPatientMedication,
  getDrugCatalog,
  getDrugPermissions,
  getPatientMedicationAssessment,
  getPatientMedications,
  updatePatientMedication,
} from '../../services/api'
import type {
  DrugCatalogRecord,
  DrugPermissionRecord,
  DrugPermissionRole,
  MedicationAdequacyAssessment,
  PatientCase,
  PatientMedicationRecord,
  PatientMedicationReviewStatus,
  PatientMedicationStatus,
  PatientMedicationUpsertRequest,
} from '../../services/types'

const props = defineProps<{
  patient: PatientCase
  modelAdvice: string[]
  doctorRole: string
}>()

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const medications = ref<PatientMedicationRecord[]>([])
const drugCatalog = ref<DrugCatalogRecord[]>([])
const permission = ref<DrugPermissionRecord | null>(null)
const editingMedicationId = ref<string | null>(null)
const assessment = ref<MedicationAdequacyAssessment>(buildEmptyAssessment())

const form = reactive<PatientMedicationUpsertRequest>(buildEmptyForm())

const canView = computed(() => Boolean(permission.value?.allow_view))
const canEdit = computed(() => Boolean(permission.value && (permission.value.allow_prescribe || permission.value.allow_review)))
const canReview = computed(() => Boolean(permission.value?.allow_review))
const canUseControlledDrug = computed(() => Boolean(permission.value?.allow_controlled_drug))

const availableDrugs = computed(() =>
  [...drugCatalog.value]
    .filter((drug) => drug.status === 'active')
    .sort((left, right) => `${left.generic_name} ${left.drug_id}`.localeCompare(`${right.generic_name} ${right.drug_id}`))
)

const selectedDrug = computed(() => drugCatalog.value.find((item) => item.drug_id === form.drug_id) ?? null)

const activeMedicationCount = computed(() => medications.value.filter((item) => item.status === 'active').length)
const pendingReviewCount = computed(() => medications.value.filter((item) => item.review_status === 'pending').length)
const duplicateHint = computed(() => assessment.value.hasDuplicateMedication)
const baselineHint = computed(() => assessment.value.coversBaselineTherapy)
const pharmacistReviewHint = computed(() => assessment.value.needsPharmacistReview)
const controlledDrugBlocked = computed(() => Boolean(selectedDrug.value?.is_controlled && !canUseControlledDrug.value))

function buildEmptyAssessment(notes: string[] = []): MedicationAdequacyAssessment {
  return {
    coversBaselineTherapy: false,
    hasDuplicateMedication: false,
    hasContraindicationConflictPlaceholder: false,
    alignsWithModelAdvice: true,
    needsPharmacistReview: true,
    suggestSupplementClasses: [],
    notes: notes.length ? notes : ['Medication assessment has not been loaded from the backend rule service.'],
    evaluatedAt: new Date().toISOString(),
    evaluator: 'frontend-display-shell',
    source: 'frontend-fallback',
  }
}

function buildEmptyForm(): PatientMedicationUpsertRequest {
  const now = new Date().toISOString().slice(0, 10)
  return {
    medication_id: `med-${props?.patient?.patientId ?? 'patient'}-${Date.now().toString(36)}`,
    patient_id: props?.patient?.patientId ?? '',
    drug_id: '',
    drug_name_snapshot: '',
    dosage: '',
    frequency: '',
    route: 'po',
    start_date: now,
    end_date: '',
    status: 'active' as PatientMedicationStatus,
    review_status: 'pending' as PatientMedicationReviewStatus,
    note: '',
  }
}

function applyDrugSnapshot(drugId: string) {
  const item = drugCatalog.value.find((drug) => drug.drug_id === drugId)
  form.drug_name_snapshot = item ? medicationLabel(item) : ''
}

function medicationLabel(drug: DrugCatalogRecord): string {
  return [drug.generic_name, drug.brand_name ? `(${drug.brand_name})` : ''].filter(Boolean).join(' ').trim() || drug.drug_id
}

function formatDate(value: string): string {
  return value ? value.slice(0, 10) : '--'
}

function reviewBadgeText(status: PatientMedicationReviewStatus): string {
  switch (status) {
    case 'approved':
      return '已通过'
    case 'rejected':
      return '已拒绝'
    case 'not_required':
      return '无需复核'
    default:
      return '待复核'
  }
}

function reviewBadgeClass(status: PatientMedicationReviewStatus): string {
  switch (status) {
    case 'approved':
      return 'badge-good'
    case 'rejected':
      return 'badge-bad'
    case 'not_required':
      return 'badge-neutral'
    default:
      return 'badge-warn'
  }
}

function statusText(status: PatientMedicationStatus): string {
  switch (status) {
    case 'paused':
      return '暂停'
    case 'stopped':
      return '停用'
    default:
      return '使用中'
  }
}

function statusClass(status: PatientMedicationStatus): string {
  switch (status) {
    case 'paused':
      return 'badge-warn'
    case 'stopped':
      return 'badge-bad'
    default:
      return 'badge-good'
  }
}

function resetForm(nextMedication?: PatientMedicationRecord | null) {
  const next = nextMedication ?? null
  form.medication_id = next?.medication_id ?? `med-${props.patient.patientId}-${Date.now().toString(36)}`
  form.patient_id = props.patient.patientId
  form.drug_id = next?.drug_id ?? availableDrugs.value[0]?.drug_id ?? ''
  form.drug_name_snapshot = next?.drug_name_snapshot ?? ''
  form.dosage = next?.dosage ?? ''
  form.frequency = next?.frequency ?? ''
  form.route = next?.route ?? 'po'
  form.start_date = next?.start_date ?? new Date().toISOString().slice(0, 10)
  form.end_date = next?.end_date ?? ''
  form.status = next?.status ?? 'active'
  form.review_status = next?.review_status ?? 'pending'
  form.note = next?.note ?? ''
  editingMedicationId.value = next?.medication_id ?? null
  if (form.drug_id) {
    applyDrugSnapshot(form.drug_id)
  }
}

function beginCreate() {
  resetForm()
}

function beginEdit(item: PatientMedicationRecord) {
  resetForm(item)
}

function buildPayload(): PatientMedicationUpsertRequest {
  const snapshot = form.drug_name_snapshot || (selectedDrug.value ? medicationLabel(selectedDrug.value) : '')
  return {
    ...form,
    patient_id: props.patient.patientId,
    drug_name_snapshot: snapshot,
    note: form.note.trim(),
    dosage: form.dosage.trim(),
    frequency: form.frequency.trim(),
    route: form.route.trim(),
    start_date: form.start_date.trim(),
    end_date: form.end_date.trim(),
  }
}

async function reloadWorkspace() {
  loading.value = true
  errorMessage.value = ''

  try {
    const [medicationItems, catalogItems, permissionItems, assessmentResult] = await Promise.all([
      getPatientMedications(props.patient.patientId),
      getDrugCatalog({ status: 'active' }),
      getDrugPermissions(props.doctorRole as DrugPermissionRole),
      getPatientMedicationAssessment(props.patient.patientId, { modelAdvice: props.modelAdvice }),
    ])

    medications.value = medicationItems
    drugCatalog.value = catalogItems
    permission.value = permissionItems[0] ?? null
    assessment.value = assessmentResult

    const currentMedication = editingMedicationId.value
      ? medicationItems.find((item) => item.medication_id === editingMedicationId.value) ?? null
      : null

    if (currentMedication) {
      resetForm(currentMedication)
    } else {
      resetForm(null)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载当前用药失败。'
    assessment.value = buildEmptyAssessment([errorMessage.value])
  } finally {
    loading.value = false
  }
}

async function reloadAssessment() {
  try {
    assessment.value = await getPatientMedicationAssessment(props.patient.patientId, { modelAdvice: props.modelAdvice })
  } catch (error) {
    assessment.value = buildEmptyAssessment([error instanceof Error ? error.message : 'Medication assessment failed.'])
  }
}

async function submitMedication() {
  if (!canEdit.value) {
    errorMessage.value = '当前角色没有编辑当前用药的权限。'
    return
  }
  if (!form.drug_id) {
    errorMessage.value = '请选择一个药品。'
    return
  }
  if (controlledDrugBlocked.value) {
    errorMessage.value = '当前角色没有管制药开立权限。'
    return
  }

  saving.value = true
  errorMessage.value = ''

  try {
    const payload = buildPayload()
    if (editingMedicationId.value) {
      await updatePatientMedication(props.patient.patientId, editingMedicationId.value, payload)
    } else {
      await createPatientMedication(props.patient.patientId, payload)
    }
    await reloadWorkspace()
    beginCreate()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存当前用药失败。'
  } finally {
    saving.value = false
  }
}

watch(
  () => props.patient.patientId,
  () => {
    editingMedicationId.value = null
    beginCreate()
    void reloadWorkspace()
  },
  { immediate: true }
)

watch(
  () => props.doctorRole,
  () => {
    void reloadWorkspace()
  }
)

watch(
  () => form.drug_id,
  (drugId) => {
    if (!drugId) {
      form.drug_name_snapshot = ''
      return
    }
    applyDrugSnapshot(drugId)
  },
  { immediate: true }
)

watch(
  () => props.modelAdvice.join('|'),
  () => {
    void reloadAssessment()
  }
)

onMounted(() => {
  void reloadWorkspace()
})
</script>

<template>
  <section class="medication-workspace">
    <header class="workspace-head">
      <div>
        <h3>当前用药与用药充分性</h3>
        <p>只承接患者当前用药，不进入完整处方流。</p>
      </div>

      <div class="header-actions">
        <button class="secondary-button" type="button" @click="reloadWorkspace">刷新</button>
        <button class="primary-button" type="button" :disabled="!canEdit" @click="beginCreate">新增用药</button>
      </div>
    </header>

    <div v-if="errorMessage" class="banner error-banner">{{ errorMessage }}</div>

    <section class="status-strip">
      <article class="status-card">
        <span>当前用药</span>
        <strong>{{ activeMedicationCount }}</strong>
      </article>
      <article class="status-card">
        <span>待复核</span>
        <strong>{{ pendingReviewCount }}</strong>
      </article>
      <article class="status-card" :class="{ 'status-good': baselineHint }">
        <span>基础治疗覆盖</span>
        <strong>{{ baselineHint ? '已覆盖' : '未覆盖' }}</strong>
      </article>
      <article class="status-card" :class="{ 'status-bad': duplicateHint }">
        <span>重复用药</span>
        <strong>{{ duplicateHint ? '已提示' : '未发现' }}</strong>
      </article>
      <article class="status-card" :class="{ 'status-warn': pharmacistReviewHint }">
        <span>复核需求</span>
        <strong>{{ pharmacistReviewHint ? '需要复核' : '暂不需要' }}</strong>
      </article>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div>
          <h4>当前用药列表</h4>
          <p>展示药品、剂量、频次、状态和药师复核状态。</p>
        </div>
        <span class="meta">{{ medications.length }} 条记录</span>
      </div>

      <div v-if="loading" class="empty-state">正在加载当前用药...</div>
      <div v-else-if="!canView" class="empty-state">当前角色没有查看当前用药的权限。</div>
      <div v-else-if="!medications.length" class="empty-state">当前没有用药记录。</div>
      <div v-else class="medication-table">
        <table>
          <thead>
            <tr>
              <th>药品</th>
              <th>剂量 / 频次</th>
              <th>区间</th>
              <th>状态</th>
              <th>复核</th>
              <th>开立人</th>
              <th>备注</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in medications" :key="item.medication_id">
              <td>
                <strong>{{ item.drug_name_snapshot }}</strong>
                <p class="meta">ID: {{ item.drug_id }}</p>
              </td>
              <td>
                <div>{{ item.dosage }}</div>
                <div class="meta">{{ item.frequency }} · {{ item.route }}</div>
              </td>
              <td>
                <div>{{ formatDate(item.start_date) }}</div>
                <div class="meta">至 {{ formatDate(item.end_date) }}</div>
              </td>
              <td><span class="badge" :class="statusClass(item.status)">{{ statusText(item.status) }}</span></td>
              <td><span class="badge" :class="reviewBadgeClass(item.review_status)">{{ reviewBadgeText(item.review_status) }}</span></td>
              <td>{{ item.prescribed_by || '--' }}</td>
              <td class="note-cell">{{ item.note || '--' }}</td>
              <td>
                <button class="secondary-button" type="button" :disabled="!canEdit" @click="beginEdit(item)">编辑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div>
          <h4>{{ editingMedicationId ? '编辑当前用药' : '新增当前用药' }}</h4>
          <p>药品目录来自后端目录，保存前会检查当前角色是否可操作管制药。</p>
        </div>
        <span v-if="selectedDrug" class="meta">
          当前药品：{{ selectedDrug.generic_name }}{{ selectedDrug.brand_name ? ` / ${selectedDrug.brand_name}` : '' }}
          <span v-if="selectedDrug.is_controlled"> · 管制药</span>
        </span>
      </div>

      <div v-if="controlledDrugBlocked" class="banner warn-banner">当前选择的是管制药，但当前角色没有管制药权限。</div>

      <div class="form-grid">
        <label class="field">
          <span>药品目录</span>
          <select v-model="form.drug_id" :disabled="saving || !canEdit">
            <option value="">请选择药品</option>
            <option v-for="drug in availableDrugs" :key="drug.drug_id" :value="drug.drug_id">
              {{ drug.generic_name }}{{ drug.brand_name ? ` / ${drug.brand_name}` : '' }}
            </option>
          </select>
        </label>

        <label class="field">
          <span>药名快照</span>
          <input :value="form.drug_name_snapshot" type="text" readonly />
        </label>

        <label class="field">
          <span>剂量</span>
          <input v-model="form.dosage" type="text" :disabled="saving || !canEdit" placeholder="例如 500 mg" />
        </label>

        <label class="field">
          <span>频次</span>
          <input v-model="form.frequency" type="text" :disabled="saving || !canEdit" placeholder="例如 bid" />
        </label>

        <label class="field">
          <span>给药途径</span>
          <input v-model="form.route" type="text" :disabled="saving || !canEdit" placeholder="例如 po" />
        </label>

        <label class="field">
          <span>开始日期</span>
          <input v-model="form.start_date" type="date" :disabled="saving || !canEdit" />
        </label>

        <label class="field">
          <span>结束日期</span>
          <input v-model="form.end_date" type="date" :disabled="saving || !canEdit" />
        </label>

        <label class="field">
          <span>状态</span>
          <select v-model="form.status" :disabled="saving || !canEdit">
            <option value="active">使用中</option>
            <option value="paused">暂停</option>
            <option value="stopped">停用</option>
          </select>
        </label>

        <label class="field">
          <span>药师复核状态</span>
          <select v-model="form.review_status" :disabled="saving || !canReview">
            <option value="pending">待复核</option>
            <option value="approved">已通过</option>
            <option value="rejected">已拒绝</option>
            <option value="not_required">无需复核</option>
          </select>
        </label>

        <label class="field full">
          <span>备注</span>
          <textarea v-model="form.note" rows="3" :disabled="saving || !canEdit" placeholder="补充当前用药说明"></textarea>
        </label>
      </div>

      <div class="actions">
        <button class="secondary-button" type="button" :disabled="saving" @click="beginCreate">清空新建</button>
        <button class="primary-button" type="button" :disabled="saving || !canEdit || controlledDrugBlocked || !form.drug_id" @click="submitMedication">
          {{ saving ? '保存中...' : editingMedicationId ? '保存修改' : '保存当前用药' }}
        </button>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <div>
          <h4>用药充分性评估</h4>
          <p>基于当前患者、现用药、药品目录和模型建议生成。</p>
        </div>
        <span class="meta">{{ assessment.evaluatedAt.replace('T', ' ').slice(0, 16) }}</span>
      </div>

      <div class="assessment-grid">
        <article class="assessment-card" :class="{ 'status-good': assessment.coversBaselineTherapy }">
          <span>基础治疗覆盖</span>
          <strong>{{ assessment.coversBaselineTherapy ? '已覆盖' : '未覆盖' }}</strong>
        </article>
        <article class="assessment-card" :class="{ 'status-bad': assessment.hasDuplicateMedication }">
          <span>重复用药提示</span>
          <strong>{{ assessment.hasDuplicateMedication ? '存在重复' : '未发现重复' }}</strong>
        </article>
        <article class="assessment-card" :class="{ 'status-bad': assessment.hasContraindicationConflictPlaceholder }">
          <span>禁忌 / 冲突</span>
          <strong>{{ assessment.hasContraindicationConflictPlaceholder ? '需要复核' : '暂无冲突' }}</strong>
        </article>
        <article class="assessment-card" :class="{ 'status-warn': assessment.needsPharmacistReview }">
          <span>药师复核</span>
          <strong>{{ assessment.needsPharmacistReview ? '建议复核' : '暂不需要' }}</strong>
        </article>
      </div>

      <div class="assessment-note">
        <h5>评估说明</h5>
        <ul>
          <li v-for="item in assessment.notes" :key="item">{{ item }}</li>
        </ul>
      </div>

      <div v-if="assessment.suggestSupplementClasses.length" class="assessment-note">
        <h5>建议补充药物线索</h5>
        <ul>
          <li v-for="item in assessment.suggestSupplementClasses" :key="item">{{ item }}</li>
        </ul>
      </div>
    </section>
  </section>
</template>

<style scoped>
.medication-workspace {
  display: grid;
  gap: 14px;
}

.workspace-head,
.panel-head,
.actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.workspace-head h3,
.panel h4,
.assessment-note h5 {
  margin: 0;
}

.workspace-head p,
.panel-head p,
.assessment-note ul,
.meta {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 12px;
}

.header-actions,
.actions {
  display: flex;
  gap: 8px;
}

.banner {
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
}

.error-banner {
  background: #fff1f2;
  border: 1px solid #fecdd3;
  color: #9f1239;
}

.warn-banner {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  color: #92400e;
}

.status-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.status-card,
.assessment-card,
.panel {
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 12px;
  background: #ffffff;
  padding: 12px;
}

.status-card span,
.assessment-card span {
  display: block;
  color: #64748b;
  font-size: 12px;
}

.status-card strong,
.assessment-card strong {
  display: block;
  margin-top: 4px;
  color: #0f172a;
}

.status-good {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.06);
}

.status-warn {
  border-color: rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.06);
}

.status-bad {
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.06);
}

.empty-state {
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  padding: 14px;
  color: #64748b;
  text-align: center;
}

.medication-table {
  overflow-x: auto;
}

.medication-table table {
  width: 100%;
  border-collapse: collapse;
}

.medication-table th,
.medication-table td {
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  vertical-align: top;
}

.medication-table td p,
.note-cell {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 12px;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.badge-good {
  background: rgba(34, 197, 94, 0.12);
  color: #166534;
}

.badge-warn {
  background: rgba(245, 158, 11, 0.12);
  color: #92400e;
}

.badge-bad {
  background: rgba(239, 68, 68, 0.12);
  color: #991b1b;
}

.badge-neutral {
  background: rgba(100, 116, 139, 0.12);
  color: #334155;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.field {
  display: grid;
  gap: 6px;
}

.field span {
  font-size: 12px;
  color: #64748b;
}

.field input,
.field select,
.field textarea {
  width: 100%;
}

.field.full {
  grid-column: 1 / -1;
}

.assessment-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.assessment-note {
  margin-top: 12px;
}

.assessment-note ul {
  padding-left: 18px;
}

@media (max-width: 1100px) {
  .status-strip,
  .assessment-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .workspace-head,
  .panel-head,
  .actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .status-strip,
  .assessment-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
