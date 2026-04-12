<script setup lang="ts">
import ArchiveWorkspace from '../../components/ArchiveWorkspace.vue'
import type { PatientCase, PatientEventPayload, PatientUpsertPayload, TimelineEvent } from '../../services/types'

defineProps<{
  patientForm: PatientUpsertPayload
  selectedPatientId: string
  eventForm: PatientEventPayload
  relationOptions: string[]
  savingPatient: boolean
  savingEvent: boolean
  timelineItems: TimelineEvent[]
  selectedPatient: PatientCase | null
}>()

const emit = defineEmits<{
  (e: 'submit-archive'): void
  (e: 'submit-event'): void
  (e: 'prepare-new'): void
  (e: 'back'): void
}>()
</script>

<template>
  <section class="module-shell archive-page-shell">
    <article class="card archive-page-hero archive-page-hero-practical">
      <div>
        <p class="eyebrow">新建建档</p>
        <h3>登记患者基础信息</h3>
        <p class="page-copy">先建立基础档案，保存后自动进入详情页，再继续补录结构化事件。</p>
      </div>
      <div class="module-hero-actions">
        <button class="secondary-button" @click="emit('back')">返回档案列表</button>
      </div>
    </article>

    <ArchiveWorkspace
      mode="create"
      :patient-form="patientForm"
      :selected-patient-id="selectedPatientId"
      :event-form="eventForm"
      :relation-options="relationOptions"
      :saving-patient="savingPatient"
      :saving-event="savingEvent"
      :timeline-items="timelineItems"
      :selected-patient="selectedPatient"
      @submit-archive="emit('submit-archive')"
      @submit-event="emit('submit-event')"
      @prepare-new="emit('prepare-new')"
    />
  </section>
</template>
