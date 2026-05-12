<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getPatientMedications, getPatientMedicationAssessment } from '../../services/api'
import type { PatientMedicationRecord, MedicationAdequacyAssessment } from '../../services/types'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const router = useRouter()
const patient = computed(() => workspace.selectedPatient)

const medications = ref<PatientMedicationRecord[]>([])
const assessment = ref<MedicationAdequacyAssessment | null>(null)
const loading = ref(false)
const loadingAssessment = ref(false)
const error = ref('')

const activeMedications = computed(() => medications.value.filter((m) => m.status === 'active'))
const inactiveMedications = computed(() => medications.value.filter((m) => m.status !== 'active'))
const pendingReviewCount = computed(() => medications.value.filter((m) => m.review_status === 'pending').length)

async function loadMedications() {
  if (!patient.value) return
  loading.value = true
  error.value = ''
  try {
    medications.value = await getPatientMedications(patient.value.patientId)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '用药数据加载失败。'
  } finally {
    loading.value = false
  }
}

async function loadAssessment() {
  if (!patient.value) return
  loadingAssessment.value = true
  try {
    const advice = workspace.predictionResult?.advice ?? patient.value?.careAdvice ?? []
    assessment.value = await getPatientMedicationAssessment(patient.value.patientId, { modelAdvice: advice })
  } catch {
    assessment.value = null
  } finally {
    loadingAssessment.value = false
  }
}

function reviewStatusLabel(status: string) {
  if (status === 'approved') return '已审核'
  if (status === 'rejected') return '已驳回'
  if (status === 'pending') return '待审核'
  return '无需审核'
}

function reviewStatusClass(status: string) {
  if (status === 'approved') return 'status-approved'
  if (status === 'rejected') return 'status-rejected'
  if (status === 'pending') return 'status-pending'
  return 'status-muted'
}

function goPharmacy() {
  void router.push({ name: 'pharmacy-medication-review' })
}

watch(
  () => patient.value?.patientId,
  () => {
    medications.value = []
    assessment.value = null
    void loadMedications().then(() => loadAssessment())
  },
  { immediate: true }
)
</script>

<template>
  <section v-if="patient" class="medications-page">
    <div class="section-header">
      <div>
        <p class="eyebrow">当前用药</p>
        <h2>患者用药管理</h2>
      </div>
      <button class="secondary-button" type="button" @click="goPharmacy">药事复核入口</button>
    </div>

    <div class="metric-row">
      <article class="clinical-card metric-card">
        <span>活跃用药</span>
        <strong>{{ activeMedications.length }}</strong>
      </article>
      <article class="clinical-card metric-card">
        <span>待药师审核</span>
        <strong :class="{ 'tone-warning': pendingReviewCount > 0 }">{{ pendingReviewCount }}</strong>
      </article>
      <article class="clinical-card metric-card">
        <span>主诊断</span>
        <strong class="small-text">{{ patient.primaryDisease }}</strong>
      </article>
      <article class="clinical-card metric-card">
        <span>药事状态</span>
        <strong :class="pendingReviewCount > 0 ? 'tone-warning' : 'tone-ok'">{{ pendingReviewCount > 0 ? '待复核' : '已通过' }}</strong>
      </article>
    </div>

    <p v-if="loading" class="muted-line">正在加载用药数据...</p>
    <p v-if="error" class="error-line">{{ error }}</p>

    <article v-if="activeMedications.length" class="clinical-card med-table-card">
      <p class="eyebrow">活跃用药列表</p>
      <h2>当前在用药物</h2>
      <table class="med-table">
        <thead>
          <tr>
            <th>药品</th>
            <th>剂量</th>
            <th>频次</th>
            <th>给药途径</th>
            <th>起始日期</th>
            <th>审核状态</th>
            <th>备注</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="med in activeMedications" :key="med.medication_id">
            <td><strong>{{ med.drug_name_snapshot }}</strong></td>
            <td>{{ med.dosage }}</td>
            <td>{{ med.frequency }}</td>
            <td>{{ med.route }}</td>
            <td>{{ med.start_date }}</td>
            <td><span class="status-pill" :class="reviewStatusClass(med.review_status)">{{ reviewStatusLabel(med.review_status) }}</span></td>
            <td>{{ med.note || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </article>
    <article v-else-if="!loading" class="clinical-card empty-card">
      <p>当前无活跃用药记录。</p>
    </article>

    <article v-if="inactiveMedications.length" class="clinical-card med-table-card">
      <p class="eyebrow">历史用药</p>
      <h2>已停用/暂停药物</h2>
      <table class="med-table">
        <thead>
          <tr>
            <th>药品</th>
            <th>剂量</th>
            <th>状态</th>
            <th>起止日期</th>
            <th>审核状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="med in inactiveMedications" :key="med.medication_id">
            <td><strong>{{ med.drug_name_snapshot }}</strong></td>
            <td>{{ med.dosage }}</td>
            <td>{{ med.status === 'paused' ? '暂停' : '已停用' }}</td>
            <td>{{ med.start_date }} ~ {{ med.end_date || '至今' }}</td>
            <td><span class="status-pill" :class="reviewStatusClass(med.review_status)">{{ reviewStatusLabel(med.review_status) }}</span></td>
          </tr>
        </tbody>
      </table>
    </article>

    <article v-if="assessment" class="clinical-card assessment-card">
      <p class="eyebrow">用药充分性评估</p>
      <h2>充分性与安全性</h2>
      <dl class="assessment-grid">
        <div>
          <dt>基线治疗覆盖</dt>
          <dd :class="assessment.coversBaselineTherapy ? 'tone-ok' : 'tone-warning'">
            {{ assessment.coversBaselineTherapy ? '已覆盖' : '未覆盖' }}
          </dd>
        </div>
        <div>
          <dt>重复用药</dt>
          <dd :class="!assessment.hasDuplicateMedication ? 'tone-ok' : 'tone-warning'">
            {{ assessment.hasDuplicateMedication ? '存在重复' : '无重复' }}
          </dd>
        </div>
        <div>
          <dt>禁忌冲突</dt>
          <dd :class="!assessment.hasContraindicationConflictPlaceholder ? 'tone-ok' : 'tone-warning'">
            {{ assessment.hasContraindicationConflictPlaceholder ? '存在冲突' : '无冲突' }}
          </dd>
        </div>
        <div>
          <dt>与模型建议一致</dt>
          <dd :class="assessment.alignsWithModelAdvice ? 'tone-ok' : 'tone-warning'">
            {{ assessment.alignsWithModelAdvice ? '一致' : '不一致' }}
          </dd>
        </div>
        <div>
          <dt>需药师审核</dt>
          <dd :class="!assessment.needsPharmacistReview ? 'tone-ok' : 'tone-warning'">
            {{ assessment.needsPharmacistReview ? '需要' : '不需要' }}
          </dd>
        </div>
      </dl>
      <div v-if="assessment.suggestSupplementClasses.length" class="supplement-section">
        <p class="eyebrow">建议补充用药类别</p>
        <ul>
          <li v-for="cls in assessment.suggestSupplementClasses" :key="cls">{{ cls }}</li>
        </ul>
      </div>
      <div v-if="assessment.notes.length" class="notes-section">
        <p class="eyebrow">评估说明</p>
        <p v-for="note in assessment.notes" :key="note" class="note-line">{{ note }}</p>
      </div>
    </article>
    <article v-else-if="!loadingAssessment && !error" class="clinical-card empty-card">
      <p>用药充分性评估数据暂未加载。</p>
    </article>
  </section>
</template>

<style scoped>
.medications-page {
  display: grid;
  gap: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.metric-card {
  display: grid;
  gap: 6px;
}

.metric-card span {
  color: #526772;
  font-size: 12px;
  font-weight: 800;
}

.metric-card strong {
  color: #0f6f99;
  font-size: 24px;
  font-weight: 900;
}

.metric-card strong.small-text {
  font-size: 16px;
}

.tone-ok {
  color: #007f65 !important;
}

.tone-warning {
  color: #9a5b00 !important;
}

.med-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #d5e6ef;
}

.med-table th,
.med-table td {
  padding: 10px;
  border-bottom: 1px solid #d5e6ef;
  text-align: left;
}

.med-table th {
  background: #edf7fc;
  color: #275d70;
  font-weight: 800;
}

.status-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 800;
}

.status-approved {
  background: #e6f9f0;
  color: #007f65;
}

.status-rejected {
  background: #fff5f5;
  color: #b42318;
}

.status-pending {
  background: #fff7ed;
  color: #9a5b00;
}

.status-muted {
  background: #f0f5f9;
  color: #526772;
}

.assessment-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin: 0;
}

.assessment-grid div {
  border: 1px solid #d5e6ef;
  background: #f7fbfd;
  padding: 10px;
  text-align: center;
}

.assessment-grid dt {
  color: #527384;
  font-size: 12px;
  font-weight: 800;
}

.assessment-grid dd {
  margin: 4px 0 0;
  font-weight: 900;
  font-size: 14px;
}

.supplement-section ul {
  display: grid;
  gap: 6px;
  padding-left: 20px;
  margin: 0;
}

.note-line {
  margin: 4px 0;
  padding: 8px;
  background: #f7fbfd;
  border: 1px solid #d5e6ef;
  color: #526772;
  font-size: 13px;
  line-height: 1.6;
}

.error-line {
  color: #b42318;
  font-weight: 700;
}

.muted-line {
  color: #526772;
}

@media (max-width: 900px) {
  .metric-row,
  .assessment-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
