<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import {
  addCurrentMedication,
  evaluateMedicationAdequacy,
  getCurrentMedications,
} from '../../services/medicationAssessmentAdapter'
import type {
  CurrentMedicationInput,
  CurrentMedicationItem,
  MedicationAdequacyAssessment,
  PatientCase,
} from '../../services/types'

const props = defineProps<{
  patient: PatientCase
  modelAdvice: string[]
}>()

const medications = ref<CurrentMedicationItem[]>([])
const assessment = ref<MedicationAdequacyAssessment | null>(null)
const saving = ref(false)
const localError = ref('')

const form = reactive<CurrentMedicationInput>({
  drugName: '',
  genericName: '',
  dosage: '',
  frequency: '',
  route: 'po',
  startedAt: new Date().toISOString().slice(0, 10),
  expectedEndAt: '',
  indication: '',
})

const hasMedications = computed(() => medications.value.length > 0)

function resetForm() {
  form.drugName = ''
  form.genericName = ''
  form.dosage = ''
  form.frequency = ''
  form.route = 'po'
  form.startedAt = new Date().toISOString().slice(0, 10)
  form.expectedEndAt = ''
  form.indication = ''
}

function refreshWorkspace() {
  medications.value = getCurrentMedications(props.patient)
  assessment.value = evaluateMedicationAdequacy(props.patient, medications.value, props.modelAdvice)
}

function yesNo(value: boolean): string {
  return value ? '是' : '否'
}

function toneClass(value: boolean, reverse = false): string {
  const ok = reverse ? !value : value
  return ok ? 'tone-ok' : 'tone-alert'
}

async function submitMedication() {
  if (!props.patient.patientId) return
  if (!form.drugName.trim() || !form.genericName.trim() || !form.dosage.trim()) {
    localError.value = '请至少填写药品名称、通用名、剂量。'
    return
  }

  localError.value = ''
  saving.value = true
  try {
    medications.value = addCurrentMedication(props.patient.patientId, {
      drugName: form.drugName.trim(),
      genericName: form.genericName.trim(),
      dosage: form.dosage.trim(),
      frequency: form.frequency.trim() || '--',
      route: form.route.trim() || '--',
      startedAt: form.startedAt,
      expectedEndAt: form.expectedEndAt || '--',
      indication: form.indication.trim() || '--',
    })
    assessment.value = evaluateMedicationAdequacy(props.patient, medications.value, props.modelAdvice)
    resetForm()
  } finally {
    saving.value = false
  }
}

watch(
  () => [props.patient.patientId, props.patient.primaryDisease, props.modelAdvice.join('|')],
  () => {
    refreshWorkspace()
  },
  { immediate: true }
)
</script>

<template>
  <section class="card medication-workspace">
    <header class="workspace-head">
      <div>
        <h3>当前用药与用药充分性评估</h3>
        <p>用于医生核对模型建议后的临床用药覆盖情况</p>
      </div>
      <button class="secondary-button" @click="refreshWorkspace">刷新评估</button>
    </header>

    <article class="medication-block">
      <h4>当前用药</h4>
      <div v-if="!hasMedications" class="empty-state">暂无当前用药记录，请补录后进行评估。</div>
      <div v-else class="med-table">
        <header>
          <span>药品名称</span>
          <span>通用名</span>
          <span>剂量</span>
          <span>频率</span>
          <span>给药方式</span>
          <span>开始时间</span>
          <span>预计结束时间</span>
          <span>适应症</span>
        </header>
        <article v-for="item in medications" :key="item.medicationId">
          <span>{{ item.drugName }}</span>
          <span>{{ item.genericName }}</span>
          <span>{{ item.dosage }}</span>
          <span>{{ item.frequency }}</span>
          <span>{{ item.route }}</span>
          <span>{{ item.startedAt }}</span>
          <span>{{ item.expectedEndAt }}</span>
          <span>{{ item.indication }}</span>
        </article>
      </div>
    </article>

    <article class="add-block">
      <h4>补录当前用药</h4>
      <p v-if="localError" class="error-tip">{{ localError }}</p>
      <div class="form-grid">
        <label><span>药品名称</span><input v-model="form.drugName" type="text" /></label>
        <label><span>通用名</span><input v-model="form.genericName" type="text" /></label>
        <label><span>剂量</span><input v-model="form.dosage" type="text" placeholder="如 500 mg" /></label>
        <label><span>频率</span><input v-model="form.frequency" type="text" placeholder="如 bid" /></label>
        <label><span>给药方式</span><input v-model="form.route" type="text" placeholder="如 po" /></label>
        <label><span>开始时间</span><input v-model="form.startedAt" type="date" /></label>
        <label><span>预计结束时间</span><input v-model="form.expectedEndAt" type="date" /></label>
        <label class="full"><span>适应症</span><input v-model="form.indication" type="text" /></label>
      </div>
      <div class="actions">
        <button class="primary-button" :disabled="saving" @click="submitMedication">
          {{ saving ? '保存中...' : '新增当前用药' }}
        </button>
      </div>
    </article>

    <article class="assessment-block" v-if="assessment">
      <h4>用药充分性评估</h4>
      <div class="assessment-grid">
        <div class="assessment-item" :class="toneClass(assessment.coversBaselineTherapy)">
          <span>是否覆盖基础治疗</span>
          <strong>{{ yesNo(assessment.coversBaselineTherapy) }}</strong>
        </div>
        <div class="assessment-item" :class="toneClass(assessment.hasDuplicateMedication, true)">
          <span>是否存在重复用药</span>
          <strong>{{ yesNo(assessment.hasDuplicateMedication) }}</strong>
        </div>
        <div class="assessment-item" :class="toneClass(assessment.hasContraindicationConflictPlaceholder, true)">
          <span>是否存在禁忌/冲突占位</span>
          <strong>{{ yesNo(assessment.hasContraindicationConflictPlaceholder) }}</strong>
        </div>
        <div class="assessment-item" :class="toneClass(assessment.alignsWithModelAdvice)">
          <span>是否与模型建议一致</span>
          <strong>{{ yesNo(assessment.alignsWithModelAdvice) }}</strong>
        </div>
      </div>

      <div class="assessment-sub" v-if="assessment.suggestSupplementClasses.length">
        <h5>建议补充药物类别</h5>
        <ul>
          <li v-for="item in assessment.suggestSupplementClasses" :key="item">{{ item }}</li>
        </ul>
      </div>

      <div class="assessment-sub">
        <h5>评估说明</h5>
        <ul>
          <li v-for="item in assessment.notes" :key="item">{{ item }}</li>
        </ul>
        <p class="meta">
          评估时间：{{ assessment.evaluatedAt.replace('T', ' ').slice(0, 16) }}
          / 评估人：{{ assessment.evaluator }}
        </p>
      </div>
    </article>
  </section>
</template>

<style scoped>
.medication-workspace {
  padding: 14px;
  display: grid;
  gap: 14px;
}

.workspace-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.workspace-head h3 {
  margin: 0;
  color: #10263c;
  font-size: 17px;
}

.workspace-head p {
  margin: 4px 0 0;
  color: #617385;
  font-size: 12px;
}

.medication-block,
.add-block,
.assessment-block {
  border: 1px solid #cfd9e5;
  border-radius: 10px;
  background: #fbfdff;
  padding: 10px;
  display: grid;
  gap: 10px;
}

.medication-block h4,
.add-block h4,
.assessment-block h4,
.assessment-sub h5 {
  margin: 0;
  color: #1b3856;
}

.empty-state {
  border: 1px dashed #b8c7d8;
  border-radius: 8px;
  padding: 10px;
  color: #617385;
  font-size: 12px;
  text-align: center;
}

.med-table {
  border: 1px solid #d8e2ee;
  border-radius: 8px;
  overflow: hidden;
}

.med-table header,
.med-table article {
  display: grid;
  grid-template-columns: 1.1fr 1.1fr .7fr .7fr .7fr .8fr .9fr 1.3fr;
  gap: 8px;
  padding: 8px;
  font-size: 12px;
}

.med-table header {
  background: #eef4fa;
  color: #46627f;
  font-weight: 600;
}

.med-table article {
  border-top: 1px solid #e5edf5;
  color: #243f5c;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.form-grid label {
  display: grid;
  gap: 4px;
}

.form-grid label.full {
  grid-column: span 2;
}

.form-grid span {
  font-size: 12px;
  color: #5f7894;
}

.form-grid input {
  border: 1px solid #c7d5e5;
  border-radius: 6px;
  padding: 6px 8px;
  background: #fff;
  font-size: 12px;
}

.actions {
  display: flex;
  justify-content: flex-end;
}

.error-tip {
  margin: 0;
  color: #a4383f;
  background: #fff0f2;
  border: 1px solid #efc2c5;
  border-radius: 8px;
  padding: 8px;
  font-size: 12px;
}

.assessment-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.assessment-item {
  border: 1px solid;
  border-radius: 8px;
  padding: 8px;
  display: grid;
  gap: 4px;
}

.assessment-item span {
  font-size: 12px;
}

.assessment-item strong {
  font-size: 16px;
}

.tone-ok {
  background: #eaf8f0;
  border-color: #bde7d1;
  color: #1d7b5c;
}

.tone-alert {
  background: #fff4e9;
  border-color: #efdbb2;
  color: #9b6518;
}

.assessment-sub ul {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 5px;
  color: #314f6d;
  font-size: 12px;
}

.meta {
  margin: 8px 0 0;
  font-size: 12px;
  color: #617385;
}

@media (max-width: 1360px) {
  .med-table header,
  .med-table article,
  .form-grid,
  .assessment-grid {
    grid-template-columns: 1fr;
  }

  .form-grid label.full {
    grid-column: span 1;
  }
}
</style>
