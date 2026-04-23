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
    { section: 'coordination', label: '医护协调', description: '查看多角色协同记录和患者推进事项。' },
    { section: 'insights', label: '模型洞察', description: '查看当前患者预测结果、证据摘要和建议来源。' },
    { section: 'governance', label: '治理看板', description: '查看数据质量概览、异常时间线和治理动作。' },
    { section: 'role-workspaces', label: '权限与角色', description: '查看角色边界、权限矩阵和协同分工。' },
  ],
  nurse: [
    { section: 'tasks', label: '随访任务', description: '处理待随访患者、联系记录和任务状态。' },
    { section: 'contacts', label: '联系记录', description: '记录患者随访联系和沟通结果。' },
    { section: 'flow', label: '病程流转', description: '查看患者病程状态与后续动作。' },
    { section: 'coordination', label: '医护协调', description: '查看协同事项、护理追踪和任务推进。' },
    { section: 'role-workspaces', label: '权限与角色', description: '查看角色边界、权限矩阵和协同分工。' },
  ],
  pharmacist: [
    { section: 'pharmacy', label: '药房药库', description: '查看药房库存、批次和药品流转状态。' },
    { section: 'drug-management', label: '药品目录', description: '查看药品目录、剂型规格和状态。' },
    { section: 'drug-permission-management', label: '药品权限', description: '查看不同角色的药品使用权限。' },
    { section: 'coordination', label: '医护协调', description: '查看多角色协同记录和患者推进事项。' },
    { section: 'role-workspaces', label: '权限与角色', description: '查看角色边界、权限矩阵和协同分工。' },
  ],
  archivist: [
    { section: 'archive', label: '患者档案', description: '维护患者身份信息、附件和建档资料。' },
    { section: 'data-quality', label: '数据质量', description: '查看档案缺失字段、冲突记录和补全待办。' },
    { section: 'drug-management', label: '药品目录', description: '查看药品目录、剂型规格和状态。' },
    { section: 'drug-permission-management', label: '药品权限', description: '查看不同角色的药品使用权限。' },
    { section: 'governance', label: '治理看板', description: '查看数据质量概览、异常时间线和治理动作。' },
    { section: 'role-workspaces', label: '权限与角色', description: '查看角色边界、权限矩阵和协同分工。' },
  ],
  admin: [
    { section: 'doctor', label: '医生工作台', description: '查看待处理患者、风险提示和主操作入口。' },
    { section: 'archive', label: '患者档案', description: '查看患者身份、病程、附件和电子档案。' },
    { section: 'tasks', label: '随访任务', description: '处理待随访患者、联系记录和任务状态。' },
    { section: 'contacts', label: '联系记录', description: '记录患者随访联系和沟通结果。' },
    { section: 'flow', label: '病程流转', description: '查看患者病程状态与后续动作。' },
    { section: 'coordination', label: '医护协调', description: '查看跨角色协同记录和待处理事项。' },
    { section: 'insights', label: '模型洞察', description: '查看当前患者预测结果、证据摘要和建议来源。' },
    { section: 'governance', label: '治理看板', description: '查看数据质量、异常记录和治理动作。' },
    { section: 'data-quality', label: '数据质量', description: '查看缺失字段、冲突记录和异常时间线。' },
    { section: 'pharmacy', label: '药房药库', description: '查看药房库存、批次和药品流转状态。' },
    { section: 'drug-management', label: '药品目录', description: '查看药品目录、剂型规格和状态。' },
    { section: 'drug-permission-management', label: '药品权限', description: '查看不同角色的药品使用权限。' },
    { section: 'model-dashboard', label: '模型看板', description: '查看模型版本、训练指标和健康状态。' },
    { section: 'training-center', label: '训练中心', description: '管理模型训练任务和数据集导入。' },
    { section: 'model-operations', label: '模型调试台', description: '查看测试样本、原始输入输出和回退原因。' },
    { section: 'role-workspaces', label: '权限与角色', description: '查看角色边界、权限矩阵和协同分工。' },
    { section: 'system', label: '系统中心', description: '查看系统状态和基础配置。' },
  ],
}

export const SECTION_LABELS: Partial<Record<AppSection, string>> = {
  doctor: '医生工作台',
  archive: '患者档案',
  'model-dashboard': '模型看板',
  'training-center': '训练中心',
  'model-operations': '模型调试台',
  'role-workspaces': '权限与角色工作台',
  pharmacy: '药房药库',
  coordination: '医护协调',
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
