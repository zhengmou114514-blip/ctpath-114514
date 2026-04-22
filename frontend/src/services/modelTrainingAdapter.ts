import axios from 'axios'
import type {
  ModelDatasetImportRecord,
  ModelTrainingParams,
  ModelTrainingTaskRecord,
} from './types'

const client = axios.create({ baseURL: 'http://127.0.0.1:8001/api' })

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

export async function listModelDatasets(): Promise<ModelDatasetImportRecord[]> {
  const { data } = await client.get<ModelDatasetImportRecord[]>('/model/datasets')
  return data
}

export async function importModelDataset(file: File, datasetName?: string): Promise<ModelDatasetImportRecord> {
  const content = await file.text()
  const { data } = await client.post<ModelDatasetImportRecord>('/model/datasets/import', {
    datasetName: datasetName?.trim() || file.name.replace(/\.[^.]+$/, ''),
    fileName: file.name,
    content,
  })
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
