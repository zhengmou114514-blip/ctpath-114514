<script setup lang="ts">
import { computed } from 'vue'
import type { PatientCase } from '../../services/types'

const props = defineProps<{
  patient: PatientCase
  dataMode: string
  lastUpdatedAt: string
  degradedReasons: string[]
}>()

function riskTone(level: string) {
  const raw = level.toLowerCase()
  if (raw.includes('high') || level.includes('高')) return 'risk-high'
  if (raw.includes('medium') || level.includes('中')) return 'risk-medium'
  return 'risk-low'
}

const updatedAtLabel = computed(() => {
  if (!props.lastUpdatedAt) return '--'
  return props.lastUpdatedAt.replace('T', ' ').slice(0, 19)
})
</script>

<template>
  <header class="workstation-header card">
    <div class="header-main">
      <div>
        <p class="eyebrow">Patient Summary</p>
        <h2>{{ patient.name }}</h2>
        <p class="basic-line">ID: {{ patient.patientId }} | {{ patient.age }}岁 | {{ patient.gender }}</p>
      </div>
      <div class="meta-line">
        <span>数据源: {{ dataMode }}</span>
        <span>最后更新: {{ updatedAtLabel }}</span>
      </div>
    </div>

    <div class="header-tags">
      <span class="tag">主诊断: {{ patient.primaryDisease || '--' }}</span>
      <span class="tag">当前阶段: {{ patient.currentStage || '--' }}</span>
      <span class="tag" :class="riskTone(patient.riskLevel)">风险等级: {{ patient.riskLevel || '--' }}</span>
      <span class="tag">最近就诊: {{ patient.lastVisit || '--' }}</span>
      <span class="tag">主治医生: {{ patient.primaryDoctor || '--' }}</span>
    </div>
  </header>
</template>

<style scoped>
.workstation-header {
  position: sticky;
  top: 8px;
  z-index: 6;
  padding: 12px 14px;
  display: grid;
  gap: 10px;
}

.header-main {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
}

.header-main h2 {
  margin: 0;
  font-size: 1.08rem;
}

.basic-line {
  margin: 6px 0 0;
  color: var(--ws-text-muted, #617385);
  font-size: 0.84rem;
}

.meta-line {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--ws-text-muted, #617385);
  font-size: 0.8rem;
  text-align: right;
}

.header-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  border: 1px solid var(--ws-border, #cfd9e5);
  border-radius: 999px;
  background: #f7fafd;
  padding: 4px 10px;
  color: var(--ws-title, #10263c);
  font-size: 0.8rem;
}

.risk-high {
  background: #fdeced;
  border-color: #efc2c5;
  color: #a4383f;
}

.risk-medium {
  background: #fff4e2;
  border-color: #efdbb2;
  color: #9b6518;
}

.risk-low {
  background: #e9f8f1;
  border-color: #bde7d1;
  color: #1d7b5c;
}

@media (max-width: 980px) {
  .header-main {
    flex-direction: column;
    align-items: start;
  }

  .meta-line {
    text-align: left;
  }
}
</style>
