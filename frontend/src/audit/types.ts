export type AuditActionType =
  | 'login'
  | 'view_patient_detail'
  | 'trigger_prediction'
  | 'generate_advice'
  | 'confirm_advice'
  | 'reject_advice'
  | 'create_followup_task'
  | 'modify_archive'

export type AuditResult = 'success' | 'failed' | 'degraded'

export interface AuditActor {
  username: string
  name: string
  role: 'doctor' | 'nurse' | 'archivist' | 'unknown'
}

export interface AuditTarget {
  type: string
  id: string
  label?: string
}

export interface AuditLogEntry {
  id: string
  actor: AuditActor
  action: AuditActionType
  target: AuditTarget
  time: string
  result: AuditResult
  detail: string
}

export interface AuditLogCreateInput {
  actor?: Partial<AuditActor>
  action: AuditActionType
  target: AuditTarget
  result: AuditResult
  detail: string
  time?: string
}