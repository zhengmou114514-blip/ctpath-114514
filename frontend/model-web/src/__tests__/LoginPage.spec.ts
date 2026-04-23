import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import LoginPage from '../pages/LoginPage.vue'

const { replace, workspace } = vi.hoisted(() => ({
  replace: vi.fn(),
  workspace: {
    initialize: vi.fn().mockResolvedValue(undefined),
    isAuthenticated: false,
    currentUser: null as any,
    submitLogin: vi.fn(),
    username: 'model_admin',
    password: 'model123456',
    loginError: '',
    loadingLogin: false,
    health: {
      model_available: true,
      mode: 'model',
    },
  },
}))

vi.mock('../composables/useModelWorkspace', () => ({
  useModelWorkspace: () => workspace,
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ replace }),
}))

describe('model login page', () => {
  beforeEach(() => {
    replace.mockReset()
    workspace.initialize.mockClear()
    workspace.isAuthenticated = false
    workspace.currentUser = null
  })

  it('renders the model platform title and demo account hint', async () => {
    const wrapper = mount(LoginPage)
    await nextTick()

    expect(workspace.initialize).toHaveBeenCalled()
    expect(wrapper.text()).toContain('CTpath 模型治理与训练平台')
    expect(wrapper.text()).toContain('model_admin / model123456')
    expect(replace).not.toHaveBeenCalled()
  })
})
