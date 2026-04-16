import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

export interface WorkspaceMenuItem {
  section: AppSection
  label: string
  description: string
}

export const ROLE_WORKSPACE_MENUS: Record<DoctorUser['role'], WorkspaceMenuItem[]> = {
  doctor: [
    {
      section: 'doctor',
      label: '诊疗工作台',
      description: '慢病辅助诊疗、风险识别与处置建议',
    },
    {
      section: 'archive',
      label: '患者档案',
      description: '患者档案维护与事件补录',
    },
    {
      section: 'model-dashboard',
      label: '模型看板',
      description: '模型版本、训练任务与运行指标管理',
    },
    {
      section: 'insights',
      label: '模型洞察',
      description: '模型表现、预测依据与趋势观察',
    },
    {
      section: 'governance',
      label: '治理看板',
      description: '数据质量、档案完整性与治理动作',
    },
    {
      section: 'system',
      label: '系统中心',
      description: '健康状态、权限能力与系统审计',
    },
  ],
  nurse: [
    {
      section: 'tasks',
      label: '随访任务',
      description: '待办随访任务与执行情况',
    },
    {
      section: 'contacts',
      label: '患者联络记录',
      description: '电话/微信/家属联络记录管理',
    },
    {
      section: 'flow',
      label: '流转看板',
      description: '患者流转状态与下一步动作',
    },
    {
      section: 'system',
      label: '系统中心',
      description: '健康状态、权限能力与系统审计',
    },
  ],
  archivist: [
    {
      section: 'archive',
      label: '档案管理',
      description: '档案建档、更新与质量维护',
    },
    {
      section: 'data-quality',
      label: '数据完整性',
      description: '结构化字段与关键信息完整性检查',
    },
    {
      section: 'governance',
      label: '治理模块',
      description: '治理模块与数据维护状态',
    },
    {
      section: 'system',
      label: '系统中心',
      description: '健康状态、权限能力与系统审计',
    },
  ],
}

export const SECTION_LABELS: Record<AppSection, string> = {
  doctor: '诊疗工作台',
  archive: '患者档案',
  tasks: '随访任务',
  'model-dashboard': '模型看板',
  governance: '治理看板',
  insights: '模型洞察',
  contacts: '患者联络记录',
  flow: '流转看板',
  'data-quality': '数据完整性',
  system: '系统中心',
}

export function allowedSectionsForRole(role: DoctorUser['role']): AppSection[] {
  return ROLE_WORKSPACE_MENUS[role].map((item) => item.section)
}

export function sectionLabel(section: AppSection): string {
  return SECTION_LABELS[section] ?? section
}
