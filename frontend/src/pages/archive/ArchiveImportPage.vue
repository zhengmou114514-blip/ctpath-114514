<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import type { ImportPreviewPatient } from '../../services/types'

type ImportMode = 'batch' | 'single'
type SourcePlatform = 'his' | 'emr' | 'regional' | 'other'
type ImportMethod = 'mrn' | 'idCard' | 'visitNo'

const props = defineProps<{
  importing: boolean
  resultText: string
}>()

const emit = defineEmits<{
  (e: 'submit-import', rows: ImportPreviewPatient[]): void
  (e: 'back'): void
}>()

const activeMode = ref<ImportMode>('batch')
const parseError = ref('')
const detectedHeaders = ref<string[]>([])
const sourceName = ref('')
const previewRows = ref<ImportPreviewPatient[]>([])
const singlePreview = ref<ImportPreviewPatient | null>(null)

const batchTemplateColumns = [
  'patientId',
  'name',
  'age',
  'gender',
  'primaryDisease',
  'currentStage',
  'lastVisit',
  'summary',
]

const singleImportForm = reactive({
  sourcePlatform: 'his' as SourcePlatform,
  importMethod: 'mrn' as ImportMethod,
  externalId: '',
  patientId: '',
  name: '',
  gender: '女',
  age: 0,
  primaryDisease: 'Diabetes',
  currentStage: 'Early',
  lastVisit: new Date().toISOString().slice(0, 10),
  summary: '',
  sections: ['basic', 'diagnosis', 'visit'] as string[],
})

const previewCount = computed(() => previewRows.value.length)

const platformOptions: Array<{ value: SourcePlatform; label: string; detail: string }> = [
  { value: 'his', label: '院内 HIS', detail: '适合门诊挂号、病案号、基础信息导入' },
  { value: 'emr', label: '电子病历', detail: '适合从病历系统导入诊断和病情摘要' },
  { value: 'regional', label: '区域平台', detail: '适合跨院调阅基础档案与最近就诊信息' },
  { value: 'other', label: '其他系统', detail: '用于接收第三方平台或人工整理档案' },
]

function normalizeHeader(value: string) {
  return value.trim().toLowerCase()
}

function splitCsvLine(line: string) {
  const result: string[] = []
  let current = ''
  let inQuotes = false

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index]
    if (char === '"') {
      if (inQuotes && line[index + 1] === '"') {
        current += '"'
        index += 1
      } else {
        inQuotes = !inQuotes
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }

  result.push(current.trim())
  return result
}

function findValue(row: Record<string, string>, aliases: string[]) {
  for (const alias of aliases) {
    const match = row[normalizeHeader(alias)]
    if (match !== undefined && match !== '') return match
  }
  return ''
}

function normalizeGender(value: string) {
  if (!value) return '女'
  if (['male', '男', 'm'].includes(value.trim().toLowerCase())) return '男'
  return '女'
}

function normalizeStage(value: string) {
  const raw = value.trim().toLowerCase()
  if (['mid', 'middle', '中期'].includes(raw)) return 'Mid'
  if (['late', '晚期'].includes(raw)) return 'Late'
  return 'Early'
}

function buildPreviewPatient(row: Partial<ImportPreviewPatient>, rowIndex = 0): ImportPreviewPatient {
  const patientId = row.patientId?.trim() || `IMP${Date.now().toString().slice(-6)}${String(rowIndex + 1).padStart(3, '0')}`
  return {
    rowKey: `${patientId}-${rowIndex}`,
    patientId,
    name: row.name?.trim() || `导入患者${rowIndex + 1}`,
    age: Number(row.age) || 0,
    gender: row.gender || '女',
    avatarUrl: row.avatarUrl?.trim() || '',
    phone: row.phone?.trim() || '',
    emergencyContactName: row.emergencyContactName?.trim() || '',
    emergencyContactRelation: row.emergencyContactRelation?.trim() || '',
    emergencyContactPhone: row.emergencyContactPhone?.trim() || '',
    identityMasked: row.identityMasked?.trim() || '',
    insuranceType: row.insuranceType?.trim() || '城镇职工',
    department: row.department?.trim() || '慢病管理门诊',
    primaryDoctor: row.primaryDoctor?.trim() || '周医生',
    caseManager: row.caseManager?.trim() || '张护士',
    allergyHistory: row.allergyHistory?.trim() || '无',
    familyHistory: row.familyHistory?.trim() || '无特殊家族史',
    medicalRecordNumber: row.medicalRecordNumber?.trim() || patientId,
    archiveSource: row.archiveSource?.trim() || 'outpatient',
    archiveStatus: row.archiveStatus?.trim() || 'active',
    consentStatus: row.consentStatus?.trim() || 'signed',
    primaryDisease: row.primaryDisease?.trim() || 'Diabetes',
    currentStage: row.currentStage || 'Early',
    riskLevel: row.riskLevel || '中风险',
    lastVisit: row.lastVisit || new Date().toISOString().slice(0, 10),
    summary: row.summary?.trim() || '',
    dataSupport: row.dataSupport || 'medium',
    sourceName: row.sourceName || sourceName.value || '导入档案',
  }
}

function mapRowToPatient(row: Record<string, string>, rowIndex: number): ImportPreviewPatient {
  return buildPreviewPatient(
    {
      patientId: findValue(row, ['patientId', 'patient_id', '编号', '患者编号', '病案号', 'mrn']),
      name: findValue(row, ['name', '姓名', '患者姓名']),
      age: Number(findValue(row, ['age', '年龄'])) || 0,
      gender: normalizeGender(findValue(row, ['gender', '性别'])),
      avatarUrl: findValue(row, ['avatarUrl', 'avatar', '头像']),
      phone: findValue(row, ['phone', '手机号', '联系电话', 'mobile']),
      emergencyContactName: findValue(row, ['emergencyContactName', '紧急联系人', '联系人姓名']),
      emergencyContactRelation: findValue(row, ['emergencyContactRelation', '联系人关系', '与患者关系']),
      emergencyContactPhone: findValue(row, ['emergencyContactPhone', '紧急联系人电话', '联系人电话']),
      primaryDisease: findValue(row, ['primaryDisease', 'disease', '主要疾病', '疾病']),
      currentStage: normalizeStage(findValue(row, ['currentStage', 'stage', '阶段', '当前阶段'])),
      riskLevel: '中风险',
      lastVisit: findValue(row, ['lastVisit', '最近就诊', '就诊日期', 'visitDate']),
      summary: findValue(row, ['summary', '摘要', '病情摘要', 'remark']),
      dataSupport: 'medium',
      sourceName: sourceName.value || '批量导入',
    },
    rowIndex
  )
}

async function handleFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  parseError.value = ''
  previewRows.value = []
  detectedHeaders.value = []

  if (!file) return

  sourceName.value = file.name
  const text = await file.text()
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)

  if (lines.length < 2) {
    parseError.value = '导入文件至少需要包含表头和一行数据。'
    return
  }

  const headers = splitCsvLine(lines[0] ?? '').map(normalizeHeader)
  detectedHeaders.value = headers

  const rows = lines.slice(1).map((line) => splitCsvLine(line))
  const mapped = rows.map((cells) => {
    const row = headers.reduce<Record<string, string>>((accumulator, header, index) => {
      accumulator[header] = cells[index] ?? ''
      return accumulator
    }, {})
    return row
  })

  previewRows.value = mapped.map((row, index) => mapRowToPatient(row, index))
}

function generateSinglePreview() {
  singlePreview.value = buildPreviewPatient(
    {
      patientId: singleImportForm.patientId || `${singleImportForm.sourcePlatform.toUpperCase()}-${singleImportForm.externalId}`,
      name: singleImportForm.name,
      age: singleImportForm.age,
      gender: singleImportForm.gender,
      avatarUrl: '',
      phone: '',
      emergencyContactName: '',
      emergencyContactRelation: '',
      emergencyContactPhone: '',
      identityMasked: '',
      insuranceType: '城镇职工',
      department: '慢病管理门诊',
      primaryDoctor: '周医生',
      caseManager: '张护士',
      allergyHistory: '无',
      familyHistory: '无特殊家族史',
      medicalRecordNumber: singleImportForm.patientId || `${singleImportForm.sourcePlatform.toUpperCase()}-${singleImportForm.externalId}`,
      archiveSource: singleImportForm.sourcePlatform === 'regional' ? 'community_referral' : 'outpatient',
      archiveStatus: 'active',
      consentStatus: 'signed',
      primaryDisease: singleImportForm.primaryDisease,
      currentStage: singleImportForm.currentStage,
      riskLevel: '中风险',
      lastVisit: singleImportForm.lastVisit,
      summary: singleImportForm.summary,
      dataSupport: 'medium',
      sourceName: `${singleImportForm.sourcePlatform}-${singleImportForm.importMethod}`,
    },
    0
  )
}

function submitSingleImport() {
  if (!singlePreview.value) {
    generateSinglePreview()
  }
  if (singlePreview.value) {
    emit('submit-import', [singlePreview.value])
  }
}
</script>

<template>
  <section class="module-shell archive-page-shell">
    <article class="card archive-page-hero archive-page-hero-practical">
      <div>
        <p class="eyebrow">档案导入</p>
        <h3>外院档案接入</h3>
        <p class="page-copy">按实际业务拆成两条流程：批量导入用于集中迁移，个人导入用于门诊现场调阅单个患者档案。</p>
      </div>
      <div class="module-hero-actions">
        <button class="secondary-button" @click="emit('back')">返回档案列表</button>
      </div>
    </article>

    <article class="card archive-tab-card">
      <div class="archive-tabbar">
        <button class="secondary-button" :class="{ active: activeMode === 'batch' }" @click="activeMode = 'batch'">大型导入</button>
        <button class="secondary-button" :class="{ active: activeMode === 'single' }" @click="activeMode = 'single'">个人档案导入</button>
      </div>
    </article>

    <section v-if="activeMode === 'batch'" class="archive-import-grid">
      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">大型导入</p>
            <h3>批量患者档案迁移</h3>
          </div>
          <span class="panel-meta">适合上线初期批量导入历史档案、院外整理数据或信息科集中迁移。</span>
        </div>

        <div class="archive-process-strip">
          <div class="archive-process-step active">
            <strong>1</strong>
            <span>准备 CSV 模板</span>
          </div>
          <div class="archive-process-step active">
            <strong>2</strong>
            <span>上传并识别字段</span>
          </div>
          <div class="archive-process-step">
            <strong>3</strong>
            <span>预览后批量写入</span>
          </div>
        </div>

        <label class="field">
          <span>选择导入文件</span>
          <input type="file" accept=".csv,text/csv" @change="handleFileChange" />
        </label>

        <div class="archive-import-template">
          <span class="data-label">推荐表头</span>
          <code>{{ batchTemplateColumns.join(',') }}</code>
        </div>

        <p v-if="parseError" class="error-text">{{ parseError }}</p>
        <p v-if="props.resultText" class="panel-meta">{{ props.resultText }}</p>

        <div class="form-actions">
          <button class="primary-button" :disabled="!previewRows.length || props.importing" @click="emit('submit-import', previewRows)">
            {{ props.importing ? '导入中...' : `开始导入 ${previewCount} 条档案` }}
          </button>
        </div>
      </article>

      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">预览结果</p>
            <h3>字段识别与写入预览</h3>
          </div>
          <span class="panel-meta">识别字段：{{ detectedHeaders.length ? detectedHeaders.join(' / ') : '尚未识别' }}</span>
        </div>

        <div v-if="previewRows.length" class="archive-import-preview">
          <div class="archive-import-preview-head">
            <span>患者编号</span>
            <span>姓名</span>
            <span>年龄</span>
            <span>主要疾病</span>
            <span>阶段</span>
            <span>最近就诊</span>
          </div>
          <div class="archive-import-preview-body">
            <div v-for="row in previewRows.slice(0, 10)" :key="row.rowKey" class="archive-import-preview-row">
              <span>{{ row.patientId }}</span>
              <span>{{ row.name }}</span>
              <span>{{ row.age }}</span>
              <span>{{ row.primaryDisease }}</span>
              <span>{{ row.currentStage }}</span>
              <span>{{ row.lastVisit }}</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-card compact">
          <p>上传 CSV 后，这里会展示即将写入平台的患者基础档案。</p>
        </div>
      </article>
    </section>

    <section v-else class="archive-import-grid">
      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">个人档案导入</p>
            <h3>单患者跨系统调入</h3>
          </div>
          <span class="panel-meta">参考门诊建档场景，适用于医生或档案员在接诊过程中临时调入某一位患者的外部档案。</span>
        </div>

        <div class="single-import-platforms">
          <button
            v-for="item in platformOptions"
            :key="item.value"
            class="platform-tile"
            :class="{ active: singleImportForm.sourcePlatform === item.value }"
            @click="singleImportForm.sourcePlatform = item.value"
          >
            <strong>{{ item.label }}</strong>
            <span>{{ item.detail }}</span>
          </button>
        </div>

        <div class="form-grid">
          <label class="field">
            <span>检索方式</span>
            <select v-model="singleImportForm.importMethod">
              <option value="mrn">病案号</option>
              <option value="idCard">身份证号</option>
              <option value="visitNo">就诊卡号</option>
            </select>
          </label>
          <label class="field">
            <span>外部档案编号</span>
            <input v-model="singleImportForm.externalId" type="text" placeholder="请输入外部系统编号" />
          </label>
          <label class="field">
            <span>患者编号</span>
            <input v-model="singleImportForm.patientId" type="text" placeholder="可留空，系统会自动生成" />
          </label>
          <label class="field">
            <span>患者姓名</span>
            <input v-model="singleImportForm.name" type="text" placeholder="请输入患者姓名" />
          </label>
          <label class="field">
            <span>年龄</span>
            <input v-model.number="singleImportForm.age" type="number" min="0" max="120" />
          </label>
          <label class="field">
            <span>性别</span>
            <select v-model="singleImportForm.gender">
              <option value="女">女</option>
              <option value="男">男</option>
            </select>
          </label>
          <label class="field">
            <span>主要疾病</span>
            <input v-model="singleImportForm.primaryDisease" type="text" />
          </label>
          <label class="field">
            <span>当前阶段</span>
            <select v-model="singleImportForm.currentStage">
              <option value="Early">早期</option>
              <option value="Mid">中期</option>
              <option value="Late">晚期</option>
            </select>
          </label>
          <label class="field">
            <span>最近就诊</span>
            <input v-model="singleImportForm.lastVisit" type="date" />
          </label>
          <label class="field full-span">
            <span>外部病情摘要</span>
            <textarea v-model="singleImportForm.summary" rows="4" placeholder="记录从外部病历或区域平台调入的核心病情摘要" />
          </label>
        </div>

        <div class="single-import-sections">
          <span class="data-label">本次导入内容</span>
          <div class="patient-tags">
            <span>基础身份信息</span>
            <span>主要疾病/阶段</span>
            <span>最近就诊信息</span>
            <span>病情摘要</span>
          </div>
        </div>

        <div class="form-actions">
          <button class="secondary-button" @click="generateSinglePreview">生成导入预览</button>
          <button class="primary-button" :disabled="props.importing" @click="submitSingleImport">
            {{ props.importing ? '导入中...' : '确认导入该患者档案' }}
          </button>
        </div>
      </article>

      <article class="card archive-import-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">单患者预览</p>
            <h3>导入前核对</h3>
          </div>
          <span class="panel-meta">导入完成后，可继续进入档案详情补录结构化事件。</span>
        </div>

        <div v-if="singlePreview" class="archive-single-preview">
          <div class="archive-preview-grid">
            <div class="archive-preview-item">
              <span>来源平台</span>
              <strong>{{ singleImportForm.sourcePlatform }}</strong>
            </div>
            <div class="archive-preview-item">
              <span>外部编号</span>
              <strong>{{ singleImportForm.externalId || '-' }}</strong>
            </div>
            <div class="archive-preview-item">
              <span>患者编号</span>
              <strong>{{ singlePreview.patientId }}</strong>
            </div>
            <div class="archive-preview-item">
              <span>患者姓名</span>
              <strong>{{ singlePreview.name }}</strong>
            </div>
            <div class="archive-preview-item">
              <span>主要疾病</span>
              <strong>{{ singlePreview.primaryDisease }}</strong>
            </div>
            <div class="archive-preview-item">
              <span>最近就诊</span>
              <strong>{{ singlePreview.lastVisit }}</strong>
            </div>
          </div>

          <article class="preview-row">
            <strong>病情摘要</strong>
            <p>{{ singlePreview.summary || '未填写摘要' }}</p>
          </article>
        </div>
        <div v-else class="empty-card compact">
          <p>填写单患者导入信息后，先生成预览，再确认导入。</p>
        </div>
      </article>
    </section>
  </section>
</template>
