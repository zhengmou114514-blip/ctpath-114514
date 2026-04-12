<script setup lang="ts">
import { computed, ref } from 'vue'
import type {
  ContactLogCreatePayload,
  EncounterStatus,
  FlowBoardRow,
  MedicationPlanGeneratePayload,
  MedicationPlanResponse,
  OutpatientPlanItem,
  PatientCase,
  PatientQuadruple,
  PatientSummary,
  PredictResponse,
} from '../services/types'
import CareWorkspace from '../components/CareWorkspace.vue'
import ClinicSessionBoard from '../components/ClinicSessionBoard.vue'
import ClinicalAlertBoard from '../components/ClinicalAlertBoardV2.vue'
import DoctorOverviewBoard from '../components/DoctorOverviewBoardV2.vue'
import PatientWorkspaceBoard from '../components/PatientWorkspaceBoard.vue'

type DoctorMode = 'list' | 'detail'
type DoctorBoardPage = 'clinic' | 'summary' | 'alerts' | 'reminders' | 'queue' | 'risk'

interface OverviewMetric {
  label: string
  value: string | number
  note: string
  tone?: 'danger' | 'warning' | 'normal'
}

interface ReminderItem {
  id: string
  title: string
  detail: string
  patientId: string
  priority: 'high' | 'medium' | 'low'
}

interface QueueItem {
  patientId: string
  name: string
  primaryDisease: string
  riskLevel: string
  dataSupport: string
  dueLabel: string
}

const props = defineProps<{
  mode: DoctorMode
  allPatients: PatientSummary[]
  patients: PatientSummary[]
  recentViewed: PatientSummary[]
  flowBoardItems: FlowBoardRow[]
  selectedPatient: PatientCase | null
  patientQuadruples: PatientQuadruple[]
  predictionResult: PredictResponse | null
  medicationPlanResult: MedicationPlanResponse | null
  encounterStatus: EncounterStatus
  savingContactLog: boolean
  loadingPatients: boolean
  loadingPatient: boolean
  loadingPredict: boolean
  searchText: string
  riskFilter: string
  riskOptions: string[]
  hiddenCount: number
  showAllPending: boolean
}>()

const emit = defineEmits<{
  (e: 'update:search-text', value: string): void
  (e: 'update:risk-filter', value: string): void
  (e: 'toggle-show-all'): void
  (e: 'open', patientId: string): void
  (e: 'open-archive', patientId: string): void
  (e: 'open-archive-events', patientId: string): void
  (e: 'open-followup', patientId: string): void
  (e: 'update-encounter-status', patientId: string, status: EncounterStatus): void
  (e: 'create-outpatient-task', patientId: string, item: OutpatientPlanItem): void
  (e: 'submit-contact-log', patientId: string, payload: ContactLogCreatePayload): void
  (e: 'generate-medication-plan', patientId: string, payload: MedicationPlanGeneratePayload): void
  (e: 'predict'): void
  (e: 'back'): void
}>()

const activeBoardPage = ref<DoctorBoardPage>('clinic')

function isHighRisk(level: string) {
  return level.includes('高') || level.toLowerCase().includes('high')
}

function isMediumRisk(level: string) {
  return level.includes('中') || level.toLowerCase().includes('medium')
}

function supportLabel(value: string) {
  if (value === 'high') return '高支持'
  if (value === 'medium') return '中支持'
  if (value === 'low') return '低支持'
  return value
}

const highRiskPatients = computed(() => props.allPatients.filter((item) => isHighRisk(item.riskLevel)))
const mediumRiskPatients = computed(() =>
  props.allPatients.filter((item) => !isHighRisk(item.riskLevel) && isMediumRisk(item.riskLevel))
)
const lowSupportPatients = computed(() => props.allPatients.filter((item) => item.dataSupport === 'low'))

const reviewCount = computed(() =>
  props.flowBoardItems.filter((item) => item.flowStatus.includes('复核') || item.flowStatus.includes('待复核')).length
)
const supplementCount = computed(() =>
  props.flowBoardItems.filter((item) => item.flowStatus.includes('补录') || item.nextAction.includes('补录')).length
)

const overviewMetrics = computed<OverviewMetric[]>(() => [
  { label: '患者总数', value: props.allPatients.length, note: '当前工作台纳入管理的患者规模。', tone: 'normal' },
  { label: '工作队列', value: props.patients.length + props.hiddenCount, note: '按筛选条件进入当前处理队列。', tone: 'warning' },
  { label: '高风险患者', value: highRiskPatients.value.length, note: '建议优先安排复核与随访。', tone: 'danger' },
  { label: '低数据支持', value: lowSupportPatients.value.length, note: '建议补齐结构化事件后再复判。', tone: 'warning' },
])

const overviewReminders = computed<ReminderItem[]>(() => {
  const preferred = [...props.flowBoardItems].sort((left, right) => {
    const order = (value: string) => {
      if (value.includes('复核')) return 0
      if (value.includes('补录')) return 1
      if (value.includes('随访')) return 2
      return 3
    }
    return order(left.flowStatus) - order(right.flowStatus)
  })

  return preferred.slice(0, 6).map((item, index) => ({
    id: `${item.patientId}-${index}`,
    title: item.flowStatus,
    detail: `${item.patientName} / ${item.primaryDisease}，下一步：${item.nextAction}`,
    patientId: item.patientId,
    priority: item.flowStatus.includes('复核') || isHighRisk(item.riskLevel) ? 'high' : 'medium',
  }))
})

const riskQueue = computed<QueueItem[]>(() =>
  [...props.allPatients]
    .sort((left, right) => {
      const leftRank = isHighRisk(left.riskLevel) ? 0 : isMediumRisk(left.riskLevel) ? 1 : 2
      const rightRank = isHighRisk(right.riskLevel) ? 0 : isMediumRisk(right.riskLevel) ? 1 : 2
      if (leftRank !== rightRank) return leftRank - rightRank
      if (left.dataSupport !== right.dataSupport) {
        const supportRank = { low: 0, medium: 1, high: 2 }
        return supportRank[left.dataSupport] - supportRank[right.dataSupport]
      }
      return right.lastVisit.localeCompare(left.lastVisit)
    })
    .slice(0, 8)
    .map((item) => ({
      patientId: item.patientId,
      name: item.name,
      primaryDisease: item.primaryDisease,
      riskLevel: item.riskLevel,
      dataSupport: supportLabel(item.dataSupport),
      dueLabel: `最近就诊：${item.lastVisit}`,
    }))
)

const compactRiskGroups = computed(() => [
  {
    key: 'high',
    label: '高风险',
    count: highRiskPatients.value.length,
    patients: highRiskPatients.value.slice(0, 4),
    tone: 'risk-high',
  },
  {
    key: 'medium',
    label: '中风险',
    count: mediumRiskPatients.value.length,
    patients: mediumRiskPatients.value.slice(0, 4),
    tone: 'risk-medium',
  },
  {
    key: 'support',
    label: '低支持',
    count: lowSupportPatients.value.length,
    patients: lowSupportPatients.value.slice(0, 4),
    tone: 'risk-low',
  },
])

const domainCards = computed(() => [
  {
    code: 'CIS',
    title: '临床评估域',
    description: '接诊、风险评估、预测复核与方案调整统一入口。',
    value: props.patients.length,
    note: '待处理患者',
  },
  {
    code: 'PDS/MRMS',
    title: '档案联查域',
    description: '支持门诊病历、事件补录、质控与主索引联动。',
    value: supplementCount.value,
    note: '待补录项',
  },
  {
    code: 'Follow-up',
    title: '随访协同域',
    description: '复诊计划、电话随访、门诊任务闭环联动。',
    value: props.flowBoardItems.length,
    note: '流程项',
  },
  {
    code: 'Governance',
    title: '治理联动域',
    description: '从流程状态回流治理视角，便于跨角色协同。',
    value: reviewCount.value,
    note: '待复核项',
  },
])

function switchBoardPage(page: DoctorBoardPage) {
  activeBoardPage.value = page
}
</script>

<template>
  <section v-if="props.mode === 'list'" class="doctor-page-shell role-page-stack doctor-command-shell">
    <article class="card doctor-command-header">
      <div class="doctor-command-copy">
        <p class="eyebrow">CIS Clinical Command</p>
        <h2>医生工作台</h2>
        <p>参考 openhis 的业务域组织方式，将接诊、复核、随访、治理入口按工作流展开，减少切换成本。</p>
      </div>

      <div class="doctor-command-metrics">
        <article class="summary-chip">
          <span>在列患者</span>
          <strong>{{ props.patients.length }}</strong>
        </article>
        <article class="summary-chip">
          <span>高风险</span>
          <strong>{{ highRiskPatients.length }}</strong>
        </article>
        <article class="summary-chip">
          <span>待复核</span>
          <strong>{{ reviewCount }}</strong>
        </article>
        <article class="summary-chip">
          <span>待补录</span>
          <strong>{{ supplementCount }}</strong>
        </article>
      </div>
    </article>

    <section class="doctor-domain-strip">
      <article v-for="card in domainCards" :key="card.code" class="card doctor-domain-card">
        <span class="doctor-domain-code">{{ card.code }}</span>
        <strong>{{ card.title }}</strong>
        <p>{{ card.description }}</p>
        <div class="doctor-domain-foot">
          <b>{{ card.value }}</b>
          <small>{{ card.note }}</small>
        </div>
      </article>
    </section>

    <div class="doctor-workbench-grid">
      <section class="doctor-left-rail">
        <article class="card followup-tab-card doctor-nav-card">
          <div class="followup-tabbar">
            <button class="secondary-button" :class="{ active: activeBoardPage === 'clinic' }" @click="switchBoardPage('clinic')">今日接诊</button>
            <button class="secondary-button" :class="{ active: activeBoardPage === 'summary' }" @click="switchBoardPage('summary')">工作摘要</button>
            <button class="secondary-button" :class="{ active: activeBoardPage === 'alerts' }" @click="switchBoardPage('alerts')">临床预警</button>
            <button class="secondary-button" :class="{ active: activeBoardPage === 'reminders' }" @click="switchBoardPage('reminders')">待办提醒</button>
            <button class="secondary-button" :class="{ active: activeBoardPage === 'queue' }" @click="switchBoardPage('queue')">风险队列</button>
            <button class="secondary-button" :class="{ active: activeBoardPage === 'risk' }" @click="switchBoardPage('risk')">风险分组</button>
          </div>
        </article>

        <PatientWorkspaceBoard
          :patients="props.patients"
          :recent-viewed="props.recentViewed"
          :loading-patients="props.loadingPatients"
          :search-text="props.searchText"
          :risk-filter="props.riskFilter"
          :risk-options="props.riskOptions"
          :hidden-count="props.hiddenCount"
          :show-all-pending="props.showAllPending"
          @update:search-text="emit('update:search-text', $event)"
          @update:risk-filter="emit('update:risk-filter', $event)"
          @toggle-show-all="emit('toggle-show-all')"
          @open="emit('open', $event)"
          @open-archive="emit('open-archive', $event)"
        />
      </section>

      <section class="doctor-main-panel doctor-main-panel-stack">
        <ClinicSessionBoard
          v-if="activeBoardPage === 'clinic'"
          :patients="props.allPatients"
          :flow-board-items="props.flowBoardItems"
          :recent-viewed="props.recentViewed"
          @open="emit('open', $event)"
        />

        <ClinicalAlertBoard
          v-else-if="activeBoardPage === 'alerts'"
          :patients="props.allPatients"
          :flow-board-items="props.flowBoardItems"
          @open="emit('open', $event)"
        />

        <DoctorOverviewBoard
          v-else-if="activeBoardPage !== 'risk'"
          :metrics="overviewMetrics"
          :reminders="overviewReminders"
          :queue="riskQueue"
          :view="activeBoardPage === 'summary' ? 'summary' : activeBoardPage === 'reminders' ? 'reminders' : 'queue'"
          @open="emit('open', $event)"
        />

        <article v-else class="card compact-risk-board">
          <div class="panel-head">
            <div>
              <p class="eyebrow">风险分组</p>
              <h3>按风险层级展开快速视图</h3>
            </div>
            <span class="panel-meta">便于门诊医生先处理高风险与低支持患者。</span>
          </div>

          <div class="compact-risk-grid">
            <section v-for="group in compactRiskGroups" :key="group.key" class="compact-risk-column">
              <div class="compact-risk-head">
                <strong>{{ group.label }}</strong>
                <span class="risk-pill" :class="group.tone">{{ group.count }}</span>
              </div>
              <button
                v-for="patient in group.patients"
                :key="patient.patientId"
                class="compact-risk-row"
                @click="emit('open', patient.patientId)"
              >
                <strong>{{ patient.name }}</strong>
                <span>{{ patient.patientId }} / {{ patient.primaryDisease }}</span>
              </button>
              <p v-if="!group.patients.length" class="risk-group-empty">当前暂无患者。</p>
            </section>
          </div>
        </article>
      </section>
    </div>
  </section>

  <CareWorkspace
    v-else
    :patient="props.selectedPatient"
    :quadruples="props.patientQuadruples"
    :prediction-result="props.predictionResult"
    :medication-plan-result="props.medicationPlanResult"
    :encounter-status="props.encounterStatus"
    :saving-contact-log="props.savingContactLog"
    :loading-predict="props.loadingPredict || props.loadingPatient"
    @predict="emit('predict')"
    @back="emit('back')"
    @open-archive="emit('open-archive', $event)"
    @open-archive-events="emit('open-archive-events', $event)"
    @open-followup="emit('open-followup', $event)"
    @update-encounter-status="emit('update-encounter-status', props.selectedPatient?.patientId ?? '', $event)"
    @create-outpatient-task="emit('create-outpatient-task', props.selectedPatient?.patientId ?? '', $event)"
    @submit-contact-log="emit('submit-contact-log', props.selectedPatient?.patientId ?? '', $event)"
    @generate-medication-plan="emit('generate-medication-plan', props.selectedPatient?.patientId ?? '', $event)"
  />
</template>
