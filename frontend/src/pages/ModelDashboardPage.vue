<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelMetrics: any
  health: any
  loadingMetrics: boolean
}>()

const emit = defineEmits<{
  refresh: []
}>()

// 模型版本信息
const modelVersion = computed(() => {
  return props.modelMetrics?.currentModel?.version ?? 'v1.0.0'
})

// 最近训练时间
const lastTrainingTime = computed(() => {
  return props.modelMetrics?.currentModel?.lastTrainingTime ?? '2024-01-01'
})

// MRR (Mean Reciprocal Rank)
const mrr = computed(() => {
  const value = props.modelMetrics?.currentModel?.mrr
  if (value === null || value === undefined) return '--'
  return `${(value * 100).toFixed(1)}%`
})

// Hits@1
const hits1 = computed(() => {
  const value = props.modelMetrics?.currentModel?.hits1
  if (value === null || value === undefined) return '--'
  return `${(value * 100).toFixed(1)}%`
})

// Hits@10
const hits10 = computed(() => {
  const value = props.modelMetrics?.currentModel?.hits10
  if (value === null || value === undefined) return '--'
  return `${(value * 100).toFixed(1)}%`
})

// 推理调用量（7天）
const inferenceCalls7d = computed(() => {
  return props.modelMetrics?.currentModel?.inferenceCalls7d ?? 0
})

// 回退比例
const fallbackRatio = computed(() => {
  const value = props.modelMetrics?.currentModel?.fallbackRatio
  if (value === null || value === undefined) return '--'
  return `${(value * 100).toFixed(1)}%`
})

// 模型状态
const modelStatus = computed(() => {
  if (!props.health) return '未知'
  if (props.health.model_available) return '正常'
  if (props.health.model_error) return '异常'
  return '降级'
})

const modelStatusClass = computed(() => {
  if (!props.health) return 'neutral'
  if (props.health.model_available) return 'success'
  if (props.health.model_error) return 'error'
  return 'warning'
})
</script>

<template>
  <section class="model-dashboard-page">
    <header class="page-header card">
      <div class="header-left">
        <h2>模型看板</h2>
        <span class="module-badge">模型版本、训练任务与运行指标管理</span>
      </div>
      <button class="primary-button" @click="emit('refresh')">刷新数据</button>
    </header>

    <section v-if="loadingMetrics" class="card state">加载中...</section>

    <template v-else>
      <!-- 模型状态概览 -->
      <section class="metric-block card">
        <div class="block-head">
          <h3>模型状态概览</h3>
          <span class="hint">当前模型运行状态与基本信息</span>
        </div>

        <div class="metric-grid">
          <article class="metric-card">
            <h4>模型版本</h4>
            <strong class="metric-value">{{ modelVersion }}</strong>
            <p>当前生产环境模型版本</p>
          </article>

          <article class="metric-card">
            <h4>最近训练时间</h4>
            <strong class="metric-value">{{ lastTrainingTime }}</strong>
            <p>模型最近一次训练完成时间</p>
          </article>

          <article class="metric-card" :class="`status-${modelStatusClass}`">
            <h4>模型状态</h4>
            <strong class="metric-value">{{ modelStatus }}</strong>
            <p>模型服务可用性状态</p>
          </article>
        </div>
      </section>

      <!-- 模型性能指标 -->
      <section class="metric-block card">
        <div class="block-head">
          <h3>模型性能指标</h3>
          <span class="hint">模型在测试集上的性能表现</span>
        </div>

        <div class="metric-grid">
          <article class="metric-card">
            <h4>MRR</h4>
            <strong class="metric-value">{{ mrr }}</strong>
            <p>平均倒数排名 (Mean Reciprocal Rank)</p>
          </article>

          <article class="metric-card">
            <h4>Hits@1</h4>
            <strong class="metric-value">{{ hits1 }}</strong>
            <p>Top-1 命中率</p>
          </article>

          <article class="metric-card">
            <h4>Hits@10</h4>
            <strong class="metric-value">{{ hits10 }}</strong>
            <p>Top-10 命中率</p>
          </article>
        </div>
      </section>

      <!-- 运行指标 -->
      <section class="metric-block card">
        <div class="block-head">
          <h3>运行指标</h3>
          <span class="hint">模型在生产环境的运行统计</span>
        </div>

        <div class="metric-grid">
          <article class="metric-card">
            <h4>推理调用量 (7天)</h4>
            <strong class="metric-value">{{ inferenceCalls7d }}</strong>
            <p>最近7天的模型推理调用次数</p>
          </article>

          <article class="metric-card">
            <h4>回退比例</h4>
            <strong class="metric-value">{{ fallbackRatio }}</strong>
            <p>规则/相似病例回退占比</p>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.model-dashboard-page {
  padding: 24px;
  display: grid;
  gap: 24px;
  align-content: start;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2d3748;
}

.module-badge {
  padding: 4px 12px;
  border-radius: 4px;
  background: #e6f7ff;
  color: #1890ff;
  font-size: 13px;
  font-weight: 500;
}

.metric-block {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f3f5;
}

.block-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2d3748;
}

.hint {
  font-size: 13px;
  color: #718096;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  padding: 16px;
  border-radius: 8px;
  background: #f8f9fa;
  border: 1px solid #e2e8f0;
  display: grid;
  gap: 8px;
}

.metric-card h4 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #4a5568;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #2d3748;
}

.metric-card p {
  margin: 0;
  font-size: 12px;
  color: #a0aec0;
}

.metric-card.status-success {
  background: #c6f6d5;
  border-color: #9ae6b4;
}

.metric-card.status-success .metric-value {
  color: #276749;
}

.metric-card.status-warning {
  background: #feebc8;
  border-color: #fbd38d;
}

.metric-card.status-warning .metric-value {
  color: #c05621;
}

.metric-card.status-error {
  background: #fed7d7;
  border-color: #fc8181;
}

.metric-card.status-error .metric-value {
  color: #c53030;
}

.state {
  padding: 40px;
  text-align: center;
  color: #718096;
  font-size: 14px;
}

@media (max-width: 1200px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
