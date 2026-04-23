import { reactive } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RoleWorkspacePage from '../RoleWorkspacePage.vue'

const getCoordinationBoard = vi.fn()
const getRoleWorkspace = vi.fn()
const getRoleWorkspaces = vi.fn()
const buildModelBoardSnapshot = vi.fn()

let workspaceMock: Record<string, unknown>

vi.mock('../../composables/workspaceContext', () => ({
  useWorkspaceContext: () => workspaceMock,
}))

vi.mock('../../services/api', () => ({
  getCoordinationBoard: (...args: unknown[]) => getCoordinationBoard(...args),
  getRoleWorkspace: (...args: unknown[]) => getRoleWorkspace(...args),
  getRoleWorkspaces: (...args: unknown[]) => getRoleWorkspaces(...args),
}))

vi.mock('../../services/modelBoardAdapter', () => ({
  buildModelBoardSnapshot: (...args: unknown[]) => buildModelBoardSnapshot(...args),
}))

function mountPage() {
  return mount(RoleWorkspacePage, {
    global: {
      stubs: {
        'el-icon': {
          template: '<span class="el-icon-stub"><slot /></span>',
        },
      },
    },
  })
}

describe('RoleWorkspacePage', () => {
  beforeEach(() => {
    getCoordinationBoard.mockReset()
    getRoleWorkspace.mockReset()
    getRoleWorkspaces.mockReset()
    buildModelBoardSnapshot.mockReset()

    getRoleWorkspace.mockImplementation((role: string) => ({
      role,
      title: 'Archivist workstation',
      description: 'Owns patient identity and archive completeness.',
      primaryModules: [],
      forbiddenModules: [],
      auditFocus: [],
    }))
    getRoleWorkspaces.mockReturnValue([
      {
        role: 'doctor',
        title: 'Doctor workstation',
        description: 'Doctor workbench.',
        primaryModules: [],
      },
    ])
    buildModelBoardSnapshot.mockReturnValue({
      currentModelVersion: 'v1.0.0',
      currentModelName: 'demo-model',
      recentTrainingTime: null,
      recentTrainingTaskStatus: 'idle',
      fallbackRatio: null,
    })

    workspaceMock = reactive({
      currentDoctor: {
        username: 'demo_archivist',
        name: 'Wang Min',
        role: 'archivist',
        department: 'Medical Records',
        title: 'Archivist',
      },
      authz: {
        allowedSections: ['role-workspaces'],
        allowedApis: ['/api/authz/capabilities'],
      },
      health: { model_available: true, mode: 'demo' },
      modelMetrics: null,
      refreshSystemCenter: vi.fn(async () => undefined),
      refreshModelMetrics: vi.fn(async () => undefined),
      selectSection: vi.fn(),
    })
  })

  it('does not fetch coordination data when the role lacks coordination access', async () => {
    mountPage()
    await flushPromises()

    expect(getCoordinationBoard).not.toHaveBeenCalled()
    expect(workspaceMock.refreshSystemCenter).not.toHaveBeenCalled()
    expect(workspaceMock.refreshModelMetrics).not.toHaveBeenCalled()
  })
})
