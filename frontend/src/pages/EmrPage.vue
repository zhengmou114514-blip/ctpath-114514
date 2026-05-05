<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FollowupTaskRow, PatientCase, PatientSummary } from '../services/types'

const props = defineProps<{
  loading: boolean
  allPatients: PatientSummary[]
  selectedPatient: PatientCase | null
  followupItems: FollowupTaskRow[]
}>()

const emit = defineEmits<{
  (e: 'open-patient', patientId: string): void
  (e: 'open-archive', payload: { patientId: string; focus?: 'overview' | 'events' }): void
  (e: 'open-followup', payload: { patientId?: string; section?: 'tasks' | 'contacts' | 'flow' }): void
}>()

const activeTab = ref<'records' | 'patients' | 'management'>('records')

const selectedTimeline = computed(() => props.selectedPatient?.timeline ?? [])
const selectedContactLogs = computed(() => props.selectedPatient?.contactLogs ?? [])
const selectedAuditLogs = computed(() => props.selectedPatient?.auditLogs ?? [])
const selectedFollowups = computed(() =>
  props.followupItems.filter((item) => item.patientId === props.selectedPatient?.patientId)
)

function stageLabel(value?: string) {
  if (value === 'Early') return '早期'
  if (value === 'Mid') return '中期'
  if (value === 'Late') return '后期'
  return value || '--'
}

function riskTone(value?: string) {
  if (!value) return 'low'
  const normalized = value.toLowerCase()
  if (normalized.includes('high') || normalized.includes('高')) return 'high'
  if (normalized.includes('medium') || normalized.includes('中')) return 'medium'
  return 'low'
}

function diseaseLabel(patient: PatientSummary) {
  return patient.primaryDisease || '--'
}
</script>

<template>
  <section class="emr-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">电子病历 / 病历管理</p>
        <h1>电子病历工作台</h1>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="activeTab = 'records'">历史住院记录</button>
        <button class="secondary-button" type="button" @click="activeTab = 'patients'">患者一览</button>
        <button class="secondary-button" type="button" @click="activeTab = 'management'">我的管理</button>
      </div>
    </header>

    <section v-if="props.loading" class="empty-state-card">
      <h3>电子病历加载中</h3>
      <p>正在同步患者主索引和病程数据，请稍后。</p>
    </section>

    <section v-else class="emr-layout">
      <aside class="clinical-card emr-sidebar">
        <div class="section-header">
          <div>
            <h2>患者一览</h2>
            <p>选择患者后查看历史记录与管理信息。</p>
          </div>
        </div>

        <div class="emr-patient-list">
          <button
            v-for="patient in props.allPatients"
            :key="patient.patientId"
            type="button"
            class="emr-patient-row"
            :class="{ active: patient.patientId === props.selectedPatient?.patientId }"
            @click="emit('open-patient', patient.patientId)"
          >
            <strong>{{ patient.name }}</strong>
            <span>{{ diseaseLabel(patient) }}</span>
            <small>{{ patient.patientId }} · {{ stageLabel(patient.currentStage) }} · {{ patient.riskLevel }}</small>
          </button>
        </div>
      </aside>

      <article class="clinical-card emr-main">
        <template v-if="props.selectedPatient">
          <div class="emr-summary-panel">
            <div>
              <p class="eyebrow">当前患者</p>
              <h2>{{ props.selectedPatient.name }}</h2>
              <p>{{ props.selectedPatient.primaryDisease || '--' }} · {{ props.selectedPatient.patientId }}</p>
            </div>
            <div class="summary-chip-row">
              <span class="summary-chip">风险 {{ props.selectedPatient.riskLevel }}</span>
              <span class="summary-chip">阶段 {{ stageLabel(props.selectedPatient.currentStage) }}</span>
              <span class="summary-chip">管理师 {{ props.selectedPatient.caseManager || '--' }}</span>
            </div>
          </div>

          <div class="tab-strip">
            <button class="tab-button" :class="{ active: activeTab === 'records' }" type="button" @click="activeTab = 'records'">
              历史住院记录
            </button>
            <button class="tab-button" :class="{ active: activeTab === 'patients' }" type="button" @click="activeTab = 'patients'">
              病历摘要
            </button>
            <button class="tab-button" :class="{ active: activeTab === 'management' }" type="button" @click="activeTab = 'management'">
              我的管理
            </button>
          </div>

          <section v-if="activeTab === 'records'" class="emr-content-grid">
            <article class="document-card">
              <h3>历史住院 / 就诊记录</h3>
              <ul v-if="selectedTimeline.length" class="emr-timeline">
                <li v-for="item in selectedTimeline" :key="`${item.date}-${item.type}-${item.title}`">
                  <strong>{{ item.date }}</strong>
                  <span>{{ item.title }}</span>
                  <p>{{ item.detail }}</p>
                </li>
              </ul>
              <div v-else class="empty-inline">暂无历史住院记录，待导入住院/门诊病历。</div>
            </article>

            <article class="document-card">
              <h3>联系方式与档案状态</h3>
              <dl class="document-dl two-col">
                <div><dt>患者本人</dt><dd>{{ props.selectedPatient.phone || '--' }}</dd></div>
                <div><dt>紧急联系人</dt><dd>{{ props.selectedPatient.emergencyContactName || '--' }}</dd></div>
                <div><dt>联系人关系</dt><dd>{{ props.selectedPatient.emergencyContactRelation || '--' }}</dd></div>
                <div><dt>联系人电话</dt><dd>{{ props.selectedPatient.emergencyContactPhone || '--' }}</dd></div>
                <div><dt>档案状态</dt><dd>{{ props.selectedPatient.archiveStatus || '--' }}</dd></div>
                <div><dt>同意状态</dt><dd>{{ props.selectedPatient.consentStatus || '--' }}</dd></div>
              </dl>
            </article>
          </section>

          <section v-else-if="activeTab === 'patients'" class="emr-content-grid">
            <article class="document-card">
              <h3>病历摘要</h3>
              <dl class="document-dl">
                <div><dt>科室</dt><dd>{{ props.selectedPatient.department || '--' }}</dd></div>
                <div><dt>责任医生</dt><dd>{{ props.selectedPatient.primaryDoctor || '--' }}</dd></div>
                <div><dt>最近就诊</dt><dd>{{ props.selectedPatient.lastVisit || '--' }}</dd></div>
                <div><dt>数据支持</dt><dd>{{ props.selectedPatient.dataSupport || '--' }}</dd></div>
              </dl>
              <p class="print-note">
                {{ props.selectedPatient.summary || '当前病历暂无摘要，待补录。' }}
              </p>
              <div class="card-actions">
                <button class="secondary-button" type="button" @click="emit('open-archive', { patientId: props.selectedPatient.patientId, focus: 'overview' })">打开档案</button>
                <button class="primary-button" type="button" @click="emit('open-followup', { patientId: props.selectedPatient?.patientId, section: 'tasks' })">进入随访</button>
              </div>
            </article>

            <article class="document-card">
              <h3>患者一览 / 核心字段</h3>
              <table class="document-table compact">
                <thead>
                  <tr>
                    <th>患者</th>
                    <th>疾病</th>
                    <th>阶段</th>
                    <th>风险</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="patient in props.allPatients.slice(0, 10)" :key="patient.patientId">
                    <td>{{ patient.name }}</td>
                    <td>{{ diseaseLabel(patient) }}</td>
                    <td>{{ stageLabel(patient.currentStage) }}</td>
                    <td><span :class="`risk-pill risk-${riskTone(patient.riskLevel)}`">{{ patient.riskLevel }}</span></td>
                  </tr>
                </tbody>
              </table>
            </article>
          </section>

          <section v-else class="emr-content-grid">
            <article class="document-card">
              <h3>我的管理</h3>
              <div class="summary-grid three">
                <div class="summary-item">
                  <span>当前跟进</span>
                  <strong>{{ selectedFollowups.length }}</strong>
                </div>
                <div class="summary-item">
                  <span>联系记录</span>
                  <strong>{{ selectedContactLogs.length }}</strong>
                </div>
                <div class="summary-item">
                  <span>审核轨迹</span>
                  <strong>{{ selectedAuditLogs.length }}</strong>
                </div>
              </div>
              <ul v-if="selectedFollowups.length" class="emr-followup-list">
                <li v-for="task in selectedFollowups" :key="task.taskId || `${task.patientId}-${task.taskType}`">
                  <strong>{{ task.taskType }}</strong>
                  <span>{{ task.owner }} · {{ task.dueDate }}</span>
                  <p>{{ task.status }} · {{ task.priority }} · {{ task.source }}</p>
                </li>
              </ul>
              <div v-else class="empty-inline">当前患者暂无可管理的随访任务。</div>
            </article>

            <article class="document-card">
              <h3>联系记录</h3>
              <ul v-if="selectedContactLogs.length" class="emr-followup-list">
                <li v-for="log in selectedContactLogs" :key="`${log.contactTime}-${log.contactType}`">
                  <strong>{{ log.contactTime }}</strong>
                  <span>{{ log.contactType }} · {{ log.contactTarget }}</span>
                  <p>{{ log.contactResult }} · {{ log.note || '无备注' }}</p>
                </li>
              </ul>
              <div v-else class="empty-inline">暂无联系记录。</div>
            </article>
          </section>
        </template>

        <div v-else class="empty-state-card compact-empty">
          <h3>请选择一名患者</h3>
          <p>左侧患者一览中选中患者后，再查看历史住院记录、病历摘要和我的管理。</p>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.emr-page {
  display: grid;
  gap: 24px;
}

.emr-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.emr-sidebar,
.emr-main {
  padding: 22px;
}

.emr-patient-list {
  display: grid;
  gap: 12px;
}

.emr-patient-row {
  display: grid;
  gap: 6px;
  text-align: left;
  padding: 14px 16px;
  border: 1px solid #dce3e5;
  border-radius: 16px;
  background: white;
}

.emr-patient-row.active {
  border-color: var(--ws-primary);
  box-shadow: inset 4px 0 0 var(--ws-primary);
}

.emr-patient-row span,
.emr-patient-row small {
  color: rgba(63, 72, 73, 0.78);
}

.emr-summary-panel {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.summary-chip-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.summary-chip {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(228, 235, 236, 0.9);
  color: #3f4849;
}

.tab-strip {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tab-button {
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid #d4dcde;
  background: white;
}

.tab-button.active {
  border-color: var(--ws-primary);
  background: linear-gradient(135deg, var(--ws-primary), var(--ws-primary-container));
  color: white;
}

.emr-content-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.document-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid #dfe6e8;
  background: #fbfcfd;
}

.document-card h3 {
  margin: 0;
  font-size: 18px;
}

.document-dl {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.document-dl.two-col {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.document-dl > div {
  display: grid;
  gap: 4px;
}

.document-dl dt {
  color: rgba(29, 35, 38, 0.66);
  font-size: 12px;
}

.document-dl dd {
  margin: 0;
  font-weight: 600;
}

.document-table {
  width: 100%;
  border-collapse: collapse;
}

.document-table th,
.document-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #e4eaed;
  text-align: left;
}

.document-table thead th {
  background: #f4f7f8;
}

.summary-grid.three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.summary-grid {
  display: grid;
  gap: 12px;
}

.summary-item {
  padding: 14px;
  border-radius: 16px;
  background: white;
  border: 1px solid #e4eaed;
  display: grid;
  gap: 4px;
}

.summary-item span {
  color: rgba(29, 35, 38, 0.66);
  font-size: 12px;
}

.summary-item strong {
  font-size: 20px;
}

.emr-followup-list,
.emr-timeline {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 12px;
}

.emr-followup-list li,
.emr-timeline li {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid #e4eaed;
  background: white;
}

.emr-followup-list span,
.emr-followup-list p,
.emr-timeline p {
  margin: 0;
  color: rgba(63, 72, 73, 0.82);
}

.card-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 1200px) {
  .emr-layout,
  .emr-content-grid,
  .document-dl,
  .summary-grid.three {
    grid-template-columns: 1fr;
  }

  .emr-summary-panel {
    flex-direction: column;
  }
}
</style>
