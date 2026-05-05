import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ModelOperationsPage from '../ModelOperationsPage.vue'

const routerPush = vi.fn()
const workspaceMock = {
  currentDoctor: {
    username: 'model_admin',
    name: '模型管理员',
    title: '管理员',
    department: '模型中心',
    role: 'admin',
  },
  selectedPatientId: 'PID0001',
  selectedPatient: {
    patientId: 'PID0001',
    name: '测试患者',
    primaryDisease: '糖尿病',
    currentStage: '稳定期',
    riskLevel: '中风险',
    lastVisit: '2026-04-20',
    dataSupport: 'medium',
    timeline: [
      {
        date: '2026-04-20',
        type: 'visit',
        title: '门诊复查',
        detail: '血糖波动。',
      },
    ],
  },
  allPatients: [
    {
      patientId: 'PID0001',
      name: '测试患者',
      primaryDisease: '糖尿病',
      currentStage: '稳定期',
      riskLevel: '中风险',
      lastVisit: '2026-04-20',
      dataSupport: 'medium',
    },
  ],
  predictionResult: {
    patientId: 'PID0001',
    mode: 'similar-case',
    strategy: 'similar-case',
    generatedAt: '2026-04-21T10:00:00Z',
    supportSummary: '因模型不可用，回退到相似病例。',
    evidence: {
      eventCount: 1,
      timepointCount: 1,
      relationCount: 1,
      supportLevel: 'limited',
    },
    topk: [
      {
        label: '血糖控制不稳',
        score: 0.72,
        reason: '最近门诊复查提示血糖波动。',
      },
    ],
    advice: ['两周后复查糖化血红蛋白。'],
    adviceMeta: {
      provider: 'local-rule',
      model: 'fallback',
      source: 'fallback',
      configured: true,
      connected: false,
      note: 'DeepSeek 不可用，使用本地规则。',
    },
    pathExplanation: ['门诊复查 -> 血糖波动 -> 随访复查'],
    similarCases: [],
  },
  predictionError: '最近一次错误日志：模型服务超时。',
  loadingPredict: false,
  health: {
    mode: 'demo',
    model_available: false,
    model_error: 'model service timeout',
  },
  modelMetrics: null,
  refreshModelMetrics: vi.fn(async () => undefined),
  openPatient: vi.fn(async () => true),
  runPrediction: vi.fn(async () => undefined),
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

vi.mock('../../services/api', () => ({
  getSystemAudit: vi.fn(async () => ({ items: [] })),
}))

vi.mock('../../services/modelTrainingAdapter', () => ({
  syncModelCenterState: vi.fn(async () => undefined),
  listModelDatasets: vi.fn(() => []),
  listTrainingTasks: vi.fn(() => []),
  getCurrentModelVersionFromTasks: vi.fn(() => 'ctpath-debug-v1'),
}))

function mountPage() {
  return mount(ModelOperationsPage, {
    global: {
      stubs: {
        ElButton: {
          props: ['disabled', 'loading'],
          emits: ['click'],
          template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>',
        },
        ElTag: {
          template: '<span class="el-tag-stub"><slot /></span>',
        },
      },
    },
  })
}

describe('ModelOperationsPage', () => {
  beforeEach(() => {
    routerPush.mockReset()
    workspaceMock.refreshModelMetrics.mockClear()
    workspaceMock.openPatient.mockClear()
    workspaceMock.runPrediction.mockClear()
    workspaceMock.selectSection.mockClear()
  })

  it('renders a model operations console with raw input and output context', async () => {
    const wrapper = mountPage()
    await flushPromises()

    expect(wrapper.text()).toContain('模型运行台')
    expect(wrapper.text()).toContain('验证样本')
    expect(wrapper.text()).toContain('原始输入 JSON')
    expect(wrapper.text()).toContain('原始输出 JSON')
    expect(wrapper.text()).toContain('推理耗时')
    expect(wrapper.text()).toContain('回退原因')
    expect(wrapper.text()).toContain('错误日志')
    expect(wrapper.text()).toContain('"patientId": "PID0001"')
    expect(wrapper.text()).toContain('"strategy": "similar-case"')
  })
})
