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

        <!-- 优化后的患者列表：表格形式 -->
        <section v-else class="patient-table-container">
          <table class="patient-table">
            <thead>
              <tr>
                <th>姓名</th>
                <th>患者ID</th>
                <th>主诊断</th>
                <th>风险等级</th>
                <th>最近就诊</th>
                <th>预测状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="patient in filteredPatients"
                :key="patient.patientId"
                :class="{ active: selectedPatientId === patient.patientId }"
                @click="emit('open', patient.patientId)"
              >
                <td class="patient-name">
                  <strong>{{ patient.name }}</strong>
                </td>
                <td class="patient-id">{{ patient.patientId }}</td>
                <td class="patient-disease">{{ patient.primaryDisease }}</td>
                <td class="patient-risk">
                  <span class="risk-badge" :class="riskClass(patient.riskLevel)">
                    {{ patient.riskLevel }}
                  </span>
                </td>
                <td class="patient-visit">{{ patient.lastVisit || '--' }}</td>
                <td class="patient-prediction">
                  <span class="prediction-status">已预测</span>
                </td>
                <td class="patient-actions">
                  <button class="table-action-btn" @click.stop="emit('open', patient.patientId)">
                    查看
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
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
              {{ props.loadingOpenArchive ? '打开中...' : '打开患者详情' }}
            </button>
            <button class="primary-button" :disabled="!props.selectedPatient || props.loadingOpenFollowup" @click="emit('open-followup', selectedPatientId)">
              {{ props.loadingOpenFollowup ? '进入中...' : '进入随访工作台' }}
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
  gap: 16px;
  padding: 16px;
  background: #f5f8fc;
  min-height: 100vh;
}

.workbench-column {
  display: grid;
  gap: 14px;
  align-content: start;
}

.column-header {
  padding: 12px 16px;
  background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(30, 58, 95, 0.15);
}

.column-header .eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 500;
  color: #bee3f8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.column-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.surface-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  padding: 16px;
  display: grid;
  gap: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.2s ease;
}

.surface-card:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.queue-filter-card {
  gap: 10px;
}

.queue-filter-card label {
  display: grid;
  gap: 6px;
}

.queue-filter-card span {
  font-size: 13px;
  font-weight: 500;
  color: #4a5568;
}

.queue-filter-card input,
.queue-filter-card select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.queue-filter-card input:focus,
.queue-filter-card select:focus {
  outline: none;
  border-color: #3182ce;
  box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
}

.queue-list {
  display: grid;
  gap: 10px;
  max-height: 68vh;
  overflow: auto;
  padding-right: 4px;
}

.queue-list::-webkit-scrollbar {
  width: 6px;
}

.queue-list::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.queue-list::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.queue-list::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

.queue-row {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  text-align: left;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.queue-row:hover {
  border-color: #bee3f8;
  box-shadow: 0 2px 8px rgba(49, 130, 206, 0.15);
  transform: translateY(-1px);
}

.queue-row.active {
  border-color: #3182ce;
  box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.2);
  background: #f7fafc;
}

.queue-main strong {
  display: block;
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 4px;
}

.queue-main p {
  margin: 0 0 4px;
  font-size: 13px;
  color: #718096;
}

.queue-main small {
  display: block;
  font-size: 12px;
  color: #a0aec0;
}

.patient-summary-card {
  gap: 14px;
}

.patient-core-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.patient-core-head h4 {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 600;
  color: #1a202c;
}

.patient-core-head p {
  margin: 0;
  font-size: 14px;
  color: #718096;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.meta-grid article {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f7fafc;
  padding: 12px;
  display: grid;
  gap: 4px;
}

.meta-grid article span {
  font-size: 12px;
  color: #a0aec0;
  font-weight: 500;
}

.meta-grid article strong {
  font-size: 16px;
  color: #2d3748;
  font-weight: 600;
}

.summary-brief {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  background: #fffaf0;
}

.summary-brief span {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #975a16;
  margin-bottom: 6px;
}

.summary-brief p {
  margin: 0;
  font-size: 14px;
  color: #744210;
  line-height: 1.5;
}

.key-events-card {
  gap: 12px;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.section-title-row h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
}

.compact-note {
  font-size: 12px;
  color: #a0aec0;
}

.event-list {
  display: grid;
  gap: 10px;
}

.event-row {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px;
  background: #f7fafc;
}

.event-date {
  font-size: 12px;
  font-weight: 600;
  color: #4a5568;
  padding-top: 2px;
}

.event-row strong {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 4px;
}

.event-row p {
  margin: 0;
  font-size: 13px;
  color: #718096;
  line-height: 1.4;
}

.prediction-card {
  gap: 12px;
}

.prediction-card h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
}

.prediction-result {
  border: 1px solid #c6f6d5;
  border-radius: 8px;
  background: #f0fff4;
  padding: 12px;
  display: grid;
  gap: 6px;
}

.prediction-result strong {
  font-size: 16px;
  font-weight: 600;
  color: #22543d;
}

.prediction-result span {
  font-size: 13px;
  color: #48bb78;
  font-weight: 500;
}

.prediction-result p {
  margin: 4px 0;
  font-size: 14px;
  color: #2f855a;
  line-height: 1.5;
}

.prediction-result small {
  display: block;
  font-size: 12px;
  color: #68d391;
  margin-top: 4px;
}

.advice-card {
  gap: 12px;
}

.advice-card h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
}

.advice-summary-list {
  margin: 0;
  padding-left: 20px;
  display: grid;
  gap: 8px;
}

.advice-summary-list li {
  font-size: 14px;
  color: #4a5568;
  line-height: 1.5;
}

.action-card {
  gap: 12px;
}

.action-card h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
}

.action-grid {
  display: grid;
  gap: 10px;
}

.primary-button {
  width: 100%;
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #2b6cb0 0%, #3182ce 100%);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(49, 130, 206, 0.3);
}

.primary-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #2c5282 0%, #2b6cb0 100%);
  box-shadow: 0 4px 8px rgba(49, 130, 206, 0.4);
  transform: translateY(-1px);
}

.primary-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(49, 130, 206, 0.3);
}

.primary-button:disabled {
  background: #cbd5e0;
  cursor: not-allowed;
  box-shadow: none;
}

.secondary-button {
  padding: 8px 16px;
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #4a5568;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
}

.secondary-button:hover:not(:disabled) {
  border-color: #3182ce;
  color: #3182ce;
  background: #f7fafc;
}

.secondary-button:disabled {
  color: #cbd5e0;
  cursor: not-allowed;
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.risk-high {
  background: #fed7d7;
  color: #c53030;
  border: 1px solid #fc8181;
}

.risk-medium {
  background: #feebc8;
  color: #c05621;
  border: 1px solid #f6ad55;
}

.risk-low {
  background: #c6f6d5;
  color: #276749;
  border: 1px solid #68d391;
}

.empty-state {
  border: 2px dashed #cbd5e0;
  border-radius: 10px;
  color: #a0aec0;
  padding: 20px;
  text-align: center;
  background: #f7fafc;
  font-size: 14px;
}

.empty-state.compact {
  padding: 12px;
  font-size: 13px;
}

@media (max-width: 1360px) {
  .doctor-clinic-workbench {
    grid-template-columns: 1fr;
    padding: 12px;
  }
}

@media (max-width: 820px) {
  .meta-grid,
  .event-row {
    grid-template-columns: 1fr;
  }

  .column-header {
    padding: 10px 12px;
  }

  .column-header h3 {
    font-size: 16px;
  }

  .surface-card {
    padding: 12px;
  }
}
</style>
