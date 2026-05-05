import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

export type NavigationRole = DoctorUser['role']

export interface NavigationItem {
  title: string
  path?: string
  icon?: string
  section?: AppSection
  roles: NavigationRole[]
  children?: NavigationItem[]
}

export const navigationGroups: NavigationItem[] = [
  {
    title: '门诊医生站',
    icon: 'Grid',
    roles: ['doctor'],
    children: [
      { title: '医生工作台', path: '/doctor/workbench', section: 'doctor', roles: ['doctor'] },
      { title: '待处理患者', path: '/doctor/workbench?view=queue', section: 'doctor', roles: ['doctor'] },
      { title: '当前关注患者', path: '/doctor/workbench?view=current', section: 'doctor', roles: ['doctor'] },
      { title: '发起随访', path: '/doctor/patients', section: 'archive', roles: ['doctor'] },
    ],
  },
  {
    title: '患者档案',
    icon: 'Document',
    roles: ['doctor'],
    children: [
      { title: '患者总览', path: '/doctor/patients', section: 'archive', roles: ['doctor'] },
      { title: '基本档案', path: '/doctor/patients', section: 'archive', roles: ['doctor'] },
      { title: '联系记录', path: '/doctor/patients', section: 'archive', roles: ['doctor'] },
      { title: '病程时间线', path: '/doctor/patients', section: 'archive', roles: ['doctor'] },
      { title: '附件资料', path: '/doctor/patients', section: 'archive', roles: ['doctor'] },
      { title: '当前用药', path: '/doctor/patients', section: 'archive', roles: ['doctor'] },
      { title: '风险评估', path: '/doctor/patients', section: 'insights', roles: ['doctor'] },
    ],
  },
  {
    title: '辅助诊疗',
    icon: 'Operation',
    roles: ['doctor'],
    children: [
      { title: '风险评估', path: '/doctor/risk', section: 'insights', roles: ['doctor'] },
      { title: '证据摘要', path: '/doctor/risk?view=evidence', section: 'insights', roles: ['doctor'] },
      { title: '辅助建议', path: '/doctor/risk?view=advice', section: 'insights', roles: ['doctor'] },
    ],
  },
  {
    title: '护士随访站',
    icon: 'Memo',
    roles: ['nurse'],
    children: [
      { title: '随访工作台', path: '/nurse/followups', section: 'tasks', roles: ['nurse'] },
      { title: '今日随访', path: '/nurse/followups/today', section: 'flow', roles: ['nurse'] },
      { title: '未接通任务', path: '/nurse/followups/missed', section: 'contacts', roles: ['nurse'] },
      { title: '联系记录', path: '/nurse/followups/records', section: 'contacts', roles: ['nurse'] },
      { title: '医生复核', path: '/nurse/followups/review', section: 'coordination', roles: ['nurse'] },
      { title: '随访统计', path: '/nurse/followups/stats', section: 'tasks', roles: ['nurse'] },
    ],
  },
  {
    title: '药事管理',
    icon: 'Tickets',
    roles: ['pharmacist'],
    children: [
      { title: '药品目录', path: '/pharmacy/drugs/catalog', section: 'drug-management', roles: ['pharmacist'] },
      { title: '剂型规格', path: '/pharmacy/drugs/catalog?view=spec', section: 'drug-management', roles: ['pharmacist'] },
      { title: '药品状态', path: '/pharmacy/drugs/status', section: 'drug-management', roles: ['pharmacist'] },
      { title: '处方药标识', path: '/pharmacy/drugs/catalog?view=prescription', section: 'drug-management', roles: ['pharmacist'] },
      { title: '当前用药查看', path: '/pharmacy/medications/review', section: 'pharmacy', roles: ['pharmacist'] },
      { title: '用药复核', path: '/pharmacy/medications/review', section: 'pharmacy', roles: ['pharmacist'] },
    ],
  },
  {
    title: '系统管理',
    icon: 'SetUp',
    roles: ['admin'],
    children: [
      { title: '用户与角色', path: '/admin/permissions', section: 'role-workspaces', roles: ['admin'] },
      { title: '权限配置', path: '/admin/permissions', section: 'role-workspaces', roles: ['admin'] },
      { title: '药品权限管理', path: '/admin/drug-permissions', section: 'drug-permission-management', roles: ['admin'] },
      { title: '审计日志', path: '/admin/audit', section: 'system', roles: ['admin'] },
    ],
  },
  {
    title: '模型与治理',
    icon: 'FolderOpened',
    roles: ['admin'],
    children: [
      { title: '模型看板', path: '/admin/model-dashboard', section: 'model-dashboard', roles: ['admin'] },
      { title: '治理中心', path: '/admin/governance', section: 'governance', roles: ['admin'] },
      { title: '数据质量', path: '/admin/governance?view=data-quality', section: 'governance', roles: ['admin'] },
      { title: '异常记录', path: '/admin/governance/issues', section: 'governance', roles: ['admin'] },
      { title: '待补全档案', path: '/admin/governance?view=incomplete-archive', section: 'governance', roles: ['admin'] },
    ],
  },
]

export function visibleNavigationGroups(role: NavigationRole) {
  return navigationGroups
    .filter((group) => group.roles.includes(role))
    .map((group) => ({
      ...group,
      children: group.children?.filter((item) => item.roles.includes(role)) ?? [],
    }))
    .filter((group) => group.children.length > 0)
}

export function findNavigationByPath(path: string, role: NavigationRole) {
  for (const group of visibleNavigationGroups(role)) {
    const item = group.children.find((child) => {
      const basePath = child.path?.split('?')[0] ?? ''
      return Boolean(basePath) && path.startsWith(basePath)
    })
    if (item) return { group, item }
  }
  return null
}
