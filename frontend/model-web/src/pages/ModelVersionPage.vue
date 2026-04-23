<script setup lang="ts">
import { useModelWorkspace } from '../composables/useModelWorkspace'

const workspace = useModelWorkspace()

function statusLabel(status: string) {
  const mapping: Record<string, string> = {
    deployed: '已部署',
    staging: '待发布',
    archived: '已归档',
  }
  return mapping[status] ?? status
}
</script>

<template>
  <section class="workspace-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">Model Versions</p>
        <h1>模型版本管理</h1>
        <p>统一维护模型版本、训练来源、离线指标和发布/回滚动作，便于答辩演示和版本追踪。</p>
      </div>
    </header>

    <p v-if="workspace.versionError" class="error-text">{{ workspace.versionError }}</p>

    <div class="record-list">
      <article v-for="version in workspace.versions" :key="version.versionId" class="record-item">
        <strong>{{ version.versionName }} · {{ version.modelName }}</strong>
        <p>状态：{{ statusLabel(version.status) }} · 数据集：{{ version.datasetId }}</p>
        <small>MRR {{ version.metrics.mrr.toFixed(4) }} / Hits@1 {{ version.metrics.hits1.toFixed(4) }} / Hits@10 {{ version.metrics.hits10.toFixed(4) }}</small>
        <small>{{ version.notes }}</small>
        <div class="action-row">
          <button class="secondary-button" type="button" :disabled="workspace.loadingVersion || version.deployed" @click="workspace.handleDeploy(version.versionId)">
            发布版本
          </button>
          <button class="secondary-button" type="button" :disabled="workspace.loadingVersion" @click="workspace.handleRollback(version.versionId)">
            回滚到此版本
          </button>
        </div>
      </article>
    </div>
  </section>
</template>
