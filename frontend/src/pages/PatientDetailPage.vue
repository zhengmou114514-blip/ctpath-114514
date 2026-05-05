<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, MagicStick } from '@element-plus/icons-vue'
import PatientMedicationClosurePanel from '../components/medication/PatientMedicationClosurePanel.vue'
import { useWorkspaceContext } from '../composables/workspaceContext'
import type { ContactLog, OutpatientTask, TimelineEvent } from '../services/types'

const workspace = useWorkspaceContext()
const route = useRoute()
const router = useRouter()

const routePatientId = computed(() => {
  const value = route.params.patientId
  return typeof value === 'string' ? value : ''
})

const selectedPatient = computed(() => workspace.selectedPatient)

const latestPrediction = computed(() => {
  if (!selectedPatient.value || !workspace.predictionResult) return null
  return workspace.predictionResult.patientId === selectedPatient.value.patientId ? workspace.predictionResult : null
})

const topPrediction = computed(() => latestPrediction.value?.topk?.[0] ?? selectedPatient.value?.predictions?.[0] ?? null)
const adviceList = computed(() => latestPrediction.value?.advice ?? selectedPatient.value?.careAdvice ?? [])
const pathList = computed(() => (latestPrediction.value?.pathExplanation ?? selectedPatient.value?.pathExplanation ?? []).slice(0, 3))

const modelEvidence = computed(() => {
  const prediction = latestPrediction.value
  if (prediction?.evidence) {
    return {
      summary: prediction.supportSummary,
      eventCount: prediction.evidence.eventCount,
      relationCount: prediction.evidence.relationCount,
    }
  }
  return {
    summary: selectedPatient.value?.summary || '已根据患者病程、风险等级和历史随访记录生成辅助分析摘要。',
    eventCount: selectedPatient.value?.timeline.length ?? 0,
    relationCount: selectedPatient.value?.pathExplanation.length ?? 0,
  }
})

const timelineItems = computed<TimelineEvent[]>(() => selectedPatient.value?.timeline.slice(0, 6) ?? [])
const diagnosisRecords = computed<TimelineEvent[]>(() =>
  timelineItems.value.filter((item) => item.type === 'diagnosis' || item.type === 'visit').slice(0, 3)
)
const examRecords = computed<TimelineEvent[]>(() =>
  timelineItems.value
    .filter((item) => `${item.title} ${item.detail}`.includes('血') || `${item.title} ${item.detail}`.includes('检查'))
    .slice(0, 3)
)
const followupRecords = computed<ContactLog[]>(() => selectedPatient.value?.contactLogs.slice(0, 3) ?? [])
const outpatientTasks = computed<OutpatientTask[]>(() => selectedPatient.value?.outpatientTasks.slice(0, 3) ?? [])

const attachmentItems = computed(() => {
  const patient = selectedPatient.value
  if (!patient) return []
  return [
    { label: '患者照片', status: patient.avatarUrl ? '已归档' : '待上传' },
    { label: '身份证', status: patient.identityMasked ? '已登记' : '待补充' },
    { label: '检查报告', status: patient.timeline.length >= 3 ? '已归档' : '待补充' },
    { label: '转诊资料', status: patient.archiveSource === 'referral' ? '已归档' : '按需补充' },
    { label: '知情同意书', status: patient.consentStatus === 'signed' ? '已签署' : '待签署' },
    { label: '其他慢病资料', status: patient.summary ? '已归档' : '待补充' },
  ]
})

function archiveNumber() {
  const patient = selectedPatient.value
  if (!patient) return ''
  return patient.medicalRecordNumber || `MRN-${patient.patientId.replace(/\D/g, '').padStart(4, '0')}`
}

function riskTagType(level: string) {
  const raw = (level || '').toLowerCase()
  if (raw.includes('high') || raw.includes('高')) return 'danger'
  if (raw.includes('medium') || raw.includes('中')) return 'warning'
  return 'success'
}

function riskLabel(level: string) {
  const raw = (level || '').toLowerCase()
  if (raw.includes('high')) return '高风险'
  if (raw.includes('medium')) return '中风险'
  if (raw.includes('low')) return '低风险'
  return level || '待评估'
}

function statusLabel(value: string, type: 'archive' | 'consent') {
  const raw = (value || '').toLowerCase()
  if (type === 'archive') {
    if (raw === 'active') return '已建档'
    if (raw === 'pending') return '待补全'
    if (raw === 'closed') return '已归档'
  }
  if (raw === 'signed') return '已签署'
  if (raw === 'pending') return '待签署'
  if (raw === 'revoked') return '已撤回'
  return value || '待维护'
}

function contactResultLabel(value: string) {
  const labels: Record<string, string> = {
    reached: '已接通',
    missed: '未接通',
    scheduled: '已预约',
    urgent: '需紧急处理',
  }
  return labels[value] ?? value
}

async function loadPatientDetail(patientId: string) {
  if (!patientId) return
  if (workspace.selectedPatientId === patientId && workspace.selectedPatient) return
  await workspace.openPatient(patientId, 'doctor')
}

function handleBack() {
  void router.push({ name: 'home' })
}

function handleOpenArchive() {
  const patientId = selectedPatient.value?.patientId || routePatientId.value
  if (!patientId) return
  void workspace.openArchiveInNewTab(patientId, 'overview')
}

function handleOpenFollowup() {
  const patientId = selectedPatient.value?.patientId || routePatientId.value
  if (!patientId) return
  void workspace.openFollowupModule(patientId, 'tasks')
}

function handleOpenCoordination() {
  void router.push({ name: 'coordination', query: { patientId: selectedPatient.value?.patientId } })
}

function handleRunPrediction() {
  void workspace.runPrediction(true)
}

watch(
  routePatientId,
  (value) => {
    void loadPatientDetail(value)
  },
  { immediate: true }
)
</script>

<template>
  <section class="patient-detail-page workstation-page">
    <section v-if="!selectedPatient" class="empty-state-card">
      <h3>患者详情加载中</h3>
      <p>正在同步患者主档案、病程时间线、当前用药和辅助建议。</p>
    </section>

    <template v-else>
      <header class="detail-header clinical-card">
        <div>
          <p class="eyebrow">临床业务模块</p>
          <h1>患者详情</h1>
          <p class="header-summary">
            围绕患者维度展示主档案、病程变化、当前用药、附件资料和模型辅助建议。
          </p>
        </div>
        <div class="header-actions">
          <button class="secondary-button" type="button" @click="handleBack">
            <el-icon><ArrowLeft /></el-icon>
            返回工作台
          </button>
          <button class="secondary-button" type="button" @click="handleOpenArchive">打开档案</button>
          <button class="secondary-button" type="button" @click="handleOpenFollowup">发起随访</button>
          <button class="primary-button" type="button" :disabled="workspace.loadingPredict" @click="handleRunPrediction">
            <el-icon><MagicStick /></el-icon>
            {{ latestPrediction ? '刷新模型建议' : '运行风险预测' }}
          </button>
        </div>
      </header>

      <section class="patient-clinical-grid">
        <aside class="detail-column archive-column">
          <article class="clinical-card patient-profile-card">
            <p class="eyebrow">患者档案</p>
            <div class="patient-title-row">
              <div>
                <h2>{{ selectedPatient.name }}</h2>
                <p>{{ selectedPatient.gender }} / {{ selectedPatient.age }} 岁</p>
              </div>
              <el-tag :type="riskTagType(selectedPatient.riskLevel)" effect="light">
                {{ riskLabel(selectedPatient.riskLevel) }}
              </el-tag>
            </div>

            <dl class="archive-list">
              <div>
                <dt>患者编号</dt>
                <dd>{{ selectedPatient.patientId }}</dd>
              </div>
              <div>
                <dt>病历号</dt>
                <dd>{{ archiveNumber() }}</dd>
              </div>
              <div>
                <dt>联系方式</dt>
                <dd>{{ selectedPatient.phone || '待补充' }}</dd>
              </div>
              <div>
                <dt>主治医生</dt>
                <dd>{{ selectedPatient.primaryDoctor || '待分配' }}</dd>
              </div>
              <div>
                <dt>档案状态</dt>
                <dd>{{ statusLabel(selectedPatient.archiveStatus, 'archive') }}</dd>
              </div>
              <div>
                <dt>知情同意</dt>
                <dd>{{ statusLabel(selectedPatient.consentStatus, 'consent') }}</dd>
              </div>
            </dl>
          </article>

          <article class="clinical-card attachment-card">
            <div class="section-title-row">
              <div>
                <p class="eyebrow">电子档案附件</p>
                <h2>附件摘要</h2>
              </div>
              <button class="text-button" type="button" @click="handleOpenArchive">上传附件</button>
            </div>
            <ul class="attachment-list">
              <li v-for="item in attachmentItems" :key="item.label">
                <span>{{ item.label }}</span>
                <strong>{{ item.status }}</strong>
              </li>
            </ul>
          </article>
        </aside>

        <main class="detail-column course-column">
          <article class="clinical-card course-card">
            <div class="section-title-row">
              <div>
                <p class="eyebrow">病程与诊疗过程</p>
                <h2>病程时间线</h2>
              </div>
              <el-tag effect="light">{{ selectedPatient.currentStage || '阶段待维护' }}</el-tag>
            </div>
            <p class="course-summary">{{ selectedPatient.summary }}</p>

            <el-timeline v-if="timelineItems.length" class="course-timeline">
              <el-timeline-item
                v-for="item in timelineItems"
                :key="`${item.date}-${item.type}-${item.title}`"
                :timestamp="item.date"
                placement="top"
              >
                <strong>{{ item.title }}</strong>
                <p>{{ item.detail }}</p>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无病程时间线记录。" />
          </article>

          <section class="record-grid">
            <article class="clinical-card record-card">
              <h2>诊疗记录</h2>
              <div v-if="diagnosisRecords.length" class="compact-record-list">
                <p v-for="item in diagnosisRecords" :key="`${item.date}-${item.title}`">
                  <strong>{{ item.date }}</strong>
                  <span>{{ item.title }}：{{ item.detail }}</span>
                </p>
              </div>
              <p v-else class="muted-line">暂无诊疗记录。</p>
            </article>

            <article class="clinical-card record-card">
              <h2>检查检验摘要</h2>
              <div v-if="examRecords.length" class="compact-record-list">
                <p v-for="item in examRecords" :key="`${item.date}-${item.title}`">
                  <strong>{{ item.date }}</strong>
                  <span>{{ item.detail }}</span>
                </p>
              </div>
              <p v-else class="muted-line">暂无检查检验摘要。</p>
            </article>

            <article class="clinical-card record-card followup-record-card">
              <h2>随访记录</h2>
              <div v-if="followupRecords.length" class="compact-record-list">
                <p v-for="item in followupRecords" :key="item.logId">
                  <strong>{{ item.contactTime }}</strong>
                  <span>{{ contactResultLabel(item.contactResult) }}：{{ item.note }}</span>
                </p>
              </div>
              <p v-else class="muted-line">暂无随访联系记录。</p>
            </article>
          </section>
        </main>

        <aside class="detail-column assist-column">
          <article class="clinical-card assist-summary-card">
            <p class="eyebrow">辅助诊疗</p>
            <h2>风险与模型建议</h2>
            <div class="risk-box">
              <span>风险等级</span>
              <strong>{{ riskLabel(selectedPatient.riskLevel) }}</strong>
            </div>
            <div v-if="topPrediction" class="prediction-box">
              <div class="prediction-head">
                <strong>{{ topPrediction.label }}</strong>
                <span>{{ Math.round(topPrediction.score * 100) }}%</span>
              </div>
              <el-progress :percentage="Math.round(topPrediction.score * 100)" :stroke-width="8" />
              <p>{{ topPrediction.reason }}</p>
            </div>
            <p v-else class="muted-line">暂无模型预测结果，可点击运行风险预测。</p>
          </article>

          <article class="clinical-card evidence-card">
            <h2>证据摘要</h2>
            <p>{{ modelEvidence.summary }}</p>
            <dl class="evidence-stat-list">
              <div>
                <dt>病程事件</dt>
                <dd>{{ modelEvidence.eventCount }}</dd>
              </div>
              <div>
                <dt>证据关系</dt>
                <dd>{{ modelEvidence.relationCount }}</dd>
              </div>
            </dl>
            <div v-if="pathList.length" class="path-list">
              <p v-for="item in pathList" :key="item">{{ item }}</p>
            </div>
          </article>

          <article class="clinical-card advice-card">
            <h2>辅助建议</h2>
            <ul v-if="adviceList.length" class="advice-list">
              <li v-for="item in adviceList.slice(0, 3)" :key="item">{{ item }}</li>
            </ul>
            <p v-else class="muted-line">暂无辅助建议，请结合病程记录继续评估。</p>
            <div class="assist-actions">
              <button class="primary-button" type="button" @click="handleOpenFollowup">发起随访</button>
              <button class="secondary-button" type="button" @click="handleOpenCoordination">医生复核</button>
            </div>
          </article>

          <article v-if="outpatientTasks.length" class="clinical-card task-card">
            <h2>待处理事项</h2>
            <div class="task-list">
              <p v-for="item in outpatientTasks" :key="item.taskId">
                <strong>{{ item.title }}</strong>
                <span>{{ item.owner }} / {{ item.dueDate }}</span>
              </p>
            </div>
          </article>

          <PatientMedicationClosurePanel :patient-id="selectedPatient.patientId" :model-advice="adviceList" />
        </aside>
      </section>
    </template>
  </section>
</template>

<style scoped>
.patient-detail-page {
  gap: 12px;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
}

.detail-header h1 {
  margin: 2px 0 4px;
  font-size: 34px;
}

.header-summary {
  margin: 0;
  color: #526772;
  line-height: 1.6;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.patient-clinical-grid {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 340px;
  gap: 12px;
  align-items: start;
}

.detail-column {
  min-width: 0;
  display: grid;
  gap: 12px;
}

.clinical-card {
  display: grid;
  gap: 12px;
}

.patient-title-row,
.section-title-row,
.prediction-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.patient-title-row h2,
.section-title-row h2,
.assist-summary-card h2,
.record-card h2,
.evidence-card h2,
.advice-card h2,
.task-card h2 {
  margin: 0;
  font-size: 22px;
}

.patient-title-row p {
  margin: 4px 0 0;
  color: #526772;
}

.archive-list {
  display: grid;
  margin: 0;
  border: 1px solid #d5e6ef;
}

.archive-list div {
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr);
  border-bottom: 1px solid #d5e6ef;
}

.archive-list div:last-child {
  border-bottom: 0;
}

.archive-list dt,
.archive-list dd {
  min-height: 34px;
  margin: 0;
  padding: 8px;
  font-size: 13px;
}

.archive-list dt {
  background: #f2f9fc;
  color: #527384;
  font-weight: 700;
}

.archive-list dd {
  color: #243f4d;
  font-weight: 800;
}

.attachment-list,
.advice-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.attachment-list li {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #d5e6ef;
  border-radius: 3px;
  background: #f7fbfd;
}

.attachment-list span,
.attachment-list strong {
  font-size: 13px;
}

.course-summary,
.course-timeline p,
.prediction-box p,
.evidence-card p,
.muted-line {
  margin: 0;
  color: #526772;
  line-height: 1.65;
}

.record-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.followup-record-card {
  grid-column: 1 / -1;
}

.compact-record-list {
  display: grid;
  gap: 8px;
}

.compact-record-list p,
.task-list p {
  display: grid;
  gap: 4px;
  margin: 0;
  padding: 10px;
  border: 1px solid #d5e6ef;
  border-radius: 3px;
  background: #f7fbfd;
}

.compact-record-list strong,
.task-list strong {
  color: #003c43;
}

.compact-record-list span,
.task-list span {
  color: #526772;
  line-height: 1.55;
}

.risk-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #b7d1de;
  border-radius: 4px;
  background: #edf7fc;
}

.risk-box span {
  color: #527384;
  font-weight: 700;
}

.risk-box strong {
  color: #005761;
  font-size: 24px;
}

.prediction-box {
  display: grid;
  gap: 10px;
}

.prediction-head strong {
  font-size: 18px;
}

.prediction-head span {
  color: #0f6f99;
  font-size: 22px;
  font-weight: 900;
}

.evidence-stat-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
}

.evidence-stat-list div {
  padding: 10px;
  border: 1px solid #d5e6ef;
  border-radius: 3px;
  background: #f7fbfd;
}

.evidence-stat-list dt {
  color: #527384;
  font-size: 12px;
  font-weight: 700;
}

.evidence-stat-list dd {
  margin: 2px 0 0;
  color: #003c43;
  font-size: 22px;
  font-weight: 900;
}

.path-list {
  display: grid;
  gap: 6px;
  padding: 10px;
  border: 1px solid #d5e6ef;
  border-radius: 3px;
  background: #f7fbfd;
}

.path-list p {
  margin: 0;
  font-size: 13px;
}

.advice-list li {
  padding: 9px 10px;
  border-left: 3px solid #008bbf;
  background: #edf7fc;
  color: #243f4d;
  line-height: 1.55;
}

.assist-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.task-list {
  display: grid;
  gap: 8px;
}

@media (max-width: 1280px) {
  .patient-clinical-grid {
    grid-template-columns: 260px minmax(0, 1fr);
  }

  .assist-column {
    grid-column: 1 / -1;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .detail-header {
    flex-direction: column;
  }

  .header-actions {
    justify-content: flex-start;
  }

  .patient-clinical-grid,
  .record-grid,
  .assist-column {
    grid-template-columns: 1fr;
  }

  .assist-column {
    grid-column: auto;
  }
}
</style>
