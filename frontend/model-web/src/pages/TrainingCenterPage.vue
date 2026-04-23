<script setup lang="ts">
import { useModelWorkspace } from '../composables/useModelWorkspace'

const workspace = useModelWorkspace()

function statusLabel(status: string) {
  const mapping: Record<string, string> = {
    queued: '排队中',
    running: '训练中',
    succeeded: '已完成',
    failed: '失败',
  }
  return mapping[status] ?? status
}
</script>

<template>
  <section class="workspace-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">Training Jobs</p>
        <h1>训练任务</h1>
        <p>面向模型工程与治理流程，使用已导入的数据集发起训练任务，并追踪训练状态与输出日志。</p>
      </div>
    </header>

    <section class="training-grid">
      <article class="clinical-card form-card">
        <h2>创建训练任务</h2>
        <label class="field">
          <span>训练数据集</span>
          <select v-model="workspace.selectedDatasetId" class="training-input">
            <option disabled value="">请选择训练数据集</option>
            <option v-for="dataset in workspace.datasets" :key="dataset.datasetId" :value="dataset.datasetId">
              {{ dataset.datasetName }}
            </option>
          </select>
        </label>
        <label class="field">
          <span>模型名称</span>
          <input v-model="workspace.modelName" class="training-input" />
        </label>
        <div class="form-grid two-column">
          <label class="field"><span>Epochs</span><input v-model.number="workspace.params.epochs" class="training-input" type="number" min="1" /></label>
          <label class="field"><span>Batch Size</span><input v-model.number="workspace.params.batchSize" class="training-input" type="number" min="1" /></label>
          <label class="field"><span>Learning Rate</span><input v-model.number="workspace.params.learningRate" class="training-input" type="number" step="0.0001" /></label>
          <label class="field"><span>Embedding Dim</span><input v-model.number="workspace.params.embeddingDim" class="training-input" type="number" min="8" /></label>
          <label class="field">
            <span>优化器</span>
            <select v-model="workspace.params.optimizer" class="training-input">
              <option value="adam">Adam</option>
              <option value="adamw">AdamW</option>
              <option value="sgd">SGD</option>
            </select>
          </label>
        </div>
        <div class="action-row">
          <button class="primary-button" type="button" :disabled="workspace.loadingTask" @click="workspace.handleCreateTask">
            {{ workspace.loadingTask ? '创建中...' : '创建训练任务' }}
          </button>
        </div>
        <p v-if="workspace.taskError" class="error-text">{{ workspace.taskError }}</p>
      </article>

      <article class="clinical-card">
        <h2>训练任务清单</h2>
        <div class="record-list">
          <article v-for="task in workspace.tasks" :key="task.taskId" class="record-item">
            <strong>{{ task.modelName }}</strong>
            <p>{{ task.datasetName }} · {{ statusLabel(task.status) }} · {{ task.triggeredBy }}</p>
            <small>{{ task.logs[task.logs.length - 1] }}</small>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>
