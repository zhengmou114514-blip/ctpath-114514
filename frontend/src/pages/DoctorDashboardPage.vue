<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRight, View } from '@element-plus/icons-vue'
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

const highRiskCount = computed(() => props.allPatients.filter((patient) => patient.riskLevel.toLowerCase().includes('high')).length)
const followupCount = computed(() => props.allPatients.filter((patient) => patient.summary.toLowerCase().includes('follow')).length)
const modelCoverage = computed(() => {
  if (!props.allPatients.length) return '0%'
  const readyCount = props.allPatients.filter((patient) => patient.dataSupport !== 'low').length
  return `${Math.round((readyCount / props.allPatients.length) * 1000) / 10}%`
})

const alertCards = computed(() =>
  filteredPatients.value.slice(0, 3).map((patient, index) => {
    const isHigh = patient.riskLevel.toLowerCase().includes('high')
    return {
      patientId: patient.patientId,
      tone: isHigh ? 'critical' : index === 1 ? 'warning' : 'info',
      title: isHigh ? '高风险预警' : index === 1 ? '随访提醒' : '档案提示',
      headline: `${patient.patientId} · ${patient.name}`,
      body: patient.summary || `${patient.primaryDisease} 需要继续关注近期病程变化。`,
      action: isHigh ? '进入详情' : index === 1 ? '安排随访' : '打开档案',
    }
  })
)

function riskClass(level: string) {
  const raw = (level || '').toLowerCase()
  if (raw.includes('high')) return 'risk-high'
  if (raw.includes('medium')) return 'risk-medium'
  return 'risk-low'
}

function openPatientDetail(patientId: string) {
  emit('open', patientId)
  emit('open-detail', patientId)
}
</script>

<template>
  <section class="doctor-dashboard-page workstation-page">
    <section v-if="noPermission" class="empty-state-card">
      <h3>当前账号没有医生工作台权限</h3>
      <p>请切换到具备医生角色的账号，或从左侧导航进入你当前角色可以访问的模块。</p>
    </section>

    <template v-else>
      <section class="dashboard-metrics">
        <article class="metric-panel clinical-card">
          <p class="eyebrow">患者总量</p>
          <strong>{{ allPatients.length }}</strong>
          <span>当前工作台可见患者</span>
        </article>

        <article class="metric-panel clinical-card accent-warm">
          <p class="eyebrow">重点处理</p>
          <strong>{{ highRiskCount + followupCount }}</strong>
          <span>{{ highRiskCount }} 位高风险，{{ followupCount }} 位待随访</span>
        </article>

        <article class="metric-panel clinical-card accent-cool">
          <p class="eyebrow">模型覆盖率</p>
          <strong>{{ modelCoverage }}</strong>
          <span>按当前患者数据支持度估算</span>
        </article>
      </section>

      <section class="dashboard-grid">
        <main class="queue-panel clinical-card">
          <div class="queue-header">
            <div>
              <p class="eyebrow">患者队列</p>
              <h2>待处理患者</h2>
              <p>保持 Stitch 的工作站结构，只保留当前医生主流程需要的患者队列和入口动作。</p>
            </div>
            <div class="queue-toolbar">
              <input
                :value="searchText"
                type="text"
                placeholder="搜索患者编号、姓名或主诊断..."
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

          <div v-if="loadingPatients" class="empty-state-card">正在载入患者队列...</div>
          <div v-else-if="!filteredPatients.length" class="empty-state-card">当前筛选条件下没有可显示的患者。</div>

          <table v-else class="queue-table">
            <thead>
              <tr>
                <th>患者编号</th>
                <th>患者信息</th>
                <th>风险等级</th>
                <th>最近就诊</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="patient in filteredPatients"
                :key="patient.patientId"
                :class="{ selected: selectedPatientId === patient.patientId }"
                @click="emit('open', patient.patientId)"
              >
                <td>{{ patient.patientId }}</td>
                <td>
                  <div class="patient-cell">
                    <strong>{{ patient.name }}</strong>
                    <small>{{ patient.primaryDisease }}</small>
                  </div>
                </td>
                <td>
                  <span class="risk-pill" :class="riskClass(patient.riskLevel)">{{ patient.riskLevel }}</span>
                </td>
                <td>{{ patient.lastVisit || '--' }}</td>
                <td>
                  <div class="row-actions">
                    <button class="icon-action" type="button" :disabled="loadingPatient" @click.stop="openPatientDetail(patient.patientId)">
                      <el-icon><View /></el-icon>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </main>

        <aside class="alerts-panel">
          <div class="alerts-header">
            <div>
              <p class="eyebrow">风险提醒</p>
              <h2>临床提示</h2>
            </div>
            <button type="button" class="text-link">查看全部 <el-icon><ArrowRight /></el-icon></button>
          </div>

          <article
            v-for="alert in alertCards"
            :key="alert.patientId"
            class="clinical-card alert-card"
            :class="`alert-${alert.tone}`"
          >
            <span class="alert-title">{{ alert.title }}</span>
            <strong>{{ alert.headline }}</strong>
            <p>{{ alert.body }}</p>
            <button type="button" class="text-link" @click="openPatientDetail(alert.patientId)">{{ alert.action }}</button>
          </article>

          <article v-if="selectedPatient" class="clinical-card alert-card alert-selected">
            <span class="alert-title">当前聚焦患者</span>
            <strong>{{ selectedPatient.name }}</strong>
            <p>{{ selectedPatient.summary }}</p>
            <div class="focus-actions">
              <button class="secondary-button" type="button" @click="emit('open-archive', { patientId: selectedPatient.patientId, focus: 'overview' })">
                打开档案
              </button>
              <button class="primary-button" type="button" @click="emit('open-followup', { patientId: selectedPatient.patientId, section: 'tasks' })">
                安排随访
              </button>
            </div>
          </article>
        </aside>
      </section>
    </template>
  </section>
</template>

<style scoped>
.doctor-dashboard-page {
  gap: 26px;
}

.dashboard-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.metric-panel {
  position: relative;
  overflow: hidden;
  display: grid;
  gap: 14px;
  min-height: 176px;
}

.metric-panel::after {
  content: '';
  position: absolute;
  width: 120px;
  height: 120px;
  top: 0;
  right: 0;
  border-radius: 0 0 0 36px;
  background: rgba(207, 230, 242, 0.45);
}

.metric-panel.accent-warm::after {
  background: rgba(255, 219, 201, 0.55);
}

.metric-panel.accent-cool::after {
  background: rgba(168, 239, 244, 0.34);
}

.metric-panel strong {
  position: relative;
  z-index: 1;
  font-family: var(--ws-font-headline);
  font-size: clamp(44px, 5vw, 58px);
  line-height: 1;
}

.metric-panel span {
  position: relative;
  z-index: 1;
  color: rgba(24, 28, 29, 0.72);
  font-size: 15px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) 320px;
  gap: 20px;
  align-items: start;
}

.queue-panel,
.alerts-panel {
  min-width: 0;
  display: grid;
  gap: 18px;
}

.queue-header,
.alerts-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.queue-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.queue-toolbar input {
  min-width: 280px;
}

.queue-toolbar select {
  min-width: 168px;
}

.queue-table tbody tr.selected td {
  background: rgba(241, 244, 245, 0.98);
}

.patient-cell {
  display: grid;
  gap: 4px;
}

.patient-cell small {
  color: rgba(63, 72, 73, 0.74);
}

.row-actions {
  display: flex;
  justify-content: center;
}

.icon-action {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 12px;
  background: rgba(168, 239, 244, 0.45);
  color: var(--ws-primary);
}

.alert-card {
  display: grid;
  gap: 12px;
  min-height: 168px;
  border-left: 4px solid transparent;
}

.alert-title {
  color: rgba(24, 28, 29, 0.7);
  font-family: var(--ws-font-headline);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.alert-card p {
  margin: 0;
  color: rgba(63, 72, 73, 0.84);
  line-height: 1.55;
}

.alert-critical {
  border-left-color: var(--ws-error);
}

.alert-warning {
  border-left-color: var(--ws-tertiary);
}

.alert-info,
.alert-selected {
  border-left-color: var(--ws-primary);
}

.focus-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 1240px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .dashboard-metrics {
    grid-template-columns: 1fr;
  }

  .queue-header {
    display: grid;
  }

  .queue-toolbar {
    display: grid;
  }

  .queue-toolbar input,
  .queue-toolbar select {
    min-width: 0;
  }
}
</style>
