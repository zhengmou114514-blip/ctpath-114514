import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

export interface WorkspaceMenuItem {
  section: AppSection
  label: string
  description: string
}

export const ROLE_WORKSPACE_MENUS: Record<DoctorUser['role'], WorkspaceMenuItem[]> = {
  doctor: [
    { section: 'doctor', label: '医生工作台', description: '查看待处理患者、风险提醒和当前诊疗主动作入口。' },
    { section: 'archive', label: '患者档案', description: '维护患者基础信息、建档状态、时间线和电子档案入口。' },
    { section: 'drug-management', label: '药品目录', description: '管理慢病场景下的药品目录、剂型规格和药品状态。' },
    { section: 'drug-permission-management', label: '药品权限', description: '配置医生、护士、药师等角色的药品查看和开立权限。' },
    { section: 'model-dashboard', label: '模型看板', description: '查看模型版本、指标、调用量和健康状态。' },
    { section: 'model-operations', label: '模型运营台', description: '集中查看登录次数、用户信息、模型状态和近期训练动态。' },
    { section: 'training-center', label: '训练中心', description: '导入训练数据集、发起训练任务并跟踪训练结果。' },
    { section: 'insights', label: '模型洞察', description: '围绕当前患者查看预测结果、证据摘要和建议来源。' },
    { section: 'governance', label: '治理看板', description: '查看数据质量、档案补全、冲突记录和治理动作。' },
    { section: 'system', label: '系统中心', description: '查看账号权限、系统审计和基础运行状态。' },
  ],
  nurse: [
    { section: 'tasks', label: '随访任务', description: '查看待随访患者、任务到期情况和优先级。' },
    { section: 'contacts', label: '联系记录', description: '记录电话、微信等联系结果并更新下一次计划。' },
    { section: 'flow', label: '随访流程', description: '查看患者随访进度、当前阶段和下一步动作。' },
    { section: 'system', label: '系统中心', description: '查看当前账号权限和基础运行状态。' },
  ],
  archivist: [
    { section: 'archive', label: '患者档案', description: '负责档案建档、信息补全和电子附件归集。' },
    { section: 'drug-management', label: '药品目录', description: '维护药品目录基础信息和药品状态。' },
    { section: 'drug-permission-management', label: '药品权限', description: '查看和维护角色与药品权限映射。' },
    { section: 'data-quality', label: '数据质量', description: '查看缺失字段、冲突记录和待补全档案。' },
    { section: 'governance', label: '治理看板', description: '查看档案治理动作、冲突追踪和治理结果。' },
    { section: 'model-operations', label: '模型运营台', description: '集中查看模型运行、用户信息和登录审计摘要。' },
    { section: 'training-center', label: '训练中心', description: '为模型治理准备训练数据集和训练任务。' },
    { section: 'system', label: '系统中心', description: '查看账号、权限与系统审计信息。' },
  ],
}

export const SECTION_LABELS: Record<AppSection, string> = {
  doctor: '医生工作台',
  archive: '患者档案',
  'drug-management': '药品目录',
  'drug-permission-management': '药品权限',
  tasks: '随访任务',
  'model-dashboard': '模型看板',
  'model-operations': '模型运营台',
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
