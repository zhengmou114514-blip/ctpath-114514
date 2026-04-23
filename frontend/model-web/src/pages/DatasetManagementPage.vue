<script setup lang="ts">
import { computed } from 'vue'
import { useModelWorkspace } from '../composables/useModelWorkspace'

const workspace = useModelWorkspace()

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  workspace.selectedFile = input.files?.[0] ?? null
}

function statusLabel(status: string) {
  const mapping: Record<string, string> = {
    ready: '就绪',
    processing: '处理中',
    failed: '失败',
  }
  return mapping[status] ?? status
}

const totalRows = computed(() => workspace.datasets.reduce((sum, item) => sum + item.rowCount, 0))
</script>

<template>
  <section class="workspace-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">Dataset Management</p>
        <h1>数据集管理</h1>
        <p>训练数据集统一进入模型中心，便于导入、校验、训练任务引用和版本追溯。</p>
      </div>
    </header>

    <section class="metric-grid compact-grid">
      <article class="clinical-card metric-card">
        <span>数据集总数</span>
        <strong>{{ workspace.datasets.length }}</strong>
      </article>
      <article class="clinical-card metric-card">
        <span>累计样本行数</span>
        <strong>{{ totalRows }}</strong>
      </article>
    </section>

    <section class="clinical-card">
      <h2>导入训练数据集</h2>
      <div class="form-grid two-column">
        <label class="field">
          <span>数据集名称</span>
          <input v-model="workspace.datasetName" class="training-input" placeholder="例如：慢病知识图谱训练集 2026Q2" />
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
      <h2>数据集清单</h2>
      <div class="record-list">
        <article v-for="dataset in workspace.datasets" :key="dataset.datasetId" class="record-item">
          <strong>{{ dataset.datasetName }}</strong>
          <p>{{ dataset.fileName }} · {{ dataset.rowCount }} 行 · {{ dataset.uploadedBy }}</p>
          <small>状态：{{ statusLabel(dataset.status) }} · 来源：{{ dataset.source }} · 上传时间：{{ dataset.uploadedAt }}</small>
        </article>
      </div>
    </section>
  </section>
</template>
