<script setup lang="ts">
import { useModelWorkspace } from '../composables/useModelWorkspace'
const workspace = useModelWorkspace()

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  workspace.selectedFile = input.files?.[0] ?? null
}
</script>

<template>
  <section class="workspace-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">数据集管理</p>
        <h1>数据集导入与列表</h1>
        <p>导入暂存区、校验后的数据集和历史版本都在这里管理。</p>
      </div>
    </header>

    <section class="clinical-card">
      <div class="form-grid two-column">
        <label class="field">
          <span>数据集名称</span>
          <input v-model="workspace.datasetName" class="training-input" placeholder="例如：慢病门诊时序样本集 Q2" />
        </label>
        <label class="field">
          <span>CSV 文件</span>
          <input class="training-input file-input" type="file" accept=".csv" @change="handleFileChange" />
        </label>
      </div>
      <div class="action-row">
        <button class="primary-button" type="button" :disabled="workspace.loadingDataset" @click="workspace.handleImportDataset">
          {{ workspace.loadingDataset ? '导入中...' : '导入数据集' }}
        </button>
      </div>
      <p v-if="workspace.importError" class="error-text">{{ workspace.importError }}</p>
      <p v-if="workspace.importSuccess" class="success-text">{{ workspace.importSuccess }}</p>
    </section>

    <section class="clinical-card">
      <h2>数据集列表</h2>
      <div class="record-list">
        <article v-for="dataset in workspace.datasets" :key="dataset.datasetId" class="record-item">
          <strong>{{ dataset.datasetName }}</strong>
          <p>{{ dataset.fileName }} · {{ dataset.rowCount }} 行 · {{ dataset.uploadedBy }}</p>
        </article>
      </div>
    </section>
  </section>
</template>
