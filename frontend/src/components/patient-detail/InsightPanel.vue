<script setup lang="ts">
import { computed } from 'vue'
import type { PatientCase, PredictResponse } from '../../services/types'

const props = defineProps<{
  patient: PatientCase
  predictionResult: PredictResponse | null
  loadingPredict: boolean
}>()

const emit = defineEmits<{
  (e: 'predict'): void
}>()

const topk = computed(() => props.predictionResult?.topk ?? props.patient.predictions)
const advice = computed(() => props.predictionResult?.advice ?? props.patient.careAdvice)
const evidence = computed(() => props.predictionResult?.evidence)
const confidence = computed(() => {
  const score = topk.value[0]?.score
  if (typeof score !== 'number') return '--'
  return `${Math.round(score * 100)}%`
})
</script>

<template>
  <section class="card right-panel">
    <div class="head-row">
      <h3>模型与建议</h3>
      <button class="secondary-button" :disabled="loadingPredict" @click="emit('predict')">
        {{ loadingPredict ? '预测中...' : '刷新预测' }}
      </button>
    </div>

    <article class="block">
      <h4>Top-K 风险事件</h4>
      <div v-if="!topk.length" class="empty">暂无预测结果</div>
      <div v-else class="list">
        <article v-for="(item, idx) in topk" :key="`${item.label}-${idx}`" class="list-item">
          <div class="row">
            <strong>{{ idx + 1 }}. {{ item.label }}</strong>
            <span>{{ Math.round(item.score * 100) }}%</span>
          </div>
          <p>{{ item.reason }}</p>
        </article>
      </div>
    </article>

    <article class="block">
      <h4>证据摘要</h4>
      <div v-if="!evidence" class="empty">请先执行预测</div>
      <div v-else class="evidence-grid">
        <article><span>事件数</span><strong>{{ evidence.eventCount }}</strong></article>
        <article><span>时间点</span><strong>{{ evidence.timepointCount }}</strong></article>
        <article><span>关系数</span><strong>{{ evidence.relationCount }}</strong></article>
        <article><span>支持等级</span><strong>{{ evidence.supportLevel }}</strong></article>
      </div>
    </article>

    <article class="block">
      <h4>LLM 辅助建议</h4>
      <ul class="plain-list" v-if="advice.length">
        <li v-for="(item, idx) in advice" :key="`${idx}-${item}`">{{ item }}</li>
      </ul>
      <div v-else class="empty">暂无建议</div>
    </article>

    <article class="block">
      <h4>处置建议</h4>
      <div class="disposition">
        <p>建议可信度: <strong>{{ confidence }}</strong></p>
        <p>建议优先完成病程关键事件结构化补录，再安排随访计划闭环。</p>
      </div>
    </article>
  </section>
</template>

<style scoped>
.right-panel {
  padding: 12px;
  display: grid;
  gap: 10px;
  align-content: start;
}

.head-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.head-row h3,
.block h4 {
  margin: 0;
  color: var(--navy);
}

.block {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px;
  background: #fbfdff;
  display: grid;
  gap: 8px;
}

.list {
  display: grid;
  gap: 8px;
}

.list-item {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px;
  background: #fff;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.list-item p {
  margin: 4px 0 0;
  color: var(--ink-soft);
  font-size: 0.84rem;
}

.evidence-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.evidence-grid article {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px;
  background: #fff;
  display: grid;
  gap: 4px;
}

.evidence-grid span {
  color: var(--ink-muted);
  font-size: 0.78rem;
}

.plain-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
}

.plain-list li {
  color: var(--ink-soft);
  font-size: 0.85rem;
}

.disposition p {
  margin: 0;
  color: var(--ink-soft);
}

.empty {
  border: 1px dashed var(--border-strong);
  border-radius: 8px;
  padding: 12px;
  color: var(--ink-muted);
  text-align: center;
  font-size: 0.84rem;
}
</style>
