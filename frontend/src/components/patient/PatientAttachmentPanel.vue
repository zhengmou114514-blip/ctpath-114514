<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import {
  fetchPatientAttachmentBlob,
  getPatientAttachments,
  uploadPatientAttachment,
} from '../../services/api'
import type { PatientAttachmentRecord, PatientAttachmentType } from '../../services/types'

const props = defineProps<{
  patientId: string
  title?: string
}>()

const attachmentTypes: Array<{ value: PatientAttachmentType; label: string }> = [
  { value: 'patient_photo', label: 'Patient photo' },
  { value: 'id_card', label: 'ID card' },
  { value: 'insurance_card', label: 'Insurance card' },
  { value: 'referral_note', label: 'Referral note' },
  { value: 'exam_report', label: 'Exam report' },
  { value: 'informed_consent', label: 'Informed consent' },
]

const loading = ref(false)
const uploading = ref(false)
const errorMessage = ref('')
const attachments = ref<PatientAttachmentRecord[]>([])
const selectedType = ref<PatientAttachmentType>('exam_report')
const previewRecord = ref<PatientAttachmentRecord | null>(null)
const previewUrl = ref('')
const previewMimeType = ref('')

const attachmentCount = computed(() => attachments.value.length)

function formatDateTime(value: string): string {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function formatFileSize(value: number): string {
  if (!Number.isFinite(value) || value <= 0) return '--'
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(1)} MB`
}

async function reloadAttachments() {
  if (!props.patientId) {
    attachments.value = []
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    attachments.value = await getPatientAttachments(props.patientId)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load patient attachments.'
  } finally {
    loading.value = false
  }
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !props.patientId) {
    input.value = ''
    return
  }

  uploading.value = true
  errorMessage.value = ''
  try {
    await uploadPatientAttachment(props.patientId, {
      type: selectedType.value,
      file,
    })
    await reloadAttachments()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to upload patient attachment.'
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function openPreview(record: PatientAttachmentRecord) {
  closePreview()
  errorMessage.value = ''

  try {
    const result = await fetchPatientAttachmentBlob(record.patientId, record.attachmentId)
    previewRecord.value = record
    previewUrl.value = URL.createObjectURL(result.blob)
    previewMimeType.value = result.mimeType
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to open attachment preview.'
  }
}

function closePreview() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewRecord.value = null
  previewUrl.value = ''
  previewMimeType.value = ''
}

function openPreviewInNewTab() {
  if (!previewUrl.value) return
  window.open(previewUrl.value, '_blank', 'noopener,noreferrer')
}

watch(
  () => props.patientId,
  () => {
    closePreview()
    void reloadAttachments()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  closePreview()
})
</script>

<template>
  <section class="patient-attachment-panel">
    <header class="panel-header">
      <div>
        <p class="eyebrow">Electronic archive</p>
        <h3>{{ title || 'Patient Attachments' }}</h3>
        <p class="subtle">
          Patient {{ patientId || '--' }} / {{ attachmentCount }} attachment records
        </p>
      </div>
      <button class="secondary-button" type="button" :disabled="loading" @click="reloadAttachments">
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <p v-if="errorMessage" class="message error">{{ errorMessage }}</p>

    <section class="upload-card">
      <label class="field">
        <span>Attachment type</span>
        <select v-model="selectedType" :disabled="uploading || loading">
          <option v-for="item in attachmentTypes" :key="item.value" :value="item.value">
            {{ item.label }}
          </option>
        </select>
      </label>

      <label class="upload-button" :class="{ disabled: uploading || loading || !patientId }">
        <input
          type="file"
          accept="image/*,.pdf,.doc,.docx"
          :disabled="uploading || loading || !patientId"
          @change="handleUpload"
        />
        {{ uploading ? 'Uploading...' : 'Upload attachment' }}
      </label>
    </section>

    <section class="attachment-list">
      <div class="list-header">
        <span>Type</span>
        <span>File</span>
        <span>Uploaded at</span>
        <span>Uploaded by</span>
        <span>Size</span>
        <span>Action</span>
      </div>

      <p v-if="loading" class="empty-state">Loading attachments...</p>
      <p v-else-if="!attachments.length" class="empty-state">No attachment records yet.</p>
      <article v-else v-for="item in attachments" :key="item.attachmentId" class="list-row">
        <span class="type-pill">{{ item.typeLabel }}</span>
        <strong>{{ item.fileName }}</strong>
        <span>{{ formatDateTime(item.uploadedAt) }}</span>
        <span>{{ item.uploadedBy || '--' }}</span>
        <span>{{ formatFileSize(item.fileSize) }}</span>
        <button class="text-button" type="button" @click="openPreview(item)">Preview</button>
      </article>
    </section>

    <div v-if="previewRecord" class="preview-mask" @click.self="closePreview">
      <article class="preview-dialog">
        <header>
          <div>
            <strong>{{ previewRecord.typeLabel }}</strong>
            <p>{{ previewRecord.fileName }}</p>
          </div>
          <button type="button" @click="closePreview">Close</button>
        </header>

        <img
          v-if="previewMimeType.startsWith('image/')"
          :src="previewUrl"
          :alt="previewRecord.fileName"
        />
        <iframe
          v-else-if="previewMimeType === 'application/pdf'"
          :src="previewUrl"
          title="Patient attachment preview"
        />
        <div v-else class="preview-placeholder">
          <p>This file type cannot be embedded in the workspace preview.</p>
          <button class="primary-button" type="button" @click="openPreviewInNewTab">Open file</button>
        </div>

        <small>
          Uploaded {{ formatDateTime(previewRecord.uploadedAt) }} by {{ previewRecord.uploadedBy || '--' }}
        </small>
      </article>
    </div>
  </section>
</template>

<style scoped>
.patient-attachment-panel {
  display: grid;
  gap: 14px;
}

.panel-header,
.upload-card,
.list-header,
.list-row,
.preview-dialog header {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.panel-header h3,
.panel-header p,
.preview-dialog p {
  margin: 0;
}

.eyebrow {
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.subtle,
.field span,
.preview-dialog small {
  color: #64748b;
  font-size: 12px;
}

.message.error {
  margin: 0;
  border-left: 4px solid #dc2626;
  border-radius: 8px;
  background: #fef2f2;
  color: #991b1b;
  padding: 10px 12px;
}

.upload-card {
  border: 1px solid rgba(148, 163, 184, 0.26);
  border-radius: 12px;
  background: #f8fafc;
  padding: 12px;
}

.field {
  display: grid;
  gap: 6px;
  min-width: 220px;
}

.field select {
  border: 1px solid rgba(148, 163, 184, 0.42);
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
}

.upload-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #2563eb;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
  min-width: 148px;
  padding: 9px 12px;
}

.upload-button.disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.upload-button input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.attachment-list {
  border: 1px solid rgba(148, 163, 184, 0.26);
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}

.list-header,
.list-row {
  display: grid;
  grid-template-columns: 1fr 1.6fr 1fr 1fr 0.7fr 0.7fr;
  padding: 10px 12px;
}

.list-header {
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.list-row {
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  color: #334155;
  font-size: 13px;
}

.type-pill {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  background: #e0f2fe;
  color: #075985;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
}

.text-button {
  width: fit-content;
  border: 0;
  background: transparent;
  color: #2563eb;
  cursor: pointer;
  font-weight: 700;
  padding: 0;
}

.empty-state {
  margin: 0;
  padding: 18px;
  text-align: center;
  color: #64748b;
}

.preview-mask {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: grid;
  place-items: center;
  background: rgba(15, 23, 42, 0.48);
  padding: 20px;
}

.preview-dialog {
  width: min(920px, 100%);
  display: grid;
  gap: 12px;
  border-radius: 14px;
  background: #fff;
  padding: 14px;
}

.preview-dialog header button {
  border: 1px solid rgba(148, 163, 184, 0.42);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  padding: 6px 10px;
}

.preview-dialog img,
.preview-dialog iframe {
  width: 100%;
  min-height: 380px;
  max-height: 72vh;
  border: 1px solid rgba(148, 163, 184, 0.26);
  border-radius: 10px;
  background: #f8fafc;
  object-fit: contain;
}

.preview-placeholder {
  min-height: 260px;
  display: grid;
  place-items: center;
  gap: 12px;
  border: 1px dashed rgba(148, 163, 184, 0.58);
  border-radius: 10px;
  background: #f8fafc;
}

@media (max-width: 960px) {
  .upload-card,
  .list-header,
  .list-row {
    grid-template-columns: 1fr;
  }

  .upload-card {
    align-items: stretch;
  }
}
</style>
