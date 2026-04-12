<script setup lang="ts">
import { computed } from 'vue'
import ArchiveWorkspace from '../../components/ArchiveWorkspace.vue'
import type { PatientCase, PatientEventPayload, PatientUpsertPayload, TimelineEvent } from '../../services/types'

type ArchiveFocusSection = 'overview' | 'events'

const props = defineProps<{
  patientForm: PatientUpsertPayload
  selectedPatientId: string
  eventForm: PatientEventPayload
  relationOptions: string[]
  savingPatient: boolean
  savingEvent: boolean
  timelineItems: TimelineEvent[]
  selectedPatient: PatientCase | null
  focusSection?: ArchiveFocusSection
}>()

const emit = defineEmits<{
  (e: 'submit-archive'): void
  (e: 'submit-event'): void
  (e: 'prepare-new'): void
  (e: 'back'): void
}>()

const headerFacts = computed(() => [
  { label: '患者编号', value: props.selectedPatient?.patientId ?? props.patientForm.patientId ?? '-' },
  { label: '主要疾病', value: props.selectedPatient?.primaryDisease ?? props.patientForm.primaryDisease ?? '-' },
  { label: '当前阶段', value: props.selectedPatient?.currentStage ?? props.patientForm.currentStage ?? '-' },
  { label: '最近就诊', value: props.selectedPatient?.lastVisit ?? props.patientForm.lastVisit ?? '-' },
])
</script>

<template>
  <section class="module-shell archive-page-shell">
    <article class="card archive-page-hero archive-page-hero-practical">
      <div>
        <p class="eyebrow">档案详情</p>
        <h3>患者档案维护</h3>
        <p class="page-copy">档案详情页承担基础信息修订、结构化事件补录和病程摘要查看。</p>
      </div>
      <div class="archive-detail-facts">
        <div v-for="item in headerFacts" :key="item.label" class="summary-chip">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
        <button class="secondary-button" @click="emit('back')">返回档案列表</button>
      </div>
    </article>

    <ArchiveWorkspace
      mode="detail"
      :patient-form="props.patientForm"
      :selected-patient-id="props.selectedPatientId"
      :event-form="props.eventForm"
      :relation-options="props.relationOptions"
      :saving-patient="props.savingPatient"
      :saving-event="props.savingEvent"
      :timeline-items="props.timelineItems"
      :selected-patient="props.selectedPatient"
      :focus-section="props.focusSection"
      @submit-archive="emit('submit-archive')"
      @submit-event="emit('submit-event')"
      @prepare-new="emit('prepare-new')"
    />
  </section>
</template>
