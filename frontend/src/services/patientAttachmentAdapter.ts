import {
  fetchPatientAttachmentBlob,
  getPatientAttachments,
  uploadPatientAttachment as uploadPatientAttachmentApi,
} from './api'
import type { PatientAttachmentRecord, PatientAttachmentType } from './types'

export async function listPatientAttachments(patientId: string): Promise<PatientAttachmentRecord[]> {
  if (!patientId) return []
  return getPatientAttachments(patientId)
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

  void uploadedBy
  return uploadPatientAttachmentApi(patientId, { type, file })
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
