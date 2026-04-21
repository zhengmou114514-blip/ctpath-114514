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
  <section class="patient-context-bar" aria-label="当前患者上下文">
    <div class="context-main">
      <div class="identity">
        <strong class="name">{{ patient.name || '未选择患者' }}</strong>
        <span class="meta">
          <span class="mono">MRN {{ patient.medicalRecordNumber || patient.patientId }}</span>
          <span>{{ patient.age }} 岁</span>
          <span>{{ patient.gender }}</span>
          <span>{{ patient.primaryDisease }}</span>
        </span>
      </div>

      <div class="chips">
        <span class="chip risk-pill" :class="riskTone(patient.riskLevel)">风险 {{ patient.riskLevel || '--' }}</span>
        <span class="chip">数据支持 {{ supportLabel(patient.dataSupport) }}</span>
        <span class="chip">就诊状态 {{ patient.encounterStatus || '--' }}</span>
        <span class="chip">最近就诊 {{ patient.lastVisit || '--' }}</span>
        <span v-if="pendingTaskCount" class="chip status-warning">待处理 {{ pendingTaskCount }}</span>
      </div>
    </div>

    <div class="context-actions">
      <button class="secondary-button" type="button" @click="emit('back-to-list')">返回队列</button>
      <button class="secondary-button" type="button" @click="emit('open-archive', { patientId: patient.patientId, focus: 'overview' })">
        患者档案
      </button>
      <button class="secondary-button" type="button" @click="emit('open-archive', { patientId: patient.patientId, focus: 'events' })">
        病程事件
      </button>
      <button class="primary-button" type="button" @click="emit('open-followup', { patientId: patient.patientId, section: 'tasks' })">
        随访任务
      </button>
    </div>
  </section>
</template>

<style scoped>
.patient-context-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 16px;
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: var(--ws-surface);
}

.context-main,
.identity {
  min-width: 0;
  display: grid;
  gap: 8px;
}

.name {
  color: var(--ws-title);
  font-size: 16px;
}

.meta,
.chips,
.context-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.meta {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border: 1px solid var(--ws-border);
  border-radius: 999px;
  background: var(--ws-surface-soft);
  color: var(--ws-title);
  font-size: 12px;
  font-weight: 700;
}

.context-actions {
  justify-content: flex-end;
}

@media (max-width: 980px) {
  .patient-context-bar {
    display: grid;
  }

  .context-actions {
    justify-content: flex-start;
  }
}
</style>
