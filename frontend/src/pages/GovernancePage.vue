<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { buildModelBoardSnapshot } from '../services/modelBoardAdapter'
import {
  createTrainingTask,
  importModelDataset,
  listModelDatasets,
  listTrainingTasks,
} from '../services/modelTrainingAdapter'
import type {
  MaintenanceOverview,
  ModelCenterPanelKey,
  ModelDatasetImportRecord,
  ModelMetricsResponse,
  ModelTrainingParams,
  ModelTrainingTaskRecord,
} from '../services/types'

const props = defineProps<{
  doctorRole: string
  health: { mode?: string; model_available?: boolean } | null
  maintenance: MaintenanceOverview | null
  governanceModules: unknown
  modelMetrics: ModelMetricsResponse | null
  loadingGovernance: boolean
  loadingMaintenance: boolean
  loadingMetrics: boolean
  patientCount?: number
}>()

const emit = defineEmits<{
  refresh: []
}>()

const activePanel = ref<ModelCenterPanelKey>('offline')
const datasets = ref<ModelDatasetImportRecord[]>([])
const trainingTasks = ref<ModelTrainingTaskRecord[]>([])
const importingDataset = ref(false)
const creatingTask = ref(false)
const localMessage = ref('')
const localError = ref('')
const datasetFile = ref<File | null>(null)
const datasetName = ref('')
const selectedDatasetId = ref('')
const modelName = ref('CTpath-TransE')
const timer = ref<number | null>(null)

const trainingParams = reactive<ModelTrainingParams>({
  epochs: 120,
  batchSize: 512,
  learningRate: 0.001,
  embeddingDim: 200,
  optimizer: 'adam',
})

const board = computed(() =>
  buildModelBoardSnapshot({
    modelMetrics: props.modelMetrics,
    maintenance: props.maintenance,
    patientCount: props.patientCount ?? 0,
  })
)

const selectedDataset = computed(() =>
  datasets.value.find((item) => item.datasetId === selectedDatasetId.value) ?? null
)

const latestTask = computed(() => trainingTasks.value[0] ?? null)
const taskForLogs = computed(() => {
  if (latestTask.value) return latestTask.value
  return trainingTasks.value.find((item) => item.logs.length > 0) ?? null
})

const onlineServiceStatus = computed(() => {
  if (!props.health) return '未知'
  if (props.health.model_available === false) return '不可用'
  if (props.health.mode === 'demo') return '演示模式'
  return '可用'
})

const offlineStatus = computed(() => {
  if (!latestTask.value) return '暂无训练任务'
  return formatTaskStatus(latestTask.value.status)
})

function formatPercent(value: number | null | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return '--'
  return `${(value * 100).toFixed(1)}%`
}

function formatDateTime(value: string | undefined): string {
  if (!value || value === '--') return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function formatTaskStatus(status: ModelTrainingTaskRecord['status']): string {
  if (status === 'queued') return '排队中'
  if (status === 'running') return '训练中'
  if (status === 'succeeded') return '已完成'
  return '失败'
}

function clearFeedback() {
  localMessage.value = ''
  localError.value = ''
}

function refreshOfflineWorkspace() {
  datasets.value = listModelDatasets()
  trainingTasks.value = listTrainingTasks()
  const firstDataset = datasets.value[0]
  if (!selectedDatasetId.value && firstDataset) {
    selectedDatasetId.value = firstDataset.datasetId
  }
}

function onPickDatasetFile(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  datasetFile.value = file ?? null
}

async function onImportDataset() {
  clearFeedback()
  if (!datasetFile.value) {
    localError.value = '请先选择 CSV 数据集文件。'
    return
  }

  if (!datasetFile.value.name.toLowerCase().endsWith('.csv')) {
    localError.value = '仅支持 CSV 文件导入。'
    return
  }

  importingDataset.value = true
  try {
    const record = await importModelDataset(datasetFile.value, datasetName.value)
    refreshOfflineWorkspace()
    selectedDatasetId.value = record.datasetId
    datasetName.value = ''
    datasetFile.value = null
    localMessage.value = `数据集导入成功：${record.datasetName}（${record.rowCount} 行）`
  } catch (error) {
    localError.value = error instanceof Error ? error.message : '数据集导入失败。'
  } finally {
    importingDataset.value = false
  }
}

async function onCreateTrainingTask() {
  clearFeedback()
  if (!selectedDataset.value) {
    localError.value = '请先选择训练数据集。'
    return
  }

  creatingTask.value = true
  try {
    const task = createTrainingTask({
      datasetId: selectedDataset.value.datasetId,
      datasetName: selectedDataset.value.datasetName,
      modelName: modelName.value.trim() || 'CTpath-TransE',
      params: {
        epochs: Number(trainingParams.epochs),
        batchSize: Number(trainingParams.batchSize),
        learningRate: Number(trainingParams.learningRate),
        embeddingDim: Number(trainingParams.embeddingDim),
        optimizer: trainingParams.optimizer,
      },
    })
    refreshOfflineWorkspace()
    localMessage.value = `训练任务已创建：${task.taskId}`
  } catch (error) {
    localError.value = error instanceof Error ? error.message : '训练任务创建失败。'
  } finally {
    creatingTask.value = false
  }
}

function onRefreshAll() {
  emit('refresh')
  refreshOfflineWorkspace()
}

onMounted(() => {
  refreshOfflineWorkspace()
  timer.value = window.setInterval(() => {
    refreshOfflineWorkspace()
  }, 4000)
})

onBeforeUnmount(() => {
  if (timer.value !== null) {
    window.clearInterval(timer.value)
  }
})
</script>

<template>
  <section class="model-center-page">
    <header class="card page-header">
      <div>
        <h2>模型中心</h2>
        <p>统一管理在线推理与离线训练，不进入医生或档案员主流程。</p>
      </div>
      <button class="primary-button" @click="onRefreshAll">刷新模型中心</button>
    </header>

    <section class="panel-switch">
      <button class="secondary-button" :class="{ active: activePanel === 'offline' }" @click="activePanel = 'offline'">
        离线训练管理
      </button>
      <button class="secondary-button" :class="{ active: activePanel === 'online' }" @click="activePanel = 'online'">
        在线推理监控
      </button>
    </section>

    <p v-if="localMessage" class="banner success">{{ localMessage }}</p>
    <p v-if="localError" class="banner error">{{ localError }}</p>

    <section v-if="loadingMaintenance || loadingMetrics" class="card state-card">
      正在加载模型治理数据...
    </section>

    <template v-else>
      <section class="stats-grid">
        <article class="card stat-item">
          <span>当前模型版本</span>
          <strong>{{ board.currentModelVersion }}</strong>
          <small>{{ board.currentModelName }}</small>
        </article>
        <article class="card stat-item">
          <span>最近训练时间</span>
          <strong>{{ formatDateTime(board.recentTrainingTime) }}</strong>
          <small>最近训练任务状态：{{ board.recentTrainingTaskStatus }}</small>
        </article>
        <article class="card stat-item">
          <span>在线服务状态</span>
          <strong>{{ onlineServiceStatus }}</strong>
          <small>运行模式：{{ props.health?.mode ?? '--' }}</small>
        </article>
      </section>

      <section class="metrics-grid">
        <article class="card metric-item">
          <span>MRR</span>
          <strong>{{ formatPercent(board.mrr) }}</strong>
          <small>CHRONIC 指标基线：34.5%</small>
        </article>
        <article class="card metric-item">
          <span>Hits@1</span>
          <strong>{{ formatPercent(board.hits1) }}</strong>
          <small>CHRONIC 指标基线：23.2%</small>
        </article>
        <article class="card metric-item">
          <span>Hits@10</span>
          <strong>{{ formatPercent(board.hits10) }}</strong>
          <small>CHRONIC 指标基线：51.5%</small>
        </article>
      </section>

      <section v-if="activePanel === 'online'" class="ops-grid">
        <article class="card op-item">
          <span>最近推理调用量（7天）</span>
          <strong>{{ board.recentInferenceCalls ?? '--' }}</strong>
          <p>用于观察在线调用负载趋势与容量压力。</p>
        </article>
        <article class="card op-item">
          <span>回退比例</span>
          <strong>{{ formatPercent(board.fallbackRatio) }}</strong>
          <p>用于监控模型不可用或降级时的系统稳定性。</p>
        </article>
        <article class="card op-item">
          <span>数据集覆盖度</span>
          <strong>{{ formatPercent(board.datasetCoverage) }}</strong>
          <p>按本地导入数据集行数估算，反映训练数据准备程度。</p>
        </article>
      </section>

      <section v-else class="offline-grid">
        <article class="card trainer-item">
          <h3>数据集导入</h3>
          <p class="hint">仅在模型中心进行 CSV 数据集导入，不在前台诊疗流程出现。</p>
          <div class="form-grid">
            <label>
              <span>数据集名称</span>
              <input v-model="datasetName" type="text" placeholder="如 CHRONIC_2026Q2" />
            </label>
            <label>
              <span>CSV 文件</span>
              <input type="file" accept=".csv" @change="onPickDatasetFile" />
            </label>
          </div>
          <div class="actions">
            <button class="primary-button" :disabled="importingDataset" @click="onImportDataset">
              {{ importingDataset ? '导入中...' : '导入数据集' }}
            </button>
          </div>
          <p class="todo-note">TODO(api)：替换为后端对象存储与数据集注册服务。</p>
        </article>

        <article class="card trainer-item">
          <h3>训练任务创建</h3>
          <div class="form-grid">
            <label>
              <span>训练数据集</span>
              <select v-model="selectedDatasetId">
                <option value="">请选择数据集</option>
                <option v-for="item in datasets" :key="item.datasetId" :value="item.datasetId">
                  {{ item.datasetName }}（{{ item.rowCount }} 行）
                </option>
              </select>
            </label>
            <label>
              <span>模型名称</span>
              <input v-model="modelName" type="text" placeholder="如 CTpath-TransE" />
            </label>
          </div>
          <div class="params-grid">
            <label><span>Epochs</span><input v-model.number="trainingParams.epochs" type="number" min="1" /></label>
            <label><span>Batch Size</span><input v-model.number="trainingParams.batchSize" type="number" min="1" /></label>
            <label><span>Learning Rate</span><input v-model.number="trainingParams.learningRate" type="number" step="0.0001" min="0.0001" /></label>
            <label><span>Embedding Dim</span><input v-model.number="trainingParams.embeddingDim" type="number" min="32" /></label>
            <label>
              <span>Optimizer</span>
              <select v-model="trainingParams.optimizer">
                <option value="adam">Adam</option>
                <option value="adamw">AdamW</option>
                <option value="sgd">SGD</option>
              </select>
            </label>
          </div>
          <div class="actions">
            <button class="primary-button" :disabled="creatingTask || !selectedDatasetId" @click="onCreateTrainingTask">
              {{ creatingTask ? '创建中...' : '创建训练任务' }}
            </button>
          </div>
        </article>

        <article class="card trainer-item">
          <h3>任务状态与训练日志</h3>
          <p class="hint">离线训练状态每 4 秒刷新一次。</p>
          <div v-if="!trainingTasks.length" class="empty-mini">暂无训练任务</div>
          <div v-else class="task-table">
            <header>
              <span>任务ID</span>
              <span>数据集</span>
              <span>状态</span>
              <span>触发人</span>
              <span>创建时间</span>
            </header>
            <article v-for="task in trainingTasks" :key="task.taskId">
              <span>{{ task.taskId }}</span>
              <span>{{ task.datasetName }}</span>
              <span class="status-cell">{{ formatTaskStatus(task.status) }}</span>
              <span>{{ task.triggeredBy }}</span>
              <span>{{ formatDateTime(task.createdAt) }}</span>
            </article>
          </div>

          <div class="task-metrics">
            <p><span>离线训练总览状态</span><strong>{{ offlineStatus }}</strong></p>
            <p>
              <span>最新任务指标</span>
              <strong>
                MRR {{ latestTask?.metrics ? formatPercent(latestTask.metrics.mrr) : '--' }}
                / H@1 {{ latestTask?.metrics ? formatPercent(latestTask.metrics.hits1) : '--' }}
                / H@10 {{ latestTask?.metrics ? formatPercent(latestTask.metrics.hits10) : '--' }}
              </strong>
            </p>
          </div>

          <div class="log-box">
            <h4>训练日志</h4>
            <ul v-if="taskForLogs?.logs?.length">
              <li v-for="(line, idx) in taskForLogs.logs" :key="`${taskForLogs.taskId}-${idx}`">{{ line }}</li>
            </ul>
            <p v-else class="empty-mini">暂无日志</p>
          </div>
        </article>
      </section>

      <section class="card note-card">
        <strong>说明</strong>
        <p>本页将“数据集导入、训练任务、参数配置、训练日志”统一收纳到模型中心，医生/档案员主流程不再承载训练入口。</p>
      </section>
    </template>
  </section>
</template>

<style scoped>
.model-center-page {
  padding: 20px;
  display: grid;
  gap: 12px;
}

.page-header {
  padding: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.page-header h2 {
  margin: 0;
  color: #17344e;
}

.page-header p {
  margin: 4px 0 0;
  color: #5f758b;
  font-size: 13px;
}

.panel-switch {
  display: flex;
  gap: 8px;
}

.secondary-button.active {
  border-color: #275986;
  color: #275986;
  background: #eaf2f9;
}

.banner {
  margin: 0;
  border-radius: 8px;
  padding: 10px;
  font-size: 13px;
}

.banner.success {
  border: 1px solid #bde7d1;
  background: #eaf8f0;
  color: #1f7558;
}

.banner.error {
  border: 1px solid #efc2c5;
  background: #fff0f2;
  color: #a23840;
}

.state-card {
  padding: 14px;
  color: #5f758b;
  text-align: center;
}

.stats-grid,
.metrics-grid,
.ops-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.stat-item,
.metric-item,
.op-item,
.note-card,
.trainer-item {
  padding: 12px;
  display: grid;
  gap: 8px;
}

.stat-item span,
.metric-item span,
.op-item span {
  color: #60778e;
  font-size: 12px;
}

.stat-item strong,
.metric-item strong,
.op-item strong {
  color: #17344e;
  font-size: 20px;
}

.stat-item small,
.metric-item small,
.op-item p {
  margin: 0;
  color: #60778e;
  font-size: 12px;
}

.offline-grid {
  display: grid;
  gap: 10px;
}

.trainer-item h3 {
  margin: 0;
  color: #183c5d;
  font-size: 16px;
}

.hint {
  margin: 0;
  color: #5f758b;
  font-size: 12px;
}

.form-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.params-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

label {
  display: grid;
  gap: 4px;
}

label span {
  color: #60778e;
  font-size: 12px;
}

input,
select {
  border: 1px solid #c7d5e5;
  border-radius: 6px;
  padding: 6px 8px;
  background: #fff;
  font-size: 12px;
}

.actions {
  display: flex;
  justify-content: flex-end;
}

.task-table {
  border: 1px solid #d7e2ee;
  border-radius: 8px;
  overflow: hidden;
}

.task-table header,
.task-table article {
  display: grid;
  gap: 8px;
  padding: 8px;
  grid-template-columns: 1.3fr 1.1fr .8fr .8fr 1fr;
  font-size: 12px;
}

.task-table header {
  background: #eef4fa;
  color: #46627f;
  font-weight: 600;
}

.task-table article {
  border-top: 1px solid #e5edf5;
  color: #24405f;
}

.status-cell {
  font-weight: 600;
}

.task-metrics {
  border: 1px solid #d7e2ee;
  border-radius: 8px;
  padding: 8px;
  display: grid;
  gap: 6px;
  background: #fbfdff;
}

.task-metrics p {
  margin: 0;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  color: #3c5875;
}

.log-box {
  border: 1px solid #d7e2ee;
  border-radius: 8px;
  padding: 8px;
  background: #f9fbfd;
}

.log-box h4 {
  margin: 0 0 8px;
  color: #1b3b59;
  font-size: 14px;
}

.log-box ul {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 4px;
  color: #304f70;
  font-size: 12px;
}

.empty-mini {
  margin: 0;
  border: 1px dashed #bfd0e1;
  border-radius: 8px;
  padding: 8px;
  color: #60778e;
  text-align: center;
  font-size: 12px;
}

.todo-note {
  margin: 0;
  border: 1px dashed #d9caa1;
  border-radius: 8px;
  padding: 8px;
  color: #7f6930;
  background: #fff8eb;
  font-size: 12px;
}

.note-card p {
  margin: 0;
  color: #60778e;
  font-size: 13px;
}

@media (max-width: 1280px) {
  .stats-grid,
  .metrics-grid,
  .ops-grid,
  .form-grid,
  .params-grid,
  .task-table header,
  .task-table article {
    grid-template-columns: 1fr;
  }
}
</style>
