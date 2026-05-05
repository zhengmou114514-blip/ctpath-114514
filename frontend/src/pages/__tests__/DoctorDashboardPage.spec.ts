import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import DoctorDashboardPage from '../DoctorDashboardPage.vue'
import type { PatientSummary } from '../../services/types'

const patients: PatientSummary[] = [
  {
    patientId: 'P001',
    name: '王建国',
    age: 68,
    gender: '男',
    primaryDisease: '2型糖尿病',
    riskLevel: 'High',
    summary: '血糖波动明显，需今日处理随访计划。',
    dataSupport: 'high',
  } as any,
  {
    patientId: 'P002',
    name: '李秀兰',
    age: 61,
    gender: '女',
    primaryDisease: '高血压',
    riskLevel: 'Medium',
    summary: '近期血压控制一般，建议复核用药依从性。',
    dataSupport: 'medium',
  } as any,
]

describe('DoctorDashboardPage', () => {
  it('renders a compact HIS-style patient queue table', () => {
    const wrapper = mount(DoctorDashboardPage, {
      props: {
        allPatients: patients,
        patients,
        selectedPatient: {
          ...patients[0],
          timeline: [],
          medications: [],
          suggestions: [],
          attachments: [],
        } as any,
        loadingPatients: false,
        loadingPatient: false,
        noPermission: false,
        searchText: '',
        riskFilter: '',
        riskOptions: ['全部', 'High', 'Medium'],
      },
      global: {
        stubs: {
          'el-icon': true,
        },
      },
    })

    expect(wrapper.find('.his-queue-table').exists()).toBe(true)
    expect(wrapper.text()).toContain('患者信息')
    expect(wrapper.text()).toContain('主诊断')
    expect(wrapper.text()).toContain('风险等级')
    expect(wrapper.text()).toContain('处理摘要')
    expect(wrapper.text()).toContain('操作')
  })
})
