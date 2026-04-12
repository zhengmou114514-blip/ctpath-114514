<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type {
  ArchiveImportWorkflowMode,
  CrossSystemSourceSystem,
  ImportPreviewPatient,
  MpiCandidatePatient,
  MpiSearchCriteria,
  OnsiteArchiveRegisterForm,
  PatientSummary,
} from '../../services/types'

const props = defineProps<{
  allPatients: PatientSummary[]
  importing: boolean
  resultText: string
}>()

const emit = defineEmits<{
  (e: 'submit-import', rows: ImportPreviewPatient[]): void
  (e: 'back'): void
}>()

const activeMode = ref<ArchiveImportWorkflowMode>('cross_system')
const pageMessage = ref('')
const pageError = ref('')

const sourceOptions: Array<{ value: CrossSystemSourceSystem; label: string }> = [
  { value: 'his', label: '院内HIS' },
  { value: 'emr', label: '电子病历' },
  { value: 'regional_platform', label: '区域平台' },
  { value: 'other', label: '其他' },
]

const mpiSearch = reactive<MpiSearchCriteria>({
  sourceSystem: 'his',
  name: '',
  birthDate: '',
  phone: '',
  idLast4: '',
  medicalRecordNumber: '',
  visitCardNumber: '',
})

const searchRunning = ref(false)
const mpiCandidates = ref<MpiCandidatePatient[]>([])
const selectedCandidateId = ref('')
const identityVerified = ref(false)
const mergeTargetPatientId = ref('')

const onsiteForm = reactive<OnsiteArchiveRegisterForm>({
  name: '',
  gender: '男',
  birthDate: '',
  phone: '',
  idType: 'id_card',
  idNumber: '',
  address: '',
  emergencyContactName: '',
  emergencyContactPhone: '',
  medicalRecordNumber: '',
  visitCardNumber: '',
  insuranceType: '',
  primaryDoctor: '',
  caseManager: '',
  consentStatus: 'signed',
})

const attachmentPlaceholders = reactive({
  patientPhoto: '',
  idCardPhoto: '',
  insuranceCardPhoto: '',
  referralScan: '',
})

const governanceMerge = reactive({
  sourcePatientId: '',
  targetPatientId: '',
})

const governanceFix = reactive({
  patientId: '',
  phone: '',
  emergencyContactPhone: '',
  identityNumber: '',
})

const selectedCandidate = computed(() =>
  mpiCandidates.value.find((item) => item.candidateId === selectedCandidateId.value) ?? null
)

const mergeTargets = computed(() =>
  props.allPatients.filter((item) => !selectedCandidate.value || item.patientId !== selectedCandidate.value.sourceRecordId)
)

const duplicateGroups = computed(() => {
  const buckets = new Map<string, PatientSummary[]>()
  props.allPatients.forEach((item) => {
    const key = `${item.name}|${item.phone || 'EMPTY_PHONE'}`
    if (!buckets.has(key)) buckets.set(key, [])
    buckets.get(key)?.push(item)
  })
  return [...buckets.values()].filter((group) => group.length > 1)
})

const missingFieldRows = computed(() =>
  props.allPatients
    .map((item) => {
      const missing: string[] = []
      if (!item.phone) missing.push('手机号')
      if (!item.identityMasked) missing.push('证件号')
      if (!item.emergencyContactPhone) missing.push('紧急联系人电话')
      if (!item.medicalRecordNumber) missing.push('病案号')
      return { patient: item, missing }
    })
    .filter((row) => row.missing.length > 0)
)

const conflictRows = computed(() => {
  const buckets = new Map<string, PatientSummary[]>()
  props.allPatients.forEach((item) => {
    if (!item.medicalRecordNumber) return
    const key = item.medicalRecordNumber
    if (!buckets.has(key)) buckets.set(key, [])
    buckets.get(key)?.push(item)
  })
  return [...buckets.entries()]
    .filter(([, group]) => group.length > 1)
    .map(([mrn, group]) => ({ medicalRecordNumber: mrn, patients: group }))
})

function clearStateMessage() {
  pageError.value = ''
  pageMessage.value = ''
}

function buildImportPatient(partial: Partial<ImportPreviewPatient>, rowKey: string): ImportPreviewPatient {
  const patientId = partial.patientId || `PID${Date.now().toString().slice(-8)}`
  return {
    rowKey,
    sourceName: partial.sourceName || 'archive-adapter',
    patientId,
    name: partial.name || '未命名患者',
    age: partial.age ?? 0,
    gender: partial.gender || 'Unknown',
    avatarUrl: partial.avatarUrl || '',
    phone: partial.phone || '',
    emergencyContactName: partial.emergencyContactName || '',
    emergencyContactRelation: partial.emergencyContactRelation || '',
    emergencyContactPhone: partial.emergencyContactPhone || '',
    identityMasked: partial.identityMasked || '',
    insuranceType: partial.insuranceType || 'Urban Employee',
    department: partial.department || 'Chronic Care Clinic',
    primaryDoctor: partial.primaryDoctor || 'Doctor',
    caseManager: partial.caseManager || 'Nurse',
    medicalRecordNumber: partial.medicalRecordNumber || patientId,
    archiveSource: partial.archiveSource || 'outpatient',
    archiveStatus: partial.archiveStatus || 'active',
    consentStatus: partial.consentStatus || 'signed',
    allergyHistory: partial.allergyHistory || '',
    familyHistory: partial.familyHistory || '',
    primaryDisease: partial.primaryDisease || 'Unknown',
    currentStage: partial.currentStage || 'Early',
    riskLevel: partial.riskLevel || 'Medium Risk',
    lastVisit: partial.lastVisit || new Date().toISOString().slice(0, 10),
    summary: partial.summary || '',
    dataSupport: partial.dataSupport || 'medium',
  }
}

async function searchCrossSystemCandidates() {
  clearStateMessage()
  searchRunning.value = true
  selectedCandidateId.value = ''
  identityVerified.value = false
  mergeTargetPatientId.value = ''

  try {
    const hasAnyCondition = Boolean(
      mpiSearch.name ||
      mpiSearch.birthDate ||
      mpiSearch.phone ||
      mpiSearch.idLast4 ||
      mpiSearch.medicalRecordNumber ||
      mpiSearch.visitCardNumber
    )
    if (!hasAnyCondition) {
      pageError.value = '请至少输入一个检索条件后再查询。'
      mpiCandidates.value = []
      return
    }

    // TODO(api): Replace with backend MPI retrieval service.
    const candidates = props.allPatients
      .filter((item) => {
        if (mpiSearch.name && !item.name.includes(mpiSearch.name)) return false
        if (mpiSearch.phone && !item.phone.includes(mpiSearch.phone)) return false
        if (mpiSearch.medicalRecordNumber && !item.medicalRecordNumber.includes(mpiSearch.medicalRecordNumber)) return false
        if (mpiSearch.idLast4 && !item.identityMasked.includes(mpiSearch.idLast4)) return false
        return true
      })
      .slice(0, 12)
      .map<MpiCandidatePatient>((item, idx) => ({
        candidateId: `cand-${item.patientId}-${idx}`,
        sourceSystem: mpiSearch.sourceSystem,
        sourceRecordId: `${mpiSearch.sourceSystem.toUpperCase()}-${item.patientId}`,
        name: item.name,
        gender: item.gender,
        birthDate: '',
        phone: item.phone,
        idLast4: item.identityMasked.slice(-4),
        medicalRecordNumber: item.medicalRecordNumber,
        visitCardNumber: '',
        primaryDisease: item.primaryDisease,
        lastVisit: item.lastVisit,
        confidence: 0.78,
        summary: item.summary || '来自跨系统调阅候选记录。',
      }))

    mpiCandidates.value = candidates
    if (!candidates.length) pageMessage.value = '未检索到候选患者，请调整检索条件。'
  } finally {
    searchRunning.value = false
  }
}

function createArchiveFromCandidate() {
  clearStateMessage()
  if (!selectedCandidate.value) {
    pageError.value = '请先选择候选患者。'
    return
  }
  if (!identityVerified.value) {
    pageError.value = '请先完成身份核对。'
    return
  }

  const candidate = selectedCandidate.value
  const row = buildImportPatient(
    {
      patientId: `${candidate.sourceSystem.toUpperCase()}-${Date.now().toString().slice(-6)}`,
      name: candidate.name,
      gender: candidate.gender,
      phone: candidate.phone,
      identityMasked: candidate.idLast4 ? `************${candidate.idLast4}` : '',
      primaryDisease: candidate.primaryDisease,
      medicalRecordNumber: candidate.medicalRecordNumber,
      summary: `跨系统调阅建档：${candidate.summary}`,
      sourceName: `cross-system:${candidate.sourceSystem}`,
      archiveSource: candidate.sourceSystem === 'regional_platform' ? 'community_referral' : 'outpatient',
    },
    `cross-create-${candidate.candidateId}`
  )
  emit('submit-import', [row])
}

function mergeCandidateToExistingArchive() {
  clearStateMessage()
  if (!selectedCandidate.value) {
    pageError.value = '请先选择候选患者。'
    return
  }
  if (!identityVerified.value) {
    pageError.value = '请先完成身份核对。'
    return
  }
  if (!mergeTargetPatientId.value) {
    pageError.value = '请选择合并目标档案。'
    return
  }

  const target = props.allPatients.find((item) => item.patientId === mergeTargetPatientId.value)
  const candidate = selectedCandidate.value
  if (!target) {
    pageError.value = '未找到合并目标档案。'
    return
  }

  // TODO(api): Replace with dedicated MPI merge endpoint.
  const row = buildImportPatient(
    {
      ...target,
      rowKey: '',
      sourceName: `merge:${candidate.sourceSystem}`,
      summary: [target.summary, `合并调阅记录(${candidate.sourceRecordId})`].filter(Boolean).join('；'),
      phone: target.phone || candidate.phone,
      medicalRecordNumber: target.medicalRecordNumber || candidate.medicalRecordNumber,
    },
    `cross-merge-${candidate.candidateId}-${target.patientId}`
  )
  emit('submit-import', [row])
}

function submitOnsiteRegister() {
  clearStateMessage()
  const requiredChecks: Array<[boolean, string]> = [
    [Boolean(onsiteForm.name.trim()), '姓名'],
    [Boolean(onsiteForm.gender.trim()), '性别'],
    [Boolean(onsiteForm.birthDate), '出生日期'],
    [Boolean(onsiteForm.phone.trim()), '手机号'],
    [Boolean(onsiteForm.idType), '证件类型'],
    [Boolean(onsiteForm.idNumber.trim()), '证件号'],
    [Boolean(onsiteForm.address.trim()), '地址'],
    [Boolean(onsiteForm.emergencyContactName.trim()), '紧急联系人'],
    [Boolean(onsiteForm.medicalRecordNumber.trim() || onsiteForm.visitCardNumber.trim()), '病案号/门诊号'],
  ]
  const missing = requiredChecks.filter((item) => !item[0]).map((item) => item[1])
  if (missing.length) {
    pageError.value = `请完善必填信息：${missing.join('、')}`
    return
  }

  const row = buildImportPatient(
    {
      patientId: onsiteForm.medicalRecordNumber || onsiteForm.visitCardNumber,
      name: onsiteForm.name,
      gender: onsiteForm.gender,
      phone: onsiteForm.phone,
      identityMasked: onsiteForm.idNumber,
      emergencyContactName: onsiteForm.emergencyContactName,
      emergencyContactPhone: onsiteForm.emergencyContactPhone,
      emergencyContactRelation: '家属',
      insuranceType: onsiteForm.insuranceType || 'Urban Employee',
      primaryDoctor: onsiteForm.primaryDoctor || 'Doctor',
      caseManager: onsiteForm.caseManager || 'Nurse',
      consentStatus: onsiteForm.consentStatus || 'signed',
      medicalRecordNumber: onsiteForm.medicalRecordNumber || onsiteForm.visitCardNumber,
      archiveSource: 'outpatient',
      summary: `门诊现场建档；地址:${onsiteForm.address}；附件占位(照片/证件/转诊单)已登记。`,
      sourceName: 'onsite-register',
    },
    `onsite-${Date.now()}`
  )
  emit('submit-import', [row])
}

function pickGovernanceFix(patient: PatientSummary) {
  governanceFix.patientId = patient.patientId
  governanceFix.phone = patient.phone
  governanceFix.emergencyContactPhone = patient.emergencyContactPhone
  governanceFix.identityNumber = patient.identityMasked
}

function submitGovernanceFix() {
  clearStateMessage()
  if (!governanceFix.patientId) {
    pageError.value = '请先选择需要补齐字段的档案。'
    return
  }
  const target = props.allPatients.find((item) => item.patientId === governanceFix.patientId)
  if (!target) {
    pageError.value = '未找到需要补齐的档案。'
    return
  }

  // TODO(api): Replace with archive data quality patch endpoint.
  const row = buildImportPatient(
    {
      ...target,
      rowKey: '',
      sourceName: 'governance-fill',
      phone: governanceFix.phone || target.phone,
      emergencyContactPhone: governanceFix.emergencyContactPhone || target.emergencyContactPhone,
      identityMasked: governanceFix.identityNumber || target.identityMasked,
      summary: [target.summary, '存量档案治理：字段补齐'].filter(Boolean).join('；'),
    },
    `governance-fill-${target.patientId}`
  )
  emit('submit-import', [row])
}

function submitGovernanceMerge() {
  clearStateMessage()
  if (!governanceMerge.sourcePatientId || !governanceMerge.targetPatientId) {
    pageError.value = '请选择冲突档案的来源与目标。'
    return
  }
  if (governanceMerge.sourcePatientId === governanceMerge.targetPatientId) {
    pageError.value = '来源档案与目标档案不能相同。'
    return
  }
  const source = props.allPatients.find((item) => item.patientId === governanceMerge.sourcePatientId)
  const target = props.allPatients.find((item) => item.patientId === governanceMerge.targetPatientId)
  if (!source || !target) {
    pageError.value = '未找到冲突档案。'
    return
  }

  // TODO(api): Replace with MPI conflict merge endpoint.
  const row = buildImportPatient(
    {
      ...target,
      rowKey: '',
      sourceName: 'governance-merge',
      summary: [target.summary, `冲突合并来源:${source.patientId}`].filter(Boolean).join('；'),
      phone: target.phone || source.phone,
      emergencyContactPhone: target.emergencyContactPhone || source.emergencyContactPhone,
      medicalRecordNumber: target.medicalRecordNumber || source.medicalRecordNumber,
    },
    `governance-merge-${source.patientId}-${target.patientId}`
  )
  emit('submit-import', [row])
}
</script>

<template>
  <section class="module-shell archive-page-shell">
    <article class="card archive-page-hero archive-page-hero-practical">
      <div>
        <p class="eyebrow">档案接入工作台</p>
        <h3>医院主索引与建档治理</h3>
        <p class="page-copy">以患者主索引核验为核心，支持跨系统调阅接入、门诊现场建档、存量档案治理三类流程。</p>
      </div>
      <div class="module-hero-actions">
        <button class="secondary-button" @click="emit('back')">返回档案列表</button>
      </div>
    </article>

    <article class="card archive-tab-card">
      <div class="archive-tabbar">
        <button class="secondary-button" :class="{ active: activeMode === 'cross_system' }" @click="activeMode = 'cross_system'">
          跨系统调阅接入
        </button>
        <button class="secondary-button" :class="{ active: activeMode === 'onsite_register' }" @click="activeMode = 'onsite_register'">
          门诊现场建档
        </button>
        <button class="secondary-button" :class="{ active: activeMode === 'governance' }" @click="activeMode = 'governance'">
          存量档案治理
        </button>
      </div>
    </article>

    <p v-if="props.resultText" class="success-banner">{{ props.resultText }}</p>
    <p v-if="pageMessage" class="success-banner">{{ pageMessage }}</p>
    <p v-if="pageError" class="error-banner">{{ pageError }}</p>

    <section v-if="activeMode === 'cross_system'" class="archive-import-grid">
      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">步骤一</p>
            <h3>选择来源系统与主索引检索</h3>
          </div>
        </div>
        <div class="form-grid">
          <label class="field">
            <span>来源系统</span>
            <select v-model="mpiSearch.sourceSystem">
              <option v-for="item in sourceOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
            </select>
          </label>
          <label class="field"><span>姓名</span><input v-model="mpiSearch.name" type="text" /></label>
          <label class="field"><span>出生日期</span><input v-model="mpiSearch.birthDate" type="date" /></label>
          <label class="field"><span>手机号</span><input v-model="mpiSearch.phone" type="text" /></label>
          <label class="field"><span>身份证号后四位</span><input v-model="mpiSearch.idLast4" type="text" maxlength="4" /></label>
          <label class="field"><span>病案号</span><input v-model="mpiSearch.medicalRecordNumber" type="text" /></label>
          <label class="field"><span>就诊卡号</span><input v-model="mpiSearch.visitCardNumber" type="text" /></label>
        </div>
        <div class="form-actions">
          <button class="primary-button" :disabled="searchRunning" @click="searchCrossSystemCandidates">
            {{ searchRunning ? '检索中...' : '检索候选患者' }}
          </button>
        </div>
        <p class="panel-meta">TODO：当前使用前端 adapter/mock 生成候选记录，待接入真实 MPI 检索接口。</p>
      </article>

      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">步骤二</p>
            <h3>候选患者核对与建档决策</h3>
          </div>
        </div>
        <div v-if="mpiCandidates.length" class="archive-import-preview">
          <div class="archive-import-preview-head">
            <span>候选</span><span>姓名</span><span>主索引信息</span><span>来源记录</span><span>可信度</span>
          </div>
          <div class="archive-import-preview-body">
            <button
              v-for="item in mpiCandidates"
              :key="item.candidateId"
              class="archive-import-preview-row"
              :class="{ active: selectedCandidateId === item.candidateId }"
              @click="selectedCandidateId = item.candidateId"
            >
              <span>{{ item.candidateId }}</span>
              <span>{{ item.name }}</span>
              <span>{{ item.phone || '--' }} / {{ item.medicalRecordNumber || '--' }}</span>
              <span>{{ item.sourceRecordId }}</span>
              <span>{{ Math.round(item.confidence * 100) }}%</span>
            </button>
          </div>
        </div>
        <div v-else class="empty-card compact"><p>尚无候选患者</p></div>

        <label class="field inline">
          <input v-model="identityVerified" type="checkbox" />
          <span>已完成身份核对（姓名/手机号/证件后四位/病案号）</span>
        </label>
        <label class="field">
          <span>合并目标档案（用于“合并到已有档案”）</span>
          <select v-model="mergeTargetPatientId">
            <option value="">请选择</option>
            <option v-for="item in mergeTargets" :key="item.patientId" :value="item.patientId">
              {{ item.patientId }} / {{ item.name }}
            </option>
          </select>
        </label>
        <div class="form-actions">
          <button class="primary-button" :disabled="props.importing || !selectedCandidateId" @click="createArchiveFromCandidate">
            {{ props.importing ? '处理中...' : '新建院内档案' }}
          </button>
          <button class="secondary-button" :disabled="props.importing || !selectedCandidateId" @click="mergeCandidateToExistingArchive">
            {{ props.importing ? '处理中...' : '合并到已有档案' }}
          </button>
        </div>
      </article>
    </section>

    <section v-else-if="activeMode === 'onsite_register'" class="archive-import-grid">
      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">门诊现场建档</p>
            <h3>必填信息采集</h3>
          </div>
        </div>
        <div class="form-grid">
          <label class="field"><span>姓名*</span><input v-model="onsiteForm.name" type="text" /></label>
          <label class="field"><span>性别*</span><select v-model="onsiteForm.gender"><option value="男">男</option><option value="女">女</option></select></label>
          <label class="field"><span>出生日期*</span><input v-model="onsiteForm.birthDate" type="date" /></label>
          <label class="field"><span>手机号*</span><input v-model="onsiteForm.phone" type="text" /></label>
          <label class="field">
            <span>证件类型*</span>
            <select v-model="onsiteForm.idType">
              <option value="id_card">居民身份证</option>
              <option value="passport">护照</option>
              <option value="officer_card">军官证</option>
              <option value="other">其他</option>
            </select>
          </label>
          <label class="field"><span>证件号*</span><input v-model="onsiteForm.idNumber" type="text" /></label>
          <label class="field full-span"><span>地址*</span><input v-model="onsiteForm.address" type="text" /></label>
          <label class="field"><span>紧急联系人*</span><input v-model="onsiteForm.emergencyContactName" type="text" /></label>
          <label class="field"><span>紧急联系人电话</span><input v-model="onsiteForm.emergencyContactPhone" type="text" /></label>
          <label class="field"><span>病案号*</span><input v-model="onsiteForm.medicalRecordNumber" type="text" /></label>
          <label class="field"><span>门诊号*</span><input v-model="onsiteForm.visitCardNumber" type="text" /></label>
        </div>
      </article>

      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">推荐信息与附件占位</p>
            <h3>完善建档质量</h3>
          </div>
        </div>
        <div class="form-grid">
          <label class="field"><span>医保类型</span><input v-model="onsiteForm.insuranceType" type="text" /></label>
          <label class="field"><span>责任医生</span><input v-model="onsiteForm.primaryDoctor" type="text" /></label>
          <label class="field"><span>责任护士</span><input v-model="onsiteForm.caseManager" type="text" /></label>
          <label class="field">
            <span>知情同意状态</span>
            <select v-model="onsiteForm.consentStatus">
              <option value="signed">已签署</option>
              <option value="pending">待签署</option>
              <option value="family_authorized">家属授权</option>
            </select>
          </label>
          <label class="field"><span>患者照片（附件占位）</span><input v-model="attachmentPlaceholders.patientPhoto" type="text" placeholder="文件名/编号" /></label>
          <label class="field"><span>身份证照片（附件占位）</span><input v-model="attachmentPlaceholders.idCardPhoto" type="text" placeholder="文件名/编号" /></label>
          <label class="field"><span>医保卡照片（附件占位）</span><input v-model="attachmentPlaceholders.insuranceCardPhoto" type="text" placeholder="文件名/编号" /></label>
          <label class="field"><span>转诊单扫描件（附件占位）</span><input v-model="attachmentPlaceholders.referralScan" type="text" placeholder="文件名/编号" /></label>
        </div>
        <p class="panel-meta">TODO：附件上传待接入文档管理服务，当前仅保留业务占位。</p>
        <div class="form-actions">
          <button class="primary-button" :disabled="props.importing" @click="submitOnsiteRegister">
            {{ props.importing ? '建档中...' : '提交门诊现场建档' }}
          </button>
        </div>
      </article>
    </section>

    <section v-else class="archive-import-grid">
      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">重复档案识别</p>
            <h3>疑似重复患者</h3>
          </div>
        </div>
        <div v-if="duplicateGroups.length" class="preview-list">
          <article v-for="(group, idx) in duplicateGroups" :key="`dup-${idx}`" class="preview-row">
            <strong>{{ group[0]?.name }}（共{{ group.length }}条）</strong>
            <p>{{ group.map((item) => item.patientId).join(' / ') }}</p>
          </article>
        </div>
        <div v-else class="empty-card compact"><p>未发现重复档案</p></div>
      </article>

      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">缺字段补齐</p>
            <h3>主索引关键字段修复</h3>
          </div>
        </div>
        <div v-if="missingFieldRows.length" class="archive-import-preview">
          <div class="archive-import-preview-head"><span>患者ID</span><span>姓名</span><span>缺失字段</span><span>操作</span></div>
          <div class="archive-import-preview-body">
            <div v-for="row in missingFieldRows" :key="row.patient.patientId" class="archive-import-preview-row">
              <span>{{ row.patient.patientId }}</span>
              <span>{{ row.patient.name }}</span>
              <span>{{ row.missing.join('、') }}</span>
              <span><button class="secondary-button" @click="pickGovernanceFix(row.patient)">补齐字段</button></span>
            </div>
          </div>
        </div>
        <div class="form-grid">
          <label class="field"><span>患者ID</span><input v-model="governanceFix.patientId" type="text" /></label>
          <label class="field"><span>手机号</span><input v-model="governanceFix.phone" type="text" /></label>
          <label class="field"><span>紧急联系人电话</span><input v-model="governanceFix.emergencyContactPhone" type="text" /></label>
          <label class="field"><span>证件号</span><input v-model="governanceFix.identityNumber" type="text" /></label>
        </div>
        <div class="form-actions">
          <button class="primary-button" :disabled="props.importing" @click="submitGovernanceFix">
            {{ props.importing ? '处理中...' : '提交字段补齐' }}
          </button>
        </div>
      </article>

      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">冲突档案合并</p>
            <h3>同病案号冲突处理</h3>
          </div>
        </div>
        <div v-if="conflictRows.length" class="preview-list">
          <article v-for="row in conflictRows" :key="row.medicalRecordNumber" class="preview-row">
            <strong>病案号：{{ row.medicalRecordNumber }}</strong>
            <p>{{ row.patients.map((item) => `${item.patientId}-${item.name}`).join(' / ') }}</p>
          </article>
        </div>
        <div v-else class="empty-card compact"><p>未发现冲突档案</p></div>
        <div class="form-grid">
          <label class="field">
            <span>来源档案</span>
            <select v-model="governanceMerge.sourcePatientId">
              <option value="">请选择</option>
              <option v-for="item in props.allPatients" :key="`src-${item.patientId}`" :value="item.patientId">
                {{ item.patientId }} / {{ item.name }}
              </option>
            </select>
          </label>
          <label class="field">
            <span>目标档案</span>
            <select v-model="governanceMerge.targetPatientId">
              <option value="">请选择</option>
              <option v-for="item in props.allPatients" :key="`dst-${item.patientId}`" :value="item.patientId">
                {{ item.patientId }} / {{ item.name }}
              </option>
            </select>
          </label>
        </div>
        <p class="panel-meta">TODO：当前使用 adapter/mock 触发合并更新，待接入主索引冲突合并 API。</p>
        <div class="form-actions">
          <button class="primary-button" :disabled="props.importing" @click="submitGovernanceMerge">
            {{ props.importing ? '处理中...' : '执行冲突档案合并' }}
          </button>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.archive-import-preview-row.active {
  border-color: #2f5f8f;
  box-shadow: 0 0 0 2px rgba(47, 95, 143, 0.15);
}
</style>
