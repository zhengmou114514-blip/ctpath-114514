import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import SystemCenterPage from '../SystemCenterPage.vue'

vi.mock('../../services/api', () => ({
  getAuthzCapabilities: vi.fn(async () => ({ role: 'admin', allowedSections: ['system'], allowedApis: [] })),
  getDatabaseBrowserTable: vi.fn(async () => ({
    tableName: 'patients',
    description: '患者主索引与兼容档案字段',
    columns: [
      { name: 'patient_id', dataType: 'varchar', columnKey: 'PRI', nullable: 'NO' },
      { name: 'name', dataType: 'varchar', columnKey: '', nullable: 'NO' },
    ],
    rows: [{ patient_id: 'PID001', name: '测试患者' }],
  })),
  getDatabaseBrowserTables: vi.fn(async () => ({
    connected: true,
    mode: 'mysql',
    message: '已连接 MySQL',
    tables: [{ tableName: 'patients', description: '患者主索引与兼容档案字段', rowCount: 1, columnCount: 2 }],
  })),
  getSystemAudit: vi.fn(async () => ({ items: [] })),
}))

const admin = {
  username: 'demo_admin',
  name: '系统管理员',
  role: 'admin',
  title: '系统管理员',
  department: '系统管理中心',
} as const

describe('SystemCenterPage', () => {
  it('shows a read-only database browser for admin accounts', async () => {
    const wrapper = mount(SystemCenterPage, {
      props: {
        doctor: admin,
        health: { status: 'ok', service: 'ctpath-fastapi', mode: 'mysql', model_available: true, model_error: null },
      },
    })

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain('MySQL 数据库预览')
      expect(wrapper.text()).toContain('patients')
      expect(wrapper.text()).toContain('测试患者')
    })
  })
})
