<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import type { UploadRawFile } from 'element-plus'
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

const attachmentTypes: Array<{ value: PatientAttachmentType; label: string; tone: 'primary' | 'success' | 'warning' | 'info' }> = [
  { value: 'patient_photo', label: 'Patient photo', tone: 'success' },
  { value: 'id_card', label: 'ID card', tone: 'primary' },
  { value: 'insurance_card', label: 'Insurance card', tone: 'primary' },
  { value: 'referral_note', label: 'Referral note', tone: 'warning' },
  { value: 'exam_report', label: 'Exam report', tone: 'info' },
  { value: 'informed_consent', label: 'Informed consent', tone: 'warning' },
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
const latestUpload = computed(() => attachments.value[0]?.uploadedAt ?? '')
const previewVisible = computed({
  get: () => Boolean(previewRecord.value),
  set: (value: boolean) => {
    if (!value) closePreview()
  },
})

function typeTone(type: PatientAttachmentType) {
  return attachmentTypes.find((item) => item.value === type)?.tone ?? 'info'
}

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

async function uploadRawFile(file: UploadRawFile): Promise<boolean> {
  if (!props.patientId) return false

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
  }

  return false
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
    <el-card shadow="never" class="module-card">
      <template #header>
        <div class="module-header">
          <div>
            <p class="eyebrow">Electronic archive</p>
            <h3>{{ title || 'Patient Attachments' }}</h3>
            <p class="subtle">Patient {{ patientId || '--' }} attachment records and upload audit trail.</p>
          </div>
          <el-button :loading="loading" @click="reloadAttachments">Refresh</el-button>
        </div>
      </template>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        class="module-alert"
      />

      <el-row :gutter="12" class="summary-row">
        <el-col :xs="24" :sm="8">
          <el-statistic title="Attachment records" :value="attachmentCount" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-statistic title="Supported types" :value="attachmentTypes.length" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <div class="latest-card">
            <span>Latest upload</span>
            <strong>{{ formatDateTime(latestUpload) }}</strong>
          </div>
        </el-col>
      </el-row>

      <el-form label-position="top" class="upload-form">
        <el-form-item label="Attachment type">
          <el-select v-model="selectedType" :disabled="uploading || loading" class="full-width">
            <el-option
              v-for="item in attachmentTypes"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="Upload file">
          <el-upload
            :show-file-list="false"
            :before-upload="uploadRawFile"
            accept="image/*,.pdf,.doc,.docx"
          >
            <el-button type="primary" :loading="uploading" :disabled="loading || !patientId">
              Upload attachment
            </el-button>
          </el-upload>
          <p class="form-tip">Allowed by backend validation: images, PDF and office document formats.</p>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="attachments"
        border
        stripe
        class="attachment-table"
        empty-text="No attachment records yet."
      >
        <el-table-column label="Type" min-width="150">
          <template #default="{ row }">
            <el-tag :type="typeTone(row.type)" effect="light">{{ row.typeLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fileName" label="File" min-width="220" show-overflow-tooltip />
        <el-table-column label="Uploaded at" min-width="150">
          <template #default="{ row }">{{ formatDateTime(row.uploadedAt) }}</template>
        </el-table-column>
        <el-table-column prop="uploadedBy" label="Uploaded by" min-width="130" />
        <el-table-column label="Size" width="110">
          <template #default="{ row }">{{ formatFileSize(row.fileSize) }}</template>
        </el-table-column>
        <el-table-column label="Action" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openPreview(row)">Preview</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="previewVisible" width="min(920px, 92vw)" destroy-on-close>
      <template #header>
        <div class="preview-title">
          <strong>{{ previewRecord?.typeLabel }}</strong>
          <span>{{ previewRecord?.fileName }}</span>
        </div>
      </template>

      <img
        v-if="previewRecord && previewMimeType.startsWith('image/')"
        :src="previewUrl"
        :alt="previewRecord.fileName"
        class="preview-frame"
      />
      <iframe
        v-else-if="previewRecord && previewMimeType === 'application/pdf'"
        :src="previewUrl"
        title="Patient attachment preview"
        class="preview-frame"
      />
      <el-empty v-else description="This file type cannot be embedded in the workspace preview.">
        <el-button type="primary" @click="openPreviewInNewTab">Open file</el-button>
      </el-empty>

      <template #footer>
        <span class="preview-meta">
          Uploaded {{ formatDateTime(previewRecord?.uploadedAt || '') }} by {{ previewRecord?.uploadedBy || '--' }}
        </span>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.patient-attachment-panel {
  display: block;
}

.module-card {
  border-radius: 12px;
}

.module-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.module-header h3,
.module-header p {
  margin: 0;
}

.eyebrow {
  margin: 0 0 4px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.subtle,
.form-tip,
.latest-card span,
.preview-meta,
.preview-title span {
  color: #64748b;
  font-size: 12px;
}

.module-alert,
.summary-row,
.upload-form,
.attachment-table {
  margin-top: 14px;
}

.latest-card {
  display: grid;
  gap: 6px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  padding: 12px;
}

.latest-card strong {
  color: #303133;
  font-size: 16px;
}

.full-width {
  width: 100%;
}

.form-tip {
  margin: 8px 0 0;
}

.preview-title {
  display: grid;
  gap: 4px;
}

.preview-frame {
  width: 100%;
  min-height: 420px;
  max-height: 72vh;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  background: #f8fafc;
  object-fit: contain;
}

@media (max-width: 720px) {
  .module-header {
    display: grid;
  }
}
</style>
