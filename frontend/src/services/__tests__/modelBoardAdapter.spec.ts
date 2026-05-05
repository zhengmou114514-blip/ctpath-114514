import { describe, expect, it } from 'vitest'
import { buildModelBoardSnapshot } from '../modelBoardAdapter'
import { getCurrentModelVersionFromTasks } from '../modelTrainingAdapter'

describe('modelBoardAdapter', () => {
  it('uses a neutral version label when no succeeded training task exists', () => {
    expect(getCurrentModelVersionFromTasks([])).toEqual({
      version: '--',
      modelName: '暂无可用模型',
      trainedAt: '--',
    })
  })

  it('marks snapshots as api-backed instead of mock-local', () => {
    const snapshot = buildModelBoardSnapshot({
      modelMetrics: null,
    })

    expect(snapshot.source).toBe('api')
    expect(snapshot.currentModelVersion).not.toBe('v-demo-baseline')
  })
})
