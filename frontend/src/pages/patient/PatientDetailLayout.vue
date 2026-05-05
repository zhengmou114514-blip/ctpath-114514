<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const route = useRoute()
const router = useRouter()

const patientId = computed(() => {
  const value = route.params.patientId
  return typeof value === 'string' ? value : ''
})
const patient = computed(() => workspace.selectedPatient)

const tabs = computed(() => {
  const id = patientId.value || patient.value?.patientId || ''
  return [
    { label: '总览', name: 'patient-overview', path: `/doctor/patients/${id}/overview` },
    { label: '基本档案', name: 'patient-profile', path: `/doctor/patients/${id}/profile` },
    { label: '联系记录', name: 'patient-contacts', path: `/doctor/patients/${id}/contacts` },
    { label: '病程时间线', name: 'patient-timeline', path: `/doctor/patients/${id}/timeline` },
    { label: '附件资料', name: 'patient-attachments', path: `/doctor/patients/${id}/attachments` },
    { label: '当前用药', name: 'patient-medications', path: `/doctor/patients/${id}/medications` },
    { label: '风险评估', name: 'patient-risk', path: `/doctor/patients/${id}/risk` },
    { label: '随访记录', name: 'patient-followups', path: `/doctor/patients/${id}/followups` },
  ]
})

function riskLabel(value: string) {
  const raw = String(value || '').toLowerCase()
  if (raw.includes('high') || raw.includes('高')) return '高风险'
  if (raw.includes('medium') || raw.includes('中')) return '中风险'
  return '低风险'
}

function archiveNumber() {
  if (!patient.value) return ''
  return patient.value.medicalRecordNumber || `MRN-${patient.value.patientId.replace(/\D/g, '').padStart(4, '0')}`
}

async function loadPatient() {
  if (!patientId.value) return
  if (workspace.selectedPatientId === patientId.value && workspace.selectedPatient) return
  await workspace.openPatient(patientId.value, 'doctor')
}

function backToList() {
  void router.push('/doctor/patients')
}

watch(patientId, () => void loadPatient(), { immediate: true })
</script>

<template>
  <section class="patient-detail-layout-page workstation-page">
    <section v-if="!patient" class="empty-state-card">
      <h3>患者详情加载中</h3>
      <p>正在读取患者档案、病程和随访记录。</p>
    </section>

    <template v-else>
      <header class="clinical-card patient-detail-shell-header">
        <div>
          <p class="eyebrow">患者档案</p>
          <h1>{{ patient.name }}</h1>
          <p>{{ archiveNumber() }} / {{ patient.primaryDisease }} / {{ patient.currentStage }} / {{ riskLabel(patient.riskLevel) }}</p>
        </div>
        <button class="secondary-button" type="button" @click="backToList">返回患者列表</button>
      </header>

      <nav class="patient-subnav">
        <RouterLink
          v-for="tab in tabs"
          :key="tab.name"
          class="patient-subnav-item"
          :class="{ active: route.name === tab.name }"
          :to="tab.path"
        >
          {{ tab.label }}
        </RouterLink>
      </nav>

      <RouterView />
    </template>
  </section>
</template>

<style scoped>
.patient-detail-layout-page {
  gap: 12px;
}

.patient-detail-shell-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.patient-detail-shell-header h1 {
  margin: 2px 0 4px;
  font-size: 32px;
}

.patient-detail-shell-header p {
  margin: 0;
  color: #526772;
}

.patient-subnav {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  border-bottom: 1px solid #cfdde5;
}

.patient-subnav-item {
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  border: 1px solid #cfdde5;
  border-bottom: 0;
  border-radius: 4px 4px 0 0;
  background: #f7fbfd;
  color: #275d70;
  padding: 0 12px;
  text-decoration: none;
  font-weight: 800;
}

.patient-subnav-item.active {
  background: #008bbf;
  border-color: #008bbf;
  color: #fff;
}
</style>
