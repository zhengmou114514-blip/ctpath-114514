<script setup lang="ts">
import { computed } from 'vue'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)
const logs = computed(() => patient.value?.contactLogs.slice(0, 8) ?? [])
</script>

<template>
  <section v-if="patient" class="patient-feature-grid">
    <article class="clinical-card">
      <h2>联系方式</h2>
      <p>患者电话：{{ patient.phone || '待补充' }}</p>
      <p>紧急联系人：{{ patient.emergencyContactName || '待补充' }} {{ patient.emergencyContactPhone || '' }}</p>
      <button class="secondary-button" type="button">追加联系记录</button>
    </article>
    <article class="clinical-card">
      <h2>最近联系记录</h2>
      <div class="mini-list">
        <p v-for="item in logs" :key="item.logId"><strong>{{ item.contactTime }}</strong><span>{{ item.contactResult }}：{{ item.note }}</span></p>
      </div>
    </article>
  </section>
</template>

<style scoped>
.patient-feature-grid { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 12px; }
.mini-list { display: grid; gap: 8px; }
.mini-list p { display: grid; gap: 4px; margin: 0; padding: 10px; background: #f7fbfd; border: 1px solid #d5e6ef; }
@media (max-width: 900px) { .patient-feature-grid { grid-template-columns: 1fr; } }
</style>
