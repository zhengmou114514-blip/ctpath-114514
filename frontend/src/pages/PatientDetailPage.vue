<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, MagicStick } from '@element-plus/icons-vue'
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
const secondaryPredictions = computed(() => (latestPrediction.value?.topk ?? selectedPatient.value?.predictions ?? []).slice(1, 3))
const adviceList = computed(() => latestPrediction.value?.advice ?? selectedPatient.value?.careAdvice ?? [])
const pathList = computed(() => (latestPrediction.value?.pathExplanation ?? selectedPatient.value?.pathExplanation ?? []).slice(0, 4))
const evidence = computed(() => {
  const prediction = latestPrediction.value
  if (prediction?.evidence) {
    return {
      eventCount: prediction.evidence.eventCount,
      relationCount: prediction.evidence.relationCount,
      supportLevel: prediction.evidence.supportLevel,
      summary: prediction.supportSummary || '当前为预测服务返回的最新证据摘要。',
    }
  }

  return {
    eventCount: selectedPatient.value?.timeline.length ?? 0,
    relationCount: selectedPatient.value?.pathExplanation.length ?? 0,
    supportLevel: selectedPatient.value?.dataSupport ?? 'unknown',
    summary: selectedPatient.value?.summary || '当前展示的是预置临床摘要，尚未触发新的实时预测。',
  }
})

const modelStatus = computed(() => {
  if (workspace.modelUnavailable) return { label: '模型不可用', type: 'danger' as const }
  if (workspace.health?.mode === 'demo') return { label: 'Demo 模式', type: 'warning' as const }
  if (latestPrediction.value?.mode === 'model') return { label: '模型预测就绪', type: 'success' as const }
  if (latestPrediction.value?.mode === 'similar-case') return { label: '相似病例回退', type: 'warning' as const }
  return { label: '等待预测', type: 'info' as const }
})

const predictionButtonLabel = computed(() => (hasLatestPrediction.value ? '刷新预测' : '触发预测'))
const predictionSource = computed(() => {
  if (workspace.loadingPredict) {
    return {
      label: '预测中',
      type: 'warning' as const,
      note: '正在为当前患者调用真实 /api/predict 接口。',
    }
  }

  if (workspace.predictionError) {
    return {
      label: '预测失败',
      type: 'danger' as const,
      note: hasLatestPrediction.value
        ? `${workspace.predictionError} 当前继续展示最近一次成功预测结果。`
        : `${workspace.predictionError} 当前预测区仍展示预置摘要。`,
    }
  }

  if (hasLatestPrediction.value) {
    return {
      label: '最新预测结果',
      type: 'success' as const,
      note: `当前结果来自 /api/predict，策略：${latestPrediction.value?.strategy ?? 'unknown'}。`,
    }
  }

  return {
    label: '初始预置摘要',
    type: 'info' as const,
    note: '当前页面尚未调用 /api/predict，请点击“触发预测”获取最新结果。',
  }
})

const leftRailStats = computed(() => {
  const stats = selectedPatient.value?.stats ?? []
  if (stats.length) return stats.slice(0, 4)

  return [
    { label: '心率', value: '88 bpm', trend: '' },
    { label: '血压', value: '142/90 mmHg', trend: '' },
    { label: '血氧', value: '96%', trend: '' },
    { label: '体温', value: '37.0°C', trend: '' },
  ]
})

const labStats = computed(() => {
  const stats = selectedPatient.value?.stats ?? []
  if (stats.length > 4) return stats.slice(4, 6)

  return [
    { label: '肌酐', value: '1.8 mg/dL', trend: '+0.4 from baseline' },
    { label: '尿素氮', value: '28 mg/dL', trend: '' },
  ]
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
    <section v-if="!selectedPatient" class="empty-state-card">
      <h3>未选择患者</h3>
      <p>请先从医生工作台患者队列打开一名患者，再进入详情工作区。</p>
    </section>

    <template v-else>
      <header class="patient-detail-hero">
        <div>
          <p class="eyebrow">患者详情</p>
          <h1>{{ selectedPatient.name.toUpperCase() }}</h1>
          <p class="hero-meta">
            出生日期未录入 / {{ selectedPatient.age }} 岁 / 病案号 {{ selectedPatient.medicalRecordNumber || selectedPatient.patientId }}
          </p>
        </div>

        <div class="hero-actions">
          <span class="workspace-status-pill" :class="`status-${predictionSource.type}`">{{ predictionSource.label }}</span>
          <button class="primary-button" type="button" :disabled="workspace.loadingPredict" @click="handleRunPrediction">
            <el-icon><MagicStick /></el-icon>
            <span>{{ predictionButtonLabel }}</span>
          </button>
          <button class="secondary-button" type="button" @click="handleOpenFollowup">打开随访任务</button>
          <button class="secondary-button" type="button" @click="handleBack">
            <el-icon><ArrowLeft /></el-icon>
            <span>返回工作台</span>
          </button>
        </div>
      </header>

      <section class="patient-detail-layout">
        <aside class="patient-left-rail">
          <article class="clinical-card data-panel">
            <h2>当前生命体征</h2>
            <dl class="metric-list">
              <div v-for="item in leftRailStats" :key="item.label">
                <dt>{{ item.label }}</dt>
                <dd>{{ item.value }}</dd>
              </div>
            </dl>
          </article>

          <article class="clinical-card data-panel">
            <h2>检验重点</h2>
            <dl class="metric-list lab-list">
              <div v-for="item in labStats" :key="item.label">
                <dt>{{ item.label }}</dt>
                <dd>{{ item.value }}</dd>
                <small v-if="item.trend">{{ item.trend }}</small>
              </div>
            </dl>
          </article>

          <PatientAttachmentPanel :patient-id="selectedPatient.patientId" title="电子附件" />
        </aside>

        <main class="patient-main-rail">
          <article class="clinical-card insight-panel">
            <div class="insight-header">
              <div>
                <p class="eyebrow">模型洞察摘要</p>
                <h2>模型洞察摘要</h2>
              </div>
              <div class="insight-statuses">
                <el-tag :type="riskTagType(selectedPatient.riskLevel)" effect="light">{{ selectedPatient.riskLevel }}</el-tag>
                <el-tag :type="supportTagType(selectedPatient.dataSupport)" effect="light">数据支撑 {{ supportLabel(selectedPatient.dataSupport) }}</el-tag>
                <el-tag :type="modelStatus.type" effect="light">{{ modelStatus.label }}</el-tag>
              </div>
            </div>

            <p class="prediction-source-note">{{ predictionSource.note }}</p>

            <section class="topk-section">
              <p class="topk-label">Top-K 风险事件</p>
              <div class="topk-chips">
                <span v-if="topPrediction" class="risk-pill" :class="riskTagType(selectedPatient.riskLevel) === 'danger' ? 'risk-high' : 'risk-medium'">
                  {{ topPrediction.label }}
                </span>
                <span v-for="item in secondaryPredictions" :key="item.label" class="risk-pill risk-medium">{{ item.label }}</span>
              </div>
            </section>

            <section class="insight-grid">
              <article class="insight-block">
                <p class="eyebrow">证据摘要</p>
                <p class="block-body">{{ evidence.summary }}</p>
                <ul class="bullet-list">
                  <li>推理链路中纳入了 {{ evidence.eventCount }} 个时间线事件。</li>
                  <li>本次预测参考了 {{ evidence.relationCount }} 条图谱关系。</li>
                </ul>
              </article>

              <article class="insight-block">
                <p class="eyebrow">可解释路径</p>
                <div class="path-box">
                  <p v-for="item in pathList" :key="item">
                    {{ item }}
                  </p>
                </div>
              </article>
            </section>

            <article class="care-advice-box">
              <p class="eyebrow">模型建议</p>
              <p class="care-advice-body">
                {{ adviceList[0] || '当前尚无可展示的建议内容。' }}
              </p>
            </article>

            <div v-if="workspace.loadingPredict" class="prediction-state-shell prediction-loading">
              <strong>预测中</strong>
              <p>预测服务正在处理当前患者记录。</p>
            </div>

            <div v-else-if="workspace.predictionError" class="prediction-state-shell prediction-error">
              <strong>预测失败</strong>
              <p>{{ predictionSource.note }}</p>
            </div>

            <div class="insight-actions">
              <button class="primary-button" type="button" :disabled="workspace.loadingPredict" @click="handleRunPrediction">
                {{ predictionButtonLabel }}
              </button>
              <button class="secondary-button" type="button" @click="handleOpenFollowup">打开随访任务</button>
              <button class="secondary-button" type="button" @click="handleBack">返回工作台</button>
            </div>
          </article>

          <section class="patient-secondary-grid">
            <article class="clinical-card prediction-card">
              <div class="section-header">
                <div>
                  <h2>{{ hasLatestPrediction ? '最新预测结果' : '预测摘要' }}</h2>
                  <p>
                    {{ hasLatestPrediction ? '展示当前预测源返回的主事件。' : '在生成新预测前，先展示患者预置事件摘要。' }}
                  </p>
                </div>
              </div>

              <div v-if="topPrediction" class="prediction-box">
                <div class="prediction-head">
                  <strong>{{ topPrediction.label }}</strong>
                  <span>{{ Math.round(topPrediction.score * 100) }}%</span>
                </div>
                <el-progress :percentage="Math.round(topPrediction.score * 100)" :stroke-width="8" />
                <p>{{ topPrediction.reason }}</p>
              </div>
              <el-empty v-else description="暂无预测摘要。" />
            </article>

            <article class="clinical-card timeline-card">
              <div class="section-header">
                <div>
                  <h2>近期时间线</h2>
                  <p>当前病案共记录 {{ selectedPatient.timeline.length }} 条关键事件。</p>
                </div>
              </div>
              <el-timeline v-if="selectedPatient.timeline.length">
                <el-timeline-item
                  v-for="item in selectedPatient.timeline.slice(0, 6)"
                  :key="`${item.date}-${item.type}-${item.title}`"
                  :timestamp="item.date"
                  placement="top"
                >
                  <strong>{{ item.title }}</strong>
                  <p class="timeline-detail">{{ item.detail }}</p>
                </el-timeline-item>
              </el-timeline>
              <el-empty v-else description="暂无时间线事件。" />
            </article>
          </section>

          <PatientMedicationClosurePanel :patient-id="selectedPatient.patientId" :model-advice="adviceList" />
        </main>
      </section>
    </template>
  </section>
</template>

<style scoped>
.patient-detail-page {
  gap: 22px;
}

.patient-detail-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 30px 40px;
  border-radius: 0;
  background: rgba(240, 244, 245, 0.8);
}

.patient-detail-hero h1 {
  font-size: clamp(42px, 5vw, 66px);
}

.hero-meta {
  margin: 14px 0 0;
  color: rgba(24, 28, 29, 0.72);
  font-family: var(--ws-font-headline);
  font-size: 14px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 12px;
}

.patient-detail-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}

.patient-left-rail,
.patient-main-rail {
  min-width: 0;
  display: grid;
  gap: 22px;
}

.data-panel {
  display: grid;
  gap: 18px;
}

.metric-list {
  display: grid;
  gap: 12px;
  margin: 0;
}

.metric-list div {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 14px 12px;
  border-radius: 10px;
  background: rgba(241, 244, 245, 0.92);
}

.metric-list dt {
  color: rgba(24, 28, 29, 0.72);
  font-family: var(--ws-font-headline);
  font-size: 13px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.metric-list dd {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--ws-on-surface);
}

.lab-list div {
  grid-template-columns: 1fr auto;
}

.lab-list small {
  grid-column: 2;
  color: var(--ws-error);
  text-align: right;
}

.insight-panel {
  display: grid;
  gap: 22px;
  padding: 32px 34px;
}

.insight-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.insight-statuses {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.prediction-source-note,
.block-body,
.care-advice-body,
.timeline-detail,
.prediction-box p {
  margin: 0;
  color: rgba(63, 72, 73, 0.84);
  line-height: 1.65;
}

.topk-section {
  display: grid;
  gap: 10px;
}

.topk-label {
  margin: 0;
  color: rgba(24, 28, 29, 0.72);
  font-family: var(--ws-font-headline);
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.topk-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.insight-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 18px;
}

.insight-block {
  display: grid;
  gap: 14px;
}

.bullet-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding-left: 20px;
  color: rgba(24, 28, 29, 0.84);
}

.path-box {
  display: grid;
  gap: 10px;
  min-height: 180px;
  padding: 18px;
  border-radius: 12px;
  background: rgba(241, 244, 245, 0.92);
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 14px;
}

.path-box p {
  margin: 0;
}

.care-advice-box {
  padding: 22px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(207, 230, 242, 0.34), rgba(241, 244, 245, 0.92));
  box-shadow: inset 4px 0 0 var(--ws-primary);
}

.prediction-state-shell {
  padding: 16px 18px;
  border-radius: 14px;
}

.prediction-state-shell strong {
  display: block;
  margin-bottom: 6px;
  font-family: var(--ws-font-headline);
  font-size: 16px;
}

.prediction-state-shell p {
  margin: 0;
}

.prediction-loading {
  background: rgba(207, 230, 242, 0.65);
  color: var(--ws-secondary);
}

.prediction-error {
  background: rgba(255, 218, 214, 0.88);
  color: var(--ws-error);
}

.insight-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(190, 200, 201, 0.52);
}

.patient-secondary-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  gap: 22px;
}

.prediction-card,
.timeline-card {
  display: grid;
  gap: 16px;
}

.prediction-box {
  display: grid;
  gap: 14px;
}

.prediction-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.prediction-head strong,
.prediction-head span {
  font-size: 18px;
}

@media (max-width: 1240px) {
  .patient-detail-layout,
  .insight-grid,
  .patient-secondary-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .patient-detail-hero {
    display: grid;
    padding: 24px;
  }

  .hero-actions {
    justify-content: flex-start;
  }
}
</style>
