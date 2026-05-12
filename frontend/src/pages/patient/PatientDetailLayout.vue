<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const route = useRoute()
const router = useRouter()

const patientId = computed(() => {
  const value = route.params.patientId
  if (typeof value === 'string' && value) return value
  if (workspace.selectedPatient?.patientId) return workspace.selectedPatient.patientId
  return readStoredPatientId()
})
const patient = computed(() => workspace.selectedPatient)
const loadingPatient = ref(false)
const loadError = ref('')

function readStoredPatientId() {
  if (typeof window === 'undefined') return ''
  return window.sessionStorage.getItem('ctpath:selectedPatientId') || ''
}

function rememberPatientId(id: string) {
  if (typeof window === 'undefined' || !id) return
  window.sessionStorage.setItem('ctpath:selectedPatientId', id)
}

const tabs = computed(() => {
  const id = patientId.value || patient.value?.patientId || ''
  return [
    { label: '总览', name: 'patient-overview', to: { name: 'patient-overview', params: { patientId: id } } },
    { label: '基本档案', name: 'patient-profile', to: { name: 'patient-profile', params: { patientId: id } } },
    { label: '联系记录', name: 'patient-contacts', to: { name: 'patient-contacts', params: { patientId: id } } },
    { label: '病程时间线', name: 'patient-timeline', to: { name: 'patient-timeline', params: { patientId: id } } },
    { label: '附件资料', name: 'patient-attachments', to: { name: 'patient-attachments', params: { patientId: id } } },
    { label: '当前用药', name: 'patient-medications', to: { name: 'patient-medications', params: { patientId: id } } },
    { label: '风险评估', name: 'patient-risk', to: { name: 'patient-risk', params: { patientId: id } } },
    { label: '随访记录', name: 'patient-followups', to: { name: 'patient-followups', params: { patientId: id } } },
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
  if (!route.params.patientId && typeof route.name === 'string' && route.name.startsWith('patient-')) {
    void router.replace({ name: route.name, params: { patientId: patientId.value }, query: route.query })
  }
  if (workspace.selectedPatientId === patientId.value && workspace.selectedPatient) return
  loadingPatient.value = true
  loadError.value = ''
  try {
    const loaded = await workspace.openPatient(patientId.value, 'archive')
    if (!loaded) {
      loadError.value = workspace.screenError || '患者档案读取失败，请返回患者列表后重试。'
    } else {
      rememberPatientId(patientId.value)
    }
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '患者档案读取失败，请返回患者列表后重试。'
  } finally {
    loadingPatient.value = false
  }
}

function backToList() {
  void router.push('/doctor/patients')
}

watch(patientId, () => void loadPatient(), { immediate: true })
watch(
  () => patient.value?.patientId,
  (next) => {
    if (next) rememberPatientId(next)
  },
  { immediate: true }
)
</script>

<template>
  <section class="patient-detail-layout-page workstation-page">
    <section v-if="!patient" class="empty-state-card patient-load-state">
      <h3>{{ loadError ? '患者详情加载失败' : '患者详情加载中' }}</h3>
      <p>{{ loadError || (loadingPatient ? '正在读取患者档案、病程和随访记录。' : '请选择患者后查看详情。') }}</p>
      <button class="secondary-button" type="button" @click="backToList">返回患者列表</button>
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
          :to="tab.to"
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

.patient-load-state {
  display: grid;
  justify-items: center;
  gap: 12px;
  min-height: 220px;
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
