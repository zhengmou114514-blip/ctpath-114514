<script setup lang="ts">
import type { PatientCase } from '../services/types'

defineProps<{
  patient: PatientCase
}>()
</script>

<template>
  <section class="patient-header">
    <div>
      <p class="surface-eyebrow">Patient Overview</p>
      <h2>{{ patient.name }} / {{ patient.patientId }}</h2>
      <p class="patient-summary-text">{{ patient.summary }}</p>
      <div class="patient-tags">
        <span>{{ patient.gender }}</span>
        <span>{{ patient.age }} 岁</span>
        <span>{{ patient.primaryDisease }}</span>
        <span>{{ patient.currentStage }}</span>
      </div>
    </div>
    <div class="patient-risk">
      <span>当前风险</span>
      <strong>{{ patient.riskLevel }}</strong>
      <small>最近一次随访：{{ patient.lastVisit }}</small>
    </div>
  </section>
</template>
