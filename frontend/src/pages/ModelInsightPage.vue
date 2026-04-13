<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  createTrainingTask,
  getCurrentModelVersionFromTasks,
  importModelDataset,
  listModelDatasets,
  listTrainingTasks,
} from '../services/modelTrainingAdapter'
import type {
  ModelDatasetImportRecord,
  ModelMetricsResponse,
  ModelTrainingParams,
  ModelTrainingTaskRecord,
} from '../services/types'

const props = defineProps<{
  modelMetrics: ModelMetricsResponse | null
  patientCount: number
  followupCount: number
  systemMode: string
}>()

const emit = defineEmits<{
  refresh: []
  exportReport: []
}>()

const datasets = ref<ModelDatasetImportRecord[]>([])
const tasks = ref<ModelTrainingTaskRecord[]>([])
const loading = ref(false)
const localError = ref('')

const datasetForm = reactive({
  datasetName: '',
})

const trainForm = reactive<{
  datasetId: string
  modelName: string
  params: ModelTrainingParams
}>({
  datasetId: '',
  modelName: 'CTpath-KGE-v2',
  params: {
    epochs: 60,
    batchSize: 256,
    learningRate: 0.001,
    embeddingDim: 256,
    optimizer: 'adam',
  },
})

const currentMetric = computed(() => props.modelMetrics?.currentModel ?? null)
const currentModelName = computed(() => currentMetric.value?.model || '--')

const currentVersion = computed(() => getCurrentModelVersionFromTasks())

const onlineInferenceStats = computed(() => {
  const m = currentMetric.value
  return {
    mrr: m?.mrr ?? null,
    hits1: m?.hits1 ?? null,
    hits10: m?.hits10 ?? null,
  }
})

function toPercent(value?: number | null): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return '--'
  return `${(value * 100).toFixed(1)}%`
}

function statusLabel(status: ModelTrainingTaskRecord['status']): string {
  if (status === 'queued') return '排队中'
  if (status === 'running') return '训练中'
  if (status === 'succeeded') return '已完成'
  return '失败'
}

function statusTone(status: ModelTrainingTaskRecord['status']): string {
  if (status === 'succeeded') return 'tone-ok'
  if (status === 'running') return 'tone-running'
  if (status === 'queued') return 'tone-queued'
  return 'tone-failed'
}

function refreshOffline() {
  datasets.value = listModelDatasets()
  tasks.value = listTrainingTasks()
  const firstDataset = datasets.value[0]
  if (!trainForm.datasetId && firstDataset) {
    trainForm.datasetId = firstDataset.datasetId
  }
}

async function onDatasetFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  localError.value = ''
  loading.value = true
  try {
    await importModelDataset(file, datasetForm.datasetName)
    datasetForm.datasetName = ''
    refreshOffline()
  } catch (error) {
    localError.value = error instanceof Error ? error.message : '数据集导入失败'
  } finally {
    loading.value = false
    input.value = ''
  }
}

function submitTrainingTask() {
  localError.value = ''
  const target = datasets.value.find((item) => item.datasetId === trainForm.datasetId)
  if (!target) {
    localError.value = '请先选择数据集。'
    return
  }

  createTrainingTask({
    datasetId: target.datasetId,
    datasetName: target.datasetName,
    modelName: trainForm.modelName,
    params: trainForm.params,
  })

  refreshOffline()
}

onMounted(() => {
  refreshOffline()
})
</script>

<template>
  <section class="model-center-page">
    <header class="page-header card">
      <div class="header-left">
        <h2>模型中心 / 模型洞察</h2>
        <span class="module-badge">在线推理与离线训练分区治理</span>
      </div>
      <div class="header-actions">
        <button class="secondary-button" @click="emit('refresh')">刷新线上指标</button>
        <button class="primary-button" @click="emit('exportReport')">导出模型报告</button>
      </div>
    </header>

    <section class="card section-block">
      <div class="section-head">
        <h3>在线推理结果</h3>
        <span>服务模式：{{ systemMode }}</span>
      </div>

      <div class="stats-grid">
        <article class="stat-card">
          <span>患者总数</span>
          <strong>{{ patientCount }}</strong>
        </article>
        <article class="stat-card">
          <span>随访任务</span>
          <strong>{{ followupCount }}</strong>
        </article>
        <article class="stat-card">
          <span>当前在线模型</span>
          <strong>{{ currentModelName }}</strong>
        </article>
      </div>

      <div class="metrics-grid">
        <article class="metric-card">
          <span>MRR</span>
          <strong>{{ toPercent(onlineInferenceStats.mrr) }}</strong>
        </article>
        <article class="metric-card">
          <span>Hits@1</span>
          <strong>{{ toPercent(onlineInferenceStats.hits1) }}</strong>
        </article>
        <article class="metric-card">
          <span>Hits@10</span>
          <strong>{{ toPercent(onlineInferenceStats.hits10) }}</strong>
        </article>
      </div>
    </section>

    <section class="card section-block">
      <div class="section-head">
        <h3>离线训练管理</h3>
        <span>训练操作仅限模型管理区域</span>
      </div>

      <p v-if="localError" class="error-tip">{{ localError }}</p>

      <div class="version-card">
        <div>
          <span>当前模型版本</span>
          <strong>{{ currentVersion.version }} / {{ currentVersion.modelName }}</strong>
          <small>训练完成时间：{{ currentVersion.trainedAt === '--' ? '--' : currentVersion.trainedAt.replace('T', ' ').slice(0, 16) }}</small>
        </div>
        <div class="version-metrics" v-if="currentVersion.metrics">
          <span>MRR {{ toPercent(currentVersion.metrics.mrr) }}</span>
          <span>Hits@1 {{ toPercent(currentVersion.metrics.hits1) }}</span>
          <span>Hits@10 {{ toPercent(currentVersion.metrics.hits10) }}</span>
        </div>
      </div>

      <div class="offline-grid">
        <article class="panel-block">
          <h4>数据集导入</h4>
          <label>
            <span>数据集名称（可选）</span>
            <input v-model="datasetForm.datasetName" type="text" placeholder="如 chronic_2026Q2" />
          </label>
          <label class="upload-btn" :class="{ disabled: loading }">
            <input type="file" accept=".csv,text/csv" :disabled="loading" @change="onDatasetFileChange" />
            导入 CSV 数据集
          </label>
          <small class="hint">TODO：接入对象存储和数据集注册中心 API。</small>

          <div v-if="datasets.length" class="table-lite">
            <header>
              <span>名称</span><span>文件</span><span>行数</span><span>状态</span>
            </header>
            <article v-for="ds in datasets" :key="ds.datasetId">
              <span>{{ ds.datasetName }}</span>
              <span>{{ ds.fileName }}</span>
              <span>{{ ds.rowCount }}</span>
              <span>{{ ds.status }}</span>
            </article>
          </div>
          <p v-else class="empty-state">暂无导入数据集</p>
        </article>

        <article class="panel-block">
          <h4>训练任务创建</h4>
          <label>
            <span>选择数据集</span>
            <select v-model="trainForm.datasetId">
              <option value="">请选择</option>
              <option v-for="ds in datasets" :key="`opt-${ds.datasetId}`" :value="ds.datasetId">
                {{ ds.datasetName }} ({{ ds.rowCount }}行)
              </option>
            </select>
          </label>
          <label>
            <span>模型名称</span>
            <input v-model="trainForm.modelName" type="text" />
          </label>

          <div class="param-grid">
            <label><span>Epochs</span><input v-model.number="trainForm.params.epochs" type="number" min="1" /></label>
            <label><span>Batch</span><input v-model.number="trainForm.params.batchSize" type="number" min="1" /></label>
            <label><span>LR</span><input v-model.number="trainForm.params.learningRate" type="number" step="0.0001" min="0.0001" /></label>
            <label><span>Embedding</span><input v-model.number="trainForm.params.embeddingDim" type="number" min="16" step="16" /></label>
            <label class="full"><span>Optimizer</span><select v-model="trainForm.params.optimizer"><option value="adam">adam</option><option value="adamw">adamw</option><option value="sgd">sgd</option></select></label>
          </div>

          <div class="actions">
            <button class="primary-button" :disabled="loading || !datasets.length" @click="submitTrainingTask">创建训练任务</button>
            <button class="secondary-button" @click="refreshOffline">刷新任务状态</button>
          </div>
        </article>
      </div>

      <article class="panel-block">
        <h4>训练日志 / 任务状态</h4>
        <div v-if="tasks.length" class="table-lite">
          <header>
            <span>任务ID</span><span>数据集</span><span>状态</span><span>模型</span><span>指标</span><span>日志</span>
          </header>
          <article v-for="task in tasks" :key="task.taskId">
            <span>{{ task.taskId }}</span>
            <span>{{ task.datasetName }}</span>
            <span><em class="status-pill" :class="statusTone(task.status)">{{ statusLabel(task.status) }}</em></span>
            <span>{{ task.modelName }}</span>
            <span>{{ task.metrics ? `MRR ${toPercent(task.metrics.mrr)} / H@1 ${toPercent(task.metrics.hits1)} / H@10 ${toPercent(task.metrics.hits10)}` : '--' }}</span>
            <span>{{ task.logs[task.logs.length - 1] || '--' }}</span>
          </article>
        </div>
        <p v-else class="empty-state">暂无训练任务</p>
      </article>
    </section>
  </section>
</template>

<style scoped>
.model-center-page {
  padding: 24px;
  display: grid;
  gap: 20px;
}

.page-header,
.section-block,
.panel-block,
.stat-card,
.metric-card,
.version-card {
  border: 1px solid #d7e1ec;
  border-radius: 10px;
  background: #fff;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: #1f3854;
}

.module-badge {
  padding: 3px 10px;
  border-radius: 4px;
  background: #eef5fc;
  color: #2d5f8f;
  font-size: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.section-block {
  padding: 14px;
  display: grid;
  gap: 12px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.section-head h3,
.panel-block h4 {
  margin: 0;
  color: #1e3a5a;
}

.section-head span {
  font-size: 12px;
  color: #607790;
}

.stats-grid,
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.stat-card,
.metric-card {
  padding: 10px;
  display: grid;
  gap: 4px;
}

.stat-card span,
.metric-card span {
  font-size: 12px;
  color: #607790;
}

.stat-card strong,
.metric-card strong {
  font-size: 20px;
  color: #1f3854;
}

.version-card {
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  background: #f8fbff;
}

.version-card strong {
  display: block;
  font-size: 16px;
  color: #1f3854;
}

.version-card small {
  color: #61768d;
}

.version-metrics {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: #355b82;
}

.offline-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.panel-block {
  padding: 10px;
  display: grid;
  gap: 8px;
}

.panel-block label {
  display: grid;
  gap: 4px;
}

.panel-block label span {
  font-size: 12px;
  color: #5b728b;
}

.panel-block input,
.panel-block select {
  border: 1px solid #c8d5e4;
  border-radius: 6px;
  background: #fff;
  padding: 6px 8px;
  font-size: 12px;
}

.upload-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #c8d5e4;
  border-radius: 6px;
  background: #fff;
  padding: 8px 10px;
  font-size: 12px;
  color: #274a6f;
  cursor: pointer;
}

.upload-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-btn input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.hint {
  color: #6f8296;
  font-size: 12px;
}

.param-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.param-grid .full {
  grid-column: span 2;
}

.actions {
  display: flex;
  gap: 8px;
}

.table-lite {
  border: 1px solid #d6e0eb;
  border-radius: 8px;
  overflow: hidden;
}

.table-lite header,
.table-lite article {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  padding: 8px;
  font-size: 12px;
}

.table-lite header {
  background: #edf3f9;
  color: #3f5e7e;
  font-weight: 600;
}

.table-lite article {
  border-top: 1px solid #e4ecf4;
  color: #2a4a6a;
}

.panel-block > .table-lite header,
.panel-block > .table-lite article {
  grid-template-columns: 1.1fr 1fr .8fr .9fr 1.6fr 1.6fr;
}

.status-pill {
  display: inline-flex;
  border: 1px solid;
  border-radius: 999px;
  padding: 2px 8px;
  font-style: normal;
  font-size: 12px;
}

.tone-ok {
  color: #1d7b5c;
  background: #e9f8f1;
  border-color: #bde7d1;
}

.tone-running {
  color: #9b6518;
  background: #fff4e2;
  border-color: #efdbb2;
}

.tone-queued {
  color: #355b82;
  background: #ecf4fb;
  border-color: #c9dff2;
}

.tone-failed {
  color: #a4383f;
  background: #fdeced;
  border-color: #efc2c5;
}

.error-tip,
.empty-state {
  margin: 0;
  border: 1px dashed #b9c8d8;
  border-radius: 8px;
  padding: 8px;
  font-size: 12px;
  color: #61768d;
}

.error-tip {
  border-style: solid;
  border-color: #efc2c5;
  background: #fff0f2;
  color: #a4383f;
}

@media (max-width: 1320px) {
  .stats-grid,
  .metrics-grid,
  .offline-grid,
  .param-grid,
  .table-lite header,
  .table-lite article,
  .panel-block > .table-lite header,
  .panel-block > .table-lite article {
    grid-template-columns: 1fr;
  }

  .param-grid .full {
    grid-column: span 1;
  }

  .version-card,
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
