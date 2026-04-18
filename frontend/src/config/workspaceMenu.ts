import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

export interface WorkspaceMenuItem {
  section: AppSection
  label: string
  description: string
}

export const ROLE_WORKSPACE_MENUS: Record<DoctorUser['role'], WorkspaceMenuItem[]> = {
  doctor: [
    { section: 'doctor', label: '医生首页', description: '待处理患者、当前患者摘要和快捷入口。' },
    { section: 'archive', label: '患者档案', description: '患者身份信息、病程档案和电子档案入口。' },
    { section: 'drug-management', label: '药品管理', description: '药品目录、通用名、剂型规格和状态维护。' },
    { section: 'drug-permission-management', label: '药品权限管理', description: '按角色维护药品查看、开立、审核和执行权限。' },
    { section: 'model-dashboard', label: '模型看板', description: '模型版本、训练指标和健康状态。' },
    { section: 'insights', label: '模型洞察', description: '当前患者预测结果、证据摘要和建议来源。' },
    { section: 'governance', label: '治理看板', description: '数据质量概览、缺失字段和异常记录。' },
    { section: 'system', label: '系统中心', description: '账户、鉴权和系统状态。' },
  ],
  nurse: [
    { section: 'tasks', label: '随访工作台', description: '待随访任务、联系记录和任务闭环。' },
    { section: 'contacts', label: '联系记录', description: '联系患者、家属和外联记录。' },
    { section: 'flow', label: '流程看板', description: '随访流程状态和下一步动作。' },
    { section: 'system', label: '系统中心', description: '账户、鉴权和系统状态。' },
  ],
  archivist: [
    { section: 'archive', label: '患者档案', description: '患者身份信息、病程档案和电子档案入口。' },
    { section: 'drug-management', label: '药品管理', description: '药品目录、通用名、剂型规格和状态维护。' },
    { section: 'drug-permission-management', label: '药品权限管理', description: '按角色维护药品查看、开立、审核和执行权限。' },
    { section: 'data-quality', label: '数据治理', description: '缺失字段、冲突记录和待补全档案。' },
    { section: 'governance', label: '治理看板', description: '数据质量概览和治理动作。' },
    { section: 'system', label: '系统中心', description: '账户、鉴权和系统状态。' },
  ],
}

export const SECTION_LABELS: Record<AppSection, string> = {
  doctor: '医生首页',
  archive: '患者档案',
  'drug-management': '药品管理',
  'drug-permission-management': '药品权限管理',
  tasks: '随访工作台',
  'model-dashboard': '模型看板',
  governance: '治理看板',
  insights: '模型洞察',
  contacts: '联系记录',
  flow: '流程看板',
  'data-quality': '数据治理',
  system: '系统中心',
}

export function allowedSectionsForRole(role: DoctorUser['role']): AppSection[] {
  return ROLE_WORKSPACE_MENUS[role].map((item) => item.section)
}

export function sectionLabel(section: AppSection): string {
  return SECTION_LABELS[section] ?? section
}
