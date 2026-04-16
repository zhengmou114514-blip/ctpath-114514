from typing import List, Literal, Optional

from pydantic import BaseModel, Field


TimelineType = Literal["visit", "diagnosis", "medication", "risk"]
PriorityLevel = Literal["high", "medium", "low"]
RecommendationMode = Literal["model", "similar-case"]
DataSupport = Literal["high", "medium", "low"]
PredictionStrategy = Literal["direct-model", "proxy-model", "rules", "similar-case"]
SupportLevel = Literal["strong", "limited", "minimal"]
AdviceSource = Literal["placeholder", "deepseek", "fallback"]
EncounterStatus = Literal["waiting", "in_progress", "pending_review", "completed"]
OutpatientTaskCategory = Literal["exam", "recheck"]
OutpatientTaskStatus = Literal["待执行", "已完成", "已关闭"]
ContactType = Literal["phone", "family", "wechat", "outpatient"]
ContactTarget = Literal["patient", "emergency_contact"]
ContactResult = Literal["reached", "missed", "scheduled", "urgent"]
DoctorRole = Literal["doctor", "nurse", "archivist"]


class DoctorPublic(BaseModel):
    username: str
    name: str
    title: str
    department: str
    role: DoctorRole = "doctor"


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    doctor: DoctorPublic


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    title: str
    department: str
    role: DoctorRole = "doctor"


class PatientSummary(BaseModel):
    patientId: str
    name: str
    age: int
    gender: str
    avatarUrl: str = ""
    phone: str = ""
    emergencyContactName: str = ""
    emergencyContactRelation: str = ""
    emergencyContactPhone: str = ""
    identityMasked: str = ""
    insuranceType: str = ""
    department: str = ""
    primaryDoctor: str = ""
    caseManager: str = ""
    medicalRecordNumber: str = ""
    archiveSource: str = ""
    archiveStatus: str = ""
    consentStatus: str = ""
    allergyHistory: str = ""
    familyHistory: str = ""
    primaryDisease: str
    currentStage: str
    riskLevel: str
    lastVisit: str
    summary: str
    dataSupport: DataSupport


class TimelineEvent(BaseModel):
    date: str
    type: TimelineType
    title: str
    detail: str


class PredictionItem(BaseModel):
    label: str
    score: float
    reason: str


class StatItem(BaseModel):
    label: str
    value: str
    trend: str


class FollowUpTask(BaseModel):
    title: str
    owner: str
    dueDate: str
    priority: PriorityLevel


class SimilarCase(BaseModel):
    caseId: str
    disease: str
    matchScore: float
    summary: str
    suggestion: str


class OutpatientTaskLog(BaseModel):
    logId: str
    action: str
    actorUsername: Optional[str] = None
    actorName: Optional[str] = None
    createdAt: str
    note: str = ""


class OutpatientTask(BaseModel):
    taskId: str
    category: OutpatientTaskCategory
    title: str
    owner: str
    dueDate: str
    priority: PriorityLevel
    status: OutpatientTaskStatus
    note: str
    source: str
    updatedBy: Optional[str] = None
    updatedAt: Optional[str] = None
    logs: List[OutpatientTaskLog] = Field(default_factory=list)


class ContactLog(BaseModel):
    logId: str
    contactTime: str
    contactType: ContactType
    contactTarget: ContactTarget
    contactResult: ContactResult
    operatorUsername: Optional[str] = None
    operatorName: Optional[str] = None
    note: str = ""
    nextContactDate: Optional[str] = None


class PatientAuditLog(BaseModel):
    logId: str
    action: str
    operatorUsername: Optional[str] = None
    operatorName: Optional[str] = None
    detail: str
    createdAt: str


class PatientCase(PatientSummary):
    encounterStatus: EncounterStatus = "waiting"
    medicalRecordNumber: str = ""
    archiveSource: str = ""
    archiveStatus: str = ""
    consentStatus: str = ""
    stats: List[StatItem]
    timeline: List[TimelineEvent]
    predictions: List[PredictionItem]
    pathExplanation: List[str]
    followUps: List[FollowUpTask]
    outpatientTasks: List[OutpatientTask] = Field(default_factory=list)
    contactLogs: List[ContactLog] = Field(default_factory=list)
    auditLogs: List[PatientAuditLog] = Field(default_factory=list)
    recommendationMode: RecommendationMode
    careAdvice: List[str]
    similarCases: List[SimilarCase]


class PredictRequest(BaseModel):
    patientId: str
    topk: int = Field(default=3, ge=1, le=10)
    asOfTime: Optional[str] = None


class EvidenceSummary(BaseModel):
    eventCount: int
    timepointCount: int
    relationCount: int
    supportLevel: SupportLevel


class AdviceMeta(BaseModel):
    provider: str
    model: Optional[str] = None
    source: AdviceSource
    configured: bool
    connected: bool
    note: str


class PredictResponse(BaseModel):
    patientId: str
    mode: RecommendationMode
    strategy: PredictionStrategy
    generatedAt: str
    supportSummary: str
    evidence: EvidenceSummary
    topk: List[PredictionItem]
    advice: List[str]
    adviceMeta: AdviceMeta
    pathExplanation: List[str]
    similarCases: List[SimilarCase]


class TimelineResponse(BaseModel):
    patientId: str
    items: List[TimelineEvent]


class PatientQuadruple(BaseModel):
    subject: str
    relation: str
    relationLabel: str
    objectValue: str
    timestamp: str
    source: str


class QuadrupleResponse(BaseModel):
    patientId: str
    items: List[PatientQuadruple]


class PatientUpsertRequest(BaseModel):
    patientId: str
    name: str
    age: int = Field(ge=0, le=120)
    gender: str
    avatarUrl: str = ""
    phone: str = ""
    emergencyContactName: str = ""
    emergencyContactRelation: str = ""
    emergencyContactPhone: str = ""
    identityMasked: str = ""
    insuranceType: str = ""
    department: str = ""
    primaryDoctor: str = ""
    caseManager: str = ""
    medicalRecordNumber: str = ""
    archiveSource: str = ""
    archiveStatus: str = ""
    consentStatus: str = ""
    allergyHistory: str = ""
    familyHistory: str = ""
    primaryDisease: str
    currentStage: str
    riskLevel: str
    lastVisit: str
    summary: str = ""
    dataSupport: DataSupport = "medium"
    actorUsername: Optional[str] = None
    actorName: Optional[str] = None


class PatientEventCreateRequest(BaseModel):
    eventTime: str
    relation: str
    objectValue: str
    note: Optional[str] = None
    source: str = "manual"
    actorUsername: Optional[str] = None
    actorName: Optional[str] = None


class ContactLogCreateRequest(BaseModel):
    contactTime: str
    contactType: ContactType
    contactTarget: ContactTarget = "patient"
    contactResult: ContactResult
    note: str = ""
    nextContactDate: Optional[str] = None
    actorUsername: Optional[str] = None
    actorName: Optional[str] = None


class EncounterStatusUpdateRequest(BaseModel):
    status: EncounterStatus


class OutpatientTaskCreateRequest(BaseModel):
    category: OutpatientTaskCategory
    title: str
    owner: str
    dueDate: str
    priority: PriorityLevel
    note: str
    status: OutpatientTaskStatus = "待执行"
    source: str = "manual"
    actorUsername: Optional[str] = None
    actorName: Optional[str] = None


class OutpatientTaskStatusUpdateRequest(BaseModel):
    status: Literal["已完成", "已关闭"]
    actorUsername: Optional[str] = None
    actorName: Optional[str] = None


class AdviceGenerateRequest(BaseModel):
    patient: PatientUpsertRequest
    quadruples: List[PatientQuadruple] = Field(default_factory=list)
    predictions: List[PredictionItem] = Field(default_factory=list)
    evidence: EvidenceSummary
    pathExplanation: List[str] = Field(default_factory=list)


class AdviceResponse(BaseModel):
    advice: List[str]
    adviceMeta: AdviceMeta


class MedicationPlanItem(BaseModel):
    name: str
    purpose: str
    dosage: str
    frequency: str
    route: str = ""
    duration: str = ""
    cautions: List[str] = Field(default_factory=list)


class MedicationPlanGenerateRequest(BaseModel):
    currentMedications: List[str] = Field(default_factory=list)
    careGoals: List[str] = Field(default_factory=list)
    clinicalNotes: str = ""


class MedicationPlanResponse(BaseModel):
    patientId: str
    generatedAt: str
    medications: List[MedicationPlanItem]
    monitoring: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    disclaimer: str = ""
    adviceMeta: AdviceMeta


class ExperimentMetric(BaseModel):
    model: str
    status: Literal["done", "todo"]
    mrr: Optional[float] = None
    hits1: Optional[float] = None
    hits3: Optional[float] = None
    hits10: Optional[float] = None
    note: str


class ModelMetricsResponse(BaseModel):
    dataset: str
    currentModel: ExperimentMetric
    comparisons: List[ExperimentMetric]


class MaintenanceCountItem(BaseModel):
    label: str
    value: int


class MaintenanceRelationStat(BaseModel):
    relation: str
    label: str
    count: int


class MaintenancePatientRow(BaseModel):
    patientId: str
    name: str
    primaryDisease: str
    riskLevel: str
    dataSupport: DataSupport
    lastVisit: str


class MaintenanceIdentityAlertRow(BaseModel):
    patientId: str
    name: str
    issueType: str
    issueLabel: str
    detail: str
    archiveSource: str


class MaintenanceEventRow(BaseModel):
    patientId: str
    patientName: str
    eventTime: str
    relation: str
    relationLabel: str
    objectValue: str
    source: str


class MaintenanceOverviewResponse(BaseModel):
    mode: str
    modelAvailable: bool
    modelError: Optional[str] = None
    patientCount: int
    eventCount: int
    highRiskCount: int
    lowSupportCount: int
    overdueFollowupCount: int
    missingMrnCount: int
    pendingConsentCount: int
    duplicateRiskCount: int
    topDiseases: List[MaintenanceCountItem]
    sourceStats: List[MaintenanceCountItem]
    relationStats: List[MaintenanceRelationStat]
    recentPatients: List[MaintenancePatientRow]
    masterIndexAlerts: List[MaintenanceIdentityAlertRow]
    recentEvents: List[MaintenanceEventRow]


class GovernanceModuleItem(BaseModel):
    moduleKey: str
    title: str
    domain: str
    ownerRole: str
    status: str
    tone: Literal["healthy", "warning", "normal"]
    description: str
    capabilities: List[str]


class GovernanceModulesResponse(BaseModel):
    mode: str
    items: List[GovernanceModuleItem]


class FollowupTaskRow(BaseModel):
    taskId: Optional[str] = None
    patientId: str
    patientName: str
    primaryDisease: str
    riskLevel: str
    dataSupport: DataSupport
    dueDate: str
    owner: str
    priority: PriorityLevel
    taskType: str
    status: str
    source: Literal["followup", "outpatient-task"] = "followup"
    lastActionBy: Optional[str] = None
    lastActionAt: Optional[str] = None


class FollowupWorklistResponse(BaseModel):
    mode: str
    items: List[FollowupTaskRow]


class FlowBoardRow(BaseModel):
    patientId: str
    patientName: str
    primaryDisease: str
    currentStage: str
    riskLevel: str
    dataSupport: DataSupport
    lastVisit: str
    flowStatus: str
    nextAction: str


class FlowBoardResponse(BaseModel):
    mode: str
    items: List[FlowBoardRow]


class SystemAuditLog(BaseModel):
    logId: str
    action: str
    result: str
    role: Optional[str] = None
    username: Optional[str] = None
    path: str
    method: str
    detail: str = ""
    clientIp: Optional[str] = None
    createdAt: str


class SystemAuditResponse(BaseModel):
    items: List[SystemAuditLog]


class AuthzCapabilityResponse(BaseModel):
    role: str
    allowedSections: List[str]
    allowedApis: List[str]
