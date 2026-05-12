import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { nextTick } from 'vue'
import App from '../../App.vue'
import router from '../../router'
import { pinia } from '../../stores/pinia'
import { useAuthStore } from '../../stores/auth'

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api')
  return {
    ...actual,
    healthCheck: vi.fn(async () => ({
      status: 'ok',
      mode: 'demo',
      model_available: true,
      model_error: '',
    })),
    restoreAuthSession: vi.fn(() => null),
  }
})

describe('App bootstrap', () => {
  beforeEach(async () => {
    window.localStorage.clear()
    useAuthStore(pinia).clearSession()
    await router.replace('/login')
  })

  it('renders the login screen for an unauthenticated session', async () => {
    const wrapper = mount(App, {
      global: {
        plugins: [pinia, router, ElementPlus],
      },
    })

    await router.isReady()
    await nextTick()
    await nextTick()

    expect(router.currentRoute.value.path).toBe('/login')
    expect(wrapper.text()).toContain('慢性病辅助诊疗系统')
    expect(wrapper.text()).toContain('慢病门诊工作站')
    expect(wrapper.text()).toContain('风险识别')
    expect(wrapper.text()).toContain('随访闭环')
    expect(wrapper.text()).toContain('登录系统')
  })
})
