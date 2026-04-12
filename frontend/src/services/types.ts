export type TimelineType = 'visit' | 'diagnosis' | 'medication' | 'risk'

export interface TimelineEvent {
  date: string
  type: TimelineType
  title: string
  detail: string
}

export interface PatientQuadruple {
  subject: string
  relation: string
  relationLabel: string
  objectValue: string
  timestamp: string
  source: string
}

export interface PredictionItem {
  label: string
  score: number
  reason: string
}

export interface StatItem {
  label: string
  value: string
  trend: string
}

export interface FollowUpTask {
  title: string
  owner: string
  dueDate: string
  priority: 'high' | 'medium' | 'low'
}

export interface SimilarCase {
  caseId: string
  disease: string
  matchScore: number
  summary: string
  suggestion: string
}

export type EncounterStatus = 'waiting' | 'in_progress' | 'pending_review' | 'completed'

export interface OutpatientPlanItem {
  id: string
  category: 'exam' | 'recheck'
  title: string
  owner: string
  dueLabel: string
  priority: 'high' | 'medium' | 'low'
  note: string
}

export interface OutpatientTaskLog {
  logId: string
  action: string
  actorUsername?: string | null
  actorName?: string | null
  createdAt: string
  note: string
}

export interface OutpatientTask {
  taskId: string
  category: 'exam' | 'recheck'
  title: string
  owner: string
  dueDate: string
  priority: 'high' | 'medium' | 'low'
  status: string
  note: string
  source: string
  updatedBy?: string | null
  updatedAt?: string | null
  logs: OutpatientTaskLog[]
}

export interface ContactLog {
  logId: string
  contactTime: string
  contactType: 'phone' | 'family' | 'wechat' | 'outpatient'
  contactTarget: 'patient' | 'emergency_contact'
  contactResult: 'reached' | 'missed' | 'scheduled' | 'urgent'
  operatorUsername?: string | null
  operatorName?: string | null
  note: string
  nextContactDate?: string | null
}

export interface PatientAuditLog {
  logId: string
  action: string
  operatorUsername?: string | null
  operatorName?: string | null
  detail: string
  createdAt: string
}

export interface AdviceMeta {
  provider: string
  model: string | null
  source: 'placeholder' | 'deepseek' | 'fallback'
  configured: boolean
  connected: boolean
  note: string
}

export interface DoctorUser {
  username: string
  name: string
  title: string
  department: string
  role: 'doctor' | 'nurse' | 'archivist'
  password?: string
}

export interface AuthSession {
  token: string
  doctor: DoctorUser
}

export interface RegisterPayload {
  username: string
  password: string
  name: string
  title: string
  department: string
  role: 'doctor' | 'nurse' | 'archivist'
}

export interface PatientCase {
  patientId: string
  name: string
  age: number
  gender: string
  avatarUrl: string
  phone: string
  emergencyContactName: string
  emergencyContactRelation: string
  emergencyContactPhone: string
  identityMasked: string
  insuranceType: string
  department: string
  primaryDoctor: string
  caseManager: string
  medicalRecordNumber: string
  archiveSource: string
  archiveStatus: string
  consentStatus: string
  allergyHistory: string
  familyHistory: string
  primaryDisease: string
  currentStage: string
  riskLevel: string
  lastVisit: string
  summary: string
  encounterStatus: EncounterStatus
  stats: StatItem[]
  timeline: TimelineEvent[]
  predictions: PredictionItem[]
  pathExplanation: string[]
  followUps: FollowUpTask[]
  outpatientTasks: OutpatientTask[]
  contactLogs: ContactLog[]
  auditLogs: PatientAuditLog[]
  recommendationMode: 'model' | 'similar-case'
  dataSupport: 'high' | 'medium' | 'low'
  careAdvice: string[]
  similarCases: SimilarCase[]
}

export interface PatientSummary {
  patientId: string
  name: string
  age: number
  gender: string
  avatarUrl: string
  phone: string
  emergencyContactName: string
  emergencyContactRelation: string
  emergencyContactPhone: string
  identityMasked: string
  insuranceType: string
  department: string
  primaryDoctor: string
  caseManager: string
  medicalRecordNumber: string
  archiveSource: string
  archiveStatus: string
  consentStatus: string
  allergyHistory: string
  familyHistory: string
  primaryDisease: string
  currentStage: string
  riskLevel: string
  lastVisit: string
  summary: string
  dataSupport: 'high' | 'medium' | 'low'
}

export interface PredictResponse {
  patientId: string
  mode: 'model' | 'similar-case'
  strategy: 'direct-model' | 'proxy-model' | 'rules' | 'similar-case'
  generatedAt: string
  supportSummary: string
  evidence: {
    eventCount: number
    timepointCount: number
    relationCount: number
    supportLevel: 'strong' | 'limited' | 'minimal'
  }
  topk: PredictionItem[]
  advice: string[]
  adviceMeta: AdviceMeta
  pathExplanation: string[]
  similarCases: SimilarCase[]
}

export interface AdviceGeneratePayload {
  patient: PatientUpsertPayload
  quadruples: PatientQuadruple[]
  predictions: PredictionItem[]
  evidence: {
    eventCount: number
    timepointCount: number
    relationCount: number
    supportLevel: 'strong' | 'limited' | 'minimal'
  }
  pathExplanation: string[]
}

export interface AdviceGenerateResponse {
  advice: string[]
  adviceMeta: AdviceMeta
}

export interface MedicationPlanItem {
  name: string
  purpose: string
  dosage: string
  frequency: string
  route: string
  duration: string
  cautions: string[]
}

export interface MedicationPlanGeneratePayload {
  currentMedications: string[]
  careGoals: string[]
  clinicalNotes: string
}

export interface MedicationPlanResponse {
  patientId: string
  generatedAt: string
  medications: MedicationPlanItem[]
  monitoring: string[]
  education: string[]
  disclaimer: string
  adviceMeta: AdviceMeta
}

export interface HealthResponse {
  status: string
  service: string
  mode: string
  model_available: boolean
  model_error: string | null
}

export interface PatientUpsertPayload {
  patientId: string
  name: string
  age: number
  gender: string
  avatarUrl: string
  phone: string
  emergencyContactName: string
  emergencyContactRelation: string
  emergencyContactPhone: string
  identityMasked: string
  insuranceType: string
  department: string
  primaryDoctor: string
  caseManager: string
  medicalRecordNumber: string
  archiveSource: string
  archiveStatus: string
  consentStatus: string
  allergyHistory: string
  familyHistory: string
  primaryDisease: string
  currentStage: string
  riskLevel: string
  lastVisit: string
  summary: string
  dataSupport: 'high' | 'medium' | 'low'
  actorUsername?: string
  actorName?: string
}

export interface ImportPreviewPatient extends PatientUpsertPayload {
  rowKey: string
  sourceName: string
}

export interface PatientEventPayload {
  eventTime: string
  relation: string
  objectValue: string
  note?: string
  source?: string
  actorUsername?: string
  actorName?: string
}

export interface ContactLogCreatePayload {
  contactTime: string
  contactType: 'phone' | 'family' | 'wechat' | 'outpatient'
  contactTarget: 'patient' | 'emergency_contact'
  contactResult: 'reached' | 'missed' | 'scheduled' | 'urgent'
  note?: string
  nextContactDate?: string
  actorUsername?: string
  actorName?: string
}

export interface EncounterStatusPayload {
  status: EncounterStatus
}

export interface OutpatientTaskCreatePayload {
  category: 'exam' | 'recheck'
  title: string
  owner: string
  dueDate: string
  priority: 'high' | 'medium' | 'low'
  note: string
  status?: string
  source?: string
  actorUsername?: string
  actorName?: string
}

export interface OutpatientTaskStatusUpdatePayload {
  status: string
  actorUsername?: string
  actorName?: string
}

export interface ExperimentMetric {
  model: string
  status: 'done' | 'todo'
  mrr?: number | null
  hits1?: number | null
  hits3?: number | null
  hits10?: number | null
  note: string
}

export interface ModelMetricsResponse {
  dataset: string
  currentModel: ExperimentMetric
  comparisons: ExperimentMetric[]
}

export interface MaintenanceCountItem {
  label: string
  value: number
}

export interface MaintenanceRelationStat {
  relation: string
  label: string
  count: number
}

export interface MaintenancePatientRow {
  patientId: string
  name: string
  primaryDisease: string
  riskLevel: string
  dataSupport: 'high' | 'medium' | 'low'
  lastVisit: string
}

export interface MaintenanceIdentityAlertRow {
  patientId: string
  name: string
  issueType: string
  issueLabel: string
  detail: string
  archiveSource: string
}

export interface MaintenanceEventRow {
  patientId: string
  patientName: string
  eventTime: string
  relation: string
  relationLabel: string
  objectValue: string
  source: string
}

export interface MaintenanceOverview {
  mode: string
  modelAvailable: boolean
  modelError: string | null
  patientCount: number
  eventCount: number
  highRiskCount: number
  lowSupportCount: number
  overdueFollowupCount: number
  missingMrnCount: number
  pendingConsentCount: number
  duplicateRiskCount: number
  topDiseases: MaintenanceCountItem[]
  sourceStats: MaintenanceCountItem[]
  relationStats: MaintenanceRelationStat[]
  recentPatients: MaintenancePatientRow[]
  masterIndexAlerts: MaintenanceIdentityAlertRow[]
  recentEvents: MaintenanceEventRow[]
}

export interface GovernanceModuleItem {
  moduleKey: string
  title: string
  domain: string
  ownerRole: string
  status: string
  tone: 'healthy' | 'warning' | 'normal'
  description: string
  capabilities: string[]
}

export interface GovernanceModulesResponse {
  mode: string
  items: GovernanceModuleItem[]
}

export interface FollowupTaskRow {
  taskId?: string | null
  patientId: string
  patientName: string
  primaryDisease: string
  riskLevel: string
  dataSupport: 'high' | 'medium' | 'low'
  dueDate: string
  owner: string
  priority: 'high' | 'medium' | 'low'
  taskType: string
  status: string
  source: 'followup' | 'outpatient-task'
  lastActionBy?: string | null
  lastActionAt?: string | null
}

export interface FollowupWorklistResponse {
  mode: string
  items: FollowupTaskRow[]
}

export interface FlowBoardRow {
  patientId: string
  patientName: string
  primaryDisease: string
  currentStage: string
  riskLevel: string
  dataSupport: 'high' | 'medium' | 'low'
  lastVisit: string
  flowStatus: string
  nextAction: string
}

export interface FlowBoardResponse {
  mode: string
  items: FlowBoardRow[]
}
