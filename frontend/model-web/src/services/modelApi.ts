import axios from 'axios'

export interface ModelTrainingParams {
  epochs: number
  batchSize: number
  learningRate: number
  embeddingDim: number
  optimizer: 'adam' | 'sgd' | 'adamw'
}

export interface ModelDatasetRecord {
  datasetId: string
  datasetName: string
  fileName: string
  rowCount: number
  uploadedAt: string
  uploadedBy: string
  status: 'ready' | 'processing' | 'failed'
  source: 'api' | 'seed'
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
  source: 'api' | 'seed'
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
  source: 'mixed' | 'api' | 'mock-local'
}

export interface ModelUser {
  username: string
  name: string
  title: string
  department: string
  role: 'model_admin' | 'engineer'
}

export interface ModelLoginResponse {
  token: string
  user: ModelUser
}

export interface ModelHealthResponse {
  status: string
  mode: string
  model_available: boolean
  model_error: string | null
  current_deployment?: string | null
  last_sync_at?: string | null
}

export interface ModelDashboardResponse {
  loginCount: number
  currentUser: string
  currentDeployment: string | null
  activeDatasetCount: number
  runningTaskCount: number
  deployedVersionCount: number
  latestTaskStatus: string
  latestVersionName: string
  health: ModelHealthResponse
}

export interface ModelVersionRecord {
  versionId: string
  versionName: string
  modelName: string
  status: 'deployed' | 'staging' | 'archived'
  createdAt: string
  publishedAt?: string | null
  datasetId: string
  metrics: { mrr: number; hits1: number; hits10: number }
  notes: string
  deployed: boolean
}

export interface ModelVersionListResponse {
  items: ModelVersionRecord[]
}

export interface ModelActivityRecord {
  id: string
  action: string
  detail: string
  operator: string
  createdAt: string
}

export interface ModelOperationsResponse {
  loginCount: number
  currentUser: ModelUser
  modelUsers: ModelUser[]
  activityLog: ModelActivityRecord[]
}

const client = axios.create({ baseURL: '/api' })

client.interceptors.request.use((config) => {
  const raw = window.localStorage.getItem('ctpath.model.session')
  if (raw) {
    try {
      const session = JSON.parse(raw) as { token?: string }
      if (session.token) {
        config.headers = config.headers ?? {}
        config.headers.Authorization = `Bearer ${session.token}`
      }
    } catch {}
  }
  return config
})

export async function loginModelUser(username: string, password: string): Promise<ModelLoginResponse> {
  const { data } = await client.post<ModelLoginResponse>('/login', { username, password })
  return data
}

export async function getModelHealth(): Promise<ModelHealthResponse> {
  const { data } = await client.get<ModelHealthResponse>('/health')
  return data
}

export async function getModelDashboard(): Promise<ModelDashboardResponse> {
  const { data } = await client.get<ModelDashboardResponse>('/model/dashboard')
  return data
}

export async function listModelDatasets(): Promise<ModelDatasetRecord[]> {
  const { data } = await client.get<ModelDatasetRecord[]>('/model/datasets')
  return data
}

export async function importModelDataset(payload: {
  datasetName: string
  fileName: string
  content: string
}): Promise<ModelDatasetRecord> {
  const { data } = await client.post<ModelDatasetRecord>('/model/datasets/import', payload)
  return data
}

export async function listTrainingTasks(): Promise<ModelTrainingTaskRecord[]> {
  const { data } = await client.get<ModelTrainingTaskRecord[]>('/model/training-tasks')
  return data
}

export async function createTrainingTask(input: {
  datasetId: string
  datasetName: string
  modelName: string
  params: ModelTrainingParams
}): Promise<ModelTrainingTaskRecord> {
  const { data } = await client.post<ModelTrainingTaskRecord>('/model/training-tasks', input)
  return data
}

export async function listModelVersions(): Promise<ModelVersionRecord[]> {
  const { data } = await client.get<ModelVersionListResponse>('/model/model-versions')
  return data.items
}

export async function deployModelVersion(versionId: string): Promise<ModelVersionRecord> {
  const { data } = await client.post<ModelVersionRecord>(`/model/model-versions/${versionId}/deploy`)
  return data
}

export async function rollbackModelVersion(versionId: string): Promise<ModelVersionRecord> {
  const { data } = await client.post<ModelVersionRecord>(`/model/model-versions/${versionId}/rollback`)
  return data
}

export async function getModelOperations(): Promise<ModelOperationsResponse> {
  const { data } = await client.get<ModelOperationsResponse>('/model/operations')
  return data
}
