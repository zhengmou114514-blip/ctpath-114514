import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import AppShell from '../../layouts/AppShell.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({
    name: 'home',
  }),
}))

const baseProps = {
  doctor: {
    username: 'demo_doctor',
    name: '张医生',
    role: 'doctor',
    title: '主治医师',
    department: '慢病管理中心',
  },
  activeSection: 'doctor',
  health: null,
  patientCount: 6,
  followupCount: 3,
  selectedPatient: null,
  errorMessage: '',
  successMessage: '',
  loading: false,
} as const

function mountShell() {
  return mount(AppShell, {
    props: baseProps as any,
    slots: {
      workspace: '<div class="workspace-slot">workspace</div>',
    },
    global: {
      stubs: {
        AppSidebar: true,
        WorkspaceTopbar: true,
        PatientContextBar: true,
      },
    },
  })
}

describe('AppShell', () => {
  it('keeps hospital-workstation workspace tabs for visited sections', async () => {
    const wrapper = mountShell()

    expect(wrapper.find('.workspace-tabbar').exists()).toBe(true)
    expect(wrapper.text()).toContain('医生工作台')

    await wrapper.setProps({ activeSection: 'archive' })

    expect(wrapper.text()).toContain('医生工作台')
    expect(wrapper.text()).toContain('患者档案')
    expect(wrapper.findAll('.workspace-tab')).toHaveLength(2)
  })
})
