import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

export type NavigationRole = DoctorUser['role']

export interface NavigationItem {
  title: string
  path?: string
  routeName?: string
  query?: Record<string, string>
  icon?: string
  section?: AppSection
  requirePatient?: boolean
  roles: NavigationRole[]
  children?: NavigationItem[]
}

export const navigationGroups: NavigationItem[] = [
  {
    title: '门诊医生站',
    icon: 'Grid',
    roles: ['doctor'],
    children: [
      { title: '医生工作台', routeName: 'doctor-workbench', query: { view: 'overview' }, section: 'doctor', roles: ['doctor'] },
      { title: '待处理患者', routeName: 'doctor-workbench', query: { view: 'pending' }, section: 'doctor', roles: ['doctor'] },
      { title: '当前关注患者', routeName: 'doctor-workbench', query: { view: 'current' }, section: 'doctor', roles: ['doctor'] },
      { title: '发起随访', routeName: 'patient-followups', section: 'archive', requirePatient: true, roles: ['doctor'] },
    ],
  },
  {
    title: '患者档案',
    icon: 'Document',
    roles: ['doctor'],
    children: [
      { title: '患者总览', routeName: 'doctor-patients', section: 'archive', roles: ['doctor'] },
      { title: '基本档案', routeName: 'patient-profile', section: 'archive', requirePatient: true, roles: ['doctor'] },
      { title: '联系记录', routeName: 'patient-contacts', section: 'archive', requirePatient: true, roles: ['doctor'] },
      { title: '病程时间线', routeName: 'patient-timeline', section: 'archive', requirePatient: true, roles: ['doctor'] },
      { title: '附件资料', routeName: 'patient-attachments', section: 'archive', requirePatient: true, roles: ['doctor'] },
      { title: '当前用药', routeName: 'patient-medications', section: 'archive', requirePatient: true, roles: ['doctor'] },
      { title: '风险评估', routeName: 'patient-risk', section: 'insights', requirePatient: true, roles: ['doctor'] },
    ],
  },
  {
    title: '辅助诊疗',
    icon: 'Operation',
    roles: ['doctor'],
    children: [
      { title: '风险评估', routeName: 'doctor-risk', query: { tab: 'current' }, section: 'insights', roles: ['doctor'] },
      { title: '证据摘要', routeName: 'doctor-risk', query: { tab: 'evidence' }, section: 'insights', roles: ['doctor'] },
      { title: '辅助建议', routeName: 'doctor-risk', query: { tab: 'advice' }, section: 'insights', roles: ['doctor'] },
    ],
  },
  {
    title: '护士随访站',
    icon: 'Memo',
    roles: ['nurse'],
    children: [
      { title: '随访工作台', routeName: 'nurse-followups', query: { view: 'overview' }, section: 'tasks', roles: ['nurse'] },
      { title: '今日随访', routeName: 'nurse-followups-today', section: 'flow', roles: ['nurse'] },
      { title: '未接通任务', routeName: 'nurse-followups-missed', section: 'contacts', roles: ['nurse'] },
      { title: '联系记录', routeName: 'nurse-followups-records', section: 'contacts', roles: ['nurse'] },
      { title: '医生复核', routeName: 'nurse-followups-review', section: 'coordination', roles: ['nurse'] },
      { title: '随访统计', routeName: 'nurse-followups-stats', section: 'tasks', roles: ['nurse'] },
    ],
  },
  {
    title: '药事管理',
    icon: 'Tickets',
    roles: ['pharmacist'],
    children: [
      { title: '药品目录', routeName: 'pharmacy-drug-catalog', query: { view: 'catalog' }, section: 'drug-management', roles: ['pharmacist'] },
      { title: '剂型规格', routeName: 'pharmacy-drug-catalog', query: { view: 'spec' }, section: 'drug-management', roles: ['pharmacist'] },
      { title: '药品状态', routeName: 'pharmacy-drug-status', section: 'drug-management', roles: ['pharmacist'] },
      { title: '处方药标识', routeName: 'pharmacy-drug-catalog', query: { view: 'prescription' }, section: 'drug-management', roles: ['pharmacist'] },
      { title: '库存与批次', routeName: 'pharmacy-medication-review', query: { view: 'inventory' }, section: 'pharmacy', roles: ['pharmacist'] },
      { title: '处方复核', routeName: 'pharmacy-medication-review', query: { view: 'review' }, section: 'pharmacy', roles: ['pharmacist'] },
    ],
  },
  {
    title: '系统管理',
    icon: 'SetUp',
    roles: ['admin'],
    children: [
      { title: '用户与角色', routeName: 'admin-permissions', query: { view: 'users' }, section: 'role-workspaces', roles: ['admin'] },
      { title: '权限配置', routeName: 'admin-permissions', query: { view: 'permissions' }, section: 'role-workspaces', roles: ['admin'] },
      { title: '药品权限管理', routeName: 'admin-drug-permissions', section: 'drug-permission-management', roles: ['admin'] },
      { title: '审计日志', routeName: 'admin-audit', section: 'system', roles: ['admin'] },
    ],
  },
  {
    title: '模型与治理',
    icon: 'FolderOpened',
    roles: ['admin'],
    children: [
      { title: '模型看板', routeName: 'admin-model-dashboard', section: 'model-dashboard', roles: ['admin'] },
      { title: '治理中心', routeName: 'admin-governance', query: { view: 'overview' }, section: 'governance', roles: ['admin'] },
      { title: '数据质量', routeName: 'admin-governance', query: { view: 'data-quality' }, section: 'governance', roles: ['admin'] },
      { title: '异常记录', routeName: 'admin-governance-issues', section: 'governance', roles: ['admin'] },
      { title: '待补全档案', routeName: 'admin-governance', query: { view: 'incomplete-archive' }, section: 'governance', roles: ['admin'] },
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
