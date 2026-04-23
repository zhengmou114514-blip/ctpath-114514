import axios from 'axios'
import type {
  ModelDatasetImportRecord,
  ModelTrainingParams,
  ModelTrainingTaskRecord,
} from './types'

const client = axios.create({ baseURL: 'http://127.0.0.1:8001/api' })
const DATASETS_STORAGE_KEY = 'ctpath.model.datasets'
const TASKS_STORAGE_KEY = 'ctpath.model.trainingTasks'

client.interceptors.request.use((config) => {
  try {
    const raw = window.localStorage.getItem('ctpath.model.session')
    if (raw) {
      const session = JSON.parse(raw) as { token?: string }
      if (session.token) {
        config.headers = config.headers ?? {}
        config.headers.Authorization = `Bearer ${session.token}`
      }
    }
  } catch {}
  return config
})

function nowIso() {
  return new Date().toISOString()
}

function defaultDatasets(): ModelDatasetImportRecord[] {
  return [
    {
      datasetId: 'dataset-demo-001',
      datasetName: '2026Q2 Chronic Training Set',
      fileName: 'chronic_training_demo.csv',
      rowCount: 128,
      uploadedAt: '2026-04-23T09:00:00.000Z',
      uploadedBy: 'system',
      status: 'ready',
      source: 'mock-local',
    },
  ]
}

function defaultTasks(): ModelTrainingTaskRecord[] {
  return [
    {
      taskId: 'task-demo-001',
      datasetId: 'dataset-demo-001',
      datasetName: '2026Q2 Chronic Training Set',
      modelName: 'CTpath Temporal KG',
      status: 'succeeded',
      createdAt: '2026-04-22T08:00:00.000Z',
      startedAt: '2026-04-22T08:03:00.000Z',
      finishedAt: '2026-04-22T08:28:00.000Z',
      triggeredBy: 'demo_clinic',
      params: {
        epochs: 32,
        batchSize: 128,
        learningRate: 0.001,
        embeddingDim: 200,
        optimizer: 'adamw',
      },
      metrics: {
        mrr: 0.345,
        hits1: 0.232,
        hits10: 0.515,
      },
      logs: ['Demo training task seeded for the model center.'],
      source: 'mock-local',
    },
  ]
}

function readJson<T>(key: string, fallback: T): T {
  try {
    if (typeof window === 'undefined') return fallback
    const raw = window.localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function writeJson(key: string, value: unknown) {
  try {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Ignore storage errors and keep the in-memory cache working.
  }
}

let datasetStore = readJson<ModelDatasetImportRecord[]>(DATASETS_STORAGE_KEY, defaultDatasets())
let taskStore = readJson<ModelTrainingTaskRecord[]>(TASKS_STORAGE_KEY, defaultTasks())

function persistStores() {
  writeJson(DATASETS_STORAGE_KEY, datasetStore)
  writeJson(TASKS_STORAGE_KEY, taskStore)
}

export function listModelDatasets(): ModelDatasetImportRecord[] {
  return [...datasetStore]
}

export async function importModelDataset(file: File, datasetName?: string): Promise<ModelDatasetImportRecord> {
  const content = await file.text()
  const rowCount = Math.max(0, content.split(/\r?\n/).filter((line) => line.trim()).length - 1)
  const localRecord: ModelDatasetImportRecord = {
    datasetId: `dataset-${Date.now()}`,
    datasetName: datasetName?.trim() || file.name.replace(/\.[^.]+$/, ''),
    fileName: file.name,
    rowCount,
    uploadedAt: nowIso(),
    uploadedBy: 'local-user',
    status: 'ready',
    source: 'mock-local',
  }

  datasetStore = [localRecord, ...datasetStore.filter((item) => item.datasetId !== localRecord.datasetId)]
  persistStores()

  try {
    const { data } = await client.post<ModelDatasetImportRecord>('/model/datasets/import', {
      datasetName: localRecord.datasetName,
      fileName: localRecord.fileName,
      content,
    })
    const backendRecord = { ...data, source: 'api' as const }
    datasetStore = [backendRecord, ...datasetStore.filter((item) => item.datasetId !== backendRecord.datasetId)]
    persistStores()
    return backendRecord
  } catch {
    return localRecord
  }
}

export function listTrainingTasks(): ModelTrainingTaskRecord[] {
  return [...taskStore]
}

export async function createTrainingTask(input: {
  datasetId: string
  datasetName: string
  modelName: string
  params: ModelTrainingParams
}): Promise<ModelTrainingTaskRecord> {
  const localTask: ModelTrainingTaskRecord = {
    taskId: `task-${Date.now()}`,
    datasetId: input.datasetId,
    datasetName: input.datasetName,
    modelName: input.modelName,
    status: 'queued',
    createdAt: nowIso(),
    triggeredBy: 'local-user',
    params: input.params,
    logs: ['Training task created locally and queued for execution.'],
    source: 'mock-local',
  }

  taskStore = [localTask, ...taskStore.filter((item) => item.taskId !== localTask.taskId)]
  persistStores()

  try {
    const { data } = await client.post<ModelTrainingTaskRecord>('/model/training-tasks', input)
    const backendTask = { ...data, source: 'api' as const }
    taskStore = [backendTask, ...taskStore.filter((item) => item.taskId !== backendTask.taskId)]
    persistStores()
    return backendTask
  } catch {
    return localTask
  }
}

export function getCurrentModelVersionFromTasks(tasks: ModelTrainingTaskRecord[] = []) {
  const succeeded = tasks.find((task) => task.status === 'succeeded' && task.metrics)
  if (!succeeded) {
    return {
      version: 'v-demo-baseline',
      modelName: 'CTpath Demo Rules',
      trainedAt: '--',
    }
  }

  return {
    version: `v-${succeeded.taskId.slice(-6)}`,
    modelName: succeeded.modelName,
    trainedAt: succeeded.finishedAt || succeeded.createdAt,
    metrics: succeeded.metrics,
  }
}
