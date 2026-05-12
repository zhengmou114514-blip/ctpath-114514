<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { deletePatientAttachment, fetchPatientAttachmentBlob, getPatientAttachments, uploadPatientAttachment } from '../../services/api'
import type { PatientAttachmentRecord, PatientAttachmentType } from '../../services/types'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)
const attachments = ref<PatientAttachmentRecord[]>([])
const selectedType = ref<PatientAttachmentType>('exam_report')
const selectedFile = ref<File | null>(null)
const loading = ref(false)
const uploading = ref(false)
const deletingAttachmentId = ref('')
const message = ref('')
const error = ref('')
const thumbnailUrls = ref<Record<string, string>>({})

const attachmentTypes: Array<{ value: PatientAttachmentType; label: string }> = [
  { value: 'patient_photo', label: '患者照片' },
  { value: 'id_card', label: '身份证' },
  { value: 'insurance_card', label: '医保卡' },
  { value: 'exam_report', label: '检查报告' },
  { value: 'referral_note', label: '转诊资料' },
  { value: 'informed_consent', label: '知情同意书' },
  { value: 'other_chronic_material', label: '其他慢病资料' },
]

const grouped = computed(() =>
  attachmentTypes.map((item) => ({
    ...item,
    records: attachments.value.filter((record) => record.type === item.value),
  }))
)

function formatSize(size: number) {
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  if (size >= 1024) return `${Math.round(size / 1024)} KB`
  return `${size} B`
}

async function loadAttachments() {
  if (!patient.value) return
  loading.value = true
  error.value = ''
  try {
    attachments.value = await getPatientAttachments(patient.value.patientId)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '附件列表加载失败。'
  } finally {
    loading.value = false
  }
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
}

async function submitUpload() {
  if (!patient.value || !selectedFile.value) {
    error.value = '请选择附件类型和本地文件。'
    return
  }
  uploading.value = true
  error.value = ''
  message.value = ''
  try {
    const record = await uploadPatientAttachment(patient.value.patientId, {
      type: selectedType.value,
      file: selectedFile.value,
    })
    attachments.value = [record, ...attachments.value.filter((item) => item.attachmentId !== record.attachmentId)]
    selectedFile.value = null
    message.value = '附件已上传并归档。'
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '附件上传失败。'
  } finally {
    uploading.value = false
  }
}

async function previewAttachment(record: PatientAttachmentRecord) {
  if (!patient.value) return
  error.value = ''
  try {
    const { blob } = await fetchPatientAttachmentBlob(patient.value.patientId, record.attachmentId)
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank', 'noopener,noreferrer')
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '附件预览失败。'
  }
}

function isImageFile(record: PatientAttachmentRecord) {
  const mime = record.mimeType || ''
  const name = record.fileName || ''
  return mime.startsWith('image/') || /\.(jpg|jpeg|png|webp|gif|bmp)$/i.test(name)
}

async function loadThumbnail(record: PatientAttachmentRecord) {
  if (!patient.value || !isImageFile(record) || thumbnailUrls.value[record.attachmentId]) return
  try {
    const { blob } = await fetchPatientAttachmentBlob(patient.value.patientId, record.attachmentId)
    thumbnailUrls.value[record.attachmentId] = URL.createObjectURL(blob)
  } catch {}
}

async function removeAttachment(record: PatientAttachmentRecord) {
  if (!patient.value) return
  const confirmed = window.confirm(`确定删除附件“${record.fileName}”吗？`)
  if (!confirmed) return

  deletingAttachmentId.value = record.attachmentId
  error.value = ''
  message.value = ''
  try {
    await deletePatientAttachment(patient.value.patientId, record.attachmentId)
    attachments.value = attachments.value.filter((item) => item.attachmentId !== record.attachmentId)
    message.value = '附件已删除。'
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '附件删除失败。'
  } finally {
    deletingAttachmentId.value = ''
  }
}

watch(
  () => patient.value?.patientId,
  () => {
    attachments.value = []
    thumbnailUrls.value = {}
    void loadAttachments()
  },
  { immediate: true }
)

watch(
  () => attachments.value.length,
  () => {
    for (const record of attachments.value) {
      if (isImageFile(record) && !thumbnailUrls.value[record.attachmentId]) {
        void loadThumbnail(record)
      }
    }
  }
)
</script>

<template>
  <section v-if="patient" class="clinical-card">
    <div class="section-header">
      <div>
        <p class="eyebrow">附件资料</p>
        <h2>电子档案附件</h2>
      </div>
    </div>

    <form class="upload-panel" @submit.prevent="submitUpload">
      <label>
        附件类型
        <select v-model="selectedType">
          <option v-for="item in attachmentTypes" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
      </label>
      <label>
        本地文件
        <input type="file" accept=".jpg,.jpeg,.png,.webp,.pdf,.doc,.docx,image/*,application/pdf" @change="onFileChange" />
      </label>
      <button class="primary-button" type="submit" :disabled="uploading">
        {{ uploading ? '正在上传...' : '上传附件' }}
      </button>
    </form>

    <p v-if="message" class="success-line">{{ message }}</p>
    <p v-if="error" class="error-line">{{ error }}</p>
    <p v-if="loading" class="muted-line">正在加载附件...</p>

    <div class="attachment-grid">
      <article v-for="group in grouped" :key="group.value">
        <header>
          <strong>{{ group.label }}</strong>
          <span>{{ group.records.length ? `${group.records.length} 份` : '待上传' }}</span>
        </header>
        <div v-for="record in group.records" :key="record.attachmentId" class="attachment-row">
          <button type="button" class="attachment-preview" @click="previewAttachment(record)">
            <img v-if="thumbnailUrls[record.attachmentId]" :src="thumbnailUrls[record.attachmentId]" class="thumbnail" alt="" />
            <span v-else class="file-icon">{{ isImageFile(record) ? '🖼' : '📄' }}</span>
            <span>{{ record.fileName }}</span>
            <small>{{ formatSize(record.fileSize) }} · {{ record.uploadedAt.slice(0, 10) }} · {{ record.uploadedBy }}</small>
          </button>
          <button
            class="danger-button"
            type="button"
            :disabled="deletingAttachmentId === record.attachmentId"
            @click="removeAttachment(record)"
          >
            {{ deletingAttachmentId === record.attachmentId ? '删除中' : '删除' }}
          </button>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.upload-panel {
  display: grid;
  grid-template-columns: minmax(160px, 220px) 1fr auto;
  gap: 10px;
  align-items: end;
  margin-bottom: 14px;
}
.upload-panel label { display: grid; gap: 6px; color: #526772; font-size: 13px; font-weight: 700; }
.upload-panel select,
.upload-panel input {
  min-height: 38px;
  border: 1px solid #c9dce6;
  border-radius: 4px;
  padding: 7px 9px;
  background: #fff;
}
.attachment-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.attachment-grid article { display: grid; align-content: start; gap: 8px; border: 1px solid #d5e6ef; background: #f7fbfd; padding: 14px; min-height: 118px; }
.attachment-grid header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.attachment-grid header span { color: #526772; font-size: 12px; }
.attachment-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  border: 1px solid #d5e6ef;
  background: #fff;
  padding: 8px;
}
.attachment-preview { display: grid; grid-template-columns: auto minmax(0, 1fr); grid-template-rows: auto auto; gap: 3px; min-width: 0; text-align: left; border: 0; background: transparent; padding: 0; cursor: pointer; }
.thumbnail { width: 48px; height: 48px; object-fit: cover; border-radius: 4px; border: 1px solid #d5e6ef; grid-row: 1 / 3; }
.file-icon { width: 48px; height: 48px; display: grid; place-items: center; background: #f0f5f9; border-radius: 4px; font-size: 20px; grid-row: 1 / 3; }
.attachment-preview span { font-weight: 700; color: #003f43; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.attachment-preview small { color: #526772; }
.danger-button { min-height: 30px; border: 1px solid #f3b8b8; background: #fff5f5; color: #b42318; font-weight: 700; cursor: pointer; }
.danger-button:disabled { opacity: 0.65; cursor: not-allowed; }
.success-line { color: #027a48; font-weight: 700; }
.error-line { color: #b42318; font-weight: 700; }
.muted-line { color: #526772; }
@media (max-width: 900px) {
  .upload-panel,
  .attachment-grid { grid-template-columns: 1fr; }
}
</style>
