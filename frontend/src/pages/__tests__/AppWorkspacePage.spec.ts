import { reactive } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AppWorkspacePage from '../AppWorkspacePage.vue'

const route = reactive<{
  name: string
  path: string
  fullPath: string
  query: Record<string, unknown>
}>({
  name: 'home',
  path: '/',
  fullPath: '/',
  query: {},
})

const routerPush = vi.fn()
const routerReplace = vi.fn(async (target: unknown) => {
  if (typeof target === 'string') {
    route.name = target === '/login' ? 'login' : 'home'
    route.path = target
    route.fullPath = target
    route.query = {}
    return
  }

  const next = target as { name?: string | symbol; query?: Record<string, unknown> }
  route.name = typeof next.name === 'string' ? next.name : 'home'
  route.path = route.name === 'home' ? '/' : `/${route.name}`
  route.query = next.query ?? {}
  route.fullPath = `${route.path}${route.query.module ? `?module=${route.query.module}` : ''}`
})

const routerResolve = (target: unknown) => {
  if (typeof target === 'string') {
    return { fullPath: target }
  }

  const next = target as { name?: string | symbol; query?: Record<string, unknown> }
  const name = typeof next.name === 'string' ? next.name : 'home'
  const path = name === 'home' ? '/' : `/${name}`
  const query = next.query ?? {}
  return {
    fullPath: `${path}${query.module ? `?module=${query.module}` : ''}`,
  }
}

let workspaceMock: Record<string, unknown>

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({
    push: routerPush,
    replace: routerReplace,
    resolve: routerResolve,
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
          emits: ['logout', 'select'],
          template: `
            <div class="app-shell-stub">
              <button data-testid="select-archive" @click="$emit('select', 'archive')">Archive</button>
              <button data-testid="logout" @click="$emit('logout')">Logout</button>
              <slot name="workspace" />
            </div>
          `,
        },
        DoctorDashboardPage: { template: '<div class="doctor-page-stub" />' },
        PatientArchivePage: { template: '<div class="archive-page-stub" />' },
        FollowupWorkbenchPage: { template: '<div class="followup-page-stub" />' },
        RoleWorkspacePage: { template: '<div class="role-workspace-page-stub" />' },
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
      selectSection: vi.fn((nextSection: string) => {
        workspaceMock.section = nextSection
        workspaceMock.currentWorkspace = nextSection === 'archive' ? 'archive' : nextSection
      }),
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

  it('switches to the archive workspace through the sidebar selection', async () => {
    const wrapper = mountPage()

    await wrapper.get('[data-testid="select-archive"]').trigger('click')
    await flushPromises()

    expect(workspaceMock.selectSection).toHaveBeenCalledWith('archive')
    expect(workspaceMock.section).toBe('archive')
    expect(workspaceMock.currentWorkspace).toBe('archive')
    expect(routerReplace).toHaveBeenCalledWith({ name: 'home', query: { module: 'archive' } })
  })

  it('routes to the role workspace when selected', async () => {
    mountPage()

    workspaceMock.selectSection('role-workspaces')
    await flushPromises()

    expect(workspaceMock.selectSection).toHaveBeenCalledWith('role-workspaces')
    expect(workspaceMock.section).toBe('role-workspaces')
    expect(workspaceMock.currentWorkspace).toBe('role-workspaces')
    expect(routerReplace).toHaveBeenCalledWith({ name: 'role-workspaces' })
  })
})
