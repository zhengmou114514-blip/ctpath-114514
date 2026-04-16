<script setup lang="ts">
import { computed } from 'vue'
import type { PatientCase } from '../services/types'

const props = defineProps<{
  patient: PatientCase
  followupFocusPatientId?: string
}>()

const emit = defineEmits<{
  (e: 'open-archive', payload: { patientId: string; focus?: 'overview' | 'events' }): void
  (e: 'open-followup', payload: { patientId: string; section?: 'tasks' | 'contacts' | 'flow' }): void
  (e: 'back-to-list'): void
}>()

function riskTone(level: string) {
  const raw = (level || '').toLowerCase()
  if (raw.includes('high') || (level || '').includes('高')) return 'risk-high'
  if (raw.includes('medium') || (level || '').includes('中')) return 'risk-medium'
  return 'risk-low'
}

function supportTone(value: string) {
  if (value === 'high') return 'support-strong'
  if (value === 'medium') return 'support-limited'
  return 'support-minimal'
}

function supportLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value || '--'
}

const pendingTaskCount = computed(() => {
  const tasks = props.patient.outpatientTasks ?? []
  return tasks.filter((t) => !['已完成', '已关闭', 'Completed', 'Closed'].includes(String(t.status))).length
})
</script>

<template>
  <section class="patient-context-bar card" aria-label="patient-context">
    <div class="context-main">
      <div class="identity">
        <strong class="name">{{ props.patient.name || '未命名患者' }}</strong>
        <span class="meta">
          <span class="mono">MRN {{ props.patient.medicalRecordNumber || props.patient.patientId }}</span>
          <span class="dot">·</span>
          <span>{{ props.patient.age }} 岁</span>
          <span class="dot">·</span>
          <span>{{ props.patient.gender }}</span>
        </span>
      </div>

      <div class="chips">
        <span class="chip risk-pill" :class="riskTone(props.patient.riskLevel)">
          风险 {{ props.patient.riskLevel || '--' }}
        </span>
        <span class="chip support-badge" :class="supportTone(props.patient.dataSupport)">
          支持度 {{ supportLabel(props.patient.dataSupport) }}
        </span>
        <span class="chip">
          接诊状态 {{ props.patient.encounterStatus || '--' }}
        </span>
        <span class="chip">最近就诊 {{ props.patient.lastVisit || '--' }}</span>
        <span v-if="props.patient.primaryDisease" class="chip">主诊断 {{ props.patient.primaryDisease }}</span>
        <span v-if="pendingTaskCount" class="chip">
          待办 {{ pendingTaskCount }}
        </span>
      </div>
    </div>

    <div class="context-actions">
      <button class="secondary-button" type="button" @click="emit('back-to-list')">返回列表</button>
      <button class="secondary-button" type="button" @click="emit('open-archive', { patientId: props.patient.patientId, focus: 'overview' })">
        打开档案
      </button>
      <button class="secondary-button" type="button" @click="emit('open-archive', { patientId: props.patient.patientId, focus: 'events' })">
        补录事件
      </button>
      <button class="primary-button" type="button" @click="emit('open-followup', { patientId: props.patient.patientId, section: 'tasks' })">
        打开随访
      </button>
    </div>
  </section>
</template>

<style scoped>
.patient-context-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 12px;
  margin: 12px 0 14px;
}

.context-main {
  min-width: 0;
  display: grid;
  gap: 10px;
}

.identity {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.name {
  font-size: 1rem;
  letter-spacing: 0.01em;
}

.meta {
  color: var(--ws-text-muted, #617385);
  font-size: 0.84rem;
  display: inline-flex;
  gap: 8px;
  flex-wrap: wrap;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.dot {
  opacity: 0.6;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.chip {
  border: 1px solid var(--ws-border, #cfd9e5);
  background: #f7fafd;
  color: var(--ws-title, #10263c);
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  white-space: nowrap;
}

.context-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

@media (max-width: 980px) {
  .patient-context-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .context-actions {
    justify-content: flex-start;
  }
}
</style>

