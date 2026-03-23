export type TimelineType = 'visit' | 'diagnosis' | 'medication' | 'risk'

export interface TimelineEvent {
  date: string
  type: TimelineType
  title: string
  detail: string
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

export interface DoctorUser {
  username: string
  name: string
  title: string
  department: string
  password?: string
}

export interface AuthSession {
  token: string
  doctor: DoctorUser
}

export interface PatientCase {
  patientId: string
  name: string
  age: number
  gender: string
  primaryDisease: string
  currentStage: string
  riskLevel: string
  lastVisit: string
  summary: string
  stats: StatItem[]
  timeline: TimelineEvent[]
  predictions: PredictionItem[]
  pathExplanation: string[]
  followUps: FollowUpTask[]
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
  generatedAt: string
  topk: PredictionItem[]
  advice: string[]
  pathExplanation: string[]
  similarCases: SimilarCase[]
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
  primaryDisease: string
  currentStage: string
  riskLevel: string
  lastVisit: string
  summary: string
  dataSupport: 'high' | 'medium' | 'low'
}

export interface PatientEventPayload {
  eventTime: string
  relation: string
  objectValue: string
  note?: string
  source?: string
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
