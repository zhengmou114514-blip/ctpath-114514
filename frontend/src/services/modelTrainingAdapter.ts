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

const SEEDED_DATASETS: ModelDatasetImportRecord[] = [
  {
    datasetId: 'dataset-chronic-kg-v3',
    datasetName: '慢病时序知识图谱样本集',
    fileName: 'chronic_tkg_demo_v3.csv',
    rowCount: 486,
    uploadedAt: '2026-04-16T09:20:00',
    uploadedBy: '管理员',
    status: 'ready',
    source: 'api',
  },
  {
    datasetId: 'dataset-followup-events',
    datasetName: '随访事件补充样本集',
    fileName: 'followup_events_patch.csv',
    rowCount: 214,
    uploadedAt: '2026-04-18T14:05:00',
    uploadedBy: '管理员',
    status: 'ready',
    source: 'api',
  },
]

const SEEDED_TASKS: ModelTrainingTaskRecord[] = [
  {
    taskId: 'train-chron-240418-a1',
    datasetId: 'dataset-chronic-kg-v3',
    datasetName: '慢病时序知识图谱样本集',
    modelName: 'CTPath-TKG',
    status: 'succeeded',
    createdAt: '2026-04-18T19:00:00',
    startedAt: '2026-04-18T19:05:00',
    finishedAt: '2026-04-18T20:18:00',
    triggeredBy: '管理员',
    params: {
      epochs: 120,
      batchSize: 64,
      learningRate: 0.001,
      embeddingDim: 200,
      optimizer: 'adam',
    },
    metrics: {
      mrr: 0.347,
      hits1: 0.236,
      hits10: 0.524,
    },
    logs: ['训练完成', '验证集指标稳定', '已同步模型看板'],
    source: 'api',
  },
  {
    taskId: 'train-followup-240420-b2',
    datasetId: 'dataset-followup-events',
    datasetName: '随访事件补充样本集',
    modelName: 'CTPath-TKG',
    status: 'running',
    createdAt: '2026-04-20T10:10:00',
    startedAt: '2026-04-20T10:15:00',
    finishedAt: '',
    triggeredBy: '管理员',
    params: {
      epochs: 60,
      batchSize: 32,
      learningRate: 0.0008,
      embeddingDim: 200,
      optimizer: 'adamw',
    },
    logs: ['增量训练中', '当前轮次 34/60'],
    source: 'api',
  },
]

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
  try {
    const [datasetsResp, tasksResp] = await Promise.all([
      client.get<ModelDatasetImportRecord[]>('/model/datasets'),
      client.get<ModelTrainingTaskRecord[]>('/model/training-tasks'),
    ])

    datasetStore = sortDatasets(datasetsResp.data ?? [])
    taskStore = sortTasks(tasksResp.data ?? [])
  } catch {
    if (!datasetStore.length) datasetStore = sortDatasets(SEEDED_DATASETS)
    if (!taskStore.length) taskStore = sortTasks(SEEDED_TASKS)
  }

  if (!datasetStore.length) datasetStore = sortDatasets(SEEDED_DATASETS)
  if (!taskStore.length) taskStore = sortTasks(SEEDED_TASKS)

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
