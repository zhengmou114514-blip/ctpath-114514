<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PatientMedicationClosurePanel from '../components/medication/PatientMedicationClosurePanel.vue'
import PatientAttachmentPanel from '../components/patient/PatientAttachmentPanel.vue'
import { useWorkspaceContext } from '../composables/workspaceContext'

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
const hasLatestPrediction = computed(() => Boolean(latestPrediction.value))
const topPrediction = computed(() => latestPrediction.value?.topk?.[0] ?? selectedPatient.value?.predictions?.[0] ?? null)
const adviceList = computed(() => latestPrediction.value?.advice ?? selectedPatient.value?.careAdvice ?? [])
const evidence = computed(() => {
  const prediction = latestPrediction.value
  if (prediction?.evidence) {
    return {
      eventCount: prediction.evidence.eventCount,
      relationCount: prediction.evidence.relationCount,
      supportLevel: prediction.evidence.supportLevel,
      summary: prediction.supportSummary || '已加载当前患者的结构化证据摘要。',
    }
  }

  return {
    eventCount: selectedPatient.value?.timeline.length ?? 0,
    relationCount: selectedPatient.value?.pathExplanation.length ?? 0,
    supportLevel: selectedPatient.value?.dataSupport ?? 'unknown',
    summary: selectedPatient.value?.summary || '暂无结构化证据摘要。',
  }
})

const modelStatus = computed(() => {
  if (workspace.modelUnavailable) return { label: '模型不可用', type: 'danger' as const }
  if (workspace.health?.mode === 'demo') return { label: 'Demo 模式', type: 'warning' as const }
  if (latestPrediction.value?.mode === 'model') return { label: '模型结果', type: 'success' as const }
  if (latestPrediction.value?.mode === 'similar-case') return { label: '相似病例回退', type: 'warning' as const }
  return { label: '待预测', type: 'info' as const }
})

const predictionButtonLabel = computed(() => (hasLatestPrediction.value ? 'Refresh Prediction' : 'Run Prediction'))
const predictionSource = computed(() => {
  if (workspace.loadingPredict) {
    return {
      label: 'Predicting',
      type: 'warning' as const,
      note: 'Calling the real /api/predict endpoint for the current patient.',
    }
  }

  if (workspace.predictionError) {
    return {
      label: 'Prediction Failed',
      type: 'danger' as const,
      note: hasLatestPrediction.value
        ? `${workspace.predictionError} Showing the last successful prediction below.`
        : `${workspace.predictionError} The prediction area is still showing the preloaded summary.`,
    }
  }

  if (hasLatestPrediction.value) {
    return {
      label: 'Latest Prediction',
      type: 'success' as const,
      note: `Latest result loaded from /api/predict via ${latestPrediction.value?.strategy ?? 'unknown'}.`,
    }
  }

  return {
    label: 'Preloaded Summary',
    type: 'info' as const,
    note: 'This page has not called /api/predict yet. Click Run Prediction to fetch the latest result.',
  }
})

function riskTagType(level: string) {
  const raw = (level || '').toLowerCase()
  if (raw.includes('high')) return 'danger'
  if (raw.includes('medium')) return 'warning'
  return 'success'
}

function supportTagType(value: string) {
  if (value === 'high' || value === 'strong') return 'success'
  if (value === 'medium' || value === 'limited') return 'warning'
  return 'info'
}

function supportLabel(value: string) {
  if (value === 'strong' || value === 'high') return '高'
  if (value === 'limited' || value === 'medium') return '中'
  if (value === 'minimal' || value === 'low') return '低'
  return value || '--'
}

async function loadPatientDetail(patientId: string) {
  if (!patientId) return
  if (workspace.selectedPatientId === patientId && workspace.selectedPatient) return
  await workspace.openPatient(patientId, 'doctor')
}

function handleBack() {
  void router.push({ name: 'home' })
}

function handleOpenFollowup() {
  const patientId = selectedPatient.value?.patientId || routePatientId.value
  if (!patientId) return
  void workspace.openFollowupModule(patientId, 'tasks')
}

function handleRunPrediction() {
  void workspace.runPrediction()
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
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">Patient detail</p>
        <h1>患者详情 / 电子档案</h1>
        <p>围绕当前患者组织档案、附件、病程时间线、用药评估和模型建议。</p>
      </div>
      <div class="header-actions">
        <el-button @click="handleBack">返回医生工作台</el-button>
        <el-button type="primary" :disabled="!selectedPatient" @click="handleOpenFollowup">打开随访</el-button>
      </div>
    </header>

    <el-empty v-if="!selectedPatient" description="请从医生工作台选择患者，或打开带患者 ID 的详情路由。" />

    <template v-else>
      <section class="patient-detail-three-column">
        <aside class="detail-column left-column">
          <article class="clinical-card profile-card">
            <div class="profile-head">
              <div class="avatar-box">{{ selectedPatient.name.slice(-2) }}</div>
              <div>
                <h2>{{ selectedPatient.name }}</h2>
                <p>{{ selectedPatient.patientId }} / {{ selectedPatient.primaryDisease }}</p>
              </div>
            </div>

            <div class="tag-row">
              <el-tag :type="riskTagType(selectedPatient.riskLevel)" effect="light">{{ selectedPatient.riskLevel }}</el-tag>
              <el-tag :type="supportTagType(selectedPatient.dataSupport)" effect="light">
                数据支持 {{ supportLabel(selectedPatient.dataSupport) }}
              </el-tag>
              <el-tag :type="modelStatus.type" effect="light">{{ modelStatus.label }}</el-tag>
            </div>

            <dl class="facts-list">
              <div><dt>年龄 / 性别</dt><dd>{{ selectedPatient.age }} / {{ selectedPatient.gender }}</dd></div>
              <div><dt>病案号</dt><dd>{{ selectedPatient.medicalRecordNumber || '--' }}</dd></div>
              <div><dt>医保类型</dt><dd>{{ selectedPatient.insuranceType || '--' }}</dd></div>
              <div><dt>主管医生</dt><dd>{{ selectedPatient.primaryDoctor || '--' }}</dd></div>
              <div><dt>个案管理</dt><dd>{{ selectedPatient.caseManager || '--' }}</dd></div>
              <div><dt>最近就诊</dt><dd>{{ selectedPatient.lastVisit || '--' }}</dd></div>
              <div><dt>档案状态</dt><dd>{{ selectedPatient.archiveStatus || '--' }}</dd></div>
              <div><dt>知情同意</dt><dd>{{ selectedPatient.consentStatus || '--' }}</dd></div>
            </dl>
          </article>

          <PatientAttachmentPanel :patient-id="selectedPatient.patientId" title="电子档案 / 附件" />
        </aside>

        <main class="detail-column center-column">
          <article class="clinical-card timeline-card">
            <div class="section-header">
              <div>
                <h2>病程时间线</h2>
                <p>{{ selectedPatient.timeline.length }} 条事件</p>
              </div>
            </div>
            <el-timeline v-if="selectedPatient.timeline.length">
              <el-timeline-item
                v-for="item in selectedPatient.timeline.slice(0, 10)"
                :key="`${item.date}-${item.type}-${item.title}`"
                :timestamp="item.date"
                placement="top"
              >
                <strong>{{ item.title }}</strong>
                <p class="timeline-detail">{{ item.detail }}</p>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无病程事件。" />
          </article>

          <article class="clinical-card evidence-card">
            <div class="section-header">
              <div>
                <h2>证据摘要</h2>
                <p>当前患者相关结构化证据。</p>
              </div>
              <span class="status-chip">支持 {{ supportLabel(evidence.supportLevel) }}</span>
            </div>
            <p class="evidence-summary">{{ evidence.summary }}</p>
            <div class="mini-metric-grid">
              <article><span>事件</span><strong>{{ evidence.eventCount }}</strong></article>
              <article><span>关系</span><strong>{{ evidence.relationCount }}</strong></article>
              <article><span>支持</span><strong>{{ supportLabel(evidence.supportLevel) }}</strong></article>
            </div>
          </article>
        </main>

        <aside class="detail-column right-column">
          <article class="clinical-card prediction-card">
            <div class="section-header">
              <div>
                <h2>模型建议摘要</h2>
                <p>{{ modelStatus.label }}</p>
              </div>
              <div class="prediction-actions">
                <el-tag :type="predictionSource.type">{{ predictionSource.label }}</el-tag>
                <el-button
                  type="primary"
                  plain
                  size="small"
                  :disabled="!selectedPatient"
                  :loading="workspace.loadingPredict"
                  @click="handleRunPrediction"
                >
                  {{ predictionButtonLabel }}
                </el-button>
              </div>
            </div>
            <div class="prediction-meta-row">
              <el-tag :type="modelStatus.type" effect="light">{{ modelStatus.label }}</el-tag>
            </div>
            <p class="prediction-source-note">{{ predictionSource.note }}</p>
            <div v-if="topPrediction" class="prediction-box">
              <div class="prediction-head">
                <strong>{{ topPrediction.label }}</strong>
                <span>{{ Math.round(topPrediction.score * 100) }}%</span>
              </div>
              <el-progress :percentage="Math.round(topPrediction.score * 100)" :stroke-width="8" />
              <p>{{ topPrediction.reason }}</p>
            </div>
            <el-empty v-else description="暂无预测结果。" />
          </article>

          <PatientMedicationClosurePanel :patient-id="selectedPatient.patientId" :model-advice="adviceList" />

          <article class="clinical-card advice-card">
            <div class="section-header">
              <div>
                <h2>建议摘要</h2>
                <p>{{ adviceList.length }} 条建议</p>
              </div>
            </div>
            <el-empty v-if="!adviceList.length" description="暂无建议。" />
            <ol v-else class="advice-list">
              <li v-for="(item, index) in adviceList.slice(0, 5)" :key="`${index}-${item}`">{{ item }}</li>
            </ol>
          </article>
        </aside>
      </section>
    </template>
  </section>
</template>

<style scoped>
.patient-detail-page {
  display: grid;
  gap: 24px;
}

.patient-detail-three-column {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr) 360px;
  gap: 24px;
  align-items: start;
}

.detail-column {
  min-width: 0;
  display: grid;
  gap: 24px;
}

.profile-card,
.prediction-card,
.timeline-card,
.evidence-card,
.advice-card {
  display: grid;
  gap: 16px;
}

.profile-head {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.avatar-box {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--ws-primary);
  color: #fff;
  font-weight: 800;
}

.profile-head h2,
.profile-head p,
.timeline-detail,
.evidence-summary,
.prediction-box p {
  margin: 0;
}

.profile-head h2 {
  font-size: 18px;
}

.profile-head p,
.timeline-detail,
.evidence-summary,
.prediction-box p {
  color: var(--ws-text-muted);
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.facts-list {
  display: grid;
  gap: 10px;
  margin: 0;
}

.facts-list div {
  display: grid;
  gap: 3px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--ws-border);
}

.facts-list div:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.facts-list dt {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.facts-list dd {
  margin: 0;
  color: var(--ws-title);
  font-weight: 700;
}

.prediction-box {
  display: grid;
  gap: 12px;
}

.prediction-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.prediction-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.prediction-source-note {
  margin: 0;
  color: var(--ws-text-muted);
  line-height: 1.6;
}

.prediction-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.prediction-head strong,
.prediction-head span {
  color: var(--ws-title);
  font-size: 16px;
}

.mini-metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.mini-metric-grid article {
  display: grid;
  gap: 4px;
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: var(--ws-surface-soft);
  padding: 10px;
}

.mini-metric-grid span {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.mini-metric-grid strong {
  color: var(--ws-title);
  font-size: 16px;
}

.advice-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding-left: 20px;
}

.advice-list li {
  color: var(--ws-text);
  line-height: 1.7;
}

@media (max-width: 1320px) {
  .patient-detail-three-column {
    grid-template-columns: 1fr;
  }
}
</style>
