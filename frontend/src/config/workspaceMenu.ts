import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

export interface WorkspaceMenuItem {
  section: AppSection
  label: string
  description: string
}

export const ROLE_WORKSPACE_MENUS: Record<DoctorUser['role'], WorkspaceMenuItem[]> = {
  doctor: [
    { section: 'doctor', label: '医生首页', description: '查看待处理患者、当前患者摘要和快捷入口。' },
    { section: 'archive', label: '患者档案', description: '查看和维护患者基础档案、病程事件与状态。' },
    { section: 'drug-management', label: '药品管理', description: '维护药品目录、基础属性和启用状态。' },
    { section: 'model-dashboard', label: '模型看板', description: '查看模型治理指标、训练时间和健康状态。' },
    { section: 'insights', label: '模型洞察', description: '查看当前患者的预测结果、证据摘要和建议来源。' },
    { section: 'governance', label: '治理看板', description: '查看数据质量、缺失字段和治理动作记录。' },
    { section: 'system', label: '系统中心', description: '查看账户、权限、审计和运行状态。' },
  ],
  nurse: [
    { section: 'tasks', label: '随访工作台', description: '处理待办随访任务和联系记录。' },
    { section: 'contacts', label: '联系记录', description: '查看联系日志和外联记录。' },
    { section: 'flow', label: '流程看板', description: '查看随访与流转状态。' },
    { section: 'system', label: '系统中心', description: '查看账户、权限、审计和运行状态。' },
  ],
  archivist: [
    { section: 'archive', label: '患者档案', description: '维护患者档案、事件和电子材料。' },
    { section: 'drug-management', label: '药品管理', description: '维护药品目录、基础属性和启用状态。' },
    { section: 'data-quality', label: '数据质量', description: '查看缺失字段、异常记录和补全任务。' },
    { section: 'governance', label: '治理看板', description: '查看数据质量和治理动作记录。' },
    { section: 'system', label: '系统中心', description: '查看账户、权限、审计和运行状态。' },
  ],
}

export const SECTION_LABELS: Record<AppSection, string> = {
  doctor: '医生首页',
  archive: '患者档案',
  'drug-management': '药品管理',
  tasks: '随访工作台',
  'model-dashboard': '模型看板',
  governance: '治理看板',
  insights: '模型洞察',
  contacts: '联系记录',
  flow: '流程看板',
  'data-quality': '数据质量',
  system: '系统中心',
}

export function allowedSectionsForRole(role: DoctorUser['role']): AppSection[] {
  return ROLE_WORKSPACE_MENUS[role].map((item) => item.section)
}

export function sectionLabel(section: AppSection): string {
  return SECTION_LABELS[section] ?? section
}
