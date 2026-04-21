import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

export interface WorkspaceMenuItem {
  section: AppSection
  label: string
  description: string
}

export const ROLE_WORKSPACE_MENUS: Record<DoctorUser['role'], WorkspaceMenuItem[]> = {
  doctor: [
    { section: 'doctor', label: '医生工作台', description: '查看待处理患者、风险提示与主闭环入口。' },
    { section: 'archive', label: '患者档案', description: '维护患者身份信息、建档资料与病程记录。' },
    { section: 'drug-management', label: '药品目录', description: '查看药品目录、规格、状态与处方属性。' },
    { section: 'drug-permission-management', label: '药品权限', description: '查看角色与药品权限映射关系。' },
    { section: 'model-dashboard', label: '模型看板', description: '查看模型版本、最近训练与运行健康状态。' },
    { section: 'training-center', label: '训练中心', description: '导入训练数据集并发起模型训练任务。' },
    { section: 'insights', label: '模型洞察', description: '围绕当前患者查看预测、证据摘要与建议来源。' },
    { section: 'governance', label: '治理看板', description: '查看数据质量、档案治理与异常巡检结果。' },
    { section: 'system', label: '系统中心', description: '查看当前账号、权限能力与系统健康信息。' },
  ],
  nurse: [
    { section: 'tasks', label: '随访任务', description: '处理待随访任务、逾期任务与完成闭环。' },
    { section: 'contacts', label: '联系记录', description: '登记患者联系结果、下次计划与回访情况。' },
    { section: 'flow', label: '随访流程', description: '查看患者随访状态流转与下一步动作。' },
    { section: 'system', label: '系统中心', description: '查看当前账号与系统运行状态。' },
  ],
  archivist: [
    { section: 'archive', label: '患者档案', description: '维护档案主数据、建档状态与电子档案入口。' },
    { section: 'drug-management', label: '药品目录', description: '协同维护药品目录基础信息。' },
    { section: 'drug-permission-management', label: '药品权限', description: '查看药品权限映射与角色边界。' },
    { section: 'data-quality', label: '数据质量', description: '聚焦缺失字段、主索引冲突与待补档案。' },
    { section: 'governance', label: '治理看板', description: '查看治理动作记录与档案巡检结果。' },
    { section: 'training-center', label: '训练中心', description: '配合模型中心管理训练数据导入与任务观察。' },
    { section: 'system', label: '系统中心', description: '查看系统健康、权限与审计信息。' },
  ],
}

export const SECTION_LABELS: Record<AppSection, string> = {
  doctor: '医生工作台',
  archive: '患者档案',
  'drug-management': '药品目录',
  'drug-permission-management': '药品权限',
  tasks: '随访任务',
  'model-dashboard': '模型看板',
  'training-center': '训练中心',
  governance: '治理看板',
  insights: '模型洞察',
  contacts: '联系记录',
  flow: '随访流程',
  'data-quality': '数据质量',
  system: '系统中心',
}

export function allowedSectionsForRole(role: DoctorUser['role']): AppSection[] {
  return ROLE_WORKSPACE_MENUS[role].map((item) => item.section)
}

export function sectionLabel(section: AppSection): string {
  return SECTION_LABELS[section] ?? section
}
