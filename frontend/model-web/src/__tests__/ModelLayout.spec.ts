import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ModelLayout from '../layouts/ModelLayout.vue'

const { replace, workspace } = vi.hoisted(() => ({
  replace: vi.fn(),
  workspace: {
    currentUser: { name: '陈若宁', department: '模型治理中心', username: 'model_admin', title: '模型平台主管', role: 'model_admin' },
    health: { model_available: true, mode: 'model' },
    dashboard: null,
    refreshAll: vi.fn(),
    logout: vi.fn(),
    loading: false,
  },
}))

vi.mock('../composables/useModelWorkspace', () => ({
  useModelWorkspace: () => workspace,
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ replace }),
}))

describe('model layout', () => {
  it('logs out and redirects to /login immediately', async () => {
    const wrapper = mount(ModelLayout, {
      global: {
        stubs: {
          'router-view': true,
          ModelSidebar: { template: '<button class="sidenav-logout" @click="$emit(\'logout\')">退出登录</button>' },
          ModelTopbar: { template: '<div />' },
        },
      },
    })

    await wrapper.find('.sidenav-logout').trigger('click')

    expect(workspace.logout).toHaveBeenCalled()
    expect(replace).toHaveBeenCalledWith('/login')
  })
})
