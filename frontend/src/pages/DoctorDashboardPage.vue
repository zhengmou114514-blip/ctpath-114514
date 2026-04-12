<script setup lang="ts">
import { computed } from 'vue'
import type {
  EncounterStatus,  OutpatientPlanItem,
  PatientCase,
  PatientQuadruple,
  PatientSummary,
  PredictResponse,
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

const topk = computed(() => props.predictionResult?.topk ?? props.selectedPatient?.predictions ?? [])

const evidenceSummary = computed(() => {
  const evidence = props.predictionResult?.evidence
  if (!evidence) return null
  return [
    { label: '事件数', value: evidence.eventCount },
    { label: '时间点', value: evidence.timepointCount },
    { label: '关系数', value: evidence.relationCount },
    { label: '支持等级', value: evidence.supportLevel },
  ]
})

const adviceList = computed(() => props.predictionResult?.advice ?? props.selectedPatient?.careAdvice ?? [])

const suggestionConfidence = computed(() => {
  const score = topk.value[0]?.score
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

function runQuickTask() {
  if (!props.selectedPatient) return
  emit('create-outpatient-task', props.selectedPatient.patientId, {
    id: `quick-${Date.now()}`,
    category: 'recheck',
    title: '慢病复诊安排',
    owner: props.selectedPatient.caseManager || '随访护士',
    dueLabel: '1周内',
    priority: 'high',
    note: '医生工作台快捷创建',
  })
}
</script>

<template>
  <section class="clinic-workbench card">
    <aside class="workbench-column left-column">
      <header class="column-header">
        <p class="eyebrow">患者检索</p>
        <h3>待处理患者</h3>
      </header>

      <div class="filter-box">
        <input
          :value="props.searchText"
          type="text"
          placeholder="按患者ID/姓名/病种检索"
          @input="emit('update:search-text', ($event.target as HTMLInputElement).value)"
        />
        <select
          :value="props.riskFilter"
          @change="emit('update:risk-filter', ($event.target as HTMLSelectElement).value)"
        >
          <option v-for="risk in props.riskOptions" :key="risk" :value="risk">{{ risk }}</option>
        </select>
      </div>

      <div v-if="props.loadingPatients" class="empty-state">患者列表加载中...</div>

      <div v-else class="patient-list">
        <button
          v-for="patient in filteredPatients"
          :key="patient.patientId"
          class="patient-row"
          :class="{ active: selectedPatientId === patient.patientId }"
          @click="emit('open', patient.patientId)"
        >
          <div>
            <strong>{{ patient.name }}</strong>
            <p>{{ patient.patientId }} · {{ patient.primaryDisease }}</p>
          </div>
          <span class="risk-badge" :class="riskClass(patient.riskLevel)">{{ patient.riskLevel }}</span>
        </button>
      </div>
    </aside>

    <main class="workbench-column center-column">
      <header class="column-header">
        <p class="eyebrow">患者概览</p>
        <h3>当前患者信息</h3>
      </header>

      <div v-if="props.loadingPatient" class="empty-state">患者详情加载中...</div>
      <div v-else-if="!props.selectedPatient" class="empty-state">请从左侧选择患者</div>
      <template v-else>
        <section class="patient-core card-section">
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
              <span>最近就诊时间</span>
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
              <span>建议可信度</span>
              <strong>{{ suggestionConfidence }}</strong>
            </article>
          </div>
        </section>

        <section class="card-section">
          <h4>病程时间线</h4>
          <div class="timeline-list">
            <article v-for="(item, idx) in props.selectedPatient.timeline" :key="`${item.date}-${item.type}-${idx}`" class="timeline-item">
              <div class="timeline-date">{{ item.date }}</div>
              <div>
                <strong>{{ item.title }}</strong>
                <p>{{ item.detail }}</p>
              </div>
            </article>
          </div>
        </section>

        <section class="card-section">
          <h4>关键四元组</h4>
          <div v-if="!props.patientQuadruples.length" class="empty-state compact">暂无结构化四元组</div>
          <div v-else class="quadruple-table">
            <header>
              <span>关系</span>
              <span>对象</span>
              <span>时间</span>
            </header>
            <article v-for="(q, idx) in props.patientQuadruples" :key="`${q.relation}-${q.objectValue}-${idx}`">
              <span>{{ q.relationLabel || q.relation }}</span>
              <span>{{ q.objectValue }}</span>
              <span>{{ q.timestamp.slice(0, 10) }}</span>
            </article>
          </div>
        </section>
      </template>
    </main>

    <aside class="workbench-column right-column">
      <header class="column-header">
        <p class="eyebrow">AI 辅助</p>
        <h3>预测与建议</h3>
      </header>

      <section class="card-section">
        <div class="section-title-row">
          <h4>模型预测 Top-K</h4>
          <button class="secondary-button" :disabled="!props.selectedPatient || props.loadingPredict" @click="emit('predict')">
            {{ props.loadingPredict ? '预测中...' : '更新预测' }}
          </button>
        </div>

        <div v-if="!topk.length" class="empty-state compact">暂无预测结果</div>
        <div v-else class="topk-list">
          <article v-for="(item, idx) in topk" :key="`${item.label}-${idx}`">
            <strong>{{ idx + 1 }}. {{ item.label }}</strong>
            <span>{{ Math.round(item.score * 100) }}%</span>
            <p>{{ item.reason }}</p>
          </article>
        </div>
      </section>

      <section class="card-section">
        <h4>证据摘要</h4>
        <div v-if="!evidenceSummary" class="empty-state compact">请先执行预测以查看证据</div>
        <div v-else class="evidence-grid">
          <article v-for="item in evidenceSummary" :key="item.label">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </article>
        </div>
      </section>

      <section class="card-section">
        <h4>LLM 辅助建议</h4>
        <ul v-if="adviceList.length" class="advice-list">
          <li v-for="(advice, idx) in adviceList" :key="`${idx}-${advice}`">{{ advice }}</li>
        </ul>
        <div v-else class="empty-state compact">暂无建议</div>
      </section>

      <section class="card-section">
        <h4>下一步动作</h4>
        <div class="action-grid">
          <button class="primary-button" :disabled="!props.selectedPatient" @click="emit('open-followup', selectedPatientId)">
            进入随访工作台
          </button>
          <button class="secondary-button" :disabled="!props.selectedPatient" @click="emit('open-archive', selectedPatientId)">
            打开患者档案
          </button>
          <button class="secondary-button" :disabled="!props.selectedPatient" @click="runQuickTask">
            创建复诊任务
          </button>
          <button
            class="secondary-button"
            :disabled="!props.selectedPatient"
            @click="emit('update-encounter-status', selectedPatientId, 'pending_review')"
          >
            标记待复核
          </button>
        </div>
      </section>
    </aside>
  </section>
</template>

<style scoped>
.clinic-workbench {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 360px;
  gap: 14px;
  padding: 14px;
  border-radius: 16px;
  box-shadow: none;
}

.workbench-column {
  display: grid;
  gap: 12px;
  align-content: start;
}

.column-header h3 {
  margin: 2px 0 0;
  color: var(--navy);
  font-size: 1.02rem;
}

.filter-box {
  display: grid;
  gap: 8px;
}

.patient-list {
  display: grid;
  gap: 8px;
  max-height: 70vh;
  overflow: auto;
  padding-right: 2px;
}

.patient-row {
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  text-align: left;
}

.patient-row.active {
  border-color: #4f89be;
  box-shadow: 0 0 0 2px rgba(79, 137, 190, 0.12);
}

.patient-row p {
  margin: 4px 0 0;
  color: var(--ink-muted);
  font-size: 0.82rem;
}

.card-section {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  padding: 12px;
  display: grid;
  gap: 10px;
}

.card-section h4 {
  margin: 0;
  font-size: 0.96rem;
  color: var(--navy);
}

.patient-core-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}

.patient-core-head h4 {
  margin: 0;
}

.patient-core-head p {
  margin: 4px 0 0;
  color: var(--ink-muted);
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.meta-grid article {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #f8fafc;
  padding: 10px;
  display: grid;
  gap: 5px;
}

.meta-grid span {
  font-size: 0.78rem;
  color: var(--ink-muted);
}

.meta-grid strong {
  color: var(--navy);
}

.timeline-list {
  display: grid;
  gap: 8px;
}

.timeline-item {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px;
  background: #fafcfe;
}

.timeline-date {
  color: var(--ink-muted);
  font-size: 0.82rem;
}

.timeline-item p {
  margin: 4px 0 0;
  color: var(--ink-soft);
  font-size: 0.85rem;
}

.quadruple-table {
  display: grid;
  gap: 6px;
}

.quadruple-table header,
.quadruple-table article {
  display: grid;
  grid-template-columns: 1fr 1fr 110px;
  gap: 8px;
}

.quadruple-table header {
  color: var(--ink-muted);
  font-size: 0.78rem;
  padding: 0 2px;
}

.quadruple-table article {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px;
  font-size: 0.86rem;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.topk-list {
  display: grid;
  gap: 8px;
}

.topk-list article {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #f8fbff;
  padding: 10px;
  display: grid;
  gap: 4px;
}

.topk-list span {
  color: #205f98;
  font-weight: 600;
}

.topk-list p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 0.84rem;
}

.evidence-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.evidence-grid article {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px;
  background: #f8fafc;
  display: grid;
  gap: 4px;
}

.evidence-grid span {
  color: var(--ink-muted);
  font-size: 0.78rem;
}

.advice-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
}

.advice-list li {
  color: var(--ink-soft);
  font-size: 0.88rem;
}

.action-grid {
  display: grid;
  gap: 8px;
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: fit-content;
  padding: 4px 9px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
}

.risk-high {
  background: rgba(193, 74, 60, 0.14);
  color: #b03428;
}

.risk-medium {
  background: rgba(184, 122, 38, 0.16);
  color: #8d5c16;
}

.risk-low {
  background: rgba(23, 130, 93, 0.14);
  color: #16684b;
}

.empty-state {
  border: 1px dashed var(--border-strong);
  border-radius: 10px;
  color: var(--ink-muted);
  font-size: 0.86rem;
  padding: 14px;
  text-align: center;
}

.empty-state.compact {
  padding: 10px;
}

@media (max-width: 1400px) {
  .clinic-workbench {
    grid-template-columns: 1fr;
  }

  .patient-list {
    max-height: 260px;
  }
}

@media (max-width: 800px) {
  .timeline-item,
  .quadruple-table header,
  .quadruple-table article,
  .meta-grid,
  .evidence-grid {
    grid-template-columns: 1fr;
  }
}
</style>

