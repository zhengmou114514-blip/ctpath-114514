<script setup lang="ts">
import type {
  DoctorUser,
  ImportPreviewPatient,
  PatientCase,
  PatientEventPayload,
  PatientSummary,
  PatientUpsertPayload,
  TimelineEvent,
} from '../services/types'
import ArchivistWorkbenchOverview from '../components/ArchivistWorkbenchOverview.vue'
import ArchiveQualityBoard from '../components/ArchiveQualityBoard.vue'
import ArchiveCreatePage from './archive/ArchiveCreatePage.vue'
import ArchiveDetailPage from './archive/ArchiveDetailPage.vue'
import ArchiveImportPage from './archive/ArchiveImportPage.vue'
import ArchiveListPage from './archive/ArchiveListPage.vue'

type ArchiveMode = 'list' | 'detail' | 'create' | 'import'
type ArchiveFocusSection = 'overview' | 'events'

defineProps<{
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
  <section v-if="mode === 'list'" class="role-page-stack">
    <ArchivistWorkbenchOverview
      v-if="doctorRole === 'archivist'"
      :patients="allPatients"
      @open="emit('open', $event)"
      @create="emit('create')"
      @import="emit('import')"
      @export="emit('export')"
    />

    <ArchiveQualityBoard
      v-if="doctorRole === 'archivist'"
      :patients="allPatients"
      @open="emit('open', $event)"
    />

    <ArchiveListPage
      :patients="patients"
      :loading-patients="loadingPatients"
      :current-page="currentPage"
      :total-pages="totalPages"
      :patient-count="patientCount"
      @open="emit('open', $event)"
      @create="emit('create')"
      @import="emit('import')"
      @prev-page="emit('prev-page')"
      @next-page="emit('next-page')"
    />
  </section>

  <ArchiveCreatePage
    v-else-if="mode === 'create'"
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
    @back="emit('back')"
  />

  <ArchiveImportPage
    v-else-if="mode === 'import'"
    :all-patients="allPatients"
    :importing="importingArchive ?? false"
    :result-text="importResultText ?? ''"
    @submit-import="emit('submit-import', $event)"
    @back="emit('back')"
  />

  <ArchiveDetailPage
    v-else
    :patient-form="patientForm"
    :selected-patient-id="selectedPatientId"
    :event-form="eventForm"
    :relation-options="relationOptions"
    :saving-patient="savingPatient"
    :saving-event="savingEvent"
    :timeline-items="timelineItems"
    :selected-patient="selectedPatient"
    :focus-section="focusSection"
    @submit-archive="emit('submit-archive')"
    @submit-event="emit('submit-event')"
    @prepare-new="emit('prepare-new')"
    @back="emit('back')"
  />
</template>
