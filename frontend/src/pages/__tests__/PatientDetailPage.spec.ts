import { reactive } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { PatientCase, PredictResponse } from '../../services/types'
import PatientDetailPage from '../PatientDetailPage.vue'

const route = reactive({
  name: 'patient-detail',
  params: { patientId: 'PID0001' },
})

const routerPush = vi.fn()

let workspaceMock: Record<string, unknown>

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({
    push: routerPush,
  }),
}))

vi.mock('../../composables/workspaceContext', () => ({
  useWorkspaceContext: () => workspaceMock,
}))

function createPatient(): PatientCase {
  return {
    patientId: 'PID0001',
    name: 'Test Patient',
    age: 58,
    gender: 'F',
    avatarUrl: '',
    phone: '13800000000',
    emergencyContactName: 'Family A',
    emergencyContactRelation: 'Spouse',
    emergencyContactPhone: '13900000000',
    identityMasked: '110***********1234',
    insuranceType: 'Insurance',
    department: 'Chronic Clinic',
    primaryDoctor: 'Dr. Li',
    caseManager: 'Nurse Wang',
    medicalRecordNumber: 'MRN-001',
    archiveSource: 'outpatient',
    archiveStatus: 'active',
    consentStatus: 'signed',
    allergyHistory: '',
    familyHistory: '',
    primaryDisease: 'Diabetes',
    currentStage: 'Stable',
    riskLevel: 'Medium Risk',
    lastVisit: '2026-04-20',
    summary: 'This is the preloaded summary.',
    encounterStatus: 'waiting',
    stats: [],
    timeline: [
      {
        date: '2026-04-20',
        type: 'visit',
        title: 'Outpatient Review',
        detail: 'Glucose control is unstable.',
      },
    ],
    predictions: [
      {
        label: 'Preloaded Risk Event',
        score: 0.52,
        reason: 'Shown from the patient preset summary.',
      },
    ],
    pathExplanation: ['Historical glucose fluctuation.'],
    followUps: [],
    outpatientTasks: [],
    contactLogs: [],
    auditLogs: [],
    recommendationMode: 'similar-case',
    dataSupport: 'medium',
    careAdvice: ['Keep a diet diary.'],
    similarCases: [],
  }
}

function createPredictionResult(): PredictResponse {
  return {
    patientId: 'PID0001',
    mode: 'model',
    strategy: 'direct-model',
    generatedAt: '2026-04-21T10:00:00Z',
    supportSummary: 'Latest response from the real prediction API.',
    evidence: {
      eventCount: 12,
      timepointCount: 4,
      relationCount: 9,
      supportLevel: 'strong',
    },
    topk: [
      {
        label: 'Latest Risk Event',
        score: 0.81,
        reason: 'Returned by the real /api/predict endpoint.',
      },
    ],
    advice: ['Review in two weeks and repeat HbA1c.'],
    adviceMeta: {
      provider: 'test',
      model: 'mock-model',
      source: 'fallback',
      configured: true,
      connected: true,
      note: '',
    },
    pathExplanation: ['根据近期血糖波动与病程事件生成的解释路径。'],
    similarCases: [],
  }
}

function mountPage() {
  return mount(PatientDetailPage, {
    global: {
      stubs: {
        PatientMedicationClosurePanel: { template: '<div class="medication-panel-stub" />' },
        PatientAttachmentPanel: { template: '<div class="attachment-panel-stub" />' },
        ElButton: {
          props: ['disabled'],
          emits: ['click'],
          template: '<button :disabled="disabled" @click="$emit(`click`)"><slot /></button>',
        },
        ElIcon: { template: '<span class="el-icon-stub"><slot /></span>' },
        ElTag: { template: '<span class="el-tag-stub"><slot /></span>' },
        ElProgress: { props: ['percentage'], template: '<div class="el-progress-stub">{{ percentage }}</div>' },
        ElEmpty: { props: ['description'], template: '<div class="el-empty-stub">{{ description }}</div>' },
        ElTimeline: { template: '<div class="el-timeline-stub"><slot /></div>' },
        ElTimelineItem: { template: '<div class="el-timeline-item-stub"><slot /></div>' },
      },
    },
  })
}

describe('PatientDetailPage', () => {
  beforeEach(() => {
    routerPush.mockReset()
    route.params.patientId = 'PID0001'

    const selectedPatient = createPatient()
    const predictionResult = createPredictionResult()
    const runPrediction = vi.fn(async () => {
      workspaceMock.loadingPredict = true
      await Promise.resolve()
      workspaceMock.predictionResult = predictionResult
      workspaceMock.predictionError = ''
      workspaceMock.loadingPredict = false
    })

    workspaceMock = reactive({
      selectedPatientId: 'PID0001',
      selectedPatient,
      predictionResult: null,
      predictionError: '',
      loadingPredict: false,
      modelUnavailable: false,
      health: { mode: 'model', model_available: true },
      screenError: '',
      openPatient: vi.fn(async () => true),
      openFollowupModule: vi.fn(async () => undefined),
      runPrediction,
    })
  })

  it('uses preloaded summary first, then switches to latest prediction after trigger', async () => {
    const wrapper = mountPage()

    expect(wrapper.text()).toContain('初始预置摘要')
    expect(wrapper.text()).toContain('Preloaded Risk Event')
    expect(wrapper.text()).not.toContain('最新预测结果')

    const actionButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('触发预测'))

    expect(actionButton).toBeTruthy()

    await actionButton!.trigger('click')
    await flushPromises()

    expect(workspaceMock.runPrediction).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('最新预测结果')
    expect(wrapper.text()).toContain('Latest Risk Event')
    expect(wrapper.text()).toContain('Review in two weeks and repeat HbA1c.')
  })
})
