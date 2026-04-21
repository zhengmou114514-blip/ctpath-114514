import { reactive } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AppWorkspacePage from '../AppWorkspacePage.vue'

const route = reactive({
  name: 'home',
  path: '/',
  fullPath: '/',
  query: {},
})

const routerPush = vi.fn()
const routerReplace = vi.fn(async (target: string) => {
  route.name = 'login'
  route.path = target
  route.fullPath = target
})

let workspaceMock: Record<string, unknown>

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({
    push: routerPush,
    replace: routerReplace,
  }),
}))

vi.mock('../../composables/useWorkspaceController', () => ({
  useWorkspaceController: () => workspaceMock,
}))

vi.mock('../../composables/workspaceContext', () => ({
  provideWorkspaceContext: vi.fn(),
}))

function mountPage() {
  return mount(AppWorkspacePage, {
    global: {
      stubs: {
        AppShell: {
          emits: ['logout'],
          template: `
            <div class="app-shell-stub">
              <button data-testid="logout" @click="$emit('logout')">Logout</button>
              <slot name="workspace" />
            </div>
          `,
        },
        DoctorDashboardPage: { template: '<div class="doctor-page-stub" />' },
        PatientArchivePage: { template: '<div class="archive-page-stub" />' },
        FollowupWorkbenchPage: { template: '<div class="followup-page-stub" />' },
        SystemCenterPage: { template: '<div class="system-page-stub" />' },
        RouterView: { template: '<div class="router-view-stub" />' },
      },
    },
  })
}

describe('AppWorkspacePage', () => {
  beforeEach(() => {
    route.name = 'home'
    route.path = '/'
    route.fullPath = '/'
    routerPush.mockReset()
    routerReplace.mockClear()

    workspaceMock = reactive({
      currentDoctor: {
        username: 'demo_clinic',
        name: 'Demo Doctor',
        role: 'doctor',
        title: 'Attending Physician',
        department: 'Chronic Care Clinic',
      },
      section: 'doctor',
      currentWorkspace: 'doctor',
      health: null,
      allPatients: [],
      followupItems: [],
      selectedPatient: { patientId: 'PID0001' },
      permissionHint: '',
      screenError: '',
      archiveSuccess: '',
      globalLoading: false,
      visiblePendingPatients: [],
      loadingPatients: false,
      loadingPatient: false,
      doctorNoPermission: false,
      workspaceSearchText: '',
      workspaceRiskFilter: '',
      riskOptions: [],
      archiveMode: 'list',
      archivePagedPatients: [],
      archivePage: 1,
      archiveTotalPages: 1,
      patientForm: {},
      selectedPatientId: 'PID0001',
      eventForm: {},
      relationOptions: [],
      savingPatient: false,
      savingEvent: false,
      archiveFocusSection: 'overview',
      importingArchive: false,
      importResultText: '',
      modelUnavailable: false,
      loadingBoards: false,
      loadingTaskStatus: false,
      loadingEncounterStatus: false,
      flowBoardItems: [],
      followupFocusPatientId: '',
      savingContactLog: false,
      followupNoPermission: false,
      initialize: vi.fn(async () => undefined),
      selectSection: vi.fn(),
      openPatient: vi.fn(async () => true),
      openArchiveInNewTab: vi.fn(async () => undefined),
      openFollowupModule: vi.fn(async () => undefined),
      backToArchiveList: vi.fn(),
      backToDoctorList: vi.fn(),
      changeOutpatientTaskStatus: vi.fn(),
      submitContactLog: vi.fn(),
      openCreateModule: vi.fn(),
      openImportModule: vi.fn(),
      handleExportPatients: vi.fn(),
      prevArchivePage: vi.fn(),
      nextArchivePage: vi.fn(),
      submitArchive: vi.fn(),
      submitEvent: vi.fn(),
      submitImport: vi.fn(),
      taskStatusCompleted: 'Completed',
      taskStatusClosed: 'Closed',
      logout: vi.fn(() => {
        workspaceMock.currentDoctor = null
        workspaceMock.selectedPatient = null
        workspaceMock.selectedPatientId = ''
        workspaceMock.predictionResult = null
      }),
    })
  })

  it('clears session state and redirects to /login on logout', async () => {
    const wrapper = mountPage()

    await wrapper.get('[data-testid="logout"]').trigger('click')
    await flushPromises()

    expect(workspaceMock.logout).toHaveBeenCalledTimes(1)
    expect(routerReplace).toHaveBeenCalledWith('/login')
    expect(workspaceMock.currentDoctor).toBeNull()
    expect(workspaceMock.selectedPatient).toBeNull()
    expect(wrapper.find('.workspace-auth-handoff').exists()).toBe(false)
  })
})
