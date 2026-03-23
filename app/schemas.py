from typing import List, Literal, Optional

from pydantic import BaseModel, Field


TimelineType = Literal["visit", "diagnosis", "medication", "risk"]
PriorityLevel = Literal["high", "medium", "low"]
RecommendationMode = Literal["model", "similar-case"]
DataSupport = Literal["high", "medium", "low"]


class DoctorPublic(BaseModel):
    username: str
    name: str
    title: str
    department: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    doctor: DoctorPublic


class PatientSummary(BaseModel):
    patientId: str
    name: str
    age: int
    gender: str
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


class PatientCase(PatientSummary):
    stats: List[StatItem]
    timeline: List[TimelineEvent]
    predictions: List[PredictionItem]
    pathExplanation: List[str]
    followUps: List[FollowUpTask]
    recommendationMode: RecommendationMode
    careAdvice: List[str]
    similarCases: List[SimilarCase]


class PredictRequest(BaseModel):
    patientId: str
    topk: int = Field(default=3, ge=1, le=10)
    asOfTime: Optional[str] = None


class PredictResponse(BaseModel):
    patientId: str
    mode: RecommendationMode
    generatedAt: str
    topk: List[PredictionItem]
    advice: List[str]
    pathExplanation: List[str]
    similarCases: List[SimilarCase]


class TimelineResponse(BaseModel):
    patientId: str
    items: List[TimelineEvent]


class PatientUpsertRequest(BaseModel):
    patientId: str
    name: str
    age: int = Field(ge=0, le=120)
    gender: str
    primaryDisease: str
    currentStage: str
    riskLevel: str
    lastVisit: str
    summary: str = ""
    dataSupport: DataSupport = "medium"


class PatientEventCreateRequest(BaseModel):
    eventTime: str
    relation: str
    objectValue: str
    note: Optional[str] = None
    source: str = "manual"


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
