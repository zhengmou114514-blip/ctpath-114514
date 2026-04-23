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
  { value: 'patient_photo', label: '患者照片', tone: 'success' },
  { value: 'id_card', label: '身份证照片', tone: 'primary' },
  { value: 'insurance_card', label: '医保卡照片', tone: 'primary' },
  { value: 'referral_note', label: '转诊单', tone: 'warning' },
  { value: 'exam_report', label: '检查报告', tone: 'info' },
  { value: 'informed_consent', label: '知情同意书', tone: 'warning' },
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
const photoCount = computed(() => attachments.value.filter((item) => item.type === 'patient_photo').length)
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
    errorMessage.value = error instanceof Error ? error.message : '患者附件加载失败。'
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
    errorMessage.value = error instanceof Error ? error.message : '附件上传失败。'
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
    errorMessage.value = error instanceof Error ? error.message : '附件预览失败。'
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
    <article class="clinical-card attachment-card">
      <div class="section-header">
        <div>
          <p class="eyebrow">电子档案 / 附件</p>
          <h2>{{ title || '患者附件工作区' }}</h2>
          <p>区分患者照片、证件、转诊单、检查报告和知情同意书，支持上传、预览和上传人追踪。</p>
        </div>
        <button class="secondary-button" type="button" :disabled="loading" @click="reloadAttachments">刷新附件</button>
      </div>

      <div v-if="errorMessage" class="inline-alert error">{{ errorMessage }}</div>

      <section class="metric-grid three">
        <article class="metric-card">
          <span>附件总数</span>
          <strong>{{ attachmentCount }}</strong>
        </article>
        <article class="metric-card">
          <span>患者照片</span>
          <strong>{{ photoCount }}</strong>
        </article>
        <article class="metric-card">
          <span>最近上传</span>
          <strong>{{ formatDateTime(latestUpload) }}</strong>
        </article>
      </section>

      <section class="attachment-toolbar">
        <label class="field compact">
          <span>附件类型</span>
          <select v-model="selectedType" :disabled="uploading || loading">
            <option v-for="item in attachmentTypes" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
        </label>

        <div class="upload-actions">
          <el-upload :show-file-list="false" :before-upload="uploadRawFile" accept="image/*,.pdf,.doc,.docx">
            <button class="primary-button" type="button" :disabled="loading || !patientId">
              {{ uploading ? '上传中...' : '上传附件' }}
            </button>
          </el-upload>
          <p class="form-tip">支持图片、PDF、Word。演示时可上传患者照片、转诊单、检查报告或知情同意书。</p>
        </div>
      </section>

      <div v-if="!attachments.length && !loading" class="empty-state-card compact-empty">
        当前患者暂无附件记录，可直接上传演示附件。
      </div>

      <div v-else class="attachment-table">
        <div class="attachment-head">
          <span>类型</span>
          <span>文件名</span>
          <span>上传时间</span>
          <span>上传人</span>
          <span>大小</span>
          <span>操作</span>
        </div>
        <div v-for="row in attachments" :key="row.attachmentId" class="attachment-row">
          <div class="attachment-cell">
            <span class="tag" :class="typeTone(row.type)">{{ row.typeLabel }}</span>
          </div>
          <div class="attachment-cell">
            <strong>{{ row.fileName }}</strong>
          </div>
          <div class="attachment-cell">{{ formatDateTime(row.uploadedAt) }}</div>
          <div class="attachment-cell">{{ row.uploadedBy }}</div>
          <div class="attachment-cell">{{ formatFileSize(row.fileSize) }}</div>
          <div class="attachment-cell">
            <button class="text-link" type="button" @click="openPreview(row)">预览</button>
          </div>
        </div>
      </div>
    </article>

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
        title="患者附件预览"
        class="preview-frame"
      />
      <el-empty v-else description="当前附件类型不支持内嵌预览，可在新窗口中打开。">
        <button class="primary-button" type="button" @click="openPreviewInNewTab">在新窗口打开</button>
      </el-empty>

      <template #footer>
        <span class="preview-meta">
          上传时间 {{ formatDateTime(previewRecord?.uploadedAt || '') }} / 上传人 {{ previewRecord?.uploadedBy || '--' }}
        </span>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.attachment-card,
.attachment-toolbar,
.upload-actions,
.attachment-table {
  display: grid;
  gap: 18px;
}

.attachment-toolbar {
  grid-template-columns: 220px minmax(0, 1fr);
  align-items: end;
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  color: #3f4848;
  font-size: 13px;
  font-weight: 700;
}

.field select {
  width: 100%;
  min-height: 48px;
  border: 1px solid #d5dde0;
  border-radius: 14px;
  background: #fff;
  padding: 0 14px;
  font: inherit;
  color: #181c1e;
}

.upload-actions {
  align-items: start;
}

.form-tip,
.preview-meta,
.preview-title span {
  color: #64748b;
  font-size: 12px;
}

.attachment-head,
.attachment-row {
  display: grid;
  grid-template-columns: 0.9fr 2fr 1.1fr 1fr 0.8fr 0.6fr;
  gap: 12px;
  align-items: center;
}

.attachment-head {
  color: #61737b;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.attachment-row {
  border-radius: 14px;
  background: rgba(241, 244, 245, 0.92);
  padding: 14px 16px;
}

.attachment-cell {
  min-width: 0;
}

.tag {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
}

.tag.primary {
  background: rgba(233, 245, 255, 0.95);
  color: #0f5fa8;
}

.tag.success {
  background: rgba(237, 247, 238, 0.95);
  color: #1f6d33;
}

.tag.warning {
  background: rgba(255, 243, 224, 0.92);
  color: #8a4b08;
}

.tag.info {
  background: rgba(241, 244, 245, 0.92);
  color: #31454c;
}

.inline-alert.error {
  border-radius: 14px;
  background: rgba(255, 218, 214, 0.75);
  color: #8c1d18;
  padding: 14px 16px;
}

.compact-empty {
  min-height: 180px;
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

@media (max-width: 1180px) {
  .attachment-toolbar,
  .attachment-head,
  .attachment-row {
    grid-template-columns: 1fr;
  }
}
</style>
