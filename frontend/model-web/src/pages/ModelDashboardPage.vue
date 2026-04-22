<script setup lang="ts">
import { useModelWorkspace } from '../composables/useModelWorkspace'
import { useRouter } from 'vue-router'

const workspace = useModelWorkspace()
const router = useRouter()

function go(name: string) {
  void router.push({ name })
}
</script>

<template>
  <section class="workspace-page model-dashboard-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">模型总览</p>
        <h1>模型管理总览</h1>
        <p>集中查看数据集、训练任务、版本发布和推理服务状态。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="go('model-datasets')">数据集管理</button>
        <button class="secondary-button" type="button" @click="go('model-training')">训练任务</button>
        <button class="primary-button" type="button" @click="go('model-operations')">模型运营台</button>
      </div>
    </header>

    <section class="metric-grid">
      <article class="clinical-card metric-card">
        <span>当前模型版本</span>
        <strong>{{ workspace.board.currentModelVersion }}</strong>
        <small>{{ workspace.board.currentModelName }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>最近训练时间</span>
        <strong>{{ workspace.board.recentTrainingTime }}</strong>
        <small>任务状态：{{ workspace.board.recentTrainingTaskStatus }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>推理服务</span>
        <strong>{{ workspace.health?.model_available ? '可用' : '降级' }}</strong>
        <small>{{ workspace.health?.mode ?? 'model' }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>数据集数量</span>
        <strong>{{ workspace.datasets.length }}</strong>
        <small>训练数据与版本独立管理</small>
      </article>
    </section>
  </section>
</template>
