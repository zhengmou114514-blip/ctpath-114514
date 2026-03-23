import type {
  AuthSession,
  HealthResponse,
  ModelMetricsResponse,
  PatientCase,
  PatientEventPayload,
  PatientSummary,
  PatientUpsertPayload,
  PredictResponse,
  TimelineEvent,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

let authToken = ''

function buildHeaders(contentType = true): HeadersInit {
  const headers: Record<string, string> = {}
  if (contentType) {
    headers['Content-Type'] = 'application/json'
  }
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`
  }
  return headers
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...buildHeaders(options.body !== undefined),
      ...(options.headers ?? {}),
    },
  })

  if (!response.ok) {
    let detail = 'Request failed'
    try {
      const payload = await response.json()
      detail = payload.detail ?? detail
    } catch {
      detail = response.statusText || detail
    }
    throw new Error(detail)
  }

  return response.json() as Promise<T>
}

export async function loginDoctor(username: string, password: string): Promise<AuthSession> {
  const session = await request<AuthSession>('/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  authToken = session.token
  return session
}

export function logoutDoctor() {
  authToken = ''
}

export async function getPatients(): Promise<PatientSummary[]> {
  return request<PatientSummary[]>('/patients', { method: 'GET' })
}

export async function getPatientCase(patientId: string): Promise<PatientCase> {
  return request<PatientCase>(`/patient/${patientId}`, { method: 'GET' })
}

export async function getTimeline(patientId: string): Promise<TimelineEvent[]> {
  const response = await request<{ patientId: string; items: TimelineEvent[] }>(`/timeline/${patientId}`, {
    method: 'GET',
  })
  return response.items
}

export async function predictPatient(payload: {
  patientId: string
  asOfTime?: string
  topk: number
}): Promise<PredictResponse> {
  return request<PredictResponse>('/predict', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function healthCheck(): Promise<HealthResponse> {
  return request<HealthResponse>('/health', { method: 'GET' })
}

export async function getModelMetrics(): Promise<ModelMetricsResponse> {
  return request<ModelMetricsResponse>('/model/metrics', { method: 'GET' })
}

export async function savePatient(payload: PatientUpsertPayload): Promise<PatientCase> {
  return request<PatientCase>('/patient', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updatePatient(patientId: string, payload: PatientUpsertPayload): Promise<PatientCase> {
  return request<PatientCase>(`/patient/${patientId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function addPatientEvent(patientId: string, payload: PatientEventPayload): Promise<PatientCase> {
  return request<PatientCase>(`/patient/${patientId}/event`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
