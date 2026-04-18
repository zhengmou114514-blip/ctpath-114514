import {
  fetchPatientAttachmentBlob,
  getPatientAttachments,
  uploadPatientAttachment as uploadPatientAttachmentApi,
} from './api'
import type { PatientAttachmentRecord, PatientAttachmentType } from './types'

const ATTACHMENTS_STORAGE_KEY = 'ctpath.patient.attachments'
const AUTH_STORAGE_KEY = 'ctpath.auth.session'

const TYPE_LABELS: Record<PatientAttachmentType, string> = {
  patient_photo: '患者照片',
  id_card: '身份证照片',
  insurance_card: '医保卡照片',
  referral_note: '转诊单',
  exam_report: '检查报告',
  informed_consent: '知情同意书',
}

function readAll(): PatientAttachmentRecord[] {
  try {
    if (!window?.localStorage) return []
    return JSON.parse(window.localStorage.getItem(ATTACHMENTS_STORAGE_KEY) || '[]') as PatientAttachmentRecord[]
  } catch {
    return []
  }
}

function writeAll(items: PatientAttachmentRecord[]) {
  try {
    if (!window?.localStorage) return
    window.localStorage.setItem(ATTACHMENTS_STORAGE_KEY, JSON.stringify(items))
  } catch {
    // ignore local write errors
  }
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('Failed to read local file.'))
    reader.readAsDataURL(file)
  })
}

function resolveUploaderName(explicit?: string): string {
  if (explicit?.trim()) return explicit.trim()
  try {
    const raw = window?.localStorage?.getItem(AUTH_STORAGE_KEY)
    if (!raw) return '当前用户'
    const session = JSON.parse(raw) as { doctor?: { name?: string; username?: string } }
    return session?.doctor?.name || session?.doctor?.username || '当前用户'
  } catch {
    return '当前用户'
  }
}

function isBackendUnavailableError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error)
  return /Cannot connect to backend API|Demo fallback does not support|Failed to fetch|NetworkError|Load failed|ECONNREFUSED|ERR_CONNECTION_REFUSED/i.test(
    message
  )
}

export async function listPatientAttachments(patientId: string): Promise<PatientAttachmentRecord[]> {
  if (!patientId) return []

  try {
    return await getPatientAttachments(patientId)
  } catch (error) {
    if (!isBackendUnavailableError(error)) {
      throw error
    }
    return readAll()
      .filter((item) => item.patientId === patientId)
      .sort((a, b) => b.uploadedAt.localeCompare(a.uploadedAt))
  }
}

export async function uploadPatientAttachment(params: {
  patientId: string
  type: PatientAttachmentType
  file: File
  uploadedBy?: string
}): Promise<PatientAttachmentRecord> {
  const { patientId, type, file, uploadedBy } = params
  if (!patientId) {
    throw new Error('Patient ID is required before uploading attachments.')
  }

  try {
    return await uploadPatientAttachmentApi(patientId, { type, file })
  } catch (error) {
    if (!isBackendUnavailableError(error)) {
      throw error
    }
  }

  const previewUrl = await fileToDataUrl(file)

  const record: PatientAttachmentRecord = {
    attachmentId: `att-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    patientId,
    type,
    typeLabel: TYPE_LABELS[type],
    fileName: file.name,
    mimeType: file.type || 'application/octet-stream',
    fileSize: file.size,
    previewUrl,
    uploadedAt: new Date().toISOString(),
    uploadedBy: resolveUploaderName(uploadedBy),
    source: 'mock-local',
  }

  const current = readAll()
  current.unshift(record)
  writeAll(current)
  return record
}

export async function resolvePatientAttachmentPreview(record: PatientAttachmentRecord): Promise<{
  url: string
  mimeType: string
}> {
  if (record.previewUrl.startsWith('data:') || record.previewUrl.startsWith('blob:')) {
    return {
      url: record.previewUrl,
      mimeType: record.mimeType,
    }
  }

  const result = await fetchPatientAttachmentBlob(record.patientId, record.attachmentId)
  return {
    url: URL.createObjectURL(result.blob),
    mimeType: result.mimeType || record.mimeType,
  }
}
