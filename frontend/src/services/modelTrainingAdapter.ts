import type {
  ModelDatasetImportRecord,
  ModelTrainingParams,
  ModelTrainingTaskRecord,
} from './types'

const DATASET_KEY = 'ctpath.model.datasets'
const TASK_KEY = 'ctpath.model.training.tasks'
const AUTH_STORAGE_KEY = 'ctpath.auth.session'

function readDatasets(): ModelDatasetImportRecord[] {
  try {
    if (!window?.localStorage) return []
    return JSON.parse(window.localStorage.getItem(DATASET_KEY) || '[]') as ModelDatasetImportRecord[]
  } catch {
    return []
  }
}

function writeDatasets(value: ModelDatasetImportRecord[]) {
  try {
    if (!window?.localStorage) return
    window.localStorage.setItem(DATASET_KEY, JSON.stringify(value))
  } catch {}
}

function readTasks(): ModelTrainingTaskRecord[] {
  try {
    if (!window?.localStorage) return []
    return JSON.parse(window.localStorage.getItem(TASK_KEY) || '[]') as ModelTrainingTaskRecord[]
  } catch {
    return []
  }
}

function writeTasks(value: ModelTrainingTaskRecord[]) {
  try {
    if (!window?.localStorage) return
    window.localStorage.setItem(TASK_KEY, JSON.stringify(value))
  } catch {}
}

function getCurrentUser(): string {
  try {
    const raw = window?.localStorage?.getItem(AUTH_STORAGE_KEY)
    if (!raw) return '当前用户'
    const session = JSON.parse(raw) as { doctor?: { name?: string; username?: string } }
    return session?.doctor?.name || session?.doctor?.username || '当前用户'
  } catch {
    return '当前用户'
  }
}

function randomMetric(min: number, max: number): number {
  return Number((Math.random() * (max - min) + min).toFixed(4))
}

function countCsvRows(text: string): number {
  const lines = text.split(/\r?\n/).filter((line) => line.trim())
  return Math.max(0, lines.length - 1)
}

function progressTasks(tasks: ModelTrainingTaskRecord[]): ModelTrainingTaskRecord[] {
  const now = Date.now()
  return tasks.map((task) => {
    const created = new Date(task.createdAt).getTime()
    const elapsed = now - created

    if (task.status === 'queued' && elapsed > 2000) {
      return {
        ...task,
        status: 'running',
        startedAt: new Date(created + 2000).toISOString(),
        logs: [...task.logs, '任务进入训练阶段，开始载入数据与参数。'],
      }
    }

    if (task.status === 'running' && elapsed > 8000) {
      return {
        ...task,
        status: 'succeeded',
        finishedAt: new Date().toISOString(),
        metrics: {
          mrr: randomMetric(0.45, 0.72),
          hits1: randomMetric(0.28, 0.58),
          hits10: randomMetric(0.62, 0.88),
        },
        logs: [...task.logs, '训练完成，模型已进入待发布状态。'],
      }
    }

    return task
  })
}

export function listModelDatasets(): ModelDatasetImportRecord[] {
  return readDatasets().sort((a, b) => b.uploadedAt.localeCompare(a.uploadedAt))
}

export async function importModelDataset(file: File, datasetName?: string): Promise<ModelDatasetImportRecord> {
  const text = await file.text()
  const rowCount = countCsvRows(text)

  const record: ModelDatasetImportRecord = {
    datasetId: `ds-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    datasetName: datasetName?.trim() || file.name.replace(/\.[^.]+$/, ''),
    fileName: file.name,
    rowCount,
    uploadedAt: new Date().toISOString(),
    uploadedBy: getCurrentUser(),
    status: 'ready',
    source: 'mock-local',
  }

  const datasets = [record, ...readDatasets()]
  writeDatasets(datasets)

  // TODO: replace local parsing/storage with backend dataset registry and object storage upload.
  return record
}

export function listTrainingTasks(): ModelTrainingTaskRecord[] {
  const progressed = progressTasks(readTasks())
  writeTasks(progressed)
  return progressed.sort((a, b) => b.createdAt.localeCompare(a.createdAt))
}

export function createTrainingTask(input: {
  datasetId: string
  datasetName: string
  modelName: string
  params: ModelTrainingParams
}): ModelTrainingTaskRecord {
  const task: ModelTrainingTaskRecord = {
    taskId: `task-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    datasetId: input.datasetId,
    datasetName: input.datasetName,
    modelName: input.modelName,
    status: 'queued',
    createdAt: new Date().toISOString(),
    triggeredBy: getCurrentUser(),
    params: input.params,
    logs: ['任务已创建，等待资源调度。'],
    source: 'mock-local',
  }

  const tasks = [task, ...readTasks()]
  writeTasks(tasks)

  // TODO: replace with backend training job orchestrator API.
  return task
}

export function getCurrentModelVersionFromTasks(): {
  version: string
  modelName: string
  trainedAt: string
  metrics?: { mrr: number; hits1: number; hits10: number }
} {
  const succeeded = listTrainingTasks().find((task) => task.status === 'succeeded' && task.metrics)
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
