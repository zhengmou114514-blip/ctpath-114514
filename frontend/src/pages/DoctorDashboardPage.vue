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
  const risk = props.riskFilter
  const keyword = props.searchText.trim().toLowerCase()
  const isAllRisk = props.riskOptions[0] === risk
  return props.allPatients.filter((item) => {
    const matchRisk = !risk || isAllRisk || item.riskLevel === risk
    const haystack = `${item.patientId} ${item.name} ${item.primaryDisease}`.toLowerCase()
    return matchRisk && (!keyword || haystack.includes(keyword))
  })
})

const currentSummary = computed(() => {
  const patient = props.selectedPatient
  if (!patient) {
    return {
      title: '请选择一位患者',
      subtitle: '当前患者摘要会显示在这里。',
      summary: '先从待处理患者列表中选择一位患者。',
      risk: '--',
      support: '--',
      stage: '--',
      lastVisit: '--',
    }
  }

  return {
    title: patient.name,
    subtitle: `${patient.patientId} · ${patient.primaryDisease}`,
    summary: patient.summary || '暂无患者摘要。',
    risk: patient.riskLevel || '--',
    support: patient.dataSupport || '--',
    stage: patient.currentStage || '--',
    lastVisit: patient.lastVisit || '--',
  }
})

const riskHint = computed(() => {
  const patient = props.selectedPatient
  if (!patient) return '请先选择患者以查看风险提示。'
  if (patient.riskLevel.toLowerCase().includes('high')) {
    return '高风险患者，请优先处理。'
  }
  if (patient.dataSupport === 'low') {
    return '当前患者数据支持偏弱，请结合时间线与病程一起判断。'
  }
  return '当前患者风险可关注，建议继续随访。'
})

function riskClass(level: string) {
  const raw = level.toLowerCase()
  if (raw.includes('high') || level.includes('高')) return 'risk-high'
  if (raw.includes('medium') || level.includes('中')) return 'risk-medium'
  return 'risk-low'
}

function dataSupportLabel(value?: string) {
  if (!value) return '--'
  if (value === 'high') return '强'
  if (value === 'medium') return '中'
  if (value === 'low') return '弱'
  return value
}

function handleOpenDetail() {
  if (!selectedPatientId.value) return
  emit('open-detail', selectedPatientId.value)
}
</script>

<template>
  <section class="doctor-home-page">
    <div v-if="props.noPermission" class="card empty-state">
      当前角色没有访问医生首页的权限。
    </div>

    <template v-else>
      <aside class="column panel">
        <header class="column-header">
          <p class="eyebrow">待处理患者</p>
          <h3>患者队列</h3>
        </header>

        <section class="surface-card filter-card">
          <label>
            <span>搜索患者</span>
            <input
              :value="props.searchText"
              type="text"
              placeholder="按姓名、ID 或疾病搜索"
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

        <div v-if="props.loadingPatients" class="card empty-state compact">正在加载患者列表...</div>
        <div v-else-if="!filteredPatients.length" class="card empty-state compact">暂无待处理患者。</div>

        <section v-else class="queue-table card">
          <table>
            <thead>
              <tr>
                <th>患者</th>
                <th>风险</th>
                <th>最近就诊</th>
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
                <td>
                  <strong>{{ patient.name }}</strong>
                  <p>{{ patient.patientId }} · {{ patient.primaryDisease }}</p>
                </td>
                <td>
                  <span class="risk-badge" :class="riskClass(patient.riskLevel)">{{ patient.riskLevel }}</span>
                </td>
                <td>{{ patient.lastVisit || '--' }}</td>
                <td>
                  <button class="secondary-button" @click.stop="emit('open', patient.patientId)">选中</button>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </aside>

      <main class="column panel">
        <header class="column-header">
          <p class="eyebrow">当前患者摘要</p>
          <h3>首页摘要卡</h3>
        </header>

        <div v-if="props.loadingPatient" class="card empty-state">正在加载当前患者...</div>
        <template v-else>
          <section class="surface-card summary-card">
            <div class="summary-head">
              <div>
                <h4>{{ currentSummary.title }}</h4>
                <p>{{ currentSummary.subtitle }}</p>
              </div>
              <span class="risk-badge" :class="riskClass(currentSummary.risk)">{{ currentSummary.risk }}</span>
            </div>

            <div class="summary-grid">
              <article>
                <span>最近就诊</span>
                <strong>{{ currentSummary.lastVisit }}</strong>
              </article>
              <article>
                <span>当前病程</span>
                <strong>{{ currentSummary.stage }}</strong>
              </article>
              <article>
                <span>数据支持</span>
                <strong>{{ dataSupportLabel(currentSummary.support) }}</strong>
              </article>
            </div>

            <div class="summary-text">
              <span>摘要</span>
              <p>{{ currentSummary.summary }}</p>
            </div>
          </section>

          <section class="surface-card risk-card">
            <h4>风险提示</h4>
            <p>{{ riskHint }}</p>
          </section>
        </template>
      </main>

      <aside class="column panel">
        <header class="column-header">
          <p class="eyebrow">快捷入口</p>
          <h3>常用动作</h3>
        </header>

        <section class="surface-card shortcut-card">
          <button class="primary-button" :disabled="!selectedPatientId || props.loadingPatient" @click="handleOpenDetail">
            查看患者详情
          </button>
          <button
            class="secondary-button"
            :disabled="!selectedPatientId || props.loadingPatient"
            @click="emit('open-followup', { patientId: selectedPatientId, section: 'tasks' })"
          >
            进入随访
          </button>
          <button
            class="secondary-button"
            :disabled="!selectedPatientId || props.loadingPatient"
            @click="emit('open-archive', { patientId: selectedPatientId, focus: 'overview' })"
          >
            打开档案
          </button>
        </section>
      </aside>
    </template>
  </section>
</template>

<style scoped>
.doctor-home-page {
  display: grid;
  grid-template-columns: 330px minmax(0, 1fr) 280px;
  gap: 16px;
  padding: 16px;
  background: #f5f8fc;
  min-height: 100%;
}

.column {
  display: grid;
  gap: 14px;
  align-content: start;
}

.panel {
  min-width: 0;
}

.column-header {
  padding: 12px 16px;
  border-radius: 10px;
  background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
  color: #fff;
}

.column-header h3,
.column-header .eyebrow {
  margin: 0;
}

.column-header h3 {
  font-size: 18px;
}

.eyebrow {
  font-size: 12px;
  opacity: 0.85;
  margin-bottom: 4px;
}

.surface-card,
.empty-state {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
  padding: 16px;
  display: grid;
  gap: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.filter-card label {
  display: grid;
  gap: 6px;
}

.filter-card span {
  font-size: 13px;
  color: #4a5568;
  font-weight: 600;
}

.filter-card input,
.filter-card select {
  border: 1px solid #cbd5e0;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 14px;
}

.queue-table {
  padding: 0;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  text-align: left;
  padding: 12px 14px;
  border-bottom: 1px solid #eef2f7;
  vertical-align: middle;
}

th {
  font-size: 12px;
  color: #5f758b;
  background: #f8fbff;
}

td strong,
.summary-head h4 {
  color: #17324d;
}

td p {
  margin: 4px 0 0;
  color: #60778e;
  font-size: 12px;
}

tbody tr {
  cursor: pointer;
}

tbody tr:hover {
  background: #f8fbff;
}

tbody tr.active {
  background: #edf5ff;
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.risk-high {
  background: #fed7d7;
  color: #c53030;
}

.risk-medium {
  background: #feebc8;
  color: #c05621;
}

.risk-low {
  background: #c6f6d5;
  color: #276749;
}

.summary-card {
  gap: 14px;
}

.summary-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.summary-head h4 {
  margin: 0 0 4px;
  font-size: 20px;
}

.summary-head p {
  margin: 0;
  color: #60778e;
  font-size: 13px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.summary-grid article {
  display: grid;
  gap: 4px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f7fafc;
  padding: 12px;
}

.summary-grid span,
.summary-text span {
  font-size: 12px;
  color: #7a8ea3;
  font-weight: 600;
}

.summary-grid strong {
  color: #17324d;
}

.summary-text {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fffaf0;
  padding: 12px;
}

.summary-text p,
.risk-card p {
  margin: 6px 0 0;
  color: #744210;
  line-height: 1.6;
}

.risk-card h4,
.shortcut-card h4 {
  margin: 0;
  color: #17324d;
  font-size: 15px;
}

.shortcut-card {
  gap: 10px;
}

.primary-button,
.secondary-button {
  width: 100%;
}

.compact {
  padding: 12px;
}

.empty-state {
  color: #60778e;
  text-align: center;
}

@media (max-width: 1280px) {
  .doctor-home-page {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .summary-grid,
  th,
  td {
    grid-template-columns: 1fr;
  }

  .summary-head {
    flex-direction: column;
  }
}
</style>
