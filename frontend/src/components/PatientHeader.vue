<script setup lang="ts">
import type { PatientCase } from '../services/types'

defineProps<{
  patient: PatientCase
}>()

function supportLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value
}

function stageLabel(value: string) {
  if (value === 'Early') return '早期'
  if (value === 'Mid') return '中期'
  if (value === 'Late') return '晚期'
  return value
}

function initials(name: string) {
  return (name || '患者').slice(0, 2)
}
</script>

<template>
  <section class="patient-header-block practical-header">
    <div class="patient-avatar-card">
      <img v-if="patient.avatarUrl" :src="patient.avatarUrl" :alt="patient.name" class="patient-avatar-image" />
      <div v-else class="patient-avatar-fallback">{{ initials(patient.name) }}</div>
    </div>

    <div class="patient-header-main">
      <p class="eyebrow">患者概览</p>
      <h2>{{ patient.name }}</h2>
      <p class="patient-id-line">{{ patient.patientId }} / {{ patient.primaryDisease }}</p>
      <p class="patient-summary">{{ patient.summary || '暂无病情摘要。' }}</p>
      <div class="patient-tags">
        <span>{{ patient.gender }}</span>
        <span>{{ patient.age }} 岁</span>
        <span>{{ stageLabel(patient.currentStage) }}</span>
        <span>支持度 {{ supportLabel(patient.dataSupport) }}</span>
        <span v-if="patient.phone">联系电话 {{ patient.phone }}</span>
        <span v-if="patient.emergencyContactName">
          紧急联系人 {{ patient.emergencyContactName }}{{ patient.emergencyContactRelation ? ` / ${patient.emergencyContactRelation}` : '' }}
        </span>
      </div>
    </div>

    <div class="patient-risk-badge">
      <span>风险等级</span>
      <strong>{{ patient.riskLevel }}</strong>
      <small>最近就诊 {{ patient.lastVisit }}</small>
      <small v-if="patient.emergencyContactPhone">联系人电话 {{ patient.emergencyContactPhone }}</small>
    </div>
  </section>
</template>
