import axios from 'axios'
import type {
  ModelDatasetImportRecord,
  ModelTrainingParams,
  ModelTrainingTaskRecord,
} from './types'

const client = axios.create({ baseURL: 'http://127.0.0.1:8001/api' })
const MODEL_SESSION_KEY = 'ctpath.model.session'

client.interceptors.request.use((config) => {
  try {
    const raw = window.localStorage.getItem(MODEL_SESSION_KEY)
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

let datasetStore: ModelDatasetImportRecord[] = []
let taskStore: ModelTrainingTaskRecord[] = []

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function sortDatasets(items: ModelDatasetImportRecord[]): ModelDatasetImportRecord[] {
  return [...items].sort((a, b) => b.uploadedAt.localeCompare(a.uploadedAt))
}

function sortTasks(items: ModelTrainingTaskRecord[]): ModelTrainingTaskRecord[] {
  return [...items].sort((a, b) => b.createdAt.localeCompare(a.createdAt))
}

function upsertDataset(record: ModelDatasetImportRecord) {
  datasetStore = sortDatasets([record, ...datasetStore.filter((item) => item.datasetId !== record.datasetId)])
}

function upsertTask(record: ModelTrainingTaskRecord) {
  taskStore = sortTasks([record, ...taskStore.filter((item) => item.taskId !== record.taskId)])
}

export async function syncModelCenterState(): Promise<{
  datasets: ModelDatasetImportRecord[]
  tasks: ModelTrainingTaskRecord[]
}> {
  const [datasetsResp, tasksResp] = await Promise.all([
    client.get<ModelDatasetImportRecord[]>('/model/datasets'),
    client.get<ModelTrainingTaskRecord[]>('/model/training-tasks'),
  ])

  datasetStore = sortDatasets(datasetsResp.data ?? [])
  taskStore = sortTasks(tasksResp.data ?? [])

  return {
    datasets: listModelDatasets(),
    tasks: listTrainingTasks(),
  }
}

export function listModelDatasets(): ModelDatasetImportRecord[] {
  return clone(datasetStore)
}

export async function importModelDataset(file: File, datasetName?: string): Promise<ModelDatasetImportRecord> {
  const content = await file.text()
  const { data } = await client.post<ModelDatasetImportRecord>('/model/datasets/import', {
    datasetName: datasetName?.trim() || file.name.replace(/\.[^.]+$/, ''),
    fileName: file.name,
    content,
  })
  const record = { ...data, source: data.source ?? 'api' }
  upsertDataset(record)
  return clone(record)
}

export function listTrainingTasks(): ModelTrainingTaskRecord[] {
  return clone(taskStore)
}

export async function createTrainingTask(input: {
  datasetId: string
  datasetName: string
  modelName: string
  params: ModelTrainingParams
}): Promise<ModelTrainingTaskRecord> {
  const { data } = await client.post<ModelTrainingTaskRecord>('/model/training-tasks', input)
  const task = { ...data, source: data.source ?? 'api' }
  upsertTask(task)
  return clone(task)
}

export function getCurrentModelVersionFromTasks(tasks: ModelTrainingTaskRecord[] = []) {
  const succeeded = tasks.find((task) => task.status === 'succeeded' && task.metrics)
  if (!succeeded) {
    return {
      version: '--',
      modelName: '暂无可用模型',
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
