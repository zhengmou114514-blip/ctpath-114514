<script setup lang="ts">
import { computed } from 'vue'
import type { PatientCase } from '../services/types'

const props = defineProps<{
  patient: PatientCase
}>()

const emit = defineEmits<{
  (e: 'open-archive', payload: { patientId: string; focus?: 'overview' | 'events' }): void
  (e: 'open-followup', payload: { patientId: string; section?: 'tasks' | 'contacts' | 'flow' }): void
  (e: 'back-to-list'): void
}>()

const pendingTaskCount = computed(() => {
  const doneStatuses = ['completed', 'closed', 'done']
  return (props.patient.outpatientTasks ?? []).filter((task) => !doneStatuses.includes(String(task.status).toLowerCase())).length
})

function riskTone(level: string) {
  const raw = (level || '').toLowerCase()
  if (raw.includes('high')) return 'risk-high'
  if (raw.includes('medium')) return 'risk-medium'
  return 'risk-low'
}

function supportLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value || '--'
}
</script>

<template>
  <section class="patient-context-bar" aria-label="当前患者摘要">
    <div class="context-main">
      <div class="identity">
        <p class="eyebrow">当前患者</p>
        <strong class="name">{{ patient.name || '已选患者' }}</strong>
        <span class="meta">
          <span class="mono">病案号 {{ patient.medicalRecordNumber || patient.patientId }}</span>
          <span>{{ patient.age }} 岁</span>
          <span>{{ patient.gender }}</span>
          <span>{{ patient.primaryDisease }}</span>
        </span>
      </div>

      <div class="chips">
        <span class="chip risk-pill" :class="riskTone(patient.riskLevel)">{{ patient.riskLevel || '--' }}</span>
        <span class="chip">数据支撑 {{ supportLabel(patient.dataSupport) }}</span>
        <span class="chip">就诊状态 {{ patient.encounterStatus || '--' }}</span>
        <span class="chip">最近就诊 {{ patient.lastVisit || '--' }}</span>
        <span v-if="pendingTaskCount" class="chip status-warning">{{ pendingTaskCount }} 个待随访任务</span>
      </div>
    </div>

    <div class="context-actions">
      <button class="secondary-button" type="button" @click="emit('back-to-list')">返回列表</button>
      <button class="secondary-button" type="button" @click="emit('open-archive', { patientId: patient.patientId, focus: 'overview' })">
        打开档案
      </button>
      <button class="secondary-button" type="button" @click="emit('open-archive', { patientId: patient.patientId, focus: 'events' })">
        打开时间线
      </button>
      <button class="primary-button" type="button" @click="emit('open-followup', { patientId: patient.patientId, section: 'tasks' })">
        打开随访任务
      </button>
    </div>
  </section>
</template>

<style scoped>
.context-main,
.identity {
  min-width: 0;
  display: grid;
  gap: 10px;
}

.name {
  font-size: 22px;
}

.meta,
.chips,
.context-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.meta {
  color: rgba(63, 72, 73, 0.76);
  font-size: 12px;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

.chip {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(241, 244, 245, 0.9);
  color: var(--ws-on-surface);
  font-size: 12px;
  font-weight: 700;
}

.context-actions {
  justify-content: flex-end;
}

@media (max-width: 980px) {
  .context-actions {
    justify-content: flex-start;
  }
}
</style>
