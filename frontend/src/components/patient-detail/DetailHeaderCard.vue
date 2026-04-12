<script setup lang="ts">
import type { PatientCase } from '../../services/types'

defineProps<{
  patient: PatientCase
}>()

function riskTone(level: string) {
  const raw = level.toLowerCase()
  if (raw.includes('high') || level.includes('高')) return 'risk-high'
  if (raw.includes('medium') || level.includes('中')) return 'risk-medium'
  return 'risk-low'
}
</script>

<template>
  <header class="detail-header card">
    <div class="main">
      <p class="eyebrow">Patient Overview</p>
      <h2>{{ patient.name }} <small>{{ patient.patientId }}</small></h2>
      <p class="primary">{{ patient.primaryDisease }} / {{ patient.currentStage }}</p>
    </div>

    <div class="chips">
      <span class="chip" :class="riskTone(patient.riskLevel)">风险: {{ patient.riskLevel }}</span>
      <span class="chip">最近就诊: {{ patient.lastVisit }}</span>
      <span class="chip">主治医生: {{ patient.primaryDoctor || '--' }}</span>
      <span class="chip">当前阶段: {{ patient.currentStage || '--' }}</span>
    </div>
  </header>
</template>

<style scoped>
.detail-header {
  padding: 14px 16px;
  display: grid;
  gap: 10px;
}

.main h2 {
  margin: 0;
  color: var(--navy);
}

.main h2 small {
  font-size: 0.82rem;
  color: var(--ink-muted);
  margin-left: 8px;
}

.main .primary {
  margin: 6px 0 0;
  color: var(--ink-soft);
}

.chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: #f8fafc;
  color: var(--navy);
  padding: 4px 10px;
  font-size: 0.8rem;
}

.risk-high {
  background: rgba(193, 74, 60, 0.14);
  color: #b03428;
}

.risk-medium {
  background: rgba(184, 122, 38, 0.16);
  color: #8d5c16;
}

.risk-low {
  background: rgba(23, 130, 93, 0.14);
  color: #16684b;
}
</style>
