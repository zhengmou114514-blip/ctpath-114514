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
  if (!workspace.health) return { label: 'Unknown', type: 'info' as const }
  if (workspace.health.model_available) return { label: 'Healthy', type: 'success' as const }
  if (workspace.health.model_error) return { label: 'Degraded', type: 'warning' as const }
  return { label: 'Unavailable', type: 'danger' as const }
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
        <p>模型版本、训练时间、MRR、Hits、调用量、回退比例和健康状态。</p>
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
          <el-statistic title="Model version" :value="board.currentModelVersion" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-statistic title="Recent training" :value="formatDateTime(board.recentTrainingTime)" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="health-card">
            <span>Model health</span>
            <el-tag :type="modelHealth.type" effect="light">{{ modelHealth.label }}</el-tag>
            <small>Mode: {{ workspace.health?.mode ?? '--' }}</small>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-skeleton v-if="loading" :rows="8" animated />

    <template v-else>
      <section class="metric-grid">
        <el-card shadow="never" class="metric-card">
          <span>MRR</span>
          <strong>{{ formatPercent(board.mrr) }}</strong>
        </el-card>
        <el-card shadow="never" class="metric-card">
          <span>Hits@1</span>
          <strong>{{ formatPercent(board.hits1) }}</strong>
        </el-card>
        <el-card shadow="never" class="metric-card">
          <span>Hits@10</span>
          <strong>{{ formatPercent(board.hits10) }}</strong>
        </el-card>
        <el-card shadow="never" class="metric-card">
          <span>Inference calls</span>
          <strong>{{ board.recentInferenceCalls ?? '--' }}</strong>
        </el-card>
        <el-card shadow="never" class="metric-card">
          <span>Fallback ratio</span>
          <strong>{{ formatPercent(board.fallbackRatio) }}</strong>
        </el-card>
        <el-card shadow="never" class="metric-card">
          <span>Training task</span>
          <strong>{{ board.recentTrainingTaskStatus || '--' }}</strong>
        </el-card>
      </section>

      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <h3>Version and service status</h3>
            <el-tag :type="modelHealth.type">{{ modelHealth.label }}</el-tag>
          </div>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="Current model">{{ board.currentModelName }}</el-descriptions-item>
          <el-descriptions-item label="Version">{{ board.currentModelVersion }}</el-descriptions-item>
          <el-descriptions-item label="Dataset coverage">{{ formatPercent(board.datasetCoverage) }}</el-descriptions-item>
          <el-descriptions-item label="Recent training">{{ formatDateTime(board.recentTrainingTime) }}</el-descriptions-item>
          <el-descriptions-item label="Service mode">{{ workspace.health?.mode ?? '--' }}</el-descriptions-item>
          <el-descriptions-item label="Patient count">{{ workspace.allPatients.length }}</el-descriptions-item>
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

.module-header,
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.module-header h2,
.module-header p,
.section-header h3 {
  margin: 0;
}

.eyebrow {
  margin: 0 0 4px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.module-header p,
.health-card span,
.health-card small,
.metric-card span {
  color: #64748b;
  font-size: 12px;
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
  border: 1px solid #ebeef5;
  border-radius: 10px;
  padding: 12px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
}

.metric-card strong {
  color: #303133;
  font-size: 24px;
}

@media (max-width: 960px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }

  .module-header,
  .section-header {
    display: grid;
  }
}
</style>
