import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import TrainingCenterPage from '../TrainingCenterPage.vue'

const routerPush = vi.fn()
const workspaceMock = {
  selectSection: vi.fn(),
}

const syncModelCenterState = vi.fn()
const listModelDatasets = vi.fn()
const listTrainingTasks = vi.fn()
const importModelDataset = vi.fn()
const createTrainingTask = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: routerPush,
  }),
}))

vi.mock('../../composables/workspaceContext', () => ({
  useWorkspaceContext: () => workspaceMock,
}))

vi.mock('../../services/modelTrainingAdapter', () => ({
  syncModelCenterState: (...args: unknown[]) => syncModelCenterState(...args),
  listModelDatasets: (...args: unknown[]) => listModelDatasets(...args),
  listTrainingTasks: (...args: unknown[]) => listTrainingTasks(...args),
  importModelDataset: (...args: unknown[]) => importModelDataset(...args),
  createTrainingTask: (...args: unknown[]) => createTrainingTask(...args),
}))

function mountPage() {
  return mount(TrainingCenterPage, {
    global: {
      stubs: {
        ElButton: {
          emits: ['click'],
          template: '<button @click="$emit(\'click\')"><slot /></button>',
        },
        ElAlert: {
          props: ['title'],
          template: '<div class="el-alert-stub">{{ title }}</div>',
        },
        ElTag: {
          template: '<span class="el-tag-stub"><slot /></span>',
        },
      },
    },
  })
}

describe('TrainingCenterPage', () => {
  let datasets: Array<Record<string, unknown>>
  let tasks: Array<Record<string, unknown>>

  beforeEach(() => {
    routerPush.mockReset()
    workspaceMock.selectSection.mockReset()
    syncModelCenterState.mockReset()
    listModelDatasets.mockReset()
    listTrainingTasks.mockReset()
    importModelDataset.mockReset()
    createTrainingTask.mockReset()

    datasets = [
      {
        datasetId: 'ds-001',
        datasetName: '真实训练集',
        fileName: 'chronic.csv',
        rowCount: 128,
        uploadedAt: '2026-04-21T10:00:00Z',
        uploadedBy: 'model_admin',
        status: 'ready',
        source: 'api',
      },
    ]
    tasks = []

    syncModelCenterState.mockResolvedValue(undefined)
    listModelDatasets.mockImplementation(() => datasets)
    listTrainingTasks.mockImplementation(() => tasks)
    importModelDataset.mockImplementation(async (_file: File, datasetName?: string) => {
      const record = {
        datasetId: 'ds-002',
        datasetName: datasetName || '新增训练集',
        fileName: 'uploaded.csv',
        rowCount: 2,
        uploadedAt: '2026-04-24T10:00:00Z',
        uploadedBy: 'model_admin',
        status: 'ready',
        source: 'api',
      }
      datasets = [record, ...datasets]
      return record
    })
    createTrainingTask.mockImplementation(async (input: Record<string, unknown>) => {
      const record = {
        taskId: 'task-001',
        datasetId: input.datasetId,
        datasetName: input.datasetName,
        modelName: input.modelName,
        status: 'queued',
        createdAt: '2026-04-24T10:05:00Z',
        triggeredBy: 'model_admin',
        params: input.params,
        logs: ['训练任务已创建，等待资源调度。'],
        source: 'api',
      }
      tasks = [record, ...tasks]
      return record
    })
  })

  it('loads training data from the adapter and launches a backend-backed task', async () => {
    const wrapper = mountPage()
    await flushPromises()

    expect(syncModelCenterState).toHaveBeenCalled()
    expect(wrapper.text()).toContain('真实训练集')

    const select = wrapper.get('select')
    await select.setValue('ds-001')

    const buttons = wrapper.findAll('button')
    const launchButton = buttons.find((item) => item.text() === '发起训练')
    expect(launchButton).toBeTruthy()

    await launchButton!.trigger('click')
    await flushPromises()

    expect(createTrainingTask).toHaveBeenCalledWith(
      expect.objectContaining({
        datasetId: 'ds-001',
        datasetName: '真实训练集',
      })
    )
    expect(wrapper.text()).toContain('排队中')
    expect(wrapper.text()).toContain('真实训练集')
  })
})
