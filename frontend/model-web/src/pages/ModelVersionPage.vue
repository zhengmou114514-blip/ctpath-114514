<script setup lang="ts">
import { useModelWorkspace } from '../composables/useModelWorkspace'
const workspace = useModelWorkspace()
</script>

<template>
  <section class="workspace-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">模型版本</p>
        <h1>模型版本管理</h1>
        <p>查看当前部署、发布新版本和执行回滚。</p>
      </div>
    </header>

    <p v-if="workspace.versionError" class="error-text">{{ workspace.versionError }}</p>

    <div class="record-list">
      <article v-for="version in workspace.versions" :key="version.versionId" class="record-item">
        <strong>{{ version.versionName }} · {{ version.modelName }}</strong>
        <p>状态：{{ version.status }} · 数据集：{{ version.datasetId }}</p>
        <small>MRR {{ version.metrics.mrr.toFixed(4) }} / Hits@1 {{ version.metrics.hits1.toFixed(4) }} / Hits@10 {{ version.metrics.hits10.toFixed(4) }}</small>
        <div class="action-row">
          <button class="secondary-button" type="button" :disabled="workspace.loadingVersion" @click="workspace.handleDeploy(version.versionId)">发布</button>
          <button class="secondary-button" type="button" :disabled="workspace.loadingVersion" @click="workspace.handleRollback(version.versionId)">回滚</button>
        </div>
      </article>
    </div>
  </section>
</template>
