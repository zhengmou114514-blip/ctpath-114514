<script setup lang="ts">
import { computed } from 'vue'
import type { PatientSummary } from '../services/types'

const props = defineProps<{
  patients: PatientSummary[]
}>()

const emit = defineEmits<{
  (e: 'create'): void
  (e: 'import'): void
  (e: 'export'): void
  (e: 'open', patientId: string): void
}>()

const summary = computed(() => ({
  total: props.patients.length,
  missingMrn: props.patients.filter((item) => !item.medicalRecordNumber).length,
  pendingConsent: props.patients.filter((item) => item.consentStatus === 'pending').length,
  draft: props.patients.filter((item) => item.archiveStatus === 'draft').length,
}))

const priorityItems = computed(() =>
  props.patients
    .filter((item) => !item.medicalRecordNumber || item.consentStatus === 'pending' || item.archiveStatus === 'draft')
    .slice(0, 6)
)
</script>

<template>
  <section class="card archivist-overview-board">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Archive Desk</p>
        <h3>档案治理总览</h3>
      </div>
      <div class="module-hero-actions">
        <button class="secondary-button" @click="emit('import')">批量导入</button>
        <button class="secondary-button" @click="emit('export')">导出档案</button>
        <button class="primary-button" @click="emit('create')">新建档案</button>
      </div>
    </div>

    <div class="archivist-overview-grid">
      <div class="role-focus-metrics">
        <article class="role-focus-metric">
          <span>档案总量</span>
          <strong>{{ summary.total }}</strong>
        </article>
        <article class="role-focus-metric">
          <span>缺失 MRN</span>
          <strong>{{ summary.missingMrn }}</strong>
        </article>
        <article class="role-focus-metric">
          <span>待签知情同意</span>
          <strong>{{ summary.pendingConsent }}</strong>
        </article>
        <article class="role-focus-metric">
          <span>草稿档案</span>
          <strong>{{ summary.draft }}</strong>
        </article>
      </div>

      <article class="role-focus-section">
        <strong>优先治理档案</strong>
        <button
          v-for="item in priorityItems"
          :key="item.patientId"
          class="role-focus-row"
          @click="emit('open', item.patientId)"
        >
          <span>{{ item.name }} / {{ item.patientId }}</span>
          <small>
            {{ item.medicalRecordNumber ? 'MRN 已建立' : '缺失 MRN' }}
            {{ item.consentStatus === 'pending' ? ' / 待签同意' : '' }}
            {{ item.archiveStatus === 'draft' ? ' / 草稿档案' : '' }}
          </small>
        </button>
        <p v-if="!priorityItems.length" class="risk-group-empty">当前没有明显待治理档案，可继续推进导入或新建建档。</p>
      </article>
    </div>
  </section>
</template>
