<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { listPatientAttachments, resolvePatientAttachmentPreview, uploadPatientAttachment } from '../../services/patientAttachmentAdapter'
import type { PatientAttachmentRecord, PatientAttachmentType } from '../../services/types'

const props = defineProps<{
  patientId: string
  title?: string
}>()

const loading = ref(false)
const uploading = ref(false)
const uploadError = ref('')
const attachments = ref<PatientAttachmentRecord[]>([])
const previewRecord = ref<PatientAttachmentRecord | null>(null)
const previewUrl = ref('')
const previewMimeType = ref('')
const selectedType = ref<PatientAttachmentType>('patient_photo')

const typeOptions: Array<{ value: PatientAttachmentType; label: string }> = [
  { value: 'patient_photo', label: '患者照片' },
  { value: 'id_card', label: '身份证照片' },
  { value: 'insurance_card', label: '医保卡照片' },
  { value: 'referral_note', label: '转诊单' },
  { value: 'exam_report', label: '检查报告' },
  { value: 'informed_consent', label: '知情同意书' },
]

const attachmentCount = computed(() => attachments.value.length)

function formatDateTime(iso: string): string {
  if (!iso) return '--'
  return iso.replace('T', ' ').slice(0, 16)
}

async function reload() {
  if (!props.patientId) {
    attachments.value = []
    return
  }

  loading.value = true
  try {
    attachments.value = await listPatientAttachments(props.patientId)
  } catch (error) {
    uploadError.value = error instanceof Error ? error.message : '附件列表加载失败'
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

  uploadError.value = ''
  uploading.value = true

  try {
    await uploadPatientAttachment({ patientId: props.patientId, type: selectedType.value, file })
    await reload()
  } catch (error) {
    uploadError.value = error instanceof Error ? error.message : '附件上传失败'
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function openPreview(record: PatientAttachmentRecord) {
  closePreview()
  try {
    const result = await resolvePatientAttachmentPreview(record)
    previewRecord.value = record
    previewUrl.value = result.url
    previewMimeType.value = result.mimeType
  } catch (error) {
    uploadError.value = error instanceof Error ? error.message : '附件预览失败'
  }
}

function closePreview() {
  if (previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewRecord.value = null
  previewUrl.value = ''
  previewMimeType.value = ''
}

function openInNewTab() {
  if (!previewUrl.value) return
  window.open(previewUrl.value, '_blank', 'noopener,noreferrer')
}

watch(
  () => props.patientId,
  () => {
    closePreview()
    void reload()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  closePreview()
})
</script>

<template>
  <section class="attachment-panel">
    <header class="panel-head">
      <div>
        <h3>{{ title || '患者附件摘要' }}</h3>
        <p class="meta" v-if="patientId">档案号：{{ patientId }} · 共 {{ attachmentCount }} 项</p>
      </div>
    </header>

    <p v-if="!patientId" class="empty-block">请先保存患者档案后再上传附件。</p>

    <template v-else>
      <p v-if="uploadError" class="error-tip">{{ uploadError }}</p>

      <section class="upload-card">
        <label>
          <span>附件类型</span>
          <select v-model="selectedType" :disabled="loading || uploading">
            <option v-for="opt in typeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </label>

        <label class="upload-btn" :class="{ disabled: loading || uploading }">
          <input
            type="file"
            accept="image/*,.pdf,.doc,.docx"
            :disabled="loading || uploading"
            @change="handleUpload"
          />
          {{ uploading ? '上传中...' : '上传附件' }}
        </label>
      </section>

      <section class="summary-card">
        <div class="summary-head">
          <h4>附件摘要列表</h4>
          <span class="meta">上传时间、上传人和预览入口统一展示</span>
        </div>

        <div v-if="loading" class="empty-inline">正在加载附件列表...</div>
        <div v-else-if="!attachments.length" class="empty-inline">暂无附件</div>
        <div v-else class="list-table">
          <header>
            <span>附件类型</span>
            <span>文件名</span>
            <span>上传时间</span>
            <span>上传人</span>
            <span>预览</span>
          </header>
          <article v-for="item in attachments" :key="item.attachmentId">
            <span class="type-badge">{{ item.typeLabel }}</span>
            <span class="file-name">{{ item.fileName }}</span>
            <span>{{ formatDateTime(item.uploadedAt) }}</span>
            <span>{{ item.uploadedBy }}</span>
            <button class="secondary-button preview-button" type="button" @click="openPreview(item)">预览</button>
          </article>
        </div>
      </section>

      <div v-if="previewRecord" class="preview-mask" @click.self="closePreview">
        <article class="preview-dialog">
          <header>
            <div>
              <strong>{{ previewRecord.typeLabel }}</strong>
              <p>{{ previewRecord.fileName }}</p>
            </div>
            <button type="button" @click="closePreview">关闭</button>
          </header>

          <img v-if="previewMimeType.startsWith('image/')" :src="previewUrl" :alt="previewRecord.fileName" />
          <iframe v-else-if="previewMimeType === 'application/pdf'" :src="previewUrl" title="附件预览"></iframe>
          <div v-else class="preview-placeholder">
            <p>当前文件类型暂不支持内嵌预览。</p>
            <button class="primary-button" type="button" @click="openInNewTab">新窗口打开</button>
          </div>

          <small>上传时间：{{ formatDateTime(previewRecord.uploadedAt) }} / 上传人：{{ previewRecord.uploadedBy }}</small>
        </article>
      </div>
    </template>
  </section>
</template>

<style scoped>
.attachment-panel {
  display: grid;
  gap: 12px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.panel-head h3 {
  margin: 0;
  font-size: 16px;
  color: var(--ink, #10263c);
}

.meta {
  font-size: 12px;
  color: var(--ink-muted, #617385);
}

.error-tip {
  margin: 0;
  padding: 8px 10px;
  border-radius: 8px;
  background: #fff0f2;
  border: 1px solid #efc2c5;
  color: #a4383f;
  font-size: 13px;
}

.upload-card,
.summary-card {
  border: 1px solid var(--border, #cfd9e5);
  border-radius: 10px;
  background: #fbfdff;
  padding: 12px;
  display: grid;
  gap: 10px;
}

.upload-card {
  grid-template-columns: minmax(180px, 1fr) auto;
  align-items: end;
}

.upload-card label {
  display: grid;
  gap: 6px;
}

.upload-card span {
  font-size: 12px;
  color: var(--ink-muted, #617385);
  font-weight: 600;
}

.upload-card select {
  border: 1px solid var(--border, #cfd9e5);
  border-radius: 6px;
  background: #fff;
  padding: 8px 10px;
  font-size: 13px;
}

.upload-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border, #cfd9e5);
  border-radius: 6px;
  background: #fff;
  padding: 9px 12px;
  font-size: 13px;
  color: #1f3b5b;
  cursor: pointer;
  min-width: 120px;
}

.upload-btn.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-btn input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.summary-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.summary-head h4 {
  margin: 0;
  color: var(--ink, #10263c);
}

.list-table {
  border: 1px solid var(--border, #cfd9e5);
  border-radius: 8px;
  overflow: hidden;
}

.list-table header,
.list-table article {
  display: grid;
  grid-template-columns: 0.9fr 1.6fr 1fr 1fr auto;
  gap: 8px;
  padding: 8px 10px;
  font-size: 12px;
  align-items: center;
}

.list-table header {
  background: #f6f9fc;
  color: #4f6681;
  font-weight: 600;
}

.list-table article {
  border-top: 1px solid #e5edf5;
  color: #2d4a68;
}

.type-badge {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 4px 8px;
  border-radius: 999px;
  background: #edf5ff;
  color: #20508a;
  font-weight: 600;
}

.file-name {
  word-break: break-all;
}

.preview-button {
  justify-self: start;
  padding: 6px 10px;
}

.empty-inline,
.empty-block {
  margin: 0;
  border: 1px dashed var(--border-strong, #b8c7d8);
  border-radius: 8px;
  padding: 10px;
  text-align: center;
  color: var(--ink-muted, #617385);
  font-size: 12px;
}

.preview-mask {
  position: fixed;
  inset: 0;
  background: rgba(11, 27, 43, 0.48);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 2000;
}

.preview-dialog {
  width: min(860px, 100%);
  background: #fff;
  border-radius: 10px;
  border: 1px solid #d5e1ee;
  padding: 12px;
  display: grid;
  gap: 8px;
}

.preview-dialog header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.preview-dialog header h4,
.preview-dialog header strong,
.preview-dialog header p {
  margin: 0;
}

.preview-dialog header button {
  border: 1px solid #c6d4e4;
  background: #fff;
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
}

.preview-dialog img,
.preview-dialog iframe {
  width: 100%;
  min-height: 360px;
  max-height: 70vh;
  object-fit: contain;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.preview-placeholder {
  min-height: 240px;
  display: grid;
  place-items: center;
  gap: 10px;
  border: 1px dashed #bfd0e1;
  border-radius: 8px;
  background: #f9fbfd;
}

.preview-dialog p,
.preview-dialog small {
  margin: 0;
  color: #617385;
}

@media (max-width: 1100px) {
  .upload-card {
    grid-template-columns: 1fr;
  }

  .list-table header,
  .list-table article {
    grid-template-columns: 1fr;
  }
}
</style>
