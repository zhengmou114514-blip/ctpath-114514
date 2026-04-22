import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

export interface WorkspaceMenuItem {
  section: AppSection
  label: string
  description: string
}

export const ROLE_WORKSPACE_MENUS: Record<DoctorUser['role'], WorkspaceMenuItem[]> = {
  doctor: [
    { section: 'doctor', label: '医生工作台', description: '查看待处理患者、风险提示和主操作入口。' },
    { section: 'archive', label: '患者档案', description: '查看患者身份、病程、附件和电子档案。' },
    { section: 'tasks', label: '随访任务', description: '处理待随访患者、联系记录和任务状态。' },
    { section: 'contacts', label: '联系记录', description: '记录患者随访联系和沟通结果。' },
    { section: 'flow', label: '病程流转', description: '查看患者病程状态与后续动作。' },
    { section: 'drug-management', label: '药品目录', description: '查看药品目录、剂型规格和状态。' },
    { section: 'drug-permission-management', label: '药品权限', description: '查看不同角色的药品使用权限。' },
  ],
  nurse: [
    { section: 'tasks', label: '随访任务', description: '处理待随访患者、联系记录和任务状态。' },
    { section: 'contacts', label: '联系记录', description: '记录患者随访联系和沟通结果。' },
    { section: 'flow', label: '病程流转', description: '查看患者病程状态与后续动作。' },
  ],
  archivist: [
    { section: 'archive', label: '患者档案', description: '维护患者身份信息、附件和建档资料。' },
    { section: 'drug-management', label: '药品目录', description: '查看药品目录、剂型规格和状态。' },
    { section: 'drug-permission-management', label: '药品权限', description: '查看不同角色的药品使用权限。' },
  ],
}

export const SECTION_LABELS: Partial<Record<AppSection, string>> = {
  doctor: '医生工作台',
  archive: '患者档案',
  'drug-management': '药品目录',
  'drug-permission-management': '药品权限',
  tasks: '随访任务',
  contacts: '联系记录',
  flow: '病程流转',
  governance: '治理看板',
  insights: '模型洞察',
  'data-quality': '数据质量',
  system: '系统中心',
}

export function allowedSectionsForRole(role: DoctorUser['role']): AppSection[] {
  return ROLE_WORKSPACE_MENUS[role].map((item) => item.section)
}

export function sectionLabel(section: AppSection): string {
  return SECTION_LABELS[section] ?? section
}
