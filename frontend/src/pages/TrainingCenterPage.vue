<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceContext } from '../composables/workspaceContext'
import {
  createTrainingTask,
  importModelDataset,
  listModelDatasets,
  listTrainingTasks,
} from '../services/modelTrainingAdapter'
import type { ModelTrainingParams } from '../services/types'

const workspace = useWorkspaceContext()
const router = useRouter()

const datasets = ref(listModelDatasets())
const tasks = ref(listTrainingTasks())
const datasetName = ref('')
const selectedDatasetId = ref('')
const selectedFile = ref<File | null>(null)
const modelName = ref('CTpath Temporal KG')
const importError = ref('')
const importSuccess = ref('')
const trainingError = ref('')
const isImporting = ref(false)
const isLaunching = ref(false)
const params = ref<ModelTrainingParams>({
  epochs: 32,
  batchSize: 128,
  learningRate: 0.001,
  embeddingDim: 200,
  optimizer: 'adamw',
})

let pollTimer: number | null = null

const runningTaskCount = computed(() => tasks.value.filter((item) => item.status === 'running').length)
const latestTask = computed(() => tasks.value[0] ?? null)
const selectedDataset = computed(() => datasets.value.find((item) => item.datasetId === selectedDatasetId.value) ?? null)

function refreshTrainingCenter() {
  datasets.value = listModelDatasets()
  tasks.value = listTrainingTasks()
  const firstDataset = datasets.value[0]
  if (!selectedDataset.value && firstDataset) {
    selectedDatasetId.value = firstDataset.datasetId
  }
}

function startPolling() {
  if (pollTimer !== null) return
  pollTimer = window.setInterval(() => {
    tasks.value = listTrainingTasks()
  }, 2000)
}

function stopPolling() {
  if (pollTimer === null) return
  window.clearInterval(pollTimer)
  pollTimer = null
}

function formatDateTime(value?: string) {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function statusLabel(status: string) {
  if (status === 'queued') return '排队中'
  if (status === 'running') return '训练中'
  if (status === 'succeeded') return '已完成'
  if (status === 'failed') return '失败'
  return status || '--'
}

function statusTagType(status: string) {
  if (status === 'queued') return 'info'
  if (status === 'running') return 'warning'
  if (status === 'succeeded') return 'success'
  if (status === 'failed') return 'danger'
  return 'info'
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
}

async function handleImportDataset() {
  if (!selectedFile.value) {
    importError.value = '请先选择一个 CSV 数据集文件。'
    importSuccess.value = ''
    return
  }

  isImporting.value = true
  importError.value = ''
  importSuccess.value = ''

  try {
    const record = await importModelDataset(selectedFile.value, datasetName.value)
    refreshTrainingCenter()
    selectedDatasetId.value = record.datasetId
    datasetName.value = ''
    selectedFile.value = null
    importSuccess.value = `数据集“${record.datasetName}”已导入，共识别 ${record.rowCount} 行。`
  } catch (error) {
    importError.value = error instanceof Error ? error.message : '数据集导入失败，请稍后重试。'
  } finally {
    isImporting.value = false
  }
}

async function handleLaunchTraining() {
  if (!selectedDataset.value) {
    trainingError.value = '请先选择一个可用数据集。'
    return
  }

  isLaunching.value = true
  trainingError.value = ''

  try {
    createTrainingTask({
      datasetId: selectedDataset.value.datasetId,
      datasetName: selectedDataset.value.datasetName,
      modelName: modelName.value.trim() || 'CTpath Temporal KG',
      params: params.value,
    })
    refreshTrainingCenter()
  } catch (error) {
    trainingError.value = error instanceof Error ? error.message : '训练任务发起失败，请稍后重试。'
  } finally {
    isLaunching.value = false
  }
}

function handleBackToModelDashboard() {
  workspace.selectSection('model-dashboard')
  void router.push({ name: 'model-dashboard' })
}

onMounted(() => {
  refreshTrainingCenter()
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<template>
  <section class="training-center-page workstation-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">模型中心</p>
        <h1>训练中心</h1>
        <p>在模型中心域内完成数据集导入、训练任务发起与任务状态跟踪，不把训练操作混入医生主工作台。</p>
      </div>
      <div class="header-actions">
        <el-button @click="refreshTrainingCenter">刷新状态</el-button>
        <el-button type="primary" @click="handleBackToModelDashboard">返回模型看板</el-button>
      </div>
    </header>

    <section class="metric-grid three">
      <article class="metric-card">
        <span>已导入数据集</span>
        <strong>{{ datasets.length }}</strong>
        <p>仅作为当前项目前端训练台的暂存数据源</p>
      </article>
      <article class="metric-card">
        <span>运行中任务</span>
        <strong>{{ runningTaskCount }}</strong>
        <p>用于观察训练调度与进度，不进入医生主流程</p>
      </article>
      <article class="metric-card">
        <span>最近任务状态</span>
        <strong>{{ latestTask ? statusLabel(latestTask.status) : '暂无任务' }}</strong>
        <p>{{ latestTask ? `${latestTask.modelName} / ${latestTask.datasetName}` : '等待创建新的训练任务' }}</p>
      </article>
    </section>

    <section class="training-grid">
      <article class="clinical-card form-card">
        <div class="section-header">
          <div>
            <h2>数据集导入</h2>
            <p>训练 CSV 只进入训练中心暂存区，不直接进入正式患者业务表。</p>
          </div>
        </div>

        <el-alert v-if="importError" :title="importError" type="error" :closable="false" show-icon />
        <el-alert v-if="importSuccess" :title="importSuccess" type="success" :closable="false" show-icon />

        <div class="form-grid">
          <label class="field">
            <span>数据集名称</span>
            <input
              :value="datasetName"
              class="training-input"
              placeholder="例如：2026Q2 慢病训练集"
              @input="datasetName = ($event.target as HTMLInputElement).value"
            />
          </label>
          <label class="field">
            <span>CSV 文件</span>
            <input class="training-input file-input" type="file" accept=".csv" @change="handleFileChange" />
          </label>
        </div>

        <div class="action-row">
          <el-button type="primary" :loading="isImporting" @click="handleImportDataset">导入数据集</el-button>
        </div>
      </article>

      <article class="clinical-card form-card">
        <div class="section-header">
          <div>
            <h2>发起训练</h2>
            <p>基于已导入数据集创建训练任务，当前实现复用现有本地训练适配层。</p>
          </div>
        </div>

        <el-alert v-if="trainingError" :title="trainingError" type="error" :closable="false" show-icon />

        <div class="form-grid two-column">
          <label class="field">
            <span>训练数据集</span>
            <select v-model="selectedDatasetId" class="training-input">
              <option disabled value="">请选择数据集</option>
              <option v-for="item in datasets" :key="item.datasetId" :value="item.datasetId">
                {{ item.datasetName }} ({{ item.rowCount }} 行)
              </option>
            </select>
          </label>
          <label class="field">
            <span>模型名称</span>
            <input
              :value="modelName"
              class="training-input"
              placeholder="例如：CTpath Temporal KG"
              @input="modelName = ($event.target as HTMLInputElement).value"
            />
          </label>
          <label class="field">
            <span>Epochs</span>
            <input
              :value="params.epochs"
              class="training-input"
              type="number"
              min="1"
              @input="params = { ...params, epochs: Number(($event.target as HTMLInputElement).value || 1) }"
            />
          </label>
          <label class="field">
            <span>Batch Size</span>
            <input
              :value="params.batchSize"
              class="training-input"
              type="number"
              min="1"
              @input="params = { ...params, batchSize: Number(($event.target as HTMLInputElement).value || 1) }"
            />
          </label>
          <label class="field">
            <span>Learning Rate</span>
            <input
              :value="params.learningRate"
              class="training-input"
              type="number"
              step="0.0001"
              min="0.0001"
              @input="params = { ...params, learningRate: Number(($event.target as HTMLInputElement).value || 0.0001) }"
            />
          </label>
          <label class="field">
            <span>Embedding Dim</span>
            <input
              :value="params.embeddingDim"
              class="training-input"
              type="number"
              min="8"
              @input="params = { ...params, embeddingDim: Number(($event.target as HTMLInputElement).value || 8) }"
            />
          </label>
          <label class="field">
            <span>优化器</span>
            <select
              :value="params.optimizer"
              class="training-input"
              @change="params = { ...params, optimizer: ($event.target as HTMLSelectElement).value as ModelTrainingParams['optimizer'] }"
            >
              <option value="adam">Adam</option>
              <option value="adamw">AdamW</option>
              <option value="sgd">SGD</option>
            </select>
          </label>
        </div>

        <div class="action-row">
          <el-button type="primary" :loading="isLaunching" @click="handleLaunchTraining">发起训练</el-button>
        </div>
      </article>
    </section>

    <section class="training-grid">
      <article class="clinical-card">
        <div class="section-header">
          <div>
            <h2>数据集列表</h2>
            <p>显示导入暂存区中的训练数据集。</p>
          </div>
        </div>

        <ul v-if="datasets.length" class="record-list">
          <li v-for="item in datasets" :key="item.datasetId">
            <div class="record-head">
              <strong>{{ item.datasetName }}</strong>
              <el-tag :type="item.status === 'failed' ? 'danger' : item.status === 'processing' ? 'warning' : 'success'">
                {{ item.status === 'ready' ? '可用' : item.status === 'processing' ? '处理中' : '失败' }}
              </el-tag>
            </div>
            <p>{{ item.fileName }} / {{ item.rowCount }} 行 / {{ item.uploadedBy }}</p>
            <small>{{ formatDateTime(item.uploadedAt) }}</small>
          </li>
        </ul>
        <p v-else class="empty-inline">当前还没有导入训练数据集。</p>
      </article>

      <article class="clinical-card">
        <div class="section-header">
          <div>
            <h2>训练任务列表</h2>
            <p>追踪模型训练任务状态、关键指标与日志摘要。</p>
          </div>
        </div>

        <ul v-if="tasks.length" class="record-list task-list">
          <li v-for="task in tasks" :key="task.taskId">
            <div class="record-head">
              <strong>{{ task.modelName }}</strong>
              <el-tag :type="statusTagType(task.status)">{{ statusLabel(task.status) }}</el-tag>
            </div>
            <p>{{ task.datasetName }} / {{ task.triggeredBy }} / {{ formatDateTime(task.createdAt) }}</p>
            <div class="metric-inline">
              <span>MRR {{ task.metrics?.mrr?.toFixed(4) ?? '--' }}</span>
              <span>Hits@1 {{ task.metrics?.hits1?.toFixed(4) ?? '--' }}</span>
              <span>Hits@10 {{ task.metrics?.hits10?.toFixed(4) ?? '--' }}</span>
            </div>
            <small>{{ task.logs[task.logs.length - 1] }}</small>
          </li>
        </ul>
        <p v-else class="empty-inline">当前还没有训练任务。</p>
      </article>
    </section>
  </section>
</template>

<style scoped>
.training-center-page {
  display: grid;
  gap: 24px;
}

.training-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.form-card,
.form-grid,
.field,
.record-list,
.task-list {
  display: grid;
  gap: 14px;
}

.form-grid.two-column {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field span {
  color: var(--ws-text-muted);
  font-size: 12px;
  font-weight: 700;
}

.training-input {
  width: 100%;
  border: 1px solid var(--ws-border);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--ws-title);
  min-height: 44px;
  padding: 10px 12px;
  font: inherit;
}

.file-input {
  padding-block: 8px;
}

.action-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.record-list {
  margin: 0;
  padding: 0;
}

.record-list li {
  list-style: none;
  border: 1px solid var(--ws-border);
  border-radius: 16px;
  background: var(--ws-surface-soft);
  padding: 16px;
  display: grid;
  gap: 8px;
}

.record-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.record-list p,
.record-list small {
  margin: 0;
  color: var(--ws-text-muted);
}

.metric-inline {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: var(--ws-title);
  font-weight: 700;
}

.empty-inline {
  margin: 0;
  border: 1px dashed var(--ws-border-strong);
  border-radius: 16px;
  padding: 18px;
  color: var(--ws-text-muted);
  text-align: center;
}

@media (max-width: 1100px) {
  .training-grid,
  .form-grid.two-column {
    grid-template-columns: 1fr;
  }
}
</style>
