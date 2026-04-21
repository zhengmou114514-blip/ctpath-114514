import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import TrainingCenterPage from '../TrainingCenterPage.vue'

const routerPush = vi.fn()
const workspaceMock = {
  selectSection: vi.fn(),
}

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: routerPush,
  }),
}))

vi.mock('../../composables/workspaceContext', () => ({
  useWorkspaceContext: () => workspaceMock,
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
  beforeEach(() => {
    routerPush.mockReset()
    workspaceMock.selectSection.mockReset()
    window.localStorage.clear()
    window.localStorage.setItem(
      'ctpath.model.datasets',
      JSON.stringify([
        {
          datasetId: 'ds-001',
          datasetName: '慢病训练集',
          fileName: 'chronic.csv',
          rowCount: 128,
          uploadedAt: '2026-04-21T10:00:00',
          uploadedBy: '演示医生',
          status: 'ready',
          source: 'mock-local',
        },
      ])
    )
    window.localStorage.setItem('ctpath.model.training.tasks', '[]')
  })

  afterEach(() => {
    window.localStorage.clear()
  })

  it('launches a training task from an imported dataset', async () => {
    const wrapper = mountPage()
    await flushPromises()

    const select = wrapper.get('select')
    await select.setValue('ds-001')

    const buttons = wrapper.findAll('button')
    const launchButton = buttons.find((item) => item.text() === '发起训练')
    expect(launchButton).toBeTruthy()

    await launchButton!.trigger('click')
    await flushPromises()

    const tasks = JSON.parse(window.localStorage.getItem('ctpath.model.training.tasks') || '[]') as Array<Record<string, unknown>>
    expect(tasks).toHaveLength(1)
    expect(tasks[0]!.datasetId).toBe('ds-001')
    expect(String(wrapper.text())).toContain('排队中')
    expect(String(wrapper.text())).toContain('慢病训练集')
  })
})
