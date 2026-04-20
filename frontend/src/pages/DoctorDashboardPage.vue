<script setup lang="ts">
import { computed } from 'vue'
import type { PatientCase, PatientSummary } from '../services/types'

const props = defineProps<{
  allPatients: PatientSummary[]
  patients: PatientSummary[]
  selectedPatient: PatientCase | null
  loadingPatients: boolean
  loadingPatient: boolean
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
}>()

const selectedPatientId = computed(() => props.selectedPatient?.patientId ?? '')

const filteredPatients = computed(() => {
  if (props.patients.length) return props.patients

  const keyword = props.searchText.trim().toLowerCase()
  const risk = props.riskFilter
  const allRisk = !risk || props.riskOptions[0] === risk

  return props.allPatients.filter((patient) => {
    const matchRisk = allRisk || patient.riskLevel === risk
    const haystack = `${patient.patientId} ${patient.name} ${patient.primaryDisease}`.toLowerCase()
    return matchRisk && (!keyword || haystack.includes(keyword))
  })
})

const currentSummary = computed(() => {
  const patient = props.selectedPatient
  if (!patient) {
    return {
      title: '请选择患者',
      subtitle: '从左侧待处理列表打开一个慢病患者',
      summary: '请选择患者后查看档案、时间线、当前用药和建议摘要。',
      risk: '--',
      support: '--',
      stage: '--',
      lastVisit: '--',
      tasks: 0,
    }
  }

  return {
    title: patient.name,
    subtitle: `${patient.patientId} / ${patient.primaryDisease}`,
    summary: patient.summary || '暂无患者摘要。',
    risk: patient.riskLevel || '--',
    support: patient.dataSupport || '--',
    stage: patient.currentStage || '--',
    lastVisit: patient.lastVisit || '--',
    tasks: patient.outpatientTasks?.length ?? 0,
  }
})

const highRiskCount = computed(() => props.allPatients.filter((patient) => patient.riskLevel.toLowerCase().includes('high')).length)
const lowSupportCount = computed(() => props.allPatients.filter((patient) => patient.dataSupport === 'low').length)

const riskHint = computed(() => {
  const patient = props.selectedPatient
  if (!patient) return '先选择患者，再进入详情或随访闭环。'
  if (patient.riskLevel.toLowerCase().includes('high')) return '该患者处于高风险队列，建议优先查看病程时间线和随访任务。'
  if (patient.dataSupport === 'low') return '该患者数据支持不足，建议补齐档案或检查报告附件。'
  return '当前患者基础信息较完整，可进入详情页查看模型摘要和用药评估。'
})

function riskClass(level: string) {
  const raw = (level || '').toLowerCase()
  if (raw.includes('high')) return 'risk-high'
  if (raw.includes('medium')) return 'risk-medium'
  return 'risk-low'
}

function dataSupportLabel(value?: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value || '--'
}

function handleOpenDetail() {
  if (!selectedPatientId.value) return
  emit('open-detail', selectedPatientId.value)
}
</script>

<template>
  <section class="doctor-home-page workstation-page">
    <section v-if="noPermission" class="empty-state-card">
      <h3>无权限访问医生工作台</h3>
      <p>当前账号没有医生首页访问权限，请从左侧选择可访问模块。</p>
    </section>

    <template v-else>
      <header class="workstation-page-header">
        <div>
          <p class="eyebrow">Doctor workstation</p>
          <h1>医生工作台</h1>
          <p>待处理患者、风险摘要和主要临床动作。</p>
        </div>
        <div class="header-metrics">
          <article>
            <span>患者档案</span>
            <strong>{{ allPatients.length }}</strong>
          </article>
          <article>
            <span>高风险</span>
            <strong>{{ highRiskCount }}</strong>
          </article>
          <article>
            <span>待补全</span>
            <strong>{{ lowSupportCount }}</strong>
          </article>
        </div>
      </header>

      <section class="doctor-workbench-grid">
        <aside class="clinical-card queue-panel">
          <div class="section-header">
            <div>
              <h2>待处理患者</h2>
              <p>{{ filteredPatients.length }} 条记录</p>
            </div>
          </div>

          <div class="filter-card">
            <label>
              <span>检索患者</span>
              <input
                :value="searchText"
                type="text"
                placeholder="姓名 / 患者ID / 疾病"
                @input="emit('update:search-text', ($event.target as HTMLInputElement).value)"
              />
            </label>
            <label>
              <span>风险筛选</span>
              <select
                :value="riskFilter"
                @change="emit('update:risk-filter', ($event.target as HTMLSelectElement).value)"
              >
                <option v-for="risk in riskOptions" :key="risk" :value="risk">{{ risk }}</option>
              </select>
            </label>
          </div>

          <div v-if="loadingPatients" class="empty-state-card compact">正在加载患者队列...</div>
          <div v-else-if="!filteredPatients.length" class="empty-state-card compact">暂无符合条件的患者。</div>

          <div v-else class="queue-list">
            <button
              v-for="patient in filteredPatients"
              :key="patient.patientId"
              type="button"
              class="queue-row"
              :class="{ active: selectedPatientId === patient.patientId }"
              @click="emit('open', patient.patientId)"
            >
              <span>
                <strong>{{ patient.name }}</strong>
                <small>{{ patient.patientId }} / {{ patient.primaryDisease }}</small>
              </span>
              <span class="risk-badge" :class="riskClass(patient.riskLevel)">{{ patient.riskLevel }}</span>
            </button>
          </div>
        </aside>

        <main class="clinical-card patient-summary-panel">
          <div class="section-header">
            <div>
              <h2>当前患者摘要</h2>
              <p>临床入口信息。</p>
            </div>
            <span class="risk-badge" :class="riskClass(currentSummary.risk)">{{ currentSummary.risk }}</span>
          </div>

          <div v-if="loadingPatient" class="empty-state-card">正在加载患者摘要...</div>
          <template v-else>
            <div class="patient-title-block">
              <h3>{{ currentSummary.title }}</h3>
              <p>{{ currentSummary.subtitle }}</p>
            </div>

            <div class="summary-grid">
              <article>
                <span>最近就诊</span>
                <strong>{{ currentSummary.lastVisit }}</strong>
              </article>
              <article>
                <span>当前阶段</span>
                <strong>{{ currentSummary.stage }}</strong>
              </article>
              <article>
                <span>数据支持</span>
                <strong>{{ dataSupportLabel(currentSummary.support) }}</strong>
              </article>
              <article>
                <span>任务数</span>
                <strong>{{ currentSummary.tasks }}</strong>
              </article>
            </div>

            <div class="summary-note">
              <strong>摘要</strong>
              <p>{{ currentSummary.summary }}</p>
            </div>

            <div class="summary-note warning">
              <strong>风险提示</strong>
              <p>{{ riskHint }}</p>
            </div>
          </template>
        </main>

        <aside class="clinical-card action-panel">
          <div class="section-header">
            <div>
              <h2>主动作</h2>
              <p>进入独立业务页处理。</p>
            </div>
          </div>
          <button class="primary-button" :disabled="!selectedPatientId || loadingPatient" type="button" @click="handleOpenDetail">
            打开患者详情
          </button>
          <button
            class="secondary-button"
            :disabled="!selectedPatientId || loadingPatient"
            type="button"
            @click="emit('open-followup', { patientId: selectedPatientId, section: 'tasks' })"
          >
            打开随访任务
          </button>
          <button
            class="secondary-button"
            :disabled="!selectedPatientId || loadingPatient"
            type="button"
            @click="emit('open-archive', { patientId: selectedPatientId, focus: 'overview' })"
          >
            打开患者档案
          </button>
        </aside>
      </section>
    </template>
  </section>
</template>

<style scoped>
.doctor-home-page {
  display: grid;
  gap: 24px;
}

.doctor-workbench-grid {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr) 280px;
  gap: 24px;
  align-items: start;
}

.queue-panel,
.patient-summary-panel,
.action-panel {
  display: grid;
  gap: 16px;
}

.filter-card {
  display: grid;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: var(--ws-surface-soft);
}

.filter-card label {
  display: grid;
  gap: 6px;
}

.filter-card span {
  color: var(--ws-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.queue-list {
  display: grid;
  gap: 8px;
  max-height: 580px;
  overflow: auto;
}

.queue-row {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: #fff;
  padding: 12px;
  text-align: left;
}

.queue-row:hover,
.queue-row.active {
  border-color: var(--ws-primary);
  background: var(--ws-primary-soft);
}

.queue-row span:first-child {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.queue-row small {
  color: var(--ws-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.patient-title-block h3,
.patient-title-block p,
.summary-note p {
  margin: 0;
}

.patient-title-block h3 {
  font-size: 18px;
}

.patient-title-block p,
.summary-note p {
  color: var(--ws-text-muted);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-grid article,
.summary-note {
  display: grid;
  gap: 6px;
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: var(--ws-surface-soft);
  padding: 12px;
}

.summary-grid span,
.summary-note strong {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.summary-grid strong {
  color: var(--ws-title);
  font-size: 16px;
}

.summary-note.warning {
  border-color: var(--ws-warning-border);
  background: var(--ws-warning-soft);
}

.action-panel .primary-button,
.action-panel .secondary-button {
  width: 100%;
}

@media (max-width: 1280px) {
  .doctor-workbench-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
