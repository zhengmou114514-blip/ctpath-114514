<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useWorkspaceContext } from '../composables/workspaceContext'
import { buildModelBoardSnapshot } from '../services/modelBoardAdapter'
import { listTrainingTasks, getCurrentModelVersionFromTasks } from '../services/modelTrainingAdapter'
import type { ModelTrainingTaskRecord } from '../services/types'

const workspace = useWorkspaceContext()

const trainingTasks = ref<ModelTrainingTaskRecord[]>([])
const selectedVersion = ref('')
const switching = ref(false)
const switchMessage = ref('')

const board = computed(() =>
  buildModelBoardSnapshot({
    modelMetrics: workspace.modelMetrics,
  })
)

const availableVersions = computed(() => {
  const succeeded = trainingTasks.value.filter((t) => t.status === 'succeeded' && t.metrics)
  return succeeded.map((t) => ({
    taskId: t.taskId,
    version: `v-${t.taskId.slice(-6)}`,
    modelName: t.modelName,
    trainedAt: t.finishedAt || t.createdAt,
    isCurrent: t.taskId === currentVersionTaskId.value,
  }))
})

const currentVersionTaskId = computed(() => {
  const succeeded = trainingTasks.value.find((t) => t.status === 'succeeded' && t.metrics)
  return succeeded?.taskId ?? ''
})

const modelHealth = computed(() => {
  if (!workspace.health) return { label: '状态待加载', tone: 'neutral' }
  if (workspace.health.model_available) return { label: '健康', tone: 'ok' }
  if (workspace.health.model_error) return { label: '降级运行', tone: 'warning' }
  return { label: '不可用', tone: 'danger' }
})

const loading = computed(() => workspace.loadingModelMetrics)
const dataSupportCoverage = computed(() => board.value.datasetCoverage)
const governanceSnapshot = computed(() => [
  { label: '模型版本', value: board.value.currentModelVersion, note: board.value.currentModelName },
  { label: '训练状态', value: board.value.recentTrainingTaskStatus, note: formatDateTime(board.value.recentTrainingTime) },
  { label: '调用量', value: formatNumber(board.value.recentInferenceCalls), note: '最近7天推理调用' },
  { label: '回退比例', value: formatPercent(board.value.fallbackRatio), note: '规则/相似病例回退占比' },
])
const recentAnomalies = computed(() => {
  const items = []
  if (workspace.health?.model_error) {
    items.push({
      time: '最近一次健康检查',
      level: 'warning',
      title: '模型服务降级',
      detail: workspace.health.model_error,
    })
  }
  if ((board.value.fallbackRatio ?? 0) >= 0.1) {
    items.push({
      time: '近 7 天',
      level: 'warning',
      title: '回退比例偏高',
      detail: '部分请求回退到相似病例或规则摘要，需要关注模型服务稳定性。',
    })
  }
  if (dataSupportCoverage.value < 0.7) {
    items.push({
      time: '当前快照',
      level: 'notice',
      title: '数据支持覆盖不足',
      detail: '部分患者病程事件或关系证据不足，可能影响预测解释完整度。',
    })
  }
  return items.length
    ? items
    : [
        {
          time: '当前快照',
          level: 'ok',
          title: '暂无明显异常',
          detail: '模型服务、数据支持覆盖和回退比例处于可演示状态。',
        },
      ]
})

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '待统计'
  return `${(value * 100).toFixed(1)}%`
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '待统计'
  return String(value)
}

function formatDateTime(value: string | undefined) {
  if (!value || value === '--') return '待同步'
  return value.replace('T', ' ').slice(0, 16)
}

async function handleRefresh() {
  await workspace.refreshModelMetrics()
  trainingTasks.value = listTrainingTasks()
  const cv = getCurrentModelVersionFromTasks(trainingTasks.value)
  selectedVersion.value = cv.version
}

async function handleVersionSwitch() {
  if (!selectedVersion.value || selectedVersion.value === board.value.currentModelVersion) return
  switching.value = true
  switchMessage.value = ''
  try {
    const target = availableVersions.value.find((v) => v.version === selectedVersion.value)
    if (target) {
      switchMessage.value = `已切换到版本 ${target.version}（${target.modelName}）。此操作需在模型服务端确认部署。`
    }
  } finally {
    switching.value = false
  }
}

onMounted(() => {
  if (!workspace.currentDoctor) return
  void handleRefresh()
})
</script>

<template>
  <section class="workspace-page model-dashboard-page">
    <header class="workstation-page-header dashboard-header">
      <div>
        <p class="eyebrow">模型辅助模块 / 管理员</p>
        <h1>模型看板</h1>
        <p>展示模型版本、运行指标、调用量、回退比例、健康状态和数据支持覆盖率。</p>
      </div>
      <button class="primary-button" type="button" :disabled="loading" @click="handleRefresh">
        {{ loading ? '刷新中...' : '刷新看板' }}
      </button>
    </header>

    <section class="dashboard-metrics">
      <article class="clinical-card metric-card">
        <span>模型版本</span>
        <strong>{{ board.currentModelVersion }}</strong>
        <small>{{ board.currentModelName }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>健康状态</span>
        <strong :class="`tone-${modelHealth.tone}`">{{ modelHealth.label }}</strong>
        <small>{{ workspace.health?.status === 'ok' ? '业务服务正常' : '服务状态待确认' }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>调用量</span>
        <strong>{{ formatNumber(board.recentInferenceCalls) }}</strong>
        <small>最近 7 天预测调用</small>
      </article>
      <article class="clinical-card metric-card">
        <span>回退比例</span>
        <strong>{{ formatPercent(board.fallbackRatio) }}</strong>
        <small>模型不可用或置信不足时回退</small>
      </article>
    </section>

    <section class="snapshot-grid">
      <article v-for="item in governanceSnapshot" :key="item.label" class="clinical-card snapshot-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.note }}</small>
      </article>
    </section>

    <section class="dashboard-grid">
      <article class="clinical-card performance-card">
        <p class="eyebrow">模型指标</p>
        <h2>预测性能</h2>
        <div class="metric-row-list">
          <div>
            <span>MRR</span>
            <strong>{{ formatPercent(board.mrr) }}</strong>
          </div>
          <div>
            <span>Hits@1</span>
            <strong>{{ formatPercent(board.hits1) }}</strong>
          </div>
          <div>
            <span>Hits@10</span>
            <strong>{{ formatPercent(board.hits10) }}</strong>
          </div>
        </div>
      </article>

      <article class="clinical-card performance-card">
        <p class="eyebrow">数据支持覆盖率</p>
        <h2>{{ formatPercent(dataSupportCoverage) }}</h2>
        <el-progress :percentage="Math.round(dataSupportCoverage * 100)" :stroke-width="10" />
        <p class="panel-note">覆盖率用于观察患者病程事件、关系证据和模型输入数据是否足以支持解释。</p>
      </article>

      <article class="clinical-card runtime-card">
        <p class="eyebrow">运行状态</p>
        <h2>当前模型快照</h2>
        <dl class="runtime-list">
          <div>
            <dt>最近训练时间</dt>
            <dd>{{ formatDateTime(board.recentTrainingTime) }}</dd>
          </div>
          <div>
            <dt>最近任务状态</dt>
            <dd>{{ board.recentTrainingTaskStatus }}</dd>
          </div>
          <div>
            <dt>快照来源</dt>
            <dd>{{ board.source }}</dd>
          </div>
        </dl>
        <div v-if="availableVersions.length > 1" class="version-switch-section">
          <p class="eyebrow">版本切换</p>
          <div class="version-switch-row">
            <select v-model="selectedVersion" class="version-select">
              <option v-for="v in availableVersions" :key="v.version" :value="v.version">
                {{ v.version }} ({{ v.modelName }}) {{ v.isCurrent ? '● 当前' : '' }}
              </option>
            </select>
            <button
              class="secondary-button"
              type="button"
              :disabled="switching || selectedVersion === board.currentModelVersion"
              @click="handleVersionSwitch"
            >
              {{ switching ? '切换中...' : '切换版本' }}
            </button>
          </div>
          <p v-if="switchMessage" class="switch-message">{{ switchMessage }}</p>
        </div>
      </article>

      <article class="clinical-card anomaly-card">
        <p class="eyebrow">最近异常</p>
        <h2>异常与提示</h2>
        <div class="anomaly-list">
          <div v-for="item in recentAnomalies" :key="`${item.time}-${item.title}`" class="anomaly-item" :class="`tone-${item.level}`">
            <span>{{ item.time }}</span>
            <strong>{{ item.title }}</strong>
            <p>{{ item.detail }}</p>
          </div>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.model-dashboard-page {
  display: grid;
  gap: 18px;
}

.dashboard-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.dashboard-header p {
  margin: 0;
  color: #526772;
}

.dashboard-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.snapshot-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.metric-card,
.performance-card,
.runtime-card,
.anomaly-card,
.snapshot-card {
  display: grid;
  gap: 12px;
}

.metric-card span,
.metric-card small,
.metric-row-list span,
.runtime-list dt,
.anomaly-item span,
.panel-note {
  color: #526772;
}

.metric-card strong {
  color: #0f6f99;
  font-size: clamp(24px, 4vw, 34px);
}

.snapshot-card span,
.snapshot-card small {
  color: #526772;
}

.snapshot-card strong {
  color: #003c43;
  font-size: 24px;
}

.tone-ok {
  color: #007f65 !important;
}

.tone-warning,
.tone-notice {
  color: #9a5b00 !important;
}

.tone-danger {
  color: #b42318 !important;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.metric-row-list {
  display: grid;
  gap: 10px;
}

.metric-row-list div,
.runtime-list div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #d5e6ef;
}

.metric-row-list strong,
.runtime-list dd {
  margin: 0;
  color: #003c43;
  font-size: 20px;
  font-weight: 900;
}

.runtime-list {
  display: grid;
  margin: 0;
}

.anomaly-list {
  display: grid;
  gap: 8px;
}

.anomaly-item {
  display: grid;
  gap: 4px;
  padding: 10px;
  border: 1px solid #d5e6ef;
  border-left-width: 3px;
  border-radius: 4px;
  background: #fff;
}

.anomaly-item.tone-ok {
  border-left-color: #007f65;
}

.anomaly-item.tone-warning,
.anomaly-item.tone-notice {
  border-left-color: #d97706;
}

.anomaly-item.tone-danger {
  border-left-color: #b42318;
}

.anomaly-item p,
.panel-note {
  margin: 0;
  line-height: 1.6;
}

.version-switch-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #d5e6ef;
}

.version-switch-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.version-select {
  flex: 1;
  min-height: 36px;
  border: 1px solid #c9dce6;
  border-radius: 4px;
  padding: 7px 9px;
  background: #fff;
  font-size: 13px;
}

.switch-message {
  margin: 8px 0 0;
  padding: 8px;
  background: #edf7fc;
  border: 1px solid #b7d1de;
  border-radius: 4px;
  color: #275d70;
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 1180px) {
  .snapshot-grid,
  .dashboard-metrics,
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
