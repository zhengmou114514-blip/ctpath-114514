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
  if (!workspace.health) return { label: '状态待确认', type: 'info' as const }
  if (workspace.health.model_available) return { label: '模型可用', type: 'success' as const }
  if (workspace.health.model_error) return { label: '降级运行', type: 'warning' as const }
  return { label: '模型不可用', type: 'danger' as const }
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

function handleOpenTrainingCenter() {
  workspace.selectSection('training-center')
  void router.push({ name: 'training-center' })
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
        <p>面向模型治理与监控，集中展示当前版本、最近训练、指标表现、回退比例与模型健康状态。</p>
      </div>
      <div class="header-actions">
        <el-button @click="handleOpenTrainingCenter">进入训练中心</el-button>
        <el-button type="primary" :loading="loading" @click="handleRefresh">刷新看板</el-button>
      </div>
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
          <el-statistic title="当前模型版本" :value="board.currentModelVersion" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-statistic title="最近训练时间" :value="formatDateTime(board.recentTrainingTime)" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="health-card">
            <span>模型服务状态</span>
            <el-tag :type="modelHealth.type" effect="light">{{ modelHealth.label }}</el-tag>
            <small>当前运行模式：{{ workspace.health?.mode ?? '--' }}</small>
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
        <el-card shadow="never" class="metric-card"><span>近七日调用量</span><strong>{{ board.recentInferenceCalls ?? '--' }}</strong></el-card>
        <el-card shadow="never" class="metric-card"><span>模型回退比例</span><strong>{{ formatPercent(board.fallbackRatio) }}</strong></el-card>
        <el-card shadow="never" class="metric-card"><span>最近任务状态</span><strong>{{ board.recentTrainingTaskStatus || '--' }}</strong></el-card>
      </section>

      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <h3>版本与运行信息</h3>
            <el-tag :type="modelHealth.type">{{ modelHealth.label }}</el-tag>
          </div>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="当前模型">{{ board.currentModelName }}</el-descriptions-item>
          <el-descriptions-item label="版本号">{{ board.currentModelVersion }}</el-descriptions-item>
          <el-descriptions-item label="数据覆盖率">{{ formatPercent(board.datasetCoverage) }}</el-descriptions-item>
          <el-descriptions-item label="最近训练时间">{{ formatDateTime(board.recentTrainingTime) }}</el-descriptions-item>
          <el-descriptions-item label="运行模式">{{ workspace.health?.mode ?? '--' }}</el-descriptions-item>
          <el-descriptions-item label="服务患者数">{{ workspace.allPatients.length }}</el-descriptions-item>
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
