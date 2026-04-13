import { getCurrentModelVersionFromTasks, listModelDatasets, listTrainingTasks } from './modelTrainingAdapter'
import type { GovernanceCenterViewModel, MaintenanceOverview, ModelBoardSnapshot, ModelMetricsResponse } from './types'

const CHRONIC_BASELINE = {
  mrr: 0.345,
  hits1: 0.232,
  hits10: 0.515,
}

function normalizePercent(value: number): number {
  if (Number.isNaN(value)) return 0
  if (value <= 1) return value
  return Math.min(1, value / 100)
}

function toTaskStatusLabel(status?: string): string {
  if (!status) return '--'
  if (status === 'queued') return '排队中'
  if (status === 'running') return '训练中'
  if (status === 'succeeded') return '已完成'
  if (status === 'failed') return '失败'
  return status
}

export function buildModelBoardSnapshot(params: {
  modelMetrics: ModelMetricsResponse | null
  maintenance: MaintenanceOverview | GovernanceCenterViewModel | null
  patientCount: number
}): ModelBoardSnapshot {
  const tasks = listTrainingTasks()
  const datasets = listModelDatasets()
  const currentVersion = getCurrentModelVersionFromTasks()
  const latestTask = tasks[0]

  const fallbackModel = params.modelMetrics?.currentModel
  const mrr = normalizePercent(fallbackModel?.mrr ?? CHRONIC_BASELINE.mrr)
  const hits1 = normalizePercent(fallbackModel?.hits1 ?? CHRONIC_BASELINE.hits1)
  const hits10 = normalizePercent(fallbackModel?.hits10 ?? CHRONIC_BASELINE.hits10)

  const totalRows = datasets.reduce((sum, item) => sum + item.rowCount, 0)
  const expectedRows = Math.max(1, params.patientCount * 20)
  const datasetCoverage = Math.min(1, totalRows / expectedRows)

  const maintenanceAny = params.maintenance as
    | (MaintenanceOverview & { modelGovernance?: { predictionCalls7d?: number | null; fallbackRatio?: number | null } })
    | null

  return {
    currentModelVersion: currentVersion.version,
    currentModelName: currentVersion.modelName,
    recentTrainingTime: currentVersion.trainedAt,
    mrr,
    hits1,
    hits10,
    datasetCoverage,
    recentInferenceCalls: maintenanceAny?.modelGovernance?.predictionCalls7d ?? null,
    fallbackRatio: maintenanceAny?.modelGovernance?.fallbackRatio ?? null,
    recentTrainingTaskStatus: toTaskStatusLabel(latestTask?.status),
    source: 'mixed',
  }
}

// TODO(api): replace dataset coverage/training status with backend model-governance API.
