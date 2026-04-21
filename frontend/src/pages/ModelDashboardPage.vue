<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceContext } from '../composables/workspaceContext'
import { buildModelBoardSnapshot } from '../services/modelBoardAdapter'

const workspace = useWorkspaceContext()
const router = useRouter()

const board = computed(() =>
  buildModelBoardSnapshot({
    modelMetrics: workspace.modelMetrics,
    maintenance: workspace.maintenanceOverview,
    patientCount: workspace.allPatients.length,
  })
)

const modelHealth = computed(() => {
  if (!workspace.health) return { label: '状态待加载', type: 'info' as const }
  if (workspace.health.model_available) return { label: '模型可用', type: 'success' as const }
  if (workspace.health.model_error) return { label: '降级运行', type: 'warning' as const }
  return { label: '模型不可用', type: 'danger' as const }
})

const loading = computed(() => workspace.loadingModelMetrics || workspace.loadingMaintenance || workspace.loadingGovernance)

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return `${(value * 100).toFixed(1)}%`
}

function formatDateTime(value: string | undefined) {
  if (!value || value === '--') return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function handleRefresh() {
  void workspace.refreshGovernanceWorkspace()
}

function handleOpenTrainingCenter() {
  workspace.selectSection('training-center')
  void router.push({ name: 'training-center' })
}

function handleOpenOperations() {
  workspace.selectSection('model-operations')
  void router.push({ name: 'model-operations' })
}

onMounted(() => {
  if (!workspace.currentDoctor) return
  if (!workspace.modelMetrics || !workspace.maintenanceOverview) {
    void workspace.refreshGovernanceWorkspace()
  }
})
</script>

<template>
  <section class="workspace-page model-dashboard-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">模型中心</p>
        <h1>模型看板</h1>
        <p>这里只承接模型治理和监控信息，不展示当前患者详情。模型运营台和训练中心通过独立入口查看。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="handleOpenOperations">进入模型运营台</button>
        <button class="secondary-button" type="button" @click="handleOpenTrainingCenter">进入训练中心</button>
        <button class="primary-button" type="button" :disabled="loading" @click="handleRefresh">刷新看板</button>
      </div>
    </header>

    <section class="metric-grid">
      <article class="clinical-card metric-card">
        <span>模型版本</span>
        <strong>{{ board.currentModelVersion }}</strong>
        <small>{{ board.currentModelName }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>最近训练</span>
        <strong>{{ formatDateTime(board.recentTrainingTime) }}</strong>
        <small>最新任务状态：{{ board.recentTrainingTaskStatus }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>模型健康</span>
        <strong>{{ modelHealth.label }}</strong>
        <small>运行模式：{{ workspace.health?.mode ?? '--' }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>数据覆盖率</span>
        <strong>{{ formatPercent(board.datasetCoverage) }}</strong>
        <small>按训练数据集规模估算</small>
      </article>
    </section>

    <section class="performance-grid">
      <article class="clinical-card performance-card">
        <p class="eyebrow">核心指标</p>
        <div class="performance-list">
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
        <p class="eyebrow">运行概况</p>
        <div class="performance-list">
          <div>
            <span>近 7 天调用量</span>
            <strong>{{ board.recentInferenceCalls ?? '--' }}</strong>
          </div>
          <div>
            <span>回退比例</span>
            <strong>{{ formatPercent(board.fallbackRatio) }}</strong>
          </div>
          <div>
            <span>患者规模</span>
            <strong>{{ workspace.allPatients.length }}</strong>
          </div>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.model-dashboard-page {
  display: grid;
  gap: 24px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.metric-card,
.performance-card {
  display: grid;
  gap: 12px;
}

.metric-card span,
.metric-card small,
.performance-card span {
  color: rgba(63, 72, 73, 0.74);
}

.metric-card strong {
  font-size: clamp(24px, 4vw, 34px);
}

.performance-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.performance-list {
  display: grid;
  gap: 14px;
}

.performance-list div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid rgba(190, 200, 201, 0.45);
}

.performance-list strong {
  font-size: 20px;
}

@media (max-width: 1180px) {
  .metric-grid,
  .performance-grid {
    grid-template-columns: 1fr;
  }
}
</style>
