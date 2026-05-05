<script setup lang="ts">
import { computed } from 'vue'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)
const topK = computed(() => workspace.predictionResult?.topk ?? patient.value?.predictions ?? [])
const advice = computed(() => workspace.predictionResult?.advice ?? patient.value?.careAdvice ?? [])
const evidence = computed(() => workspace.predictionResult?.supportSummary || patient.value?.summary || '当前展示演示推理结果和规则回退摘要。')
</script>

<template>
  <section v-if="patient" class="patient-feature-grid">
    <article class="clinical-card">
      <p class="eyebrow">风险评估</p>
      <h2>风险评估结果</h2>
      <p>当前内容为演示推理结果或规则回退结果，仅供医生诊疗参考。</p>
      <div class="risk-list">
        <p v-for="item in topK.slice(0, 3)" :key="item.label"><strong>{{ item.label }} {{ Math.round(item.score * 100) }}%</strong><span>{{ item.reason }}</span></p>
      </div>
    </article>
    <article class="clinical-card">
      <h2>证据摘要</h2>
      <p>{{ evidence }}</p>
      <h2>辅助建议</h2>
      <ol>
        <li v-for="item in advice.slice(0, 5)" :key="item">{{ item }}</li>
      </ol>
    </article>
  </section>
</template>

<style scoped>
.patient-feature-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.risk-list { display: grid; gap: 8px; }
.risk-list p { display: grid; gap: 4px; margin: 0; padding: 10px; background: #f7fbfd; border: 1px solid #d5e6ef; }
@media (max-width: 900px) { .patient-feature-grid { grid-template-columns: 1fr; } }
</style>
