<script setup lang="ts">
import { computed } from 'vue'
import {
  FolderOpened,
  Grid,
  DataAnalysis,
  Document,
  Memo,
  Operation,
  SetUp,
  SwitchButton,
  Tickets,
  UserFilled,
} from '@element-plus/icons-vue'
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

const menuLabelMap: Record<AppSection, string> = {
  doctor: '医生工作台',
  archive: '患者档案',
  tasks: '患者管理',
  contacts: '联系记录',
  flow: '随访流程',
  insights: '模型洞察',
  'model-dashboard': '模型看板',
  'training-center': '训练中心',
  governance: '治理看板',
  'data-quality': '数据质量',
  'drug-management': '药品管理',
  'drug-permission-management': '药品权限',
  system: '系统中心',
}

const menuIconMap: Record<AppSection, object> = {
  doctor: Grid,
  archive: Document,
  tasks: Memo,
  contacts: Operation,
  flow: FolderOpened,
  insights: DataAnalysis,
  'model-dashboard': DataAnalysis,
  'training-center': DataAnalysis,
  governance: FolderOpened,
  'data-quality': Document,
  'drug-management': Tickets,
  'drug-permission-management': Tickets,
  system: SetUp,
}

const navItems = computed(() => {
  const items = ROLE_WORKSPACE_MENUS[props.doctor.role] ?? []
  const seen = new Set<string>()
  return items.filter((item) => {
    const dedupeKey =
      props.doctor.role === 'doctor' && item.section === 'archive'
        ? 'patient-management'
        : props.doctor.role === 'nurse' && (item.section === 'tasks' || item.section === 'contacts' || item.section === 'flow')
          ? item.section
          : item.section

    if (seen.has(dedupeKey)) return false
    seen.add(dedupeKey)
    return true
  })
})

const sidebarMeta = computed(() => ({
  mode: `${(props.health?.mode ?? 'demo').toUpperCase()}/MYSQL 模式`,
  identity: props.doctor.name,
  department: props.doctor.department,
}))

function labelFor(section: AppSection) {
  if (props.doctor.role === 'doctor' && section === 'archive') return '患者档案'
  if (props.doctor.role === 'doctor' && section === 'insights') return '模型洞察'
  return menuLabelMap[section] ?? section
}

function iconFor(section: AppSection) {
  if (props.doctor.role === 'doctor' && section === 'archive') return UserFilled
  if (props.doctor.role === 'doctor' && section === 'insights') return DataAnalysis
  return menuIconMap[section] ?? Grid
}
</script>

<template>
  <aside class="workstation-sidebar" aria-label="主导航">
    <div class="brand-panel sidebar-brand">
      <div class="brand-mark">C</div>
      <div class="brand-copy">
        <strong>CTpath</strong>
        <span>慢病辅助诊疗业务系统</span>
      </div>
    </div>

    <div class="sidebar-session-card">
      <span class="workspace-status-pill">{{ sidebarMeta.mode }}</span>
      <div class="sidebar-user">
        <div class="sidebar-avatar">{{ doctor.name.slice(-1) }}</div>
        <div>
          <strong>{{ sidebarMeta.identity }}</strong>
          <p>{{ sidebarMeta.department }}</p>
        </div>
      </div>
      <div class="sidebar-counters">
        <article>
          <span>在管患者</span>
          <strong>{{ patientCount }}</strong>
        </article>
        <article>
          <span>待随访</span>
          <strong>{{ followupCount }}</strong>
        </article>
      </div>
    </div>

    <nav class="sidebar-nav">
      <button
        v-for="item in navItems"
        :key="item.section"
        class="nav-item stitch-nav-item"
        :class="{ active: item.section === activeSection }"
        type="button"
        @click="emit('select', item.section)"
      >
        <span class="nav-item-icon">
          <el-icon><component :is="iconFor(item.section)" /></el-icon>
        </span>
        <span>{{ labelFor(item.section) }}</span>
      </button>
    </nav>

    <div class="sidebar-footer">
      <button class="sidebar-button ghost sidebar-logout" type="button" @click="emit('logout')">
        <el-icon><SwitchButton /></el-icon>
        <span>退出登录</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar-brand {
  padding: 8px 12px 0;
}

.brand-copy {
  display: grid;
  gap: 4px;
}

.brand-copy strong {
  font-family: var(--ws-font-headline);
  font-size: 28px;
  letter-spacing: 0.12em;
  color: var(--ws-primary);
}

.brand-copy span {
  color: rgba(24, 28, 29, 0.78);
  font-family: var(--ws-font-headline);
  font-size: 13px;
  letter-spacing: 0.04em;
}

.brand-mark {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--ws-primary), var(--ws-primary-container));
}

.sidebar-session-card {
  display: grid;
  gap: 18px;
  padding: 0 12px;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar-avatar {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: rgba(207, 230, 242, 0.7);
  color: var(--ws-primary);
  font-family: var(--ws-font-headline);
  font-size: 22px;
  font-weight: 700;
}

.sidebar-user strong {
  display: block;
  font-family: var(--ws-font-headline);
  font-size: 18px;
}

.sidebar-user p {
  margin: 4px 0 0;
  color: rgba(63, 72, 73, 0.74);
}

.sidebar-counters {
  display: grid;
  gap: 10px;
}

.sidebar-counters article {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.65);
  box-shadow: inset 0 0 0 1px rgba(190, 200, 201, 0.6);
}

.sidebar-counters span {
  color: rgba(24, 28, 29, 0.68);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.sidebar-counters strong {
  font-family: var(--ws-font-headline);
  font-size: 26px;
  color: var(--ws-primary);
}

.sidebar-nav {
  display: grid;
  gap: 8px;
  align-content: start;
}

.stitch-nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 58px;
  padding: 0 18px;
  border-radius: 0;
  color: rgba(24, 28, 29, 0.62);
  font-family: var(--ws-font-headline);
  font-size: 15px;
  font-weight: 600;
}

.stitch-nav-item:hover,
.stitch-nav-item.active {
  background: rgba(255, 255, 255, 0.72);
  color: var(--ws-primary);
}

.stitch-nav-item.active::after {
  content: '';
  position: absolute;
  top: 8px;
  right: 0;
  bottom: 8px;
  width: 4px;
  border-radius: 999px;
  background: linear-gradient(180deg, var(--ws-primary), var(--ws-primary-container));
}

.nav-item-icon {
  display: inline-grid;
  place-items: center;
  width: 28px;
  color: currentColor;
  font-size: 18px;
}

.sidebar-footer {
  display: grid;
  align-content: end;
}

.sidebar-logout {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 50px;
  color: rgba(24, 28, 29, 0.72);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: inset 0 0 0 1px rgba(190, 200, 201, 0.72);
}

@media (max-width: 1080px) {
  .sidebar-session-card,
  .sidebar-footer {
    padding: 0;
  }
}
</style>
