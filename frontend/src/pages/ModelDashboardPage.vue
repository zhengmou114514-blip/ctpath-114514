<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { buildModelBoardSnapshot } from '../services/modelBoardAdapter'
import { useWorkspaceContext } from '../composables/workspaceContext'

const workspace = useWorkspaceContext()

const board = computed(() =>
  buildModelBoardSnapshot({
    modelMetrics: workspace.modelMetrics,
    maintenance: workspace.maintenanceOverview,
    patientCount: workspace.allPatients.length,
  })
)

const modelHealth = computed(() => {
  if (!workspace.health) return '未知'
  if (workspace.health.model_available) return '可用'
  if (workspace.health.model_error) return '降级'
  return '不可用'
})

const modelHealthTone = computed(() => {
  if (!workspace.health) return 'neutral'
  if (workspace.health.model_available) return 'healthy'
  if (workspace.health.model_error) return 'warning'
  return 'danger'
})

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return `${(value * 100).toFixed(1)}%`
}

function formatDateTime(value: string | undefined) {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function handleRefresh() {
  void workspace.refreshGovernanceWorkspace()
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
    <header class="card page-header">
      <div>
        <h2>模型看板</h2>
        <p>只展示模型治理指标，不承载训练台或数据导入流程。</p>
      </div>
      <button class="primary-button" @click="handleRefresh">刷新</button>
    </header>

    <section v-if="workspace.loadingModelMetrics || workspace.loadingMaintenance || workspace.loadingGovernance" class="card state">
      正在加载模型治理指标...
    </section>

    <section v-else-if="!workspace.modelMetrics" class="card state">
      暂无模型指标数据。
    </section>

    <template v-else>
      <section class="summary-grid">
        <article class="card summary-card">
          <span>模型版本</span>
          <strong>{{ board.currentModelVersion }}</strong>
        </article>

        <article class="card summary-card">
          <span>最近训练时间</span>
          <strong>{{ formatDateTime(board.recentTrainingTime) }}</strong>
        </article>

        <article class="card summary-card">
          <span>模型健康状态</span>
          <strong :class="`tone-${modelHealthTone}`">{{ modelHealth }}</strong>
          <p>当前模式：{{ workspace.health?.mode ?? '--' }}</p>
        </article>
      </section>

      <section class="metric-grid">
        <article class="card metric-card">
          <span>MRR</span>
          <strong>{{ formatPercent(board.mrr) }}</strong>
        </article>
        <article class="card metric-card">
          <span>Hits@1</span>
          <strong>{{ formatPercent(board.hits1) }}</strong>
        </article>
        <article class="card metric-card">
          <span>Hits@10</span>
          <strong>{{ formatPercent(board.hits10) }}</strong>
        </article>
        <article class="card metric-card">
          <span>调用量</span>
          <strong>{{ board.recentInferenceCalls ?? '--' }}</strong>
        </article>
        <article class="card metric-card">
          <span>回退比例</span>
          <strong>{{ formatPercent(board.fallbackRatio) }}</strong>
        </article>
      </section>
    </template>
  </section>
</template>

<style scoped>
.model-dashboard-page {
  padding: 20px;
  display: grid;
  gap: 14px;
  align-content: start;
}

.page-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  color: #17324d;
}

.page-header p {
  margin: 4px 0 0;
  color: #5f758b;
  font-size: 13px;
}

.state {
  padding: 16px;
  color: #5f758b;
  text-align: center;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.summary-card,
.metric-card {
  padding: 14px;
  display: grid;
  gap: 6px;
}

.summary-card span,
.metric-card span {
  color: #60778e;
  font-size: 12px;
}

.summary-card strong,
.metric-card strong {
  color: #17324d;
  font-size: 18px;
}

.summary-card p {
  margin: 0;
  color: #60778e;
  font-size: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  min-height: 104px;
}

.tone-healthy {
  color: #1f7a57;
}

.tone-warning {
  color: #a56b00;
}

.tone-danger {
  color: #b33a43;
}

.tone-neutral {
  color: #38536d;
}

@media (max-width: 1200px) {
  .summary-grid,
  .metric-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
