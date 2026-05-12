<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type {
  DoctorUser,
  ImportPreviewPatient,
  PatientCase,
  PatientEventPayload,
  PatientSummary,
  PatientUpsertPayload,
  TimelineEvent,
} from '../services/types'
import type { ArchiveFocusSection, ArchiveMode } from '../types/workspace'

const props = defineProps<{
  mode: ArchiveMode
  allPatients: PatientSummary[]
  patients: PatientSummary[]
  loadingPatients: boolean
  currentPage: number
  totalPages: number
  patientCount: number
  patientForm: PatientUpsertPayload
  selectedPatientId: string
  eventForm: PatientEventPayload
  relationOptions: string[]
  savingPatient: boolean
  savingEvent: boolean
  timelineItems: TimelineEvent[]
  selectedPatient: PatientCase | null
  focusSection?: ArchiveFocusSection
  importingArchive?: boolean
  importResultText?: string
  doctorRole?: DoctorUser['role']
  noPermission?: boolean
  modelUnavailable?: boolean
}>()

const emit = defineEmits<{
  (e: 'open', patientId: string): void
  (e: 'open-profile', patientId: string): void
  (e: 'open-attachments', patientId: string): void
  (e: 'open-followup', payload: { patientId?: string; section?: 'tasks' | 'contacts' | 'flow' }): void
  (e: 'create'): void
  (e: 'import'): void
  (e: 'export', patientId?: string): void
  (e: 'prev-page'): void
  (e: 'next-page'): void
  (e: 'submit-archive'): void
  (e: 'submit-event'): void
  (e: 'submit-import', rows: ImportPreviewPatient[]): void
  (e: 'prepare-new'): void
  (e: 'back'): void
}>()

const keyword = ref('')
const diseaseFilter = ref('全部')
const riskFilter = ref('全部')
const archiveStatusFilter = ref('全部')
const consentStatusFilter = ref('全部')
const archivePageSize = 8
const localPage = ref(1)

const sourcePatients = computed(() => (props.allPatients.length ? props.allPatients : props.patients))
const selected = computed(() => props.selectedPatient ?? sourcePatients.value.find((item) => item.patientId === props.selectedPatientId) ?? sourcePatients.value[0] ?? null)

const diseaseOptions = computed(() => ['全部', ...Array.from(new Set(sourcePatients.value.map((item) => item.primaryDisease).filter(Boolean)))])
const riskOptions = computed(() => ['全部', ...Array.from(new Set(sourcePatients.value.map((item) => riskText(item.riskLevel)).filter(Boolean)))])
const archiveStatusOptions = ['全部', '已建档', '待补全', '已停用']
const consentOptions = ['全部', '已签署', '待签署', '家属授权', '已撤回']

const filteredAllPatients = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return sourcePatients.value.filter((patient) => {
    const haystack = `${patient.name} ${patient.patientId} ${archiveNumber(patient)} ${patient.phone}`.toLowerCase()
    if (text && !haystack.includes(text)) return false
    if (diseaseFilter.value !== '全部' && patient.primaryDisease !== diseaseFilter.value) return false
    if (riskFilter.value !== '全部' && riskText(patient.riskLevel) !== riskFilter.value) return false
    if (archiveStatusFilter.value !== '全部' && archiveStatusLabel(patient.archiveStatus) !== archiveStatusFilter.value) return false
    if (consentStatusFilter.value !== '全部' && consentStatusLabel(patient.consentStatus) !== consentStatusFilter.value) return false
    return true
  })
})

const filteredTotalPages = computed(() => Math.max(1, Math.ceil(filteredAllPatients.value.length / archivePageSize)))
const filteredPatients = computed(() => {
  const page = Math.min(localPage.value, filteredTotalPages.value)
  const start = (page - 1) * archivePageSize
  return filteredAllPatients.value.slice(start, start + archivePageSize)
})

const activeCount = computed(() => sourcePatients.value.filter((item) => archiveStatusLabel(item.archiveStatus) === '已建档').length)
const incompleteCount = computed(() => sourcePatients.value.filter((item) => item.dataSupport === 'low' || archiveStatusLabel(item.archiveStatus) === '待补全').length)
const pendingConsentCount = computed(() => sourcePatients.value.filter((item) => consentStatusLabel(item.consentStatus) === '待签署').length)

function archiveNumber(patient: PatientSummary | PatientCase) {
  return patient.medicalRecordNumber || `MRN-${patient.patientId.replace(/\D/g, '').padStart(4, '0')}`
}

function riskText(value: string) {
  if (value.includes('高') || value.toLowerCase().includes('high')) return '高风险'
  if (value.includes('中') || value.toLowerCase().includes('medium')) return '中风险'
  return '低风险'
}

function riskClass(value: string) {
  const text = riskText(value)
  if (text === '高风险') return 'risk-high'
  if (text === '中风险') return 'risk-medium'
  return 'risk-low'
}

function stageLabel(value: string) {
  if (value === 'Early') return '早期'
  if (value === 'Mid') return '中期'
  if (value === 'Late') return '后期'
  return value || '未标注'
}

function archiveStatusLabel(value: string) {
  if (value === 'active' || value === '已启用') return '已建档'
  if (value === 'draft' || !value) return '待补全'
  if (value === 'suspended' || value === 'closed') return '已停用'
  return value
}

function consentStatusLabel(value: string) {
  if (value === 'signed' || value === '已签署') return '已签署'
  if (value === 'family_authorized') return '家属授权'
  if (value === 'withdrawn') return '已撤回'
  return '待签署'
}

function missingItems(patient: PatientSummary | PatientCase | null) {
  if (!patient) return ['请选择患者']
  const items = []
  if (!patient.phone) items.push('联系方式')
  if (!patient.medicalRecordNumber) items.push('病历号')
  if (patient.dataSupport === 'low') items.push('病程资料')
  if (consentStatusLabel(patient.consentStatus) === '待签署') items.push('知情同意书')
  return items.length ? items : ['无明显缺失']
}

function attachmentSummary(patient: PatientSummary | PatientCase | null) {
  if (!patient) return '请选择患者后查看附件情况'
  const signed = consentStatusLabel(patient.consentStatus) !== '待签署'
  return signed ? '患者照片、检查报告和知情同意书可在详情页查看' : '需补充知情同意书和相关慢病资料'
}

function latestCourse(patient: PatientSummary | PatientCase | null) {
  if (!patient) return '请选择患者'
  if ('timeline' in patient && patient.timeline.length) return patient.timeline[0]?.detail || patient.timeline[0]?.title || patient.summary
  return patient.summary || '已纳入慢病患者长期管理'
}

function openSelectedDetail() {
  if (selected.value) emit('open', selected.value.patientId)
}

function prevLocalPage() {
  if (localPage.value > 1) localPage.value -= 1
}

function nextLocalPage() {
  if (localPage.value < filteredTotalPages.value) localPage.value += 1
}

watch([keyword, diseaseFilter, riskFilter, archiveStatusFilter, consentStatusFilter], () => {
  localPage.value = 1
})

watch(filteredTotalPages, (total) => {
  if (localPage.value > total) localPage.value = total
})
</script>

<template>
  <section v-if="props.noPermission" class="empty-state-card">
    <h3>无权限访问</h3>
    <p>当前角色暂无该业务权限，请联系管理员。</p>
  </section>

  <section v-else class="archive-page workstation-page">
    <header class="workstation-page-header archive-header">
      <div>
        <p class="eyebrow">患者主档案表</p>
        <h1>患者档案</h1>
        <p>慢病患者基础信息、档案状态与附件完整度管理</p>
      </div>
      <div class="archive-actions">
        <button class="secondary-button" type="button" :disabled="!selected" @click="openSelectedDetail">档案详情</button>
        <button class="secondary-button" type="button" :disabled="!selected" @click="emit('export', selected?.patientId)">打印档案</button>
        <button class="secondary-button" type="button" @click="emit('import')">导入暂存区</button>
        <button class="primary-button" type="button" @click="emit('create')">新建档案</button>
      </div>
    </header>

    <section class="archive-stat-strip">
      <article><span>档案总数</span><strong>{{ sourcePatients.length }}</strong></article>
      <article><span>已建档</span><strong>{{ activeCount }}</strong></article>
      <article><span>待补全</span><strong>{{ incompleteCount }}</strong></article>
      <article><span>待签署知情同意书</span><strong>{{ pendingConsentCount }}</strong></article>
    </section>

    <section class="archive-filter-bar">
      <input v-model="keyword" type="text" placeholder="姓名 / 档案号 / 联系方式" />
      <select v-model="diseaseFilter">
        <option v-for="item in diseaseOptions" :key="item" :value="item">{{ item }}</option>
      </select>
      <select v-model="riskFilter">
        <option v-for="item in riskOptions" :key="item" :value="item">{{ item }}</option>
      </select>
      <select v-model="archiveStatusFilter">
        <option v-for="item in archiveStatusOptions" :key="item" :value="item">{{ item }}</option>
      </select>
      <select v-model="consentStatusFilter">
        <option v-for="item in consentOptions" :key="item" :value="item">{{ item }}</option>
      </select>
    </section>

    <section class="archive-main-layout">
      <main class="clinical-card archive-table-card">
        <div class="section-header">
          <div>
            <h2>患者档案表</h2>
            <p>围绕 patients 主档案表管理慢病患者基础信息。</p>
          </div>
        </div>

        <div v-if="props.loadingPatients" class="archive-state">正在加载患者档案...</div>
        <div v-else-if="!filteredPatients.length" class="archive-state">当前筛选条件下暂无患者档案。</div>

        <template v-else>
          <div class="archive-table-scroll">
            <table class="archive-table">
              <thead>
                <tr>
                  <th>档案号</th>
                  <th>姓名</th>
                  <th>性别/年龄</th>
                  <th>主要疾病</th>
                  <th>当前阶段</th>
                  <th>风险等级</th>
                  <th>档案状态</th>
                  <th>同意书</th>
                  <th>最近就诊</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="patient in filteredPatients"
                  :key="patient.patientId"
                  :class="{ selected: selected?.patientId === patient.patientId }"
                  @click="emit('open', patient.patientId)"
                >
                  <td>{{ archiveNumber(patient) }}</td>
                  <td><strong>{{ patient.name }}</strong></td>
                  <td>{{ patient.gender }} / {{ patient.age }}岁</td>
                  <td>{{ patient.primaryDisease }}</td>
                  <td>{{ stageLabel(patient.currentStage) }}</td>
                  <td><span class="risk-pill" :class="riskClass(patient.riskLevel)">{{ riskText(patient.riskLevel) }}</span></td>
                  <td>{{ archiveStatusLabel(patient.archiveStatus) }}</td>
                  <td>{{ consentStatusLabel(patient.consentStatus) }}</td>
                  <td>{{ patient.lastVisit || '待补录' }}</td>
                  <td>
                    <div class="table-actions">
                      <button class="text-action" type="button" @click.stop="emit('open', patient.patientId)">详情</button>
                      <button class="text-action" type="button" @click.stop="emit('open-attachments', patient.patientId)">附件</button>
                      <button class="text-action" type="button" @click.stop="emit('open-profile', patient.patientId)">补全</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="archive-pagination">
            <span>第 {{ localPage }} / {{ filteredTotalPages }} 页，共 {{ filteredAllPatients.length }} 名患者</span>
            <div>
              <button class="secondary-button" type="button" :disabled="localPage <= 1" @click="prevLocalPage">上一页</button>
              <button class="secondary-button" type="button" :disabled="localPage >= filteredTotalPages" @click="nextLocalPage">下一页</button>
            </div>
          </div>
        </template>
      </main>

      <aside class="clinical-card archive-summary-card">
        <p class="eyebrow">当前档案摘要</p>
        <template v-if="selected">
          <h2>{{ selected.name }}</h2>
          <p class="summary-meta">{{ archiveNumber(selected) }} / {{ selected.primaryDisease }}</p>

          <dl class="summary-list">
            <div>
              <dt>档案状态</dt>
              <dd>{{ archiveStatusLabel(selected.archiveStatus) }} / {{ consentStatusLabel(selected.consentStatus) }}</dd>
            </div>
            <div>
              <dt>缺失项目</dt>
              <dd>{{ missingItems(selected).join('、') }}</dd>
            </div>
            <div>
              <dt>最近病程</dt>
              <dd>{{ latestCourse(selected) }}</dd>
            </div>
            <div>
              <dt>附件摘要</dt>
              <dd>{{ attachmentSummary(selected) }}</dd>
            </div>
          </dl>

          <div class="summary-actions">
            <button class="primary-button" type="button" @click="emit('open', selected.patientId)">进入详情</button>
            <button class="secondary-button" type="button" @click="emit('open-attachments', selected.patientId)">上传附件</button>
            <button class="secondary-button" type="button" @click="emit('open-profile', selected.patientId)">补全档案</button>
          </div>
        </template>
        <p v-else class="summary-empty">请选择患者档案。</p>
      </aside>
    </section>
  </section>
</template>

<style scoped>
.archive-page {
  gap: 12px;
}

.archive-header {
  align-items: center;
}

.archive-header h1 {
  margin: 0;
}

.archive-actions,
.table-actions,
.summary-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.archive-stat-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.archive-stat-strip article {
  border: 1px solid #c9d9df;
  border-radius: 6px;
  background: #fff;
  padding: 12px 14px;
}

.archive-stat-strip span {
  display: block;
  color: #526772;
  font-size: 12px;
  font-weight: 700;
}

.archive-stat-strip strong {
  display: block;
  margin-top: 4px;
  color: #0f6f95;
  font-family: var(--ws-font-headline);
  font-size: 28px;
}

.archive-filter-bar {
  display: grid;
  grid-template-columns: minmax(220px, 1.2fr) repeat(4, minmax(130px, 1fr));
  gap: 8px;
  border: 1px solid #c9d9df;
  border-radius: 6px;
  background: #fff;
  padding: 10px;
}

.archive-filter-bar input,
.archive-filter-bar select {
  min-height: 34px;
  border: 1px solid #d5dde0;
  border-radius: 4px;
  background: #fff;
  padding: 0 9px;
}

.archive-main-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 12px;
  align-items: start;
}

.archive-table-card,
.archive-summary-card {
  display: grid;
  gap: 12px;
}

.archive-state {
  border: 1px dashed #c9d9df;
  border-radius: 6px;
  color: #526772;
  padding: 18px;
  text-align: center;
}

.archive-table {
  width: 100%;
  min-width: 960px;
  table-layout: fixed;
  border-collapse: collapse;
  border: 1px solid #b7d1de;
}

.archive-table-scroll {
  overflow-x: auto;
}

.archive-table th,
.archive-table td {
  border-bottom: 1px solid #d5e6ef;
  padding: 9px 8px;
  color: #253f4c;
  font-size: 13px;
  text-align: left;
  vertical-align: middle;
}

.archive-table th {
  background: linear-gradient(180deg, #f8fdff, #e3f1f8);
  color: #315e73;
  font-size: 12px;
  font-weight: 800;
}

.archive-table tbody tr:nth-child(even) td {
  background: #f8fbfd;
}

.archive-table tbody tr:hover td,
.archive-table tbody tr.selected td {
  background: #e8f6fd;
}

.archive-table th:nth-child(1) { width: 96px; }
.archive-table th:nth-child(2) { width: 76px; }
.archive-table th:nth-child(3) { width: 82px; }
.archive-table th:nth-child(4) { width: 110px; }
.archive-table th:nth-child(5) { width: 82px; }
.archive-table th:nth-child(6) { width: 82px; }
.archive-table th:nth-child(7) { width: 82px; }
.archive-table th:nth-child(8) { width: 82px; }
.archive-table th:nth-child(9) { width: 92px; }
.archive-table th:nth-child(10) { width: 124px; }

.risk-pill {
  display: inline-flex;
  min-width: 54px;
  justify-content: center;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 800;
}

.risk-high {
  background: #ffe8df;
  color: #9f3a15;
}

.risk-medium {
  background: #fff4d8;
  color: #865400;
}

.risk-low {
  background: #d9f7f5;
  color: #005c61;
}

.text-action {
  min-height: 26px;
  border: 1px solid #b7d1de;
  border-radius: 3px;
  background: #f8fdff;
  color: #005c61;
  font-size: 12px;
  font-weight: 800;
  padding: 0 7px;
}

.archive-summary-card h2 {
  margin: 0;
  color: #003434;
  font-family: var(--ws-font-headline);
  font-size: 24px;
}

.summary-meta,
.summary-empty {
  margin: 0;
  color: #526772;
}

.summary-list {
  display: grid;
  gap: 10px;
  margin: 0;
}

.summary-list div {
  border: 1px solid #d5e6ef;
  border-radius: 6px;
  background: #f8fbfd;
  padding: 10px;
}

.summary-list dt {
  color: #003434;
  font-size: 12px;
  font-weight: 800;
}

.summary-list dd {
  margin: 5px 0 0;
  color: #3f4848;
  line-height: 1.55;
}

.summary-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.summary-actions .primary-button {
  grid-column: 1 / -1;
}

.archive-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-top: 1px solid #d5e6ef;
  padding-top: 10px;
  color: #526772;
  font-size: 13px;
  font-weight: 700;
}

.archive-pagination div {
  display: flex;
  gap: 8px;
}

@media (max-width: 1280px) {
  .archive-main-layout,
  .archive-stat-strip,
  .archive-filter-bar {
    grid-template-columns: 1fr;
  }
}
</style>
