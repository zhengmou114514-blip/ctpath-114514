<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceContext } from '../composables/workspaceContext'
import { getSystemAudit } from '../services/api'
import { buildModelBoardSnapshot } from '../services/modelBoardAdapter'
import { listModelDatasets, listTrainingTasks, syncModelCenterState } from '../services/modelTrainingAdapter'
import type { PatientSummary, SystemAuditLog } from '../services/types'

const workspace = useWorkspaceContext()
const router = useRouter()

const loading = ref(false)
const auditError = ref('')
const auditRows = ref<SystemAuditLog[]>([])
const datasetsCount = ref(0)
const trainingTasksCount = ref(0)
const selectedDebugPatientId = ref(workspace.selectedPatientId || workspace.allPatients[0]?.patientId || '')

const board = computed(() =>
  buildModelBoardSnapshot({
    modelMetrics: workspace.modelMetrics,
  })
)

const modelAuditRows = computed(() =>
  auditRows.value.filter((row) => {
    const haystack = `${row.action} ${row.path} ${row.detail}`.toLowerCase()
    return haystack.includes('predict') || haystack.includes('model') || haystack.includes('/api/predict')
  })
)

const currentUser = computed(() => workspace.currentDoctor)
const patients = computed<PatientSummary[]>(() => workspace.allPatients ?? [])
const selectedDebugPatient = computed(() => {
  if (workspace.selectedPatient?.patientId === selectedDebugPatientId.value) return workspace.selectedPatient
  return patients.value.find((patient) => patient.patientId === selectedDebugPatientId.value) ?? workspace.selectedPatient
})
const latestOutput = computed(() => workspace.predictionResult)

const modelHealthLabel = computed(() => {
  if (!workspace.health) return '状态待加载'
  if (workspace.health.model_available) return '模型可用'
  if (workspace.health.model_error) return `降级运行：${workspace.health.model_error}`
  return '模型不可用'
})

const dataSourceLabel = computed(() => (workspace.health?.status === 'ok' ? '业务数据源正常' : '服务连接中'))

const latencyLabel = computed(() => {
  const generatedAt = latestOutput.value?.generatedAt
  if (!generatedAt) return '暂无最近推理耗时'
  return '后端 RequestTimingMiddleware 记录接口耗时；本页保留最近推理时间点'
})

const fallbackReason = computed(() => {
  if (workspace.health?.model_error) return workspace.health.model_error
  if (latestOutput.value?.mode === 'similar-case') return latestOutput.value.supportSummary || '当前输出来自相似病例或规则回退。'
  if (latestOutput.value?.adviceMeta?.note) return latestOutput.value.adviceMeta.note
  return '当前未触发回退。'
})

const errorLogText = computed(() => {
  if (workspace.predictionError) return workspace.predictionError
  if (workspace.health?.model_error) return `模型健康检查：${workspace.health.model_error}`
  if (modelAuditRows.value[0]?.detail) return modelAuditRows.value[0].detail
  return '暂无错误日志。'
})

const rawInputPayload = computed(() => {
  const patient = selectedDebugPatient.value
  const selectedPatientDetail = workspace.selectedPatient
  return {
    patientId: selectedDebugPatientId.value || patient?.patientId || '',
    asOfTime: patient?.lastVisit || '',
    modelVersion: board.value.currentModelVersion,
    modelName: board.value.currentModelName,
    dataSourceStatus: dataSourceLabel.value,
    modelAvailable: Boolean(workspace.health?.model_available),
    patientSnapshot: patient
      ? {
          name: patient.name,
          primaryDisease: patient.primaryDisease,
          currentStage: patient.currentStage,
          riskLevel: patient.riskLevel,
          dataSupport: patient.dataSupport,
        }
      : null,
    timeline: selectedPatientDetail && patient && selectedPatientDetail.patientId === patient.patientId ? selectedPatientDetail.timeline : [],
  }
})

const rawOutputPayload = computed(() => latestOutput.value ?? {
  patientId: selectedDebugPatientId.value,
  status: '等待推理',
  strategy: '尚未运行',
  message: '尚未在当前会话触发模型推理。',
})

const rawInputJson = computed(() => JSON.stringify(rawInputPayload.value, null, 2))
const rawOutputJson = computed(() => JSON.stringify(rawOutputPayload.value, null, 2))

function formatDateTime(value?: string | null) {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function formatActor(value?: string | null) {
  if (!value) return '--'
  const labels: Record<string, string> = {
    demo_clinic: '门诊医生',
    demo_nurse: '主管护士',
    demo_pharmacist: '主管药师',
    demo_admin: '系统管理员',
    demo_archivist: '档案管理员',
    demo_specialist: '专科医生',
  }
  return labels[value] ?? value
}

async function refreshOperations() {
  loading.value = true
  auditError.value = ''
  try {
    await Promise.all([workspace.refreshModelMetrics(), syncModelCenterState()])
    const auditResp = await getSystemAudit(120)
    auditRows.value = auditResp.items
    datasetsCount.value = listModelDatasets().length
    trainingTasksCount.value = listTrainingTasks().length
  } catch (error) {
    auditError.value = error instanceof Error ? error.message : '模型运行台加载失败。'
  } finally {
    loading.value = false
  }
}

async function handleSampleChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  selectedDebugPatientId.value = value
  if (value && workspace.selectedPatientId !== value) {
    await workspace.openPatient(value, 'doctor')
  }
}

async function runDebugPrediction() {
  if (!selectedDebugPatientId.value) return
  if (workspace.selectedPatientId !== selectedDebugPatientId.value) {
    await workspace.openPatient(selectedDebugPatientId.value, 'doctor')
  }
  await workspace.runPrediction(true)
}

function openTrainingCenter() {
  workspace.selectSection('training-center')
  void router.push({ name: 'training-center' })
}

function openModelDashboard() {
  workspace.selectSection('model-dashboard')
  void router.push({ name: 'model-dashboard' })
}

onMounted(() => {
  void refreshOperations()
})

watch(
  () => workspace.selectedPatientId,
  (patientId) => {
    if (patientId) {
      selectedDebugPatientId.value = patientId
    }
  }
)
</script>

<template>
  <section class="workspace-page model-operations-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">模型中心</p>
        <h1>模型运行台</h1>
        <p>单独承接模型治理信息，展示验证样本、原始输入 JSON、原始输出 JSON、耗时线索、回退原因和错误日志。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="openModelDashboard">返回模型看板</button>
        <button class="primary-button" type="button" @click="openTrainingCenter">进入训练中心</button>
      </div>
    </header>

    <p v-if="auditError" class="error-banner">{{ auditError }}</p>

    <section class="operations-metrics">
      <article class="clinical-card metric-panel">
        <span>验证样本</span>
        <strong>{{ selectedDebugPatient?.name || '--' }}</strong>
        <small>{{ selectedDebugPatientId || '未选择患者样本' }}</small>
      </article>
      <article class="clinical-card metric-panel">
        <span>推理耗时</span>
        <strong>{{ latestOutput?.generatedAt ? formatDateTime(latestOutput.generatedAt) : '--' }}</strong>
        <small>{{ latencyLabel }}</small>
      </article>
      <article class="clinical-card metric-panel">
        <span>模型状态</span>
        <strong>{{ board.currentModelVersion }}</strong>
        <small>{{ modelHealthLabel }}</small>
      </article>
      <article class="clinical-card metric-panel">
        <span>训练资源</span>
        <strong>{{ trainingTasksCount }}</strong>
        <small>{{ datasetsCount }} 个数据集</small>
      </article>
    </section>

    <section class="debug-control-panel clinical-card">
      <div class="section-header">
        <div>
          <h2>手动验证样本</h2>
          <p>从患者样本中选择一条记录，必要时触发一次真实预测，运行记录不会进入医生首页。</p>
        </div>
        <button class="primary-button" type="button" :disabled="workspace.loadingPredict || !selectedDebugPatientId" @click="runDebugPrediction">
          {{ workspace.loadingPredict ? '推理中...' : '运行校验推理' }}
        </button>
      </div>
      <div class="debug-form-row">
        <label for="debug-patient-select">验证样本</label>
        <select id="debug-patient-select" :value="selectedDebugPatientId" @change="handleSampleChange">
          <option value="">请选择患者样本</option>
          <option v-for="patient in patients" :key="patient.patientId" :value="patient.patientId">
            {{ patient.patientId }} / {{ patient.name }} / {{ patient.primaryDisease }}
          </option>
        </select>
      </div>
    </section>

    <section class="debug-json-grid">
      <article class="clinical-card json-panel">
        <div class="section-header">
          <div>
            <h2>原始输入 JSON</h2>
            <p>患者样本、数据源状态和模型版本上下文。</p>
          </div>
        </div>
        <pre>{{ rawInputJson }}</pre>
      </article>

      <article class="clinical-card json-panel">
        <div class="section-header">
          <div>
            <h2>原始输出 JSON</h2>
            <p>展示最近一次预测返回的预测策略、Top-K、证据和建议。</p>
          </div>
        </div>
        <pre>{{ rawOutputJson }}</pre>
      </article>
    </section>

    <section class="operations-grid">
      <article class="clinical-card info-panel">
        <div class="section-header">
          <div>
            <h2>运行上下文</h2>
            <p>展示当前用户、数据源、模型版本和最近一次输出状态。</p>
          </div>
        </div>

        <dl class="detail-list">
          <div>
            <dt>人员</dt>
            <dd>{{ currentUser?.title || currentUser?.name || '--' }}</dd>
          </div>
          <div>
            <dt>姓名</dt>
            <dd>{{ currentUser?.name || '--' }}</dd>
          </div>
          <div>
            <dt>职称</dt>
            <dd>{{ currentUser?.title || '--' }}</dd>
          </div>
          <div>
            <dt>科室</dt>
            <dd>{{ currentUser?.department || '--' }}</dd>
          </div>
          <div>
            <dt>角色</dt>
            <dd>{{ currentUser?.role || '--' }}</dd>
          </div>
          <div>
            <dt>数据源</dt>
            <dd>{{ dataSourceLabel }}</dd>
          </div>
          <div>
            <dt>输出策略</dt>
            <dd>{{ latestOutput?.strategy || '--' }}</dd>
          </div>
        </dl>
      </article>

      <article class="clinical-card info-panel">
        <div class="section-header">
          <div>
            <h2>模型信息</h2>
            <p>展示当前模型版本、训练时间和线上推理概览。</p>
          </div>
        </div>

        <dl class="detail-list">
          <div>
            <dt>模型名称</dt>
            <dd>{{ board.currentModelName }}</dd>
          </div>
          <div>
            <dt>模型版本</dt>
            <dd>{{ board.currentModelVersion }}</dd>
          </div>
          <div>
            <dt>最近训练时间</dt>
            <dd>{{ formatDateTime(board.recentTrainingTime) }}</dd>
          </div>
          <div>
            <dt>MRR</dt>
            <dd>{{ board.mrr ? `${(board.mrr * 100).toFixed(1)}%` : '--' }}</dd>
          </div>
          <div>
            <dt>Hits@10</dt>
            <dd>{{ board.hits10 ? `${(board.hits10 * 100).toFixed(1)}%` : '--' }}</dd>
          </div>
          <div>
            <dt>近 7 天调用量</dt>
            <dd>{{ board.recentInferenceCalls ?? '--' }}</dd>
          </div>
          <div>
            <dt>回退比例</dt>
            <dd>{{ board.fallbackRatio ? `${(board.fallbackRatio * 100).toFixed(1)}%` : '--' }}</dd>
          </div>
        </dl>
      </article>
    </section>

    <section class="operations-grid">
      <article class="clinical-card info-panel">
        <div class="section-header">
          <div>
            <h2>错误日志</h2>
            <p>展示预测错误、模型健康错误或最近模型审计摘要。</p>
          </div>
          <button class="secondary-button" type="button" :disabled="loading" @click="refreshOperations">刷新</button>
        </div>

        <div class="debug-log-box">{{ errorLogText }}</div>
        <div v-if="modelAuditRows.length" class="audit-list">
          <article v-for="row in modelAuditRows.slice(0, 6)" :key="row.logId" class="audit-item">
            <strong>{{ formatActor(row.username) }}</strong>
            <p>{{ row.method }} {{ row.path }}</p>
            <small>{{ formatDateTime(row.createdAt) }} / {{ row.result }}</small>
          </article>
        </div>
      </article>

      <article class="clinical-card info-panel">
        <div class="section-header">
          <div>
            <h2>回退原因</h2>
            <p>集中说明当前模型降级、相似病例回退或建议生成回退原因。</p>
          </div>
        </div>
        <div class="debug-log-box">{{ fallbackReason }}</div>
        <ul class="bullet-list">
          <li>患者级正式阅读仍在“患者详情 / 模型洞察”。</li>
          <li>训练数据导入和训练任务发起仍在“训练中心”。</li>
          <li>本页仅服务模型运行核验和治理验收，不作为医生主流程入口。</li>
        </ul>
      </article>
    </section>
  </section>
</template>

<style scoped>
.model-operations-page {
  display: grid;
  gap: 24px;
}

.operations-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.metric-panel {
  display: grid;
  gap: 10px;
}

.metric-panel span,
.metric-panel small {
  color: rgba(63, 72, 73, 0.74);
}

.metric-panel strong {
  font-size: clamp(26px, 4vw, 38px);
}

.operations-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.debug-control-panel {
  display: grid;
  gap: 16px;
}

.debug-form-row {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  align-items: center;
  gap: 14px;
}

.debug-form-row label {
  color: rgba(63, 72, 73, 0.72);
  font-weight: 700;
}

.debug-form-row select {
  min-height: 38px;
  border: 1px solid rgba(155, 178, 188, 0.82);
  border-radius: 6px;
  background: #fff;
  padding: 0 10px;
  color: var(--ws-on-surface);
}

.debug-json-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.json-panel {
  min-width: 0;
  display: grid;
  gap: 14px;
}

.json-panel pre {
  overflow: auto;
  max-height: 420px;
  margin: 0;
  border: 1px solid rgba(155, 178, 188, 0.55);
  border-radius: 8px;
  background: #101820;
  padding: 14px;
  color: #d8f5ff;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.debug-log-box {
  min-height: 104px;
  border: 1px solid rgba(155, 178, 188, 0.55);
  border-radius: 8px;
  background: rgba(241, 248, 252, 0.82);
  padding: 14px;
  color: var(--ws-on-surface);
  line-height: 1.7;
}

.info-panel {
  display: grid;
  gap: 18px;
}

.detail-list {
  display: grid;
  gap: 12px;
  margin: 0;
}

.detail-list div {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(190, 200, 201, 0.45);
}

.detail-list dt {
  color: rgba(63, 72, 73, 0.72);
  font-family: var(--ws-font-headline);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.detail-list dd {
  margin: 0;
  color: var(--ws-on-surface);
  font-weight: 600;
}

.audit-list {
  display: grid;
  gap: 12px;
}

.audit-item {
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(241, 244, 245, 0.92);
}

.audit-item p,
.audit-item small {
  margin: 6px 0 0;
  color: rgba(63, 72, 73, 0.8);
}

.compact-empty {
  min-height: 180px;
}

@media (max-width: 1180px) {
  .operations-metrics,
  .operations-grid,
  .debug-json-grid {
    grid-template-columns: 1fr;
  }

  .debug-form-row {
    grid-template-columns: 1fr;
  }
}
</style>
