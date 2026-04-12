<script setup lang="ts">
import { computed } from 'vue'
import type { PatientCase } from '../../services/types'

const props = defineProps<{
  patient: PatientCase
}>()

function supportLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value || '--'
}

const completeness = computed(() => {
  const checks = [
    props.patient.summary,
    props.patient.primaryDisease,
    props.patient.currentStage,
    props.patient.lastVisit,
    props.patient.primaryDoctor,
    props.patient.phone,
    props.patient.emergencyContactName,
    props.patient.familyHistory,
    props.patient.allergyHistory,
    props.patient.medicalRecordNumber,
  ]
  const completeCount = checks.filter((item) => Boolean(String(item ?? '').trim())).length
  return Math.round((completeCount / checks.length) * 100)
})

const completenessTone = computed(() => {
  if (completeness.value >= 80) return 'high'
  if (completeness.value >= 60) return 'medium'
  return 'low'
})
</script>

<template>
  <section class="card left-panel">
    <h3>档案信息</h3>

    <article class="group">
      <h4>档案摘要</h4>
      <p>{{ patient.summary || '暂无档案摘要' }}</p>
      <p>数据支持度: <strong>{{ supportLabel(patient.dataSupport) }}</strong></p>
    </article>

    <article class="group">
      <h4>既往史 / 过敏史 / 家族史</h4>
      <p><strong>既往史</strong>: {{ patient.primaryDisease || '--' }} / {{ patient.currentStage || '--' }}</p>
      <p><strong>过敏史</strong>: {{ patient.allergyHistory || '--' }}</p>
      <p><strong>家族史</strong>: {{ patient.familyHistory || '--' }}</p>
    </article>

    <article class="group">
      <h4>联系方式</h4>
      <p><strong>患者</strong>: {{ patient.phone || '--' }}</p>
      <p><strong>紧急联系人</strong>: {{ patient.emergencyContactName || '--' }}</p>
      <p><strong>关系</strong>: {{ patient.emergencyContactRelation || '--' }}</p>
      <p><strong>电话</strong>: {{ patient.emergencyContactPhone || '--' }}</p>
    </article>

    <article class="group">
      <h4>档案完整度</h4>
      <div class="completeness-row">
        <strong :class="`tone-${completenessTone}`">{{ completeness }}%</strong>
        <span>病历号: {{ patient.medicalRecordNumber || '--' }}</span>
      </div>
      <div class="completeness-track">
        <span class="completeness-fill" :style="{ width: `${completeness}%` }" />
      </div>
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
  color: var(--ws-title, #10263c);
  font-size: 1rem;
}

.group {
  border: 1px solid var(--ws-border, #cfd9e5);
  border-radius: 10px;
  background: #fbfdff;
  padding: 10px;
}

.group h4 {
  margin: 0 0 6px;
  font-size: 0.9rem;
  color: var(--ws-title, #10263c);
}

.group p {
  margin: 4px 0;
  color: var(--ws-text-muted, #617385);
  font-size: 0.84rem;
}

.completeness-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.completeness-row strong {
  font-size: 1.2rem;
}

.completeness-row span {
  color: var(--ws-text-muted, #617385);
  font-size: 0.78rem;
}

.tone-high {
  color: #1d7b5c;
}

.tone-medium {
  color: #9b6518;
}

.tone-low {
  color: #a4383f;
}

.completeness-track {
  margin-top: 8px;
  height: 8px;
  border-radius: 999px;
  border: 1px solid var(--ws-border, #cfd9e5);
  background: #f4f7fa;
  overflow: hidden;
}

.completeness-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #f39a5f 0%, #e3bf45 45%, #4ca77e 100%);
}
</style>
