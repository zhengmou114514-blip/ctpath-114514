<script setup lang="ts">
import { computed } from 'vue'
import type {
  EncounterStatus,
  OutpatientPlanItem,
  PatientCase,
  PatientQuadruple,
  PatientSummary,
  PredictResponse,
  TimelineEvent,
} from '../services/types'

const props = defineProps<{
  allPatients: PatientSummary[]
  patients: PatientSummary[]
  selectedPatient: PatientCase | null
  patientQuadruples: PatientQuadruple[]
  predictionResult: PredictResponse | null
  loadingPatients: boolean
  loadingPatient: boolean
  loadingPredict: boolean
  loadingOpenArchive: boolean
  loadingOpenFollowup: boolean
  loadingEncounterStatus: boolean
  loadingCreateTask: boolean
  modelUnavailable: boolean
  noPermission: boolean
  searchText: string
  riskFilter: string
  riskOptions: string[]
}>()

const emit = defineEmits<{
  (e: 'update:search-text', value: string): void
  (e: 'update:risk-filter', value: string): void
  (e: 'open', patientId: string): void
  (e: 'open-archive', patientId: string): void
  (e: 'open-followup', patientId: string): void
  (e: 'update-encounter-status', patientId: string, status: EncounterStatus): void
  (e: 'create-outpatient-task', patientId: string, item: OutpatientPlanItem): void
  (e: 'predict'): void
}>()

const selectedPatientId = computed(() => props.selectedPatient?.patientId ?? '')

const filteredPatients = computed(() => {
  if (props.patients.length) return props.patients
  const risk = props.riskFilter
  const keyword = props.searchText.trim().toLowerCase()
  const isAllRisk = props.riskOptions[0] === risk
  return props.allPatients.filter((item) => {
    const matchRisk = !risk || isAllRisk || item.riskLevel === risk
    const haystack = `${item.patientId} ${item.name} ${item.primaryDisease}`.toLowerCase()
    return matchRisk && (!keyword || haystack.includes(keyword))
  })
})

const recentKeyEvents = computed<TimelineEvent[]>(() => {
  if (!props.selectedPatient) return []
  return props.selectedPatient.timeline.slice(0, 3)
})

const topPrediction = computed(() => {
  const topk = props.predictionResult?.topk ?? props.selectedPatient?.predictions ?? []
  return topk[0] ?? null
})

const adviceSummary = computed(() => {
  const list = props.predictionResult?.advice ?? props.selectedPatient?.careAdvice ?? []
  return list.slice(0, 2)
})

const supportSummary = computed(() => props.predictionResult?.supportSummary ?? '')

const suggestionConfidence = computed(() => {
  const score = topPrediction.value?.score
  if (typeof score !== 'number') return '--'
  return `${Math.round(score * 100)}%`
})

function riskClass(level: string) {
  const raw = level.toLowerCase()
  if (raw.includes('high') || level.includes('高')) return 'risk-high'
  if (raw.includes('medium') || level.includes('中')) return 'risk-medium'
  return 'risk-low'
}

function dataSupportLabel(value?: string) {
  if (!value) return '--'
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value
}

function createQuickTask() {
  if (!props.selectedPatient) return
  emit('create-outpatient-task', props.selectedPatient.patientId, {
    id: `quick-${Date.now()}`,
    category: 'recheck',
    title: '门诊复诊安排',
    owner: props.selectedPatient.caseManager || '随访护士',
    dueLabel: '1周内',
    priority: 'high',
    note: '医生工作台快捷创建',
  })
}
</script>

<template>
  <section class="doctor-clinic-workbench card">
    <div v-if="props.noPermission" class="empty-state">当前账号无医生工作台权限</div>

    <template v-else>
      <aside class="workbench-column left-column">
        <header class="column-header">
          <p class="eyebrow">门诊队列</p>
          <h3>待处理患者</h3>
        </header>

        <section class="surface-card queue-filter-card">
          <label>
            <span>患者搜索</span>
            <input
              :value="props.searchText"
              type="text"
              placeholder="按患者ID/姓名/病种检索"
              @input="emit('update:search-text', ($event.target as HTMLInputElement).value)"
            />
          </label>
          <label>
            <span>风险筛选</span>
            <select
              :value="props.riskFilter"
              @change="emit('update:risk-filter', ($event.target as HTMLSelectElement).value)"
            >
              <option v-for="risk in props.riskOptions" :key="risk" :value="risk">{{ risk }}</option>
            </select>
          </label>
        </section>

        <div v-if="props.loadingPatients" class="empty-state">加载中</div>
        <div v-else-if="!filteredPatients.length" class="empty-state">无数据</div>

        <section v-else class="queue-list">
          <button
            v-for="patient in filteredPatients"
            :key="patient.patientId"
            class="queue-row"
            :class="{ active: selectedPatientId === patient.patientId }"
            @click="emit('open', patient.patientId)"
          >
            <div class="queue-main">
              <strong>{{ patient.name }}</strong>
              <p>{{ patient.patientId }} · {{ patient.primaryDisease }}</p>
              <small>最近就诊：{{ patient.lastVisit || '--' }}</small>
            </div>
            <span class="risk-badge" :class="riskClass(patient.riskLevel)">{{ patient.riskLevel }}</span>
          </button>
        </section>
      </aside>

      <main class="workbench-column center-column">
        <header class="column-header">
          <p class="eyebrow">当前患者</p>
          <h3>门诊摘要卡</h3>
        </header>

        <div v-if="props.loadingPatient" class="empty-state">加载中</div>
        <div v-else-if="!props.selectedPatient" class="empty-state">无数据</div>

        <template v-else>
          <section class="surface-card patient-summary-card">
            <div class="patient-core-head">
              <div>
                <h4>{{ props.selectedPatient.name }}</h4>
                <p>{{ props.selectedPatient.patientId }} · {{ props.selectedPatient.primaryDisease }}</p>
              </div>
              <span class="risk-badge" :class="riskClass(props.selectedPatient.riskLevel)">
                {{ props.selectedPatient.riskLevel }}
              </span>
            </div>

            <div class="meta-grid">
              <article>
                <span>最近就诊</span>
                <strong>{{ props.selectedPatient.lastVisit || '--' }}</strong>
              </article>
              <article>
                <span>当前分期</span>
                <strong>{{ props.selectedPatient.currentStage || '--' }}</strong>
              </article>
              <article>
                <span>数据支持度</span>
                <strong>{{ dataSupportLabel(props.selectedPatient.dataSupport) }}</strong>
              </article>
              <article>
                <span>预测可信度</span>
                <strong>{{ suggestionConfidence }}</strong>
              </article>
            </div>

            <div class="summary-brief">
              <span>病情摘要</span>
              <p>{{ props.selectedPatient.summary || '暂无摘要' }}</p>
            </div>
          </section>

          <section class="surface-card key-events-card">
            <div class="section-title-row">
              <h4>最近关键病程事件（3条）</h4>
              <span class="compact-note">完整病程请进入患者详情</span>
            </div>

            <div v-if="!recentKeyEvents.length" class="empty-state compact">无数据</div>
            <div v-else class="event-list">
              <article
                v-for="(item, idx) in recentKeyEvents"
                :key="`${item.date}-${item.type}-${idx}`"
                class="event-row"
              >
                <span class="event-date">{{ item.date }}</span>
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.detail }}</p>
                </div>
              </article>
            </div>
          </section>
        </template>
      </main>

      <aside class="workbench-column right-column">
        <header class="column-header">
          <p class="eyebrow">临床决策支持</p>
          <h3>预测与建议</h3>
        </header>

        <section class="surface-card prediction-card">
          <div class="section-title-row">
            <h4>预测结论</h4>
            <button class="secondary-button" :disabled="!props.selectedPatient || props.loadingPredict" @click="emit('predict')">
              {{ props.loadingPredict ? '预测中...' : '更新预测' }}
            </button>
          </div>
          <div v-if="props.modelUnavailable" class="empty-state compact">模型不可用</div>
          <div v-else-if="!topPrediction" class="empty-state compact">无数据</div>
          <div v-else class="prediction-result">
            <strong>{{ topPrediction.label }}</strong>
            <span>置信度 {{ Math.round(topPrediction.score * 100) }}%</span>
            <p>{{ topPrediction.reason }}</p>
            <small v-if="supportSummary">{{ supportSummary }}</small>
          </div>
        </section>

        <section class="surface-card advice-card">
          <h4>建议摘要</h4>
          <div v-if="!adviceSummary.length" class="empty-state compact">无数据</div>
          <ul v-else class="advice-summary-list">
            <li v-for="(advice, idx) in adviceSummary" :key="`${idx}-${advice}`">{{ advice }}</li>
          </ul>
        </section>

        <section class="surface-card action-card">
          <h4>门诊主动作</h4>
          <div class="action-grid">
            <button class="primary-button" :disabled="!props.selectedPatient || props.loadingOpenArchive" @click="emit('open-archive', selectedPatientId)">
              {{ props.loadingOpenArchive ? '打开中...' : '打开患者档案' }}
            </button>
            <button class="primary-button" :disabled="!props.selectedPatient || props.loadingOpenFollowup" @click="emit('open-followup', selectedPatientId)">
              {{ props.loadingOpenFollowup ? '进入中...' : '进入随访工作台' }}
            </button>
            <button
              class="secondary-button"
              :disabled="!props.selectedPatient || props.loadingEncounterStatus"
              @click="emit('update-encounter-status', selectedPatientId, 'pending_review')"
            >
              {{ props.loadingEncounterStatus ? '提交中...' : '标记待复核' }}
            </button>
            <button class="secondary-button" :disabled="!props.selectedPatient || props.loadingCreateTask" @click="createQuickTask">
              {{ props.loadingCreateTask ? '创建中...' : '创建复诊任务' }}
            </button>
          </div>
        </section>
      </aside>
    </template>
  </section>
</template>

<style scoped>
.doctor-clinic-workbench {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 360px;
  gap: 14px;
}

.workbench-column {
  display: grid;
  gap: 12px;
  align-content: start;
}

.surface-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #fff;
  padding: 12px;
  display: grid;
  gap: 10px;
}

.queue-list {
  display: grid;
  gap: 8px;
  max-height: 68vh;
  overflow: auto;
}

.queue-row {
  border: 1px solid #d7e1ec;
  border-radius: 10px;
  padding: 10px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  text-align: left;
  background: #fff;
}

.queue-row.active {
  border-color: #4f89be;
  box-shadow: 0 0 0 2px rgba(79, 137, 190, 0.14);
}

.queue-main p,
.queue-main small {
  margin: 4px 0 0;
  color: var(--ink-muted);
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.meta-grid article {
  border: 1px solid #dbe6f1;
  border-radius: 10px;
  background: #f8fbff;
  padding: 10px;
}

.summary-brief {
  border: 1px solid #dbe6f1;
  border-radius: 10px;
  padding: 10px;
}

.summary-brief p {
  margin: 0;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.event-list {
  display: grid;
  gap: 8px;
}

.event-row {
  display: grid;
  grid-template-columns: 116px 1fr;
  gap: 8px;
  border: 1px solid #dbe6f1;
  border-radius: 8px;
  padding: 8px;
}

.event-row p {
  margin: 4px 0 0;
}

.prediction-result {
  border: 1px solid #dbe6f1;
  border-radius: 10px;
  background: #f7fbff;
  padding: 10px;
}

.prediction-result p,
.prediction-result small {
  margin: 0;
}

.advice-summary-list {
  margin: 0;
  padding-left: 18px;
}

.action-grid {
  display: grid;
  gap: 8px;
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.risk-high {
  background: #fdeced;
  color: #a4383f;
}

.risk-medium {
  background: #fff4e2;
  color: #9b6518;
}

.risk-low {
  background: #e9f8f1;
  color: #1d7b5c;
}

.empty-state {
  border: 1px dashed var(--border-strong);
  border-radius: 10px;
  color: var(--ink-muted);
  padding: 14px;
  text-align: center;
  background: #fff;
}

.empty-state.compact {
  padding: 10px;
}

@media (max-width: 1360px) {
  .doctor-clinic-workbench {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .meta-grid,
  .event-row {
    grid-template-columns: 1fr;
  }
}
</style>
