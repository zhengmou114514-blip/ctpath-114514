<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Aim, Files, FirstAidKit, TrendCharts } from '@element-plus/icons-vue'
import type { PatientCase, PatientSummary } from '../services/types'

const props = defineProps<{
  allPatients: PatientSummary[]
  patients: PatientSummary[]
  selectedPatient: PatientCase | null
  loadingPatients: boolean
  loadingPatient: boolean
  loadingAction?: boolean
  noPermission: boolean
  searchText: string
  riskFilter: string
  riskOptions: string[]
}>()

const emit = defineEmits<{
  (e: 'update:search-text', value: string): void
  (e: 'update:risk-filter', value: string): void
  (e: 'open', patientId: string): void
  (e: 'open-detail', patientId: string): void
  (e: 'open-archive', payload: { patientId: string; focus?: 'overview' | 'events' }): void
  (e: 'open-followup', payload: { patientId: string; section?: 'tasks' | 'contacts' | 'flow' }): void
  (e: 'open-model', patientId: string): void
  (e: 'workflow-action', payload: { patientId: string; action: 'complete_processing' | 'complete_high_risk_review' | 'create_followup' | 'refresh_risk_status' }): void
}>()

type WorkbenchView = 'overview' | 'pending' | 'high-risk-review' | 'followup-due' | 'model-stale' | 'current'

const route = useRoute()
const router = useRouter()

const selectedPatientId = computed(() => props.selectedPatient?.patientId ?? '')
const workbenchView = computed<WorkbenchView>(() => {
  const raw = typeof route.query.view === 'string' ? route.query.view : 'overview'
  if (
    raw === 'pending' ||
    raw === 'high-risk-review' ||
    raw === 'followup-due' ||
    raw === 'model-stale' ||
    raw === 'current'
  ) {
    return raw
  }
  return 'overview'
})

const viewLabelMap: Record<WorkbenchView, string> = {
  overview: '全部待处理',
  pending: '待处理患者',
  'high-risk-review': '待复核高风险',
  'followup-due': '待随访患者',
  'model-stale': '模型待刷新',
  current: '当前关注患者',
}

function isHighRisk(patient: PatientSummary | PatientCase) {
  const raw = patient.riskLevel.toLowerCase()
  return patient.riskLevel.includes('高') || raw.includes('high')
}

function isFollowupDue(patient: PatientSummary | PatientCase) {
  if (patient.followupStatus === 'pending' || patient.followupStatus === 'due') return true
  const text = `${patient.summary} ${patient.lastVisit}`.toLowerCase()
  return text.includes('随访') || text.includes('复诊') || text.includes('follow')
}

function isModelStale(patient: PatientSummary | PatientCase) {
  return patient.modelCoverageStatus === 'stale' || !patient.latestAssessmentAt
}

const pendingSource = computed(() => (props.patients.length ? props.patients : props.allPatients).filter((patient) => (patient.queueStatus ?? 'pending') === 'pending'))

const viewPatients = computed<(PatientSummary | PatientCase)[]>(() => {
  if (workbenchView.value === 'high-risk-review') return props.allPatients.filter((patient) => isHighRisk(patient) && (patient.reviewStatus ?? 'pending') !== 'completed')
  if (workbenchView.value === 'followup-due') return props.allPatients.filter(isFollowupDue)
  if (workbenchView.value === 'model-stale') return props.allPatients.filter(isModelStale)
  if (workbenchView.value === 'current') return props.selectedPatient ? [props.selectedPatient] : pendingSource.value.slice(0, 1)
  return pendingSource.value
})

const filteredPatients = computed(() => {
  const source = viewPatients.value
  const keyword = props.searchText.trim().toLowerCase()
  const risk = props.riskFilter
  const allRisk = !risk || props.riskOptions[0] === risk

  return source.filter((patient) => {
    const matchRisk = allRisk || patient.riskLevel === risk
    const haystack = `${patient.patientId} ${patient.name} ${patient.primaryDisease} ${patient.summary}`.toLowerCase()
    return matchRisk && (!keyword || haystack.includes(keyword))
  })
})

const queuePatients = computed(() => filteredPatients.value.slice(0, 8))
const focusPatient = computed<PatientCase | PatientSummary | null>(() => props.selectedPatient ?? queuePatients.value[0] ?? null)

const highRiskCount = computed(() => props.allPatients.filter(isHighRisk).length)

const followupCount = computed(() => props.allPatients.filter(isFollowupDue).length)
const modelStaleCount = computed(() => props.allPatients.filter(isModelStale).length)

const modelCoverage = computed(() => {
  if (!props.allPatients.length) return '0%'
  const covered = props.allPatients.filter((patient) => patient.dataSupport !== 'low').length
  return `${Math.round((covered / props.allPatients.length) * 1000) / 10}%`
})

const overviewCards = computed(() => [
  { label: '待处理患者', value: String(pendingSource.value.length), hint: '当前需处理队列', icon: Files, view: 'pending' as const },
  { label: '待复核高风险', value: String(highRiskCount.value), hint: '需医生优先复核', icon: FirstAidKit, view: 'high-risk-review' as const },
  { label: '待随访患者', value: String(followupCount.value), hint: '需发起或查看随访', icon: Aim, view: 'followup-due' as const },
  { label: '模型待刷新', value: String(modelStaleCount.value), hint: `覆盖率 ${modelCoverage.value}`, icon: TrendCharts, view: 'model-stale' as const },
])

function switchWorkbenchView(view: WorkbenchView) {
  void router.push({
    name: 'doctor-workbench',
    query: view === 'overview' ? { view: 'overview' } : { view },
  })
}

function riskClass(level: string) {
  const raw = (level || '').toLowerCase()
  if (raw.includes('高') || raw.includes('high')) return 'risk-high'
  if (raw.includes('中') || raw.includes('medium')) return 'risk-medium'
  return 'risk-low'
}

function riskText(level: string) {
  if (level.includes('高') || level.toLowerCase().includes('high')) return '高风险'
  if (level.includes('中') || level.toLowerCase().includes('medium')) return '中风险'
  return '低风险'
}

function archiveNumber(patient: PatientSummary | PatientCase) {
  return patient.medicalRecordNumber || '待生成'
}

function completeness(patient: PatientSummary | PatientCase) {
  if (patient.dataSupport === 'high') return '完整'
  if (patient.dataSupport === 'medium') return '基本完整'
  return '待补全'
}

function todoText(patient: PatientSummary | PatientCase) {
  if (patient.queueStatus === 'completed') return '已处理'
  if (isModelStale(patient)) return '刷新模型状态'
  if (patient.riskLevel.includes('高') || patient.riskLevel.toLowerCase().includes('high')) return '风险复核'
  if (patient.dataSupport === 'low') return '补全档案'
  if (patient.summary.includes('随访') || patient.summary.includes('复诊')) return '随访跟进'
  return '诊疗评估'
}

function recentCourseSummary(patient: PatientCase | PatientSummary) {
  if ('timeline' in patient && patient.timeline.length) {
    return patient.timeline[0]?.detail || patient.timeline[0]?.title || patient.summary
  }
  return patient.summary || '已纳入慢病门诊长期管理。'
}

function medicationSummary(patient: PatientCase | PatientSummary) {
  if ('outpatientTasks' in patient && patient.outpatientTasks.length) {
    return `当前需处理：${patient.outpatientTasks[0]?.title}`
  }
  return '当前用药信息可在患者详情中查看。'
}

function modelAdviceSummary(patient: PatientCase | PatientSummary) {
  if ('careAdvice' in patient && patient.careAdvice.length) {
    return patient.careAdvice[0] || '模型建议已生成。'
  }
  if (patient.dataSupport === 'low') return '建议先补全档案和病程记录后再运行模型分析。'
  return '建议结合病程时间线、风险等级和当前用药进行复核。'
}

function openPatientDetail(patientId: string) {
  emit('open', patientId)
  emit('open-detail', patientId)
}

function openModel(patientId: string) {
  emit('open', patientId)
  emit('open-model', patientId)
}

function primaryAction(patientId: string) {
  if (workbenchView.value === 'high-risk-review') {
    emit('workflow-action', { patientId, action: 'complete_high_risk_review' })
    return
  }
  if (workbenchView.value === 'followup-due') {
    emit('workflow-action', { patientId, action: 'create_followup' })
    return
  }
  if (workbenchView.value === 'model-stale') {
    emit('workflow-action', { patientId, action: 'refresh_risk_status' })
    return
  }
  emit('workflow-action', { patientId, action: 'complete_processing' })
}

function primaryActionLabel() {
  if (workbenchView.value === 'high-risk-review') return '完成复核'
  if (workbenchView.value === 'followup-due') return '发起随访'
  if (workbenchView.value === 'model-stale') return '刷新状态'
  return '完成处理'
}
</script>

<template>
  <section class="doctor-dashboard-page workstation-page">
    <section v-if="noPermission" class="empty-state-card">
      <h3>无权限访问</h3>
      <p>当前角色暂无该业务权限，请联系管理员。</p>
    </section>

    <template v-else>
      <section class="overview-strip" aria-label="医生工作台概览">
        <button
          v-for="card in overviewCards"
          :key="card.label"
          class="overview-card"
          :class="{ active: workbenchView === card.view }"
          type="button"
          @click="switchWorkbenchView(card.view)"
        >
          <el-icon><component :is="card.icon" /></el-icon>
          <div>
            <span>{{ card.label }}</span>
            <strong>{{ card.value }}</strong>
            <small>{{ card.hint }}</small>
          </div>
        </button>
      </section>

      <section class="doctor-station-layout">
        <main class="clinical-card queue-panel">
          <div class="station-header">
            <div>
              <p class="eyebrow">慢病门诊医生站</p>
              <h2>待处理患者队列</h2>
              <small class="filter-label">当前筛选：{{ viewLabelMap[workbenchView] }}</small>
            </div>

            <div class="queue-toolbar">
              <input
                :value="searchText"
                type="text"
                placeholder="搜索患者姓名、档案号或主诊断"
                @input="emit('update:search-text', ($event.target as HTMLInputElement).value)"
              />
              <select
                :value="riskFilter"
                @change="emit('update:risk-filter', ($event.target as HTMLSelectElement).value)"
              >
                <option v-for="risk in riskOptions" :key="risk" :value="risk">{{ risk }}</option>
              </select>
            </div>
          </div>

          <div v-if="loadingPatients" class="queue-state">正在加载患者队列...</div>
          <div v-else-if="!queuePatients.length" class="queue-state">当前没有符合“{{ viewLabelMap[workbenchView] }}”条件的患者。</div>

          <table v-else class="patient-queue-table">
            <thead>
              <tr>
                <th>患者姓名</th>
                <th>档案号</th>
                <th>性别/年龄</th>
                <th>主诊断</th>
                <th>风险等级</th>
                <th>最近就诊</th>
                <th>档案完整度</th>
                <th>待处理事项</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="patient in queuePatients"
                :key="patient.patientId"
                :class="{ selected: selectedPatientId === patient.patientId }"
                @click="emit('open', patient.patientId)"
              >
                <td><strong>{{ patient.name }}</strong></td>
                <td>{{ archiveNumber(patient) }}</td>
                <td>{{ patient.gender }} / {{ patient.age }}岁</td>
                <td>{{ patient.primaryDisease }}</td>
                <td><span class="risk-pill" :class="riskClass(patient.riskLevel)">{{ riskText(patient.riskLevel) }}</span></td>
                <td>{{ patient.lastVisit || '待补录' }}</td>
                <td>{{ completeness(patient) }}</td>
                <td>{{ todoText(patient) }}</td>
                <td>
                  <div class="row-actions">
                    <button
                      v-if="workbenchView !== 'model-stale'"
                      class="text-action"
                      type="button"
                      :disabled="loadingPatient || loadingAction"
                      @click.stop="openPatientDetail(patient.patientId)"
                    >
                      进入详情
                    </button>
                    <button class="text-action" type="button" :disabled="loadingAction" @click.stop="openModel(patient.patientId)">风险评估</button>
                    <button
                      class="text-action"
                      type="button"
                      :disabled="loadingAction"
                      @click.stop="primaryAction(patient.patientId)"
                    >
                      {{ primaryActionLabel() }}
                    </button>
                    <button
                      v-if="workbenchView === 'model-stale'"
                      class="text-action"
                      type="button"
                      :disabled="loadingPatient || loadingAction"
                      @click.stop="openPatientDetail(patient.patientId)"
                    >
                      进入详情
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </main>

        <aside class="focus-panel">
          <article v-if="focusPatient" class="clinical-card focus-card">
            <p class="eyebrow">当前关注患者</p>
            <div class="focus-title">
              <strong>{{ focusPatient.name }}</strong>
              <span class="risk-pill" :class="riskClass(focusPatient.riskLevel)">{{ riskText(focusPatient.riskLevel) }}</span>
            </div>
            <p class="focus-meta">{{ archiveNumber(focusPatient) }} / {{ focusPatient.primaryDisease }}</p>

            <dl class="focus-summary">
              <div>
                <dt>最近病程摘要</dt>
                <dd>{{ recentCourseSummary(focusPatient) }}</dd>
              </div>
              <div>
                <dt>当前用药摘要</dt>
                <dd>{{ medicationSummary(focusPatient) }}</dd>
              </div>
              <div>
                <dt>模型建议摘要</dt>
                <dd>{{ modelAdviceSummary(focusPatient) }}</dd>
              </div>
            </dl>

            <div class="focus-actions">
              <button class="primary-button" type="button" @click="openPatientDetail(focusPatient.patientId)">进入详情</button>
              <button class="secondary-button" type="button" @click="openModel(focusPatient.patientId)">风险评估</button>
              <button class="secondary-button" type="button" @click="emit('open-followup', { patientId: focusPatient.patientId, section: 'tasks' })">发起随访</button>
            </div>
          </article>
        </aside>
      </section>
    </template>
  </section>
</template>

<style scoped>
.doctor-dashboard-page {
  gap: 12px;
}

.overview-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.overview-card {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
  border: 1px solid #c9d9df;
  border-radius: 6px;
  background: #fff;
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
}

.overview-card:hover,
.overview-card.active {
  border-color: #008a9b;
  background: #f2fbfd;
  box-shadow: 0 8px 18px rgba(0, 92, 97, 0.08);
}

.overview-card.active {
  outline: 2px solid rgba(0, 138, 155, 0.14);
}

.overview-card :deep(.el-icon) {
  display: grid;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 6px;
  background: #e7f3f8;
  color: #005c61;
}

.overview-card span,
.overview-card small {
  display: block;
  color: #526772;
  font-size: 12px;
}

.overview-card strong {
  display: block;
  color: #0f6f95;
  font-family: var(--ws-font-headline);
  font-size: 28px;
  line-height: 1.1;
}

.doctor-station-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 12px;
  align-items: start;
}

.queue-panel,
.focus-panel,
.focus-card {
  min-width: 0;
  display: grid;
  gap: 12px;
}

.station-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
}

.station-header h2 {
  margin: 0;
  color: #003434;
  font-family: var(--ws-font-headline);
  font-size: 24px;
}

.filter-label {
  display: inline-block;
  margin-top: 4px;
  color: #526772;
  font-size: 12px;
  font-weight: 700;
}

.queue-toolbar {
  display: flex;
  gap: 8px;
}

.queue-toolbar input {
  width: 260px;
}

.queue-toolbar select {
  width: 132px;
}

.queue-state {
  border: 1px dashed #c9d9df;
  border-radius: 6px;
  color: #526772;
  padding: 18px;
  text-align: center;
}

.patient-queue-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  border: 1px solid #b7d1de;
  background: #fff;
}

.patient-queue-table th,
.patient-queue-table td {
  border-bottom: 1px solid #d5e6ef;
  padding: 9px 8px;
  color: #253f4c;
  font-size: 13px;
  text-align: left;
  vertical-align: middle;
}

.patient-queue-table th {
  background: linear-gradient(180deg, #f8fdff, #e3f1f8);
  color: #315e73;
  font-size: 12px;
  font-weight: 800;
}

.patient-queue-table th:nth-child(1) { width: 86px; }
.patient-queue-table th:nth-child(2) { width: 86px; }
.patient-queue-table th:nth-child(3) { width: 82px; }
.patient-queue-table th:nth-child(4) { width: 112px; }
.patient-queue-table th:nth-child(5) { width: 88px; }
.patient-queue-table th:nth-child(6) { width: 92px; }
.patient-queue-table th:nth-child(7) { width: 96px; }
.patient-queue-table th:nth-child(8) { width: 96px; }
.patient-queue-table th:nth-child(9) { width: 190px; }

.patient-queue-table tbody tr {
  cursor: pointer;
}

.patient-queue-table tbody tr:nth-child(even) td {
  background: #f8fbfd;
}

.patient-queue-table tbody tr:hover td,
.patient-queue-table tbody tr.selected td {
  background: #e8f6fd;
}

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

.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
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

.focus-card {
  position: sticky;
  top: 12px;
}

.focus-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.focus-title strong {
  color: #003434;
  font-family: var(--ws-font-headline);
  font-size: 24px;
}

.focus-meta {
  margin: 0;
  color: #526772;
}

.focus-summary {
  display: grid;
  gap: 10px;
  margin: 0;
}

.focus-summary div {
  border: 1px solid #d5e6ef;
  border-radius: 6px;
  background: #f8fbfd;
  padding: 10px;
}

.focus-summary dt {
  color: #003434;
  font-size: 12px;
  font-weight: 800;
}

.focus-summary dd {
  margin: 5px 0 0;
  color: #3f4848;
  line-height: 1.55;
}

.focus-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

@media (max-width: 1280px) {
  .overview-strip,
  .doctor-station-layout {
    grid-template-columns: 1fr;
  }

  .focus-card {
    position: static;
  }
}

@media (max-width: 900px) {
  .station-header,
  .queue-toolbar {
    display: grid;
  }

  .queue-toolbar input,
  .queue-toolbar select {
    width: 100%;
  }

  .patient-queue-table {
    table-layout: auto;
  }
}
</style>
