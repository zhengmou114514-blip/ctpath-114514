<script setup lang="ts">
import { computed } from 'vue'
import { ROLE_WORKSPACE_MENUS } from '../config/workspaceMenu'
import type { DoctorUser, HealthResponse } from '../services/types'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  activeSection: AppSection
  doctor: DoctorUser
  health: HealthResponse | null
  patientCount: number
  followupCount: number
}>()

const emit = defineEmits<{
  (e: 'select', section: AppSection): void
  (e: 'logout'): void
}>()

const sectionCopy: Record<AppSection, { label: string; description: string; group: string }> = {
  doctor: { label: '医生工作台', description: '待处理患者、风险提醒与快捷入口', group: '临床工作' },
  archive: { label: '患者档案', description: '身份信息、电子档案与附件', group: '临床工作' },
  tasks: { label: '护士随访', description: '待随访任务与处理状态', group: '随访闭环' },
  contacts: { label: '联系记录', description: '电话、家属与门诊联系记录', group: '随访闭环' },
  flow: { label: '随访流程', description: '流程状态与下一步动作', group: '随访闭环' },
  'drug-management': { label: '药品管理', description: '药品目录、状态与管制标识', group: '药品与权限' },
  'drug-permission-management': { label: '药品权限', description: '角色级用药权限矩阵', group: '药品与权限' },
  insights: { label: '模型洞察', description: '当前患者预测与证据摘要', group: '模型中心' },
  'model-dashboard': { label: '模型看板', description: '模型版本、指标与健康状态', group: '模型中心' },
  governance: { label: '治理中心', description: '数据质量、冲突与审计线索', group: '治理中心' },
  'data-quality': { label: '数据质量', description: '档案缺失与质量问题', group: '治理中心' },
  system: { label: '系统状态', description: '运行模式、认证与审计状态', group: '治理中心' },
}

const roleCopy: Record<DoctorUser['role'], string> = {
  doctor: '医生',
  nurse: '护士',
  archivist: '档案员',
}

const menus = computed(() => ROLE_WORKSPACE_MENUS[props.doctor.role] ?? [])
const groupedMenus = computed(() => {
  const groups = new Map<string, typeof menus.value>()
  for (const item of menus.value) {
    const group = sectionCopy[item.section]?.group ?? '其他'
    groups.set(group, [...(groups.get(group) ?? []), item])
  }
  return [...groups.entries()].map(([group, items]) => ({ group, items }))
})

function labelFor(section: AppSection) {
  return sectionCopy[section]?.label ?? section
}

function descriptionFor(section: AppSection) {
  return sectionCopy[section]?.description ?? '业务模块'
}
</script>

<template>
  <aside class="sidebar-shell workstation-sidebar">
    <div class="brand-panel">
      <div class="brand-mark">CT</div>
      <div>
        <p class="eyebrow inverse">CTpath</p>
        <strong>慢病辅助诊疗</strong>
      </div>
    </div>

    <section class="sidebar-user-section">
      <div class="user-info">
        <span class="user-department">{{ doctor.department }}</span>
        <strong class="user-name">{{ doctor.name }}</strong>
        <span class="user-title">{{ doctor.title }}</span>
      </div>
      <div class="user-meta">
        <span class="role-tag" :class="`role-tag-${doctor.role}`">{{ roleCopy[doctor.role] }}</span>
        <span class="current-module">当前：{{ labelFor(activeSection) }}</span>
      </div>
    </section>

    <section class="sidebar-stats-section" aria-label="工作台状态">
      <div class="stat-item">
        <span class="stat-label">患者档案</span>
        <strong class="stat-value">{{ patientCount }}</strong>
      </div>
      <div class="stat-item">
        <span class="stat-label">随访任务</span>
        <strong class="stat-value">{{ followupCount }}</strong>
      </div>
      <div class="stat-item">
        <span class="stat-label">运行模式</span>
        <strong class="stat-mode">{{ health?.mode ?? 'unknown' }}</strong>
      </div>
    </section>

    <nav class="sidebar-nav" aria-label="工作台导航">
      <section v-for="group in groupedMenus" :key="group.group" class="nav-group">
        <p class="nav-group-title">{{ group.group }}</p>
        <button
          v-for="item in group.items"
          :key="item.section"
          class="nav-item nav-item-detailed"
          :class="{ active: item.section === activeSection }"
          type="button"
          @click="emit('select', item.section)"
        >
          <strong>{{ labelFor(item.section) }}</strong>
          <span>{{ descriptionFor(item.section) }}</span>
        </button>
      </section>
    </nav>

    <div class="sidebar-actions">
      <button class="sidebar-button ghost" type="button" @click="emit('logout')">退出登录</button>
    </div>
  </aside>
</template>
