<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useModelWorkspace } from '../composables/useModelWorkspace'

const workspace = useModelWorkspace()
const router = useRouter()

const healthLabel = computed(() => {
  if (!workspace.health) return '状态加载中'
  return workspace.health.model_available ? '可用' : '异常'
})

const latestTaskLabel = computed(() => {
  const value = workspace.dashboard?.latestTaskStatus || workspace.board.recentTrainingTaskStatus
  const mapping: Record<string, string> = {
    queued: '排队中',
    running: '训练中',
    succeeded: '已完成',
    failed: '失败',
    'no-task': '暂无任务',
  }
  return mapping[value] ?? value
})

function go(name: string) {
  void router.push({ name })
}

onMounted(() => {
  if (!workspace.dashboard && workspace.isAuthenticated) {
    void workspace.refreshAll()
  }
})
</script>

<template>
  <section class="workspace-page model-dashboard-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">Model Overview</p>
        <h1>模型治理总览</h1>
        <p>集中查看当前部署版本、最近训练情况、训练数据覆盖度和推理服务健康状态。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="go('model-datasets')">数据集管理</button>
        <button class="secondary-button" type="button" @click="go('model-training')">训练任务</button>
        <button class="primary-button" type="button" @click="go('model-operations')">运营与审计</button>
      </div>
    </header>

    <p v-if="workspace.workspaceError" class="error-text">{{ workspace.workspaceError }}</p>

    <section class="metric-grid">
      <article class="clinical-card metric-card">
        <span>当前部署版本</span>
        <strong>{{ workspace.currentDeployment?.versionName ?? '未部署' }}</strong>
        <small>{{ workspace.currentDeployment?.modelName ?? 'CTpath Temporal KG' }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>最近训练状态</span>
        <strong>{{ latestTaskLabel }}</strong>
        <small>{{ workspace.board.recentTrainingTime }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>推理服务状态</span>
        <strong>{{ healthLabel }}</strong>
        <small>{{ workspace.health?.current_deployment ?? '未绑定部署版本' }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>数据集数量</span>
        <strong>{{ workspace.datasets.length }}</strong>
        <small>已接入模型中心的数据集</small>
      </article>
    </section>

    <section class="training-grid">
      <article class="clinical-card">
        <h2>核心指标</h2>
        <div class="record-list">
          <article class="record-item">
            <strong>MRR</strong>
            <p>{{ workspace.board.mrr.toFixed(4) }}</p>
          </article>
          <article class="record-item">
            <strong>Hits@1</strong>
            <p>{{ workspace.board.hits1.toFixed(4) }}</p>
          </article>
          <article class="record-item">
            <strong>Hits@10</strong>
            <p>{{ workspace.board.hits10.toFixed(4) }}</p>
          </article>
          <article class="record-item">
            <strong>部署版本数</strong>
            <p>{{ workspace.dashboard?.deployedVersionCount ?? 0 }}</p>
          </article>
        </div>
      </article>

      <article class="clinical-card">
        <h2>当前部署摘要</h2>
        <div class="record-list">
          <article class="record-item">
            <strong>部署版本</strong>
            <p>{{ workspace.currentDeployment?.versionName ?? '未部署' }}</p>
          </article>
          <article class="record-item">
            <strong>来源数据集</strong>
            <p>{{ workspace.currentDeployment?.datasetId ?? '--' }}</p>
          </article>
          <article class="record-item">
            <strong>版本说明</strong>
            <p>{{ workspace.currentDeployment?.notes ?? '暂无版本说明。' }}</p>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>
