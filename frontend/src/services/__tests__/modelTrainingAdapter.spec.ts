import { describe, expect, it, vi, beforeEach } from 'vitest'

const clientMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  interceptors: {
    request: {
      use: vi.fn(),
    },
  },
}))

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => clientMock),
  },
}))

import {
  createTrainingTask,
  importModelDataset,
  listModelDatasets,
  listTrainingTasks,
  syncModelCenterState,
} from '../modelTrainingAdapter'

describe('modelTrainingAdapter', () => {
  beforeEach(async () => {
    clientMock.get.mockReset()
    clientMock.post.mockReset()
    window.localStorage.clear()
    clientMock.get
      .mockResolvedValueOnce({ data: [] })
      .mockResolvedValueOnce({ data: [] })
    await syncModelCenterState()
  })

  it('loads datasets and tasks from the backend instead of seeding mock-local records', async () => {
    clientMock.get
      .mockResolvedValueOnce({
        data: [
          {
            datasetId: 'ds-real-001',
            datasetName: '真实训练集',
            fileName: 'real.csv',
            rowCount: 42,
            uploadedAt: '2026-04-24T08:00:00Z',
            uploadedBy: 'model_admin',
            status: 'ready',
            source: 'api',
          },
        ],
      })
      .mockResolvedValueOnce({
        data: [
          {
            taskId: 'task-real-001',
            datasetId: 'ds-real-001',
            datasetName: '真实训练集',
            modelName: '时序知识图谱辅助诊疗模型',
            status: 'succeeded',
            createdAt: '2026-04-24T08:10:00Z',
            startedAt: '2026-04-24T08:11:00Z',
            finishedAt: '2026-04-24T08:18:00Z',
            triggeredBy: 'model_admin',
            params: {
              epochs: 32,
              batchSize: 128,
              learningRate: 0.001,
              embeddingDim: 200,
              optimizer: 'adamw',
            },
            metrics: {
              mrr: 0.61,
              hits1: 0.39,
              hits10: 0.84,
            },
            logs: ['训练任务已完成。'],
            source: 'api',
          },
        ],
      })

    await syncModelCenterState()

    expect(clientMock.get).toHaveBeenCalledWith('/model/datasets')
    expect(clientMock.get).toHaveBeenCalledWith('/model/training-tasks')
    expect(listModelDatasets()).toEqual([
      expect.objectContaining({
        datasetId: 'ds-real-001',
        source: 'api',
      }),
    ])
    expect(listTrainingTasks()).toEqual([
      expect.objectContaining({
        taskId: 'task-real-001',
        source: 'api',
      }),
    ])
  })

  it('surfaces backend import failures instead of creating a local fallback dataset', async () => {
    clientMock.post.mockRejectedValueOnce(new Error('backend unavailable'))
    const file = {
      name: 'real.csv',
      text: vi.fn().mockResolvedValue('a,b\n1,2\n'),
    } as unknown as File

    await expect(importModelDataset(file, '真实训练集')).rejects.toThrow('backend unavailable')
    expect(listModelDatasets()).toEqual([])
  })

  it('surfaces backend training failures instead of creating a local fallback task', async () => {
    clientMock.post.mockRejectedValueOnce(new Error('backend unavailable'))

    await expect(
      createTrainingTask({
        datasetId: 'ds-real-001',
        datasetName: '真实训练集',
        modelName: '时序知识图谱辅助诊疗模型',
        params: {
          epochs: 32,
          batchSize: 128,
          learningRate: 0.001,
          embeddingDim: 200,
          optimizer: 'adamw',
        },
      })
    ).rejects.toThrow('backend unavailable')
    expect(listTrainingTasks()).toEqual([])
  })
})
