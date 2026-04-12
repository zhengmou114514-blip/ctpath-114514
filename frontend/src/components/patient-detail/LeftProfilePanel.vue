<script setup lang="ts">
import type { PatientCase } from '../../services/types'

defineProps<{
  patient: PatientCase
}>()

function supportLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value || '--'
}
</script>

<template>
  <section class="card left-panel">
    <h3>档案与病史</h3>

    <article class="group">
      <h4>档案摘要</h4>
      <p>{{ patient.summary || '暂无摘要' }}</p>
      <p>数据支持度: <strong>{{ supportLabel(patient.dataSupport) }}</strong></p>
    </article>

    <article class="group">
      <h4>既往史</h4>
      <p>{{ patient.primaryDisease || '--' }} / {{ patient.currentStage || '--' }}</p>
    </article>

    <article class="group">
      <h4>家族史</h4>
      <p>{{ patient.familyHistory || '--' }}</p>
    </article>

    <article class="group">
      <h4>过敏史</h4>
      <p>{{ patient.allergyHistory || '--' }}</p>
    </article>

    <article class="group">
      <h4>联系方式</h4>
      <p>患者: {{ patient.phone || '--' }}</p>
      <p>紧急联系人: {{ patient.emergencyContactName || '--' }} {{ patient.emergencyContactPhone || '' }}</p>
    </article>
  </section>
</template>

<style scoped>
.left-panel {
  padding: 12px;
  display: grid;
  gap: 10px;
  align-content: start;
}

.left-panel h3 {
  margin: 0;
  color: var(--navy);
  font-size: 1rem;
}

.group {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #fbfdff;
  padding: 10px;
}

.group h4 {
  margin: 0 0 6px;
  font-size: 0.9rem;
  color: var(--navy);
}

.group p {
  margin: 4px 0;
  color: var(--ink-soft);
  font-size: 0.86rem;
}
</style>
