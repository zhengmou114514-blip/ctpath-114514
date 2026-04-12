<script setup lang="ts">
import ArchivePage from './ArchivePage.vue'
import type {
  DoctorUser,
  ImportPreviewPatient,
  PatientCase,
  PatientEventPayload,
  PatientSummary,
  PatientUpsertPayload,
  TimelineEvent,
} from '../services/types'
import type { ArchiveFocusSection, ArchiveMode } from '../types/workspace'

const props = defineProps<{
  mode: ArchiveMode
  allPatients: PatientSummary[]
  patients: PatientSummary[]
  loadingPatients: boolean
  currentPage: number
  totalPages: number
  patientCount: number
  patientForm: PatientUpsertPayload
  selectedPatientId: string
  eventForm: PatientEventPayload
  relationOptions: string[]
  savingPatient: boolean
  savingEvent: boolean
  timelineItems: TimelineEvent[]
  selectedPatient: PatientCase | null
  focusSection?: ArchiveFocusSection
  importingArchive?: boolean
  importResultText?: string
  doctorRole?: DoctorUser['role']
  noPermission?: boolean
  modelUnavailable?: boolean
}>()

const emit = defineEmits<{
  (e: 'open', patientId: string): void
  (e: 'create'): void
  (e: 'import'): void
  (e: 'export'): void
  (e: 'prev-page'): void
  (e: 'next-page'): void
  (e: 'submit-archive'): void
  (e: 'submit-event'): void
  (e: 'submit-import', rows: ImportPreviewPatient[]): void
  (e: 'prepare-new'): void
  (e: 'back'): void
}>()
</script>

<template>
  <section v-if="props.noPermission" class="empty-state-card">
    <h3>无权限</h3>
    <p>当前账号无档案模块访问权限。</p>
  </section>

  <section v-else-if="props.loadingPatients" class="empty-state-card">
    <h3>加载中</h3>
    <p>正在加载档案数据，请稍候。</p>
  </section>

  <section v-else-if="!props.allPatients.length && props.mode === 'list'" class="empty-state-card">
    <h3>无数据</h3>
    <p>当前暂无患者档案，可点击“新建档案”或“进入导入”。</p>
  </section>

  <section v-else-if="props.modelUnavailable && props.mode === 'list'" class="empty-state-card">
    <h3>模型不可用</h3>
    <p>模型服务当前不可用，档案维护功能不受影响。</p>
  </section>

  <ArchivePage
    v-else
    :mode="props.mode"
    :all-patients="props.allPatients"
    :patients="props.patients"
    :loading-patients="props.loadingPatients"
    :current-page="props.currentPage"
    :total-pages="props.totalPages"
    :patient-count="props.patientCount"
    :patient-form="props.patientForm"
    :selected-patient-id="props.selectedPatientId"
    :event-form="props.eventForm"
    :relation-options="props.relationOptions"
    :saving-patient="props.savingPatient"
    :saving-event="props.savingEvent"
    :timeline-items="props.timelineItems"
    :selected-patient="props.selectedPatient"
    :focus-section="props.focusSection"
    :importing-archive="props.importingArchive"
    :import-result-text="props.importResultText"
    :doctor-role="props.doctorRole"
    @open="emit('open', $event)"
    @create="emit('create')"
    @import="emit('import')"
    @export="emit('export')"
    @prev-page="emit('prev-page')"
    @next-page="emit('next-page')"
    @submit-archive="emit('submit-archive')"
    @submit-event="emit('submit-event')"
    @submit-import="emit('submit-import', $event)"
    @prepare-new="emit('prepare-new')"
    @back="emit('back')"
  />
</template>

