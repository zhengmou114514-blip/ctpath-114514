<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useWorkspaceContext } from '../composables/workspaceContext'
import { buildModelBoardSnapshot } from '../services/modelBoardAdapter'

const workspace = useWorkspaceContext()

const board = computed(() =>
  buildModelBoardSnapshot({
    modelMetrics: workspace.modelMetrics,
    maintenance: workspace.maintenanceOverview,
    patientCount: workspace.allPatients.length,
  })
)

const modelHealth = computed(() => {
  if (!workspace.health) return { label: '未知', type: 'info' as const }
  if (workspace.health.model_available) return { label: '健康', type: 'success' as const }
  if (workspace.health.model_error) return { label: '降级', type: 'warning' as const }
  return { label: '不可用', type: 'danger' as const }
})

const loading = computed(() =>
  workspace.loadingModelMetrics || workspace.loadingMaintenance || workspace.loadingGovernance
)

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
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">Model center</p>
        <h1>模型看板</h1>
        <p>面向后台治理，展示模型版本、训练指标、调用量、回退比例和健康状态。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="handleRefresh">刷新</el-button>
    </header>

    <el-card shadow="never" class="module-card">
      <el-alert
        v-if="workspace.health?.model_error"
        :title="workspace.health.model_error"
        type="warning"
        show-icon
        :closable="false"
        class="module-alert"
      />

      <el-row :gutter="12" class="summary-row">
        <el-col :xs="24" :sm="8">
          <el-statistic title="模型版本" :value="board.currentModelVersion" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-statistic title="最近训练" :value="formatDateTime(board.recentTrainingTime)" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="health-card">
            <span>模型健康</span>
            <el-tag :type="modelHealth.type" effect="light">{{ modelHealth.label }}</el-tag>
            <small>数据源：{{ workspace.health?.mode ?? '--' }}</small>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-skeleton v-if="loading" :rows="8" animated />

    <template v-else>
      <section class="metric-grid">
        <el-card shadow="never" class="metric-card"><span>MRR</span><strong>{{ formatPercent(board.mrr) }}</strong></el-card>
        <el-card shadow="never" class="metric-card"><span>Hits@1</span><strong>{{ formatPercent(board.hits1) }}</strong></el-card>
        <el-card shadow="never" class="metric-card"><span>Hits@10</span><strong>{{ formatPercent(board.hits10) }}</strong></el-card>
        <el-card shadow="never" class="metric-card"><span>调用量</span><strong>{{ board.recentInferenceCalls ?? '--' }}</strong></el-card>
        <el-card shadow="never" class="metric-card"><span>回退比例</span><strong>{{ formatPercent(board.fallbackRatio) }}</strong></el-card>
        <el-card shadow="never" class="metric-card"><span>训练任务</span><strong>{{ board.recentTrainingTaskStatus || '--' }}</strong></el-card>
      </section>

      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <h3>版本与服务状态</h3>
            <el-tag :type="modelHealth.type">{{ modelHealth.label }}</el-tag>
          </div>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="当前模型">{{ board.currentModelName }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ board.currentModelVersion }}</el-descriptions-item>
          <el-descriptions-item label="数据覆盖">{{ formatPercent(board.datasetCoverage) }}</el-descriptions-item>
          <el-descriptions-item label="最近训练">{{ formatDateTime(board.recentTrainingTime) }}</el-descriptions-item>
          <el-descriptions-item label="服务模式">{{ workspace.health?.mode ?? '--' }}</el-descriptions-item>
          <el-descriptions-item label="患者数">{{ workspace.allPatients.length }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </template>
  </section>
</template>

<style scoped>
.model-dashboard-page {
  display: grid;
  gap: 24px;
}

.module-card,
.metric-card {
  border-radius: 8px;
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-header h3 {
  margin: 0;
}

.module-alert,
.summary-row {
  margin-top: 14px;
}

.health-card,
.metric-card {
  display: grid;
  gap: 8px;
}

.health-card {
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  padding: 12px;
}

.health-card span,
.health-card small,
.metric-card span {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
}

.metric-card strong {
  color: var(--ws-title);
  font-size: 24px;
}

@media (max-width: 960px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .section-header {
    display: grid;
  }
}
</style>
