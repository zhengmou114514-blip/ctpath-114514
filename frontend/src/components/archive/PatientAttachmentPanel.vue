<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { listPatientAttachments, uploadPatientAttachment } from '../../services/patientAttachmentAdapter'
import type { PatientAttachmentRecord, PatientAttachmentType } from '../../services/types'

const props = defineProps<{
  patientId: string
  title?: string
}>()

const loading = ref(false)
const uploadError = ref('')
const allAttachments = ref<PatientAttachmentRecord[]>([])
const previewRecord = ref<PatientAttachmentRecord | null>(null)

const docUploadType = ref<PatientAttachmentType>('id_card')

const docTypeOptions: Array<{ value: PatientAttachmentType; label: string }> = [
  { value: 'id_card', label: '身份证照片' },
  { value: 'insurance_card', label: '医保卡照片' },
  { value: 'referral_form', label: '转诊单' },
  { value: 'exam_report', label: '检查单' },
  { value: 'other_document', label: '其他附件' },
]

const patientPhotos = computed(() => allAttachments.value.filter((item) => item.type === 'patient_photo'))
const documentAttachments = computed(() => allAttachments.value.filter((item) => item.type !== 'patient_photo'))

const latestPatientPhoto = computed(() => patientPhotos.value[0] ?? null)

function isImage(record: PatientAttachmentRecord): boolean {
  return record.mimeType.startsWith('image/')
}

function formatDateTime(iso: string): string {
  return iso.replace('T', ' ').slice(0, 16)
}

function reload() {
  allAttachments.value = listPatientAttachments(props.patientId)
}

async function handleUpload(type: PatientAttachmentType, event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !props.patientId) {
    input.value = ''
    return
  }

  uploadError.value = ''
  loading.value = true

  try {
    await uploadPatientAttachment({ patientId: props.patientId, type, file })
    reload()
  } catch (error) {
    uploadError.value = error instanceof Error ? error.message : '附件上传失败'
  } finally {
    loading.value = false
    input.value = ''
  }
}

function openPreview(record: PatientAttachmentRecord) {
  if (!isImage(record)) {
    window.open(record.previewUrl, '_blank', 'noopener,noreferrer')
    return
  }
  previewRecord.value = record
}

watch(
  () => props.patientId,
  () => {
    reload()
    previewRecord.value = null
  },
  { immediate: true }
)
</script>

<template>
  <section class="attachment-panel">
    <header class="panel-head">
      <h3>{{ title || '患者照片与证件附件' }}</h3>
      <span class="meta" v-if="patientId">档案号：{{ patientId }}</span>
    </header>

    <p v-if="!patientId" class="empty-block">请先保存患者档案后再上传附件。</p>

    <template v-else>
      <p v-if="uploadError" class="error-tip">{{ uploadError }}</p>

      <article class="block patient-photo-block">
        <div class="block-head">
          <h4>患者照片</h4>
          <label class="upload-btn" :class="{ disabled: loading }">
            <input type="file" accept="image/*" :disabled="loading" @change="handleUpload('patient_photo', $event)" />
            上传患者照片
          </label>
        </div>

        <div class="photo-zone" v-if="latestPatientPhoto">
          <img :src="latestPatientPhoto.previewUrl" alt="患者照片" @click="openPreview(latestPatientPhoto)" />
          <div class="photo-meta">
            <strong>{{ latestPatientPhoto.fileName }}</strong>
            <span>{{ latestPatientPhoto.typeLabel }}</span>
            <span>上传时间：{{ formatDateTime(latestPatientPhoto.uploadedAt) }}</span>
            <span>上传人：{{ latestPatientPhoto.uploadedBy }}</span>
          </div>
        </div>
        <p v-else class="empty-inline">暂无患者照片</p>
      </article>

      <article class="block doc-block">
        <div class="block-head">
          <h4>证件/单据附件</h4>
          <div class="doc-upload-tools">
            <select v-model="docUploadType" :disabled="loading">
              <option v-for="opt in docTypeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
            <label class="upload-btn" :class="{ disabled: loading }">
              <input
                type="file"
                accept="image/*,.pdf,.doc,.docx"
                :disabled="loading"
                @change="handleUpload(docUploadType, $event)"
              />
              上传附件
            </label>
          </div>
        </div>

        <div class="thumb-grid" v-if="documentAttachments.length">
          <button
            v-for="item in documentAttachments"
            :key="item.attachmentId"
            class="thumb-item"
            type="button"
            @click="openPreview(item)"
          >
            <img v-if="isImage(item)" :src="item.previewUrl" :alt="item.fileName" />
            <div v-else class="file-tile">{{ item.fileName.split('.').pop()?.toUpperCase() || 'FILE' }}</div>
            <div class="thumb-meta">
              <strong>{{ item.typeLabel }}</strong>
              <span>{{ item.fileName }}</span>
            </div>
          </button>
        </div>
        <p v-else class="empty-inline">暂无证件/单据附件</p>

        <div class="list-table" v-if="documentAttachments.length">
          <header>
            <span>附件类型</span>
            <span>文件名</span>
            <span>上传时间</span>
            <span>上传人</span>
          </header>
          <article v-for="item in documentAttachments" :key="`row-${item.attachmentId}`">
            <span>{{ item.typeLabel }}</span>
            <span>{{ item.fileName }}</span>
            <span>{{ formatDateTime(item.uploadedAt) }}</span>
            <span>{{ item.uploadedBy }}</span>
          </article>
        </div>
      </article>

      <div v-if="previewRecord" class="preview-mask" @click.self="previewRecord = null">
        <article class="preview-dialog">
          <header>
            <strong>{{ previewRecord.typeLabel }}</strong>
            <button type="button" @click="previewRecord = null">关闭</button>
          </header>
          <img :src="previewRecord.previewUrl" :alt="previewRecord.fileName" />
          <p>{{ previewRecord.fileName }}</p>
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
  gap: 8px;
  align-items: center;
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

.block {
  border: 1px solid var(--border, #cfd9e5);
  border-radius: 10px;
  background: #fbfdff;
  padding: 10px;
  display: grid;
  gap: 10px;
}

.block-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.block-head h4 {
  margin: 0;
  font-size: 14px;
  color: var(--ink, #10263c);
}

.upload-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--border, #cfd9e5);
  border-radius: 6px;
  background: #fff;
  padding: 6px 10px;
  font-size: 12px;
  color: #1f3b5b;
  cursor: pointer;
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

.photo-zone {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 10px;
}

.photo-zone img {
  width: 120px;
  height: 140px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--border, #cfd9e5);
  cursor: zoom-in;
}

.photo-meta {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: var(--ink-muted, #617385);
}

.doc-upload-tools {
  display: flex;
  gap: 8px;
}

.doc-upload-tools select {
  border: 1px solid var(--border, #cfd9e5);
  border-radius: 6px;
  background: #fff;
  padding: 6px 8px;
  font-size: 12px;
}

.thumb-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.thumb-item {
  border: 1px solid var(--border, #cfd9e5);
  border-radius: 8px;
  background: #fff;
  padding: 6px;
  display: grid;
  gap: 6px;
  text-align: left;
  cursor: pointer;
}

.thumb-item img,
.file-tile {
  width: 100%;
  height: 80px;
  border-radius: 6px;
  object-fit: cover;
  border: 1px solid #e2e8f0;
}

.file-tile {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f7fb;
  color: #425f80;
  font-weight: 700;
}

.thumb-meta {
  display: grid;
  gap: 2px;
}

.thumb-meta strong {
  font-size: 12px;
  color: #1f3b5b;
}

.thumb-meta span {
  font-size: 11px;
  color: #6a7f96;
  word-break: break-all;
}

.list-table {
  border: 1px solid var(--border, #cfd9e5);
  border-radius: 8px;
  overflow: hidden;
}

.list-table header,
.list-table article {
  display: grid;
  grid-template-columns: 1fr 1.4fr 1fr 1fr;
  gap: 8px;
  padding: 8px 10px;
  font-size: 12px;
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
}

.preview-dialog header button {
  border: 1px solid #c6d4e4;
  background: #fff;
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
}

.preview-dialog img {
  width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.preview-dialog p,
.preview-dialog small {
  margin: 0;
  color: #617385;
}

@media (max-width: 1100px) {
  .thumb-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .list-table header,
  .list-table article {
    grid-template-columns: 1fr;
  }

  .photo-zone {
    grid-template-columns: 1fr;
  }

  .photo-zone img {
    width: 100%;
    max-width: 240px;
    height: auto;
  }
}
</style>
