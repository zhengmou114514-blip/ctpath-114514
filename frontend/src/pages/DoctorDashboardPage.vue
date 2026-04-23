<script setup lang="ts">
import { computed } from 'vue'
import { View } from '@element-plus/icons-vue'
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

const previewPatients = computed(() => filteredPatients.value.slice(0, 5))

const highRiskCount = computed(() => props.allPatients.filter((patient) => patient.riskLevel.toLowerCase().includes('high')).length)
const followupCount = computed(() => props.allPatients.filter((patient) => patient.summary.toLowerCase().includes('follow')).length)
const modelCoverage = computed(() => {
  if (!props.allPatients.length) return '0%'
  const readyCount = props.allPatients.filter((patient) => patient.dataSupport !== 'low').length
  return `${Math.round((readyCount / props.allPatients.length) * 1000) / 10}%`
})

const focusPatient = computed(() => props.selectedPatient ?? previewPatients.value[0] ?? null)

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
          <span>当前工作台可见患者数量</span>
        </article>

        <article class="metric-panel clinical-card accent-warm">
          <p class="eyebrow">重点处理</p>
          <strong>{{ highRiskCount + followupCount }}</strong>
          <span>{{ highRiskCount }} 位高风险，{{ followupCount }} 位待随访</span>
        </article>

        <article class="metric-panel clinical-card accent-cool">
          <p class="eyebrow">模型覆盖</p>
          <strong>{{ modelCoverage }}</strong>
          <span>按当前患者数据支持度估算</span>
        </article>
      </section>

      <section class="dashboard-grid">
        <main class="summary-panel clinical-card">
          <div class="panel-header">
            <div>
              <p class="eyebrow">今日摘要</p>
              <h2>待处理患者入口</h2>
              <p>医生首页只保留摘要、筛选和少量主入口，不堆叠治理页或完整模型页内容。</p>
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

          <div v-if="loadingPatients" class="empty-state-card">正在加载患者摘要...</div>
          <div v-else-if="!previewPatients.length" class="empty-state-card">当前筛选条件下没有可展示的患者。</div>

          <div v-else class="patient-brief-list">
            <article
              v-for="patient in previewPatients"
              :key="patient.patientId"
              class="patient-brief-card clinical-card"
              :class="{ selected: selectedPatientId === patient.patientId }"
              @click="emit('open', patient.patientId)"
            >
              <div class="patient-brief-main">
                <div class="brief-head">
                  <strong>{{ patient.name }}</strong>
                  <span class="risk-pill" :class="riskClass(patient.riskLevel)">{{ patient.riskLevel }}</span>
                </div>
                <small>{{ patient.patientId }} · {{ patient.primaryDisease }}</small>
                <p>{{ patient.summary }}</p>
              </div>

              <div class="brief-actions">
                <button class="secondary-button" type="button" :disabled="loadingPatient" @click.stop="openPatientDetail(patient.patientId)">
                  <el-icon><View /></el-icon>
                  <span>查看详情</span>
                </button>
                <button
                  class="ghost-button"
                  type="button"
                  @click.stop="emit('open-archive', { patientId: patient.patientId, focus: 'overview' })"
                >
                  档案
                </button>
                <button
                  class="ghost-button"
                  type="button"
                  @click.stop="emit('open-followup', { patientId: patient.patientId, section: 'tasks' })"
                >
                  随访
                </button>
              </div>
            </article>
          </div>
        </main>

        <aside class="action-panel">
          <article class="clinical-card spotlight-card" v-if="focusPatient">
            <p class="eyebrow">当前关注患者</p>
            <strong>{{ focusPatient.name }}</strong>
            <span>{{ focusPatient.patientId }} · {{ focusPatient.primaryDisease }}</span>
            <p>{{ focusPatient.summary }}</p>
            <div class="spotlight-actions">
              <button class="primary-button" type="button" @click="openPatientDetail(focusPatient.patientId)">进入详情</button>
              <button
                class="secondary-button"
                type="button"
                @click="emit('open-archive', { patientId: focusPatient.patientId, focus: 'overview' })"
              >
                打开档案
              </button>
            </div>
          </article>

          <article class="clinical-card shortcut-card">
            <p class="eyebrow">主动作入口</p>
            <div class="shortcut-list">
              <button type="button" class="shortcut-button" @click="emit('open-followup', { patientId: previewPatients[0]?.patientId ?? '', section: 'tasks' })">
                随访工作台
              </button>
              <button type="button" class="shortcut-button" @click="emit('open-archive', { patientId: previewPatients[0]?.patientId ?? '', focus: 'overview' })">
                患者档案
              </button>
              <button type="button" class="shortcut-button" @click="previewPatients[0] && openPatientDetail(previewPatients[0].patientId)">
                患者详情
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
  grid-template-columns: minmax(0, 1.6fr) 320px;
  gap: 20px;
  align-items: start;
}

.summary-panel,
.action-panel {
  min-width: 0;
  display: grid;
  gap: 18px;
}

.panel-header {
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

.patient-brief-list {
  display: grid;
  gap: 12px;
}

.patient-brief-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  cursor: pointer;
}

.patient-brief-card.selected {
  border-color: rgba(0, 92, 97, 0.35);
  box-shadow: 0 0 0 1px rgba(0, 92, 97, 0.16) inset;
}

.patient-brief-main {
  display: grid;
  gap: 8px;
}

.brief-head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.patient-brief-main strong {
  font-size: 18px;
}

.patient-brief-main small {
  color: rgba(63, 72, 73, 0.72);
}

.patient-brief-main p {
  margin: 0;
  color: rgba(63, 72, 73, 0.88);
  line-height: 1.55;
}

.brief-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.brief-actions button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.spotlight-card {
  display: grid;
  gap: 12px;
}

.spotlight-card strong {
  font-family: var(--ws-font-headline);
  font-size: 26px;
}

.spotlight-card span {
  color: rgba(63, 72, 73, 0.76);
}

.spotlight-card p {
  margin: 0;
  color: rgba(63, 72, 73, 0.88);
  line-height: 1.55;
}

.spotlight-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.shortcut-card {
  display: grid;
  gap: 12px;
}

.shortcut-list {
  display: grid;
  gap: 10px;
}

.shortcut-button {
  min-height: 44px;
  border: 0;
  border-radius: 12px;
  background: rgba(241, 244, 245, 0.95);
  color: #004347;
  font-family: var(--ws-font-headline);
  font-weight: 800;
  text-align: left;
  padding: 0 16px;
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

  .panel-header {
    display: grid;
  }

  .queue-toolbar {
    display: grid;
  }

  .queue-toolbar input,
  .queue-toolbar select {
    min-width: 0;
  }

  .patient-brief-card {
    grid-template-columns: 1fr;
  }
}
</style>
