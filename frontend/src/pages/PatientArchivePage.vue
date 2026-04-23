<script setup lang="ts">
import { computed } from 'vue'
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

const archiveModeLabel = computed(() => {
  if (props.mode === 'create') return '新建档案'
  if (props.mode === 'detail') return '档案详情'
  if (props.mode === 'import') return '导入暂存区'
  return '档案总览'
})

const activeCount = computed(() => props.allPatients.filter((item) => item.archiveStatus === 'active').length)
const highRiskCount = computed(() =>
  props.allPatients.filter((item) => String(item.riskLevel).toLowerCase().includes('high') || String(item.riskLevel).includes('高')).length
)
const pendingConsentCount = computed(() =>
  props.allPatients.filter((item) => !['signed', 'family_authorized', '已签署'].includes(item.consentStatus)).length
)

const selectedTimeline = computed(() => props.timelineItems.length ? props.timelineItems : props.selectedPatient?.timeline ?? [])
const auditLogs = computed(() => props.selectedPatient?.auditLogs ?? [])

const importSampleRows = computed<ImportPreviewPatient[]>(() => [
  {
    rowKey: 'sample-001',
    sourceName: 'regional_platform',
    patientId: 'PID9010',
    name: '周静',
    age: 63,
    gender: '女',
    avatarUrl: '',
    phone: '13900010010',
    emergencyContactName: '周国强',
    emergencyContactRelation: '配偶',
    emergencyContactPhone: '13900010011',
    identityMasked: '500***********1028',
    insuranceType: '城镇职工医保',
    department: '慢病门诊',
    primaryDoctor: '李昊',
    caseManager: '王敏',
    medicalRecordNumber: 'MRN9010',
    archiveSource: 'community_referral',
    archiveStatus: 'draft',
    consentStatus: 'pending',
    allergyHistory: '青霉素过敏',
    familyHistory: '父亲高血压',
    primaryDisease: '2型糖尿病',
    currentStage: 'Mid',
    riskLevel: 'High Risk',
    lastVisit: '2026-04-18',
    summary: '社区转诊患者，近两周空腹血糖波动明显，需要补齐既往用药和检查记录。',
    dataSupport: 'medium',
  },
  {
    rowKey: 'sample-002',
    sourceName: 'his',
    patientId: 'PID9011',
    name: '陈立',
    age: 57,
    gender: '男',
    avatarUrl: '',
    phone: '13900010012',
    emergencyContactName: '陈欣',
    emergencyContactRelation: '女儿',
    emergencyContactPhone: '13900010013',
    identityMasked: '500***********3319',
    insuranceType: '城乡居民医保',
    department: '高血压专病门诊',
    primaryDoctor: '刘晨',
    caseManager: '赵楠',
    medicalRecordNumber: 'MRN9011',
    archiveSource: 'outpatient',
    archiveStatus: 'draft',
    consentStatus: 'pending',
    allergyHistory: '无',
    familyHistory: '母亲糖尿病',
    primaryDisease: '高血压',
    currentStage: 'Early',
    riskLevel: 'Medium Risk',
    lastVisit: '2026-04-19',
    summary: '门诊建档补录患者，需核对身份证件、用药历史与最近一次复诊时间。',
    dataSupport: 'low',
  },
])

function stageLabel(value: string) {
  if (value === 'Early') return '早期'
  if (value === 'Mid') return '中期'
  if (value === 'Late') return '后期'
  return value || '--'
}

function supportLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value || '--'
}

function archiveStatusLabel(value: string) {
  if (value === 'draft') return '待完善'
  if (value === 'active') return '已启用'
  if (value === 'suspended') return '已挂起'
  if (value === 'closed') return '已关闭'
  return value || '--'
}

function consentStatusLabel(value: string) {
  if (value === 'signed') return '已签署'
  if (value === 'pending') return '待签署'
  if (value === 'family_authorized') return '家属授权'
  if (value === 'withdrawn') return '已撤回'
  return value || '--'
}

function archiveRowClass(patient: PatientSummary) {
  if (patient.patientId === props.selectedPatientId) return 'archive-row-active'
  return ''
}
</script>

<template>
  <section v-if="props.noPermission" class="empty-state-card">
    <h3>当前账号无档案权限</h3>
    <p>请使用医生或档案员账号进入患者档案工作区。</p>
  </section>

  <section v-else-if="props.loadingPatients" class="empty-state-card">
    <h3>档案数据加载中</h3>
    <p>正在同步患者主索引、档案状态和病程摘要，请稍后。</p>
  </section>

  <section v-else class="archive-workspace-page workstation-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">电子档案 / 病案管理</p>
        <h1>患者档案工作区</h1>
        <p>围绕患者身份信息、联系方式、病程录入、建档状态和导入暂存区，完成慢病患者电子档案管理。</p>
      </div>
      <div class="header-actions">
        <span class="workspace-status-pill">{{ archiveModeLabel }}</span>
        <button class="secondary-button" type="button" @click="emit('export', props.selectedPatient?.patientId || props.patients[0]?.patientId)">打印档案</button>
        <button class="secondary-button" type="button" @click="emit('import')">导入暂存区</button>
        <button class="primary-button" type="button" @click="emit('create')">新建档案</button>
      </div>
    </header>

    <section class="metric-grid four">
      <article class="metric-card">
        <span>档案总数</span>
        <strong>{{ props.allPatients.length }}</strong>
      </article>
      <article class="metric-card">
        <span>已启用</span>
        <strong>{{ activeCount }}</strong>
      </article>
      <article class="metric-card">
        <span>高风险患者</span>
        <strong>{{ highRiskCount }}</strong>
      </article>
      <article class="metric-card">
        <span>待签署同意书</span>
        <strong>{{ pendingConsentCount }}</strong>
      </article>

      <article class="clinical-card archive-live-panel">
        <div class="section-header">
          <div>
            <h2>当前患者工作面板</h2>
            <p>这里放当前选中患者的摘要、时间线和操作入口，减少“左边一大表、右边空白”的割裂感。</p>
          </div>
        </div>

        <div v-if="props.selectedPatient" class="live-summary-grid">
          <div class="live-summary-item">
            <span>姓名</span>
            <strong>{{ props.selectedPatient.name }}</strong>
            <small>{{ props.selectedPatient.patientId }}</small>
          </div>
          <div class="live-summary-item">
            <span>主病种</span>
            <strong>{{ props.selectedPatient.primaryDisease || '--' }}</strong>
            <small>{{ props.selectedPatient.currentStage || '--' }}</small>
          </div>
          <div class="live-summary-item">
            <span>风险</span>
            <strong>{{ props.selectedPatient.riskLevel || '--' }}</strong>
            <small>支持度 {{ props.selectedPatient.dataSupport || '--' }}</small>
          </div>
          <div class="live-summary-item">
            <span>档案状态</span>
            <strong>{{ archiveStatusLabel(props.selectedPatient.archiveStatus) }}</strong>
            <small>同意：{{ consentStatusLabel(props.selectedPatient.consentStatus) }}</small>
          </div>
        </div>

        <div class="live-divider" />

        <div class="archive-quick-links">
          <button class="secondary-button" type="button" @click="emit('open-followup', { section: 'tasks' })">随访任务</button>
          <button class="secondary-button" type="button" @click="emit('open-followup', { section: 'contacts' })">联系方式</button>
          <button class="secondary-button" type="button" @click="emit('open-followup', { section: 'flow' })">病情流转</button>
        </div>

        <div class="live-list-grid">
          <section>
            <h3>最近病程</h3>
            <ul v-if="selectedTimeline.length" class="live-list">
              <li v-for="item in selectedTimeline.slice(0, 4)" :key="`${item.date}-${item.type}`">
                <strong>{{ item.date }}</strong>
                <span>{{ item.title }}</span>
              </li>
            </ul>
            <div v-else class="empty-inline">暂无病程记录</div>
          </section>

          <section>
            <h3>审核轨迹</h3>
            <ul v-if="auditLogs.length" class="live-list">
              <li v-for="(item, index) in auditLogs.slice(0, 4)" :key="`${item.createdAt}-${index}`">
                <strong>{{ item.createdAt.slice(0, 10) }}</strong>
                <span>{{ item.action }}</span>
              </li>
            </ul>
            <div v-else class="empty-inline">暂无审核记录</div>
          </section>
        </div>

        <div class="side-actions">
          <button class="secondary-button" type="button" @click="emit('create')">新建档案</button>
          <button class="secondary-button" type="button" @click="emit('import')">导入暂存</button>
          <button class="primary-button" type="button" @click="emit('export', props.selectedPatient?.patientId || props.patients[0]?.patientId)">打印档案</button>
        </div>
      </article>
    </section>

    <section v-if="props.modelUnavailable && props.mode === 'list'" class="inline-alert warning">
      推理服务当前不可用，但档案维护、事件录入和导入暂存区不受影响。
    </section>

    <section v-if="props.mode === 'list'" class="archive-layout">
      <article class="clinical-card archive-list-card">
        <div class="section-header">
          <div>
            <h2>患者档案列表</h2>
            <p>当前页 {{ props.currentPage }} / {{ props.totalPages }}，共 {{ props.patientCount }} 名患者。</p>
          </div>
          <div class="list-actions">
            <button class="secondary-button" type="button" :disabled="props.currentPage <= 1" @click="emit('prev-page')">上一页</button>
            <button class="secondary-button" type="button" :disabled="props.currentPage >= props.totalPages" @click="emit('next-page')">下一页</button>
          </div>
        </div>

        <div v-if="!props.allPatients.length" class="empty-state-card compact">
          <h3>暂无档案数据</h3>
          <p>可以先新建档案，或进入导入暂存区导入演示病例。</p>
        </div>

        <div v-else class="archive-list">
          <button
            v-for="patient in props.patients"
            :key="patient.patientId"
            class="archive-row"
            :class="archiveRowClass(patient)"
            type="button"
            @click="emit('open', patient.patientId)"
          >
            <div class="archive-row-main">
              <strong>{{ patient.name }}</strong>
              <span>{{ patient.patientId }} / {{ patient.medicalRecordNumber || '未生成病案号' }}</span>
            </div>
            <div class="archive-row-meta">
              <span>{{ patient.primaryDisease }}</span>
              <span>{{ patient.department }}</span>
              <span>{{ archiveStatusLabel(patient.archiveStatus) }}</span>
            </div>
            <div class="archive-row-tags">
              <span class="tag risk">{{ patient.riskLevel }}</span>
              <span class="tag support">数据支持 {{ supportLabel(patient.dataSupport) }}</span>
              <span class="tag consent">{{ consentStatusLabel(patient.consentStatus) }}</span>
            </div>
          </button>
        </div>
      </article>

      <article class="clinical-card archive-side-card">
        <div class="section-header">
          <div>
            <h2>档案工作提示</h2>
            <p>参考 openhis 式后台组织方式，先明确身份信息，再补病程，再进入附件与用药闭环。</p>
          </div>
        </div>

        <div class="side-guides">
          <article class="guide-tile">
            <strong>1. 身份信息</strong>
            <p>优先核对姓名、联系方式、紧急联系人、建档来源和同意书状态。</p>
          </article>
          <article class="guide-tile">
            <strong>2. 病程录入</strong>
            <p>补齐病程时间点、关系类型、事件说明，供预测和建议链路消费。</p>
          </article>
          <article class="guide-tile">
            <strong>3. 档案闭环</strong>
            <p>从档案详情进入电子附件、当前用药与随访，不在列表页堆叠所有模块。</p>
          </article>
        </div>
      </article>
    </section>

    <section v-else-if="props.mode === 'import'" class="archive-layout archive-layout-single">
      <article class="clinical-card archive-import-card">
        <div class="section-header">
          <div>
            <h2>导入暂存区</h2>
            <p>导入数据先进入暂存区，再进入正式患者档案，避免 CSV 直接进入正式主表。</p>
          </div>
          <button class="secondary-button" type="button" @click="emit('back')">返回列表</button>
        </div>

        <div class="import-guides">
          <article class="guide-tile">
            <strong>来源系统</strong>
            <p>当前演示使用 HIS / 区域平台两条导入样例，方便答辩时说明导入治理边界。</p>
          </article>
          <article class="guide-tile">
            <strong>校验逻辑</strong>
            <p>导入完成后由后端输出成功/失败统计，只有通过校验的数据会写入正式档案。</p>
          </article>
        </div>

        <div class="preview-table">
          <div class="preview-head">
            <span>患者</span>
            <span>来源</span>
            <span>疾病</span>
            <span>风险</span>
            <span>状态</span>
          </div>
          <div v-for="row in importSampleRows" :key="row.rowKey" class="preview-row">
            <span>{{ row.name }} / {{ row.patientId }}</span>
            <span>{{ row.sourceName }}</span>
            <span>{{ row.primaryDisease }}</span>
            <span>{{ row.riskLevel }}</span>
            <span>{{ archiveStatusLabel(row.archiveStatus) }}</span>
          </div>
        </div>

        <div class="form-actions">
          <button class="primary-button" type="button" :disabled="props.importingArchive" @click="emit('submit-import', importSampleRows)">
            {{ props.importingArchive ? '导入中...' : '导入演示暂存档案' }}
          </button>
          <button class="secondary-button" type="button" @click="emit('back')">取消</button>
        </div>

        <p v-if="props.importResultText" class="result-text">{{ props.importResultText }}</p>
      </article>
    </section>

    <section v-else class="archive-layout">
      <article class="clinical-card archive-editor-card">
        <div class="section-header">
          <div>
            <h2>{{ props.mode === 'create' ? '新建患者档案' : '档案详情维护' }}</h2>
            <p>围绕主索引信息、病种、建档信息和摘要，维护慢病患者的核心电子档案。</p>
          </div>
          <div class="list-actions">
            <button class="secondary-button" type="button" @click="emit('back')">返回列表</button>
            <button class="secondary-button" type="button" @click="emit('prepare-new')">重置表单</button>
          </div>
        </div>

        <div class="editor-grid">
          <label class="field">
            <span>患者编号</span>
            <input v-model="props.patientForm.patientId" :disabled="!!props.selectedPatientId" type="text" placeholder="PID9010" />
          </label>
          <label class="field">
            <span>姓名</span>
            <input v-model="props.patientForm.name" type="text" placeholder="请输入患者姓名" />
          </label>
          <label class="field">
            <span>年龄</span>
            <input v-model.number="props.patientForm.age" type="number" min="0" max="120" />
          </label>
          <label class="field">
            <span>性别</span>
            <select v-model="props.patientForm.gender">
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </label>
          <label class="field">
            <span>联系电话</span>
            <input v-model="props.patientForm.phone" type="text" placeholder="请输入联系电话" />
          </label>
          <label class="field">
            <span>身份证脱敏</span>
            <input v-model="props.patientForm.identityMasked" type="text" placeholder="500***********1234" />
          </label>
          <label class="field">
            <span>紧急联系人</span>
            <input v-model="props.patientForm.emergencyContactName" type="text" placeholder="请输入紧急联系人姓名" />
          </label>
          <label class="field">
            <span>联系人关系</span>
            <input v-model="props.patientForm.emergencyContactRelation" type="text" placeholder="配偶 / 子女 / 父母" />
          </label>
          <label class="field">
            <span>联系人电话</span>
            <input v-model="props.patientForm.emergencyContactPhone" type="text" placeholder="请输入联系人电话" />
          </label>
          <label class="field">
            <span>主要疾病</span>
            <input v-model="props.patientForm.primaryDisease" type="text" placeholder="2型糖尿病 / 高血压" />
          </label>
          <label class="field">
            <span>当前阶段</span>
            <select v-model="props.patientForm.currentStage">
              <option value="Early">早期</option>
              <option value="Mid">中期</option>
              <option value="Late">后期</option>
            </select>
          </label>
          <label class="field">
            <span>最近就诊</span>
            <input v-model="props.patientForm.lastVisit" type="date" />
          </label>
          <label class="field">
            <span>医保类型</span>
            <input v-model="props.patientForm.insuranceType" type="text" placeholder="城镇职工医保" />
          </label>
          <label class="field">
            <span>科室</span>
            <input v-model="props.patientForm.department" type="text" placeholder="慢病门诊" />
          </label>
          <label class="field">
            <span>责任医生</span>
            <input v-model="props.patientForm.primaryDoctor" type="text" placeholder="请输入责任医生" />
          </label>
          <label class="field">
            <span>个案管理师</span>
            <input v-model="props.patientForm.caseManager" type="text" placeholder="请输入个案管理师" />
          </label>
          <label class="field">
            <span>病案号</span>
            <input v-model="props.patientForm.medicalRecordNumber" type="text" placeholder="MRN9010" />
          </label>
          <label class="field">
            <span>建档来源</span>
            <select v-model="props.patientForm.archiveSource">
              <option value="outpatient">门诊建档</option>
              <option value="community_referral">社区转诊</option>
              <option value="discharge_followup">出院随访</option>
              <option value="manual">手工录入</option>
            </select>
          </label>
          <label class="field">
            <span>档案状态</span>
            <select v-model="props.patientForm.archiveStatus">
              <option value="draft">待完善</option>
              <option value="active">已启用</option>
              <option value="suspended">已挂起</option>
              <option value="closed">已关闭</option>
            </select>
          </label>
          <label class="field">
            <span>同意书状态</span>
            <select v-model="props.patientForm.consentStatus">
              <option value="signed">已签署</option>
              <option value="pending">待签署</option>
              <option value="family_authorized">家属授权</option>
              <option value="withdrawn">已撤回</option>
            </select>
          </label>
          <label class="field full-span">
            <span>过敏史</span>
            <input v-model="props.patientForm.allergyHistory" type="text" placeholder="青霉素过敏 / 无" />
          </label>
          <label class="field full-span">
            <span>家族史</span>
            <input v-model="props.patientForm.familyHistory" type="text" placeholder="父亲高血压 / 母亲糖尿病" />
          </label>
          <label class="field full-span">
            <span>档案摘要</span>
            <textarea v-model="props.patientForm.summary" rows="4" placeholder="补充患者慢病背景、近期病程、建档原因和后续工作建议。" />
          </label>
        </div>

        <div class="form-actions">
          <button class="primary-button" type="button" :disabled="props.savingPatient" @click="emit('submit-archive')">
            {{ props.savingPatient ? '保存中...' : props.mode === 'create' ? '提交档案' : '保存档案' }}
          </button>
          <button class="secondary-button" type="button" @click="emit('back')">返回列表</button>
        </div>
      </article>

      <aside class="archive-side-column">
        <article class="clinical-card archive-event-card" :class="{ focus: props.focusSection === 'events' }">
          <div class="section-header">
            <div>
              <h2>病程事件录入</h2>
              <p>维护时间、关系类型、对象值和说明，用于构建患者病程时间线。</p>
            </div>
          </div>

          <div class="editor-grid compact">
            <label class="field">
              <span>事件时间</span>
              <input v-model="props.eventForm.eventTime" type="datetime-local" />
            </label>
            <label class="field">
              <span>关系类型</span>
              <select v-model="props.eventForm.relation">
                <option v-for="item in props.relationOptions" :key="item" :value="item">{{ item }}</option>
              </select>
            </label>
            <label class="field">
              <span>对象值</span>
              <input v-model="props.eventForm.objectValue" type="text" placeholder="如 High / HbA1c / 复诊提醒" />
            </label>
            <label class="field full-span">
              <span>备注说明</span>
              <textarea v-model="props.eventForm.note" rows="3" placeholder="补充事件背景、门诊处理或后续建议。" />
            </label>
          </div>

          <div class="form-actions">
            <button class="primary-button" type="button" :disabled="props.savingEvent" @click="emit('submit-event')">
              {{ props.savingEvent ? '提交中...' : '新增病程事件' }}
            </button>
          </div>
        </article>

        <article class="clinical-card archive-preview-card">
          <div class="section-header">
            <div>
              <h2>档案摘要预览</h2>
              <p>重点展示阶段、风险、数据支持度和关键时间点，便于答辩时说明档案闭环。</p>
            </div>
          </div>

          <div class="preview-grid">
            <div class="preview-item">
              <span>阶段</span>
              <strong>{{ stageLabel(props.patientForm.currentStage) }}</strong>
            </div>
            <div class="preview-item">
              <span>风险</span>
              <strong>{{ props.patientForm.riskLevel || '--' }}</strong>
            </div>
            <div class="preview-item">
              <span>数据支持</span>
              <strong>{{ supportLabel(props.patientForm.dataSupport) }}</strong>
            </div>
            <div class="preview-item">
              <span>档案状态</span>
              <strong>{{ archiveStatusLabel(props.patientForm.archiveStatus) }}</strong>
            </div>
            <div class="preview-item">
              <span>同意书</span>
              <strong>{{ consentStatusLabel(props.patientForm.consentStatus) }}</strong>
            </div>
            <div class="preview-item">
              <span>最近就诊</span>
              <strong>{{ props.patientForm.lastVisit || '--' }}</strong>
            </div>
          </div>
        </article>
      </aside>
    </section>

    <section v-if="props.mode !== 'list'" class="archive-layout archive-layout-single">
      <article class="clinical-card timeline-card">
        <div class="section-header">
          <div>
            <h2>病程时间线</h2>
            <p>展示当前档案已录入的重要病程节点和审计记录。</p>
          </div>
        </div>

        <div v-if="selectedTimeline.length" class="timeline-list">
          <article v-for="item in selectedTimeline" :key="`${item.date}-${item.title}`" class="timeline-row">
            <strong>{{ item.title }}</strong>
            <span>{{ item.date }}</span>
            <p>{{ item.detail }}</p>
          </article>
        </div>
        <div v-else class="empty-state-card compact">
          <h3>暂无病程记录</h3>
          <p>可在右侧病程事件录入区补充患者病程节点。</p>
        </div>

        <div v-if="auditLogs.length" class="audit-list">
          <article v-for="log in auditLogs" :key="log.logId" class="timeline-row muted">
            <strong>{{ log.action }}</strong>
            <span>{{ log.createdAt }}</span>
            <p>{{ log.detail }}{{ log.operatorName ? ` / ${log.operatorName}` : '' }}</p>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.archive-workspace-page,
.archive-layout,
.archive-side-column,
.editor-grid,
.metric-grid,
.side-guides,
.import-guides,
.timeline-list,
.audit-list {
  display: grid;
  gap: 22px;
}

.archive-layout {
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 0.9fr);
  align-items: start;
}

.archive-live-panel {
  grid-column: 1 / -1;
  display: grid;
  gap: 18px;
}

.archive-layout-single {
  grid-template-columns: 1fr;
}

.archive-list-card,
.archive-side-card,
.archive-editor-card,
.archive-event-card,
.archive-preview-card,
.archive-import-card,
.timeline-card {
  display: grid;
  gap: 18px;
}

.header-actions,
.section-header,
.list-actions,
.form-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.archive-list {
  display: grid;
  gap: 12px;
}

.archive-row {
  display: grid;
  gap: 10px;
  border: 1px solid rgba(205, 214, 218, 0.9);
  border-radius: 16px;
  background: #fff;
  padding: 18px;
  text-align: left;
}

.archive-row-active {
  border-color: rgba(0, 92, 97, 0.35);
  box-shadow: 0 0 0 2px rgba(0, 92, 97, 0.08);
}

.archive-row-main,
.archive-row-meta,
.archive-row-tags,
.preview-grid,
.preview-table,
.preview-head,
.preview-row {
  display: grid;
  gap: 10px;
}

.archive-row-main strong {
  font-size: 18px;
}

.archive-row-main span,
.archive-row-meta span,
.preview-row span,
.result-text {
  color: #5c6970;
}

.archive-row-meta {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.archive-row-tags {
  grid-template-columns: repeat(3, minmax(0, max-content));
}

.tag {
  border-radius: 999px;
  padding: 6px 10px;
  background: rgba(235, 238, 239, 0.92);
  color: #31454c;
  font-size: 12px;
  font-weight: 700;
}

.tag.risk {
  background: rgba(255, 236, 226, 0.9);
}

.tag.support {
  background: rgba(233, 245, 255, 0.95);
}

.tag.consent {
  background: rgba(237, 247, 238, 0.95);
}

.guide-tile {
  display: grid;
  gap: 6px;
  border-radius: 14px;
  background: rgba(241, 244, 245, 0.92);
  padding: 16px;
}

.live-summary-grid,
.live-list-grid {
  display: grid;
  gap: 14px;
}

.live-summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.live-summary-item {
  display: grid;
  gap: 6px;
  border-radius: 14px;
  background: rgba(241, 244, 245, 0.92);
  padding: 14px;
}

.live-summary-item span {
  color: #61737b;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.live-summary-item small {
  color: #61737b;
}

.live-divider {
  height: 1px;
  background: rgba(205, 214, 218, 0.9);
}

.archive-quick-links {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.live-list-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.live-list {
  display: grid;
  gap: 10px;
}

.live-list li {
  display: grid;
  gap: 4px;
  border-radius: 12px;
  background: rgba(247, 249, 250, 0.96);
  padding: 12px 14px;
}

.live-list li span {
  color: #5c6970;
}

.side-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.empty-inline {
  border-radius: 12px;
  background: rgba(247, 249, 250, 0.96);
  padding: 12px 14px;
  color: #61737b;
}

.guide-tile p,
.section-header p,
.empty-state-card.compact p,
.timeline-row p {
  margin: 0;
  color: #526772;
  line-height: 1.65;
}

.editor-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.editor-grid.compact {
  grid-template-columns: 1fr;
}

.field {
  display: grid;
  gap: 8px;
}

.field.full-span {
  grid-column: 1 / -1;
}

.field span {
  color: #3f4848;
  font-size: 13px;
  font-weight: 700;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  min-height: 48px;
  border: 1px solid #d5dde0;
  border-radius: 14px;
  background: #fff;
  padding: 0 14px;
  font: inherit;
  color: #181c1e;
}

.field textarea {
  min-height: 110px;
  padding: 14px;
  resize: vertical;
}

.archive-event-card.focus {
  box-shadow: 0 0 0 2px rgba(0, 92, 97, 0.08);
}

.preview-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.preview-item {
  display: grid;
  gap: 6px;
  border-radius: 14px;
  background: rgba(241, 244, 245, 0.92);
  padding: 14px;
}

.preview-item span {
  color: #61737b;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.preview-head,
.preview-row {
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  align-items: center;
}

.preview-head {
  color: #526772;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.preview-row,
.timeline-row {
  border-radius: 14px;
  background: rgba(241, 244, 245, 0.92);
  padding: 14px 16px;
}

.timeline-row {
  display: grid;
  gap: 6px;
}

.timeline-row.muted {
  background: rgba(247, 249, 250, 0.96);
}

.inline-alert.warning {
  border-radius: 14px;
  background: rgba(255, 243, 224, 0.85);
  padding: 14px 16px;
  color: #8a4b08;
}

.result-text {
  margin: 0;
}

@media (max-width: 1180px) {
  .archive-layout {
    grid-template-columns: 1fr;
  }

  .archive-quick-links {
    grid-template-columns: 1fr;
  }

  .preview-grid,
  .archive-row-meta,
  .preview-head,
  .preview-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .editor-grid {
    grid-template-columns: 1fr;
  }
}
</style>
