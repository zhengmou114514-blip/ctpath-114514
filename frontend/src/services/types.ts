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

export interface MeResponse {
  username: string
  name: string
  title: string
  department: string
  role: 'doctor' | 'nurse' | 'archivist'
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

export type PatientMedicationStatus = 'active' | 'paused' | 'stopped'
export type PatientMedicationReviewStatus = 'pending' | 'approved' | 'rejected' | 'not_required'

export interface PatientMedicationRecord {
  medication_id: string
  patient_id: string
  drug_id: string
  drug_name_snapshot: string
  dosage: string
  frequency: string
  route: string
  start_date: string
  end_date: string
  status: PatientMedicationStatus
  prescribed_by: string
  review_status: PatientMedicationReviewStatus
  note: string
  created_at: string
  updated_at: string
}

export interface PatientMedicationUpsertRequest {
  medication_id: string
  patient_id: string
  drug_id: string
  drug_name_snapshot: string
  dosage: string
  frequency: string
  route: string
  start_date: string
  end_date: string
  status: PatientMedicationStatus
  review_status: PatientMedicationReviewStatus
  note: string
}

export interface CurrentMedicationItem {
  medicationId: string
  patientId: string
  drugName: string
  genericName: string
  dosage: string
  frequency: string
  route: string
  startedAt: string
  expectedEndAt: string
  indication: string
  source: 'mock-local'
}

export interface CurrentMedicationInput {
  drugName: string
  genericName: string
  dosage: string
  frequency: string
  route: string
  startedAt: string
  expectedEndAt: string
  indication: string
}

export interface MedicationAdequacyAssessment {
  coversBaselineTherapy: boolean
  hasDuplicateMedication: boolean
  hasContraindicationConflictPlaceholder: boolean
  alignsWithModelAdvice: boolean
  needsPharmacistReview: boolean
  suggestSupplementClasses: string[]
  notes: string[]
  evaluatedAt: string
  evaluator: string
  source: 'mock-local'
}

export interface HealthResponse {
  status: string
  service: string
  mode: string
  model_available: boolean
  model_error: string | null
}

export interface AuthzCapabilityResponse {
  role: string
  allowedSections: string[]
  allowedApis: string[]
}

export interface SystemAuditLog {
  logId: string
  action: string
  result: string
  role?: string | null
  username?: string | null
  path: string
  method: string
  detail: string
  clientIp?: string | null
  createdAt: string
}

export interface SystemAuditResponse {
  items: SystemAuditLog[]
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

export type ArchiveImportWorkflowMode = 'cross_system' | 'onsite_register' | 'governance'
export type CrossSystemSourceSystem = 'his' | 'emr' | 'regional_platform' | 'other'
export type IdentityDocType = 'id_card' | 'passport' | 'officer_card' | 'other'

export interface MpiSearchCriteria {
  sourceSystem: CrossSystemSourceSystem
  name: string
  birthDate: string
  phone: string
  idLast4: string
  medicalRecordNumber: string
  visitCardNumber: string
}

export interface MpiCandidatePatient {
  candidateId: string
  sourceSystem: CrossSystemSourceSystem
  sourceRecordId: string
  name: string
  gender: string
  birthDate: string
  phone: string
  idLast4: string
  medicalRecordNumber: string
  visitCardNumber: string
  primaryDisease: string
  lastVisit: string
  confidence: number
  summary: string
}

export interface OnsiteArchiveRegisterForm {
  name: string
  gender: string
  birthDate: string
  phone: string
  idType: IdentityDocType
  idNumber: string
  address: string
  emergencyContactName: string
  emergencyContactPhone: string
  medicalRecordNumber: string
  visitCardNumber: string
  insuranceType: string
  primaryDoctor: string
  caseManager: string
  consentStatus: string
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

export type GovernanceStatusTone = 'ok' | 'warning' | 'danger' | 'neutral' | 'healthy' | 'normal'

export interface GovernanceDataQualityOverview {
  missingFieldCount: number
  duplicateArchiveCount: number
  timelineAnomalyCount: number
  highRiskOverdueFollowup: number
}

export interface GovernanceModelServiceOverview {
  modelAvailable: boolean
  predictionCalls7d: number | null
  fallbackRatio: number | null
  adviceApprovalRate: number | null
}

export interface GovernanceArchiveRow {
  patientId: string
  patientName: string
  issueType: string
  detail: string
  source: string
  priority: 'high' | 'medium' | 'low'
}

export interface GovernanceOperationRecord {
  id: string
  actionType: 'governance_action' | 'correction_record' | 'risk_escalation'
  patientId: string
  patientName: string
  summary: string
  operator: string
  createdAt: string
}

export interface GovernanceCenterViewModel {
  dataQuality: GovernanceDataQualityOverview
  modelGovernance: GovernanceModelServiceOverview
  archiveGovernance: {
    pendingCompletionRows: GovernanceArchiveRow[]
    pendingReviewRows: GovernanceArchiveRow[]
  }
  operationTraces: {
    governanceActions: GovernanceOperationRecord[]
    correctionRecords: GovernanceOperationRecord[]
    riskEscalations: GovernanceOperationRecord[]
  }
}

export type PatientAttachmentType =
  | 'patient_photo'
  | 'id_card'
  | 'insurance_card'
  | 'referral_note'
  | 'exam_report'
  | 'informed_consent'

export interface PatientAttachmentRecord {
  attachmentId: string
  patientId: string
  type: PatientAttachmentType
  typeLabel: string
  fileName: string
  mimeType: string
  fileSize: number
  previewUrl: string
  uploadedAt: string
  uploadedBy: string
  source: 'local-file' | 'mock-local'
}

export type DrugCatalogStatus = 'active' | 'inactive'

export interface DrugCatalogRecord {
  drug_id: string
  generic_name: string
  brand_name: string
  dosage_form: string
  specification: string
  unit: string
  is_prescription: boolean
  is_controlled: boolean
  status: DrugCatalogStatus
  indication: string
  created_at: string
  updated_at: string
  updated_by: string
}

export interface DrugCatalogUpsertRequest {
  drug_id: string
  generic_name: string
  brand_name: string
  dosage_form: string
  specification: string
  unit: string
  is_prescription: boolean
  is_controlled: boolean
  status: DrugCatalogStatus
  indication: string
}

export type DrugPermissionRole = 'doctor' | 'nurse' | 'pharmacist' | 'archivist' | 'admin'

export interface DrugPermissionRecord {
  role: DrugPermissionRole
  allow_view: boolean
  allow_prescribe: boolean
  allow_review: boolean
  allow_execute: boolean
  allow_controlled_drug: boolean
}

export interface DrugPermissionUpsertRequest extends DrugPermissionRecord {}

export interface ModelDatasetImportRecord {
  datasetId: string
  datasetName: string
  fileName: string
  rowCount: number
  uploadedAt: string
  uploadedBy: string
  status: 'ready' | 'processing' | 'failed'
  source: 'mock-local'
}

export interface ModelTrainingParams {
  epochs: number
  batchSize: number
  learningRate: number
  embeddingDim: number
  optimizer: 'adam' | 'sgd' | 'adamw'
}

export interface ModelTrainingTaskRecord {
  taskId: string
  datasetId: string
  datasetName: string
  modelName: string
  status: 'queued' | 'running' | 'succeeded' | 'failed'
  createdAt: string
  startedAt?: string
  finishedAt?: string
  triggeredBy: string
  params: ModelTrainingParams
  metrics?: {
    mrr: number
    hits1: number
    hits10: number
  }
  logs: string[]
  source: 'mock-local'
}

export interface ModelBoardSnapshot {
  currentModelVersion: string
  currentModelName: string
  recentTrainingTime: string
  mrr: number
  hits1: number
  hits10: number
  datasetCoverage: number
  recentInferenceCalls: number | null
  fallbackRatio: number | null
  recentTrainingTaskStatus: string
  source: 'mixed' | 'mock-local'
}

export type ModelCenterPanelKey = 'online' | 'offline'
