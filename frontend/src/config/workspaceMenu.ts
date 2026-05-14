import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

export interface WorkspaceMenuItem {
  section: AppSection
  label: string
  description: string
}

export interface WorkspaceSystemGroup {
  key: string
  title: string
  subtitle: string
  openhisPort: string
  sections: AppSection[]
}

export interface RoleWorkspaceSystem {
  title: string
  subtitle: string
  portHint: string
}

export const ROLE_WORKSPACE_MENUS: Record<DoctorUser['role'], WorkspaceMenuItem[]> = {
  doctor: [
    { section: 'doctor', label: '医生工作台', description: '查看待处理患者、风险提示和主操作入口。' },
    { section: 'archive', label: '患者档案', description: '查看患者身份、病程、附件和电子档案。' },
    { section: 'coordination', label: '医护协同', description: '发起随访、查看协同记录和复核事项。' },
    { section: 'insights', label: '模型洞察', description: '查看当前患者预测结果、证据摘要和建议来源。' },
  ],
  nurse: [
    { section: 'tasks', label: '随访工作台', description: '处理今日随访任务、未接通任务和医生复核任务。' },
    { section: 'flow', label: '今日随访', description: '查看今日任务和病情流转状态。' },
    { section: 'contacts', label: '联系记录', description: '记录患者随访联系和沟通结果。' },
    { section: 'coordination', label: '医生复核', description: '查看需要医生确认的随访事项。' },
  ],
  pharmacist: [
    { section: 'drug-management', label: '药师用药复核', description: '查看待复核用药并完成批准或驳回，不进入库存或出入库流程。' },
  ],
  archivist: [
    { section: 'archive', label: '患者档案', description: '查看患者身份、病程、附件和电子档案。' },
  ],
  admin: [
    { section: 'role-workspaces', label: '角色权限管理', description: '维护用户角色和业务权限。' },
    { section: 'drug-permission-management', label: '药品权限管理', description: '配置不同角色的药品使用权限。' },
    { section: 'governance', label: '治理中心', description: '查看异常时间线、冲突记录和待补全档案。' },
    { section: 'model-dashboard', label: '模型看板', description: '查看模型版本、训练指标和健康状态。' },
    { section: 'system', label: '审计日志', description: '查看登录、操作和系统审计记录。' },
  ],
}

export const ROLE_SYSTEMS: Record<DoctorUser['role'], RoleWorkspaceSystem> = {
  doctor: {
    title: '慢性病辅助诊疗系统',
    subtitle: '门诊业务 / 患者评估 / 随访发起',
    portHint: '医生站',
  },
  nurse: {
    title: '慢性病辅助诊疗系统',
    subtitle: '随访管理 / 联系闭环 / 医生复核',
    portHint: '护士站',
  },
  pharmacist: {
    title: '慢性病辅助诊疗系统',
    subtitle: '药事管理 / 药品目录 / 药事复核',
    portHint: '药房人员',
  },
  archivist: {
    title: '慢性病辅助诊疗系统',
    subtitle: '患者档案 / 电子档案',
    portHint: '档案查看',
  },
  admin: {
    title: '慢性病辅助诊疗系统',
    subtitle: '系统管理 / 权限治理 / 模型治理',
    portHint: '管理员',
  },
}

export const ROLE_MENU_GROUPS: Record<DoctorUser['role'], Array<{ title: string; sections: AppSection[] }>> = {
  doctor: [
    { title: '门诊业务', sections: ['doctor', 'archive', 'coordination'] },
    { title: '智能辅助', sections: ['insights'] },
  ],
  nurse: [
    { title: '随访管理', sections: ['tasks', 'flow', 'contacts', 'coordination'] },
  ],
  pharmacist: [
    { title: '药事管理', sections: ['drug-management'] },
  ],
  archivist: [
    { title: '档案查看', sections: ['archive'] },
  ],
  admin: [
    { title: '系统管理', sections: ['role-workspaces', 'drug-permission-management', 'governance', 'model-dashboard', 'system'] },
  ],
}

export const OPENHIS_SYSTEM_GROUPS: WorkspaceSystemGroup[] = [
  {
    key: 'admin',
    title: '后台管理系统',
    subtitle: '角色权限 / 系统治理',
    openhisPort: '8001',
    sections: ['role-workspaces', 'system', 'governance'],
  },
  {
    key: 'care',
    title: '医护协同系统',
    subtitle: '医生 / 护士 / 患者模型辅助 / 协同闭环',
    openhisPort: '8003',
    sections: ['doctor', 'archive', 'tasks', 'contacts', 'flow', 'coordination', 'insights'],
  },
  {
    key: 'pharmacy',
    title: '药品管理系统',
    subtitle: '药品目录 / 药品权限 / 轻量用药审核',
    openhisPort: '8004',
    sections: ['drug-management', 'drug-permission-management'],
  },
  {
    key: 'emr',
    title: '电子病历系统',
    subtitle: '病程时间线 / 电子档案',
    openhisPort: '8005',
    sections: ['emr', 'archive'],
  },
  {
    key: 'archive',
    title: '病案管理系统',
    subtitle: '主索引 / 附件补全 / 数据质量',
    openhisPort: '8008',
    sections: ['archive', 'data-quality', 'governance'],
  },
  {
    key: 'model',
    title: '模型管理系统',
    subtitle: '看板 / 运行 / 训练',
    openhisPort: 'project',
    sections: ['model-dashboard', 'model-operations', 'training-center'],
  },
]

export const SECTION_LABELS: Partial<Record<AppSection, string>> = {
  doctor: '医生工作台',
  archive: '患者档案',
  'model-dashboard': '模型看板',
  'training-center': '训练中心',
  'model-operations': '模型运行台',
  'role-workspaces': '角色权限管理',
  pharmacy: '药事复核',
  coordination: '医护协同',
  'drug-management': '药品目录',
  'drug-permission-management': '药品权限管理',
  tasks: '随访工作台',
  contacts: '联系记录',
  flow: '今日随访',
  governance: '治理中心',
  insights: '模型洞察',
  'data-quality': '数据质量',
  system: '审计日志',
}

export function allowedSectionsForRole(role: DoctorUser['role']): AppSection[] {
  return ROLE_WORKSPACE_MENUS[role].map((item) => item.section)
}

export function sectionLabel(section: AppSection): string {
  return SECTION_LABELS[section] ?? section
}

export function roleSystemForRole(role: DoctorUser['role']): RoleWorkspaceSystem {
  return ROLE_SYSTEMS[role]
}
