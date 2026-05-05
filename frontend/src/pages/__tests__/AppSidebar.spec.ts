import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AppSidebar from '../../components/AppSidebar.vue'

describe('AppSidebar', () => {
  it('shows only doctor-facing care coordination modules for doctor accounts', () => {
    const wrapper = mount(AppSidebar, {
      props: {
        activeSection: 'doctor',
        doctor: {
          username: 'demo_admin',
          name: '张医生',
          role: 'doctor',
          title: '主任医师',
          department: '慢病管理中心',
        },
        health: {
          status: 'ok',
          mode: 'demo',
          model_available: true,
          model_error: '',
        } as any,
        patientCount: 18,
        followupCount: 7,
      },
      global: {
        stubs: {
          'el-icon': true,
        },
      },
    })

    expect(wrapper.text()).toContain('医护协同系统')
    expect(wrapper.text()).toContain('医生工作台')
    expect(wrapper.text()).toContain('患者档案')
    expect(wrapper.text()).toContain('模型洞察')
    expect(wrapper.text()).not.toContain('药房药库系统')
    expect(wrapper.text()).not.toContain('药房审核')
    expect(wrapper.text()).not.toContain('药品权限')
    expect(wrapper.text()).not.toContain('模型运行台')
  })

  it('keeps nurse accounts inside nursing follow-up work only', () => {
    const wrapper = mount(AppSidebar, {
      props: {
        activeSection: 'tasks',
        doctor: {
          username: 'demo_nurse',
          name: '王护士',
          role: 'nurse',
          title: '主管护师',
          department: '慢病管理中心',
        },
        health: null,
        patientCount: 18,
        followupCount: 7,
      },
      global: { stubs: { 'el-icon': true } },
    })

    expect(wrapper.text()).toContain('医护协同系统')
    expect(wrapper.text()).toContain('随访任务')
    expect(wrapper.text()).toContain('联系记录')
    expect(wrapper.text()).not.toContain('医生工作台')
    expect(wrapper.text()).not.toContain('药房审核')
    expect(wrapper.text()).not.toContain('模型看板')
  })

  it('routes pharmacist accounts to pharmacy modules without doctor workbench actions', () => {
    const wrapper = mount(AppSidebar, {
      props: {
        activeSection: 'pharmacy',
        doctor: {
          username: 'demo_pharmacist',
          name: '李药师',
          role: 'pharmacist',
          title: '主管药师',
          department: '药房药库',
        },
        health: null,
        patientCount: 18,
        followupCount: 7,
      },
      global: { stubs: { 'el-icon': true } },
    })

    expect(wrapper.text()).toContain('药房药库系统')
    expect(wrapper.text()).toContain('药房审核')
    expect(wrapper.text()).toContain('药品目录')
    expect(wrapper.text()).not.toContain('医生工作台')
    expect(wrapper.text()).not.toContain('模型洞察')
  })
})
