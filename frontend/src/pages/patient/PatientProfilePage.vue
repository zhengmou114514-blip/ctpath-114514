<script setup lang="ts">
import { computed } from 'vue'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)

function archiveStatus(value: string) {
  if (value === 'active') return '已建档'
  if (value === 'draft') return '待补全'
  return value || '待维护'
}

function consentStatus(value: string) {
  if (value === 'signed') return '已签署'
  if (value === 'family_authorized') return '家属授权'
  return '待签署'
}
</script>

<template>
  <section v-if="patient" class="clinical-card">
    <div class="section-header">
      <div>
        <p class="eyebrow">基本档案</p>
        <h2>患者基础信息</h2>
      </div>
      <button class="secondary-button" type="button">补全档案</button>
    </div>
    <dl class="profile-grid">
      <div><dt>姓名</dt><dd>{{ patient.name }}</dd></div>
      <div><dt>性别</dt><dd>{{ patient.gender }}</dd></div>
      <div><dt>年龄</dt><dd>{{ patient.age }}岁</dd></div>
      <div><dt>联系方式</dt><dd>{{ patient.phone || '待补充' }}</dd></div>
      <div><dt>病历号</dt><dd>{{ patient.medicalRecordNumber || patient.patientId }}</dd></div>
      <div><dt>主治医生</dt><dd>{{ patient.primaryDoctor || '待分配' }}</dd></div>
      <div><dt>档案状态</dt><dd>{{ archiveStatus(patient.archiveStatus) }}</dd></div>
      <div><dt>知情同意</dt><dd>{{ consentStatus(patient.consentStatus) }}</dd></div>
    </dl>
  </section>
</template>

<style scoped>
.profile-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 0; }
.profile-grid div { border: 1px solid #d5e6ef; background: #fff; padding: 10px; }
.profile-grid dt { color: #527384; font-weight: 800; }
.profile-grid dd { margin: 4px 0 0; color: #243f4d; font-weight: 900; }
@media (max-width: 900px) { .profile-grid { grid-template-columns: 1fr; } }
</style>
