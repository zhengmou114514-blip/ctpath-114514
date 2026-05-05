<script setup lang="ts">
import { computed } from 'vue'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)
const latestTimeline = computed(() => patient.value?.timeline.slice(0, 3) ?? [])
const firstAdvice = computed(() => workspace.predictionResult?.advice?.[0] ?? patient.value?.careAdvice?.[0] ?? '结合病程记录、当前用药和随访情况继续观察。')
</script>

<template>
  <section v-if="patient" class="patient-feature-grid">
    <article class="clinical-card wide-card">
      <p class="eyebrow">患者总览</p>
      <h2>{{ patient.name }}慢病管理摘要</h2>
      <p>{{ patient.summary }}</p>
    </article>
    <article class="clinical-card">
      <h2>最近病程</h2>
      <div class="mini-list">
        <p v-for="item in latestTimeline" :key="`${item.date}-${item.title}`"><strong>{{ item.date }}</strong><span>{{ item.title }}：{{ item.detail }}</span></p>
      </div>
    </article>
    <article class="clinical-card">
      <h2>当前风险</h2>
      <strong class="big-value">{{ patient.riskLevel }}</strong>
      <p>数据支持：{{ patient.dataSupport }}</p>
    </article>
    <article class="clinical-card">
      <h2>当前用药摘要</h2>
      <p>当前用药由药事管理模块维护，医生端仅展示摘要与复核结果。</p>
    </article>
    <article class="clinical-card">
      <h2>下一步动作</h2>
      <p>{{ firstAdvice }}</p>
    </article>
  </section>
</template>

<style scoped>
.patient-feature-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.wide-card { grid-column: 1 / -1; }
.mini-list { display: grid; gap: 8px; }
.mini-list p { display: grid; gap: 4px; margin: 0; padding: 10px; background: #f7fbfd; border: 1px solid #d5e6ef; }
.big-value { color: #0f6f99; font-size: 32px; }
@media (max-width: 900px) { .patient-feature-grid { grid-template-columns: 1fr; } }
</style>
