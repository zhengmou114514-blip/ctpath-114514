<script setup lang="ts">
import { computed } from 'vue'
import {
  Document,
  FolderOpened,
  Grid,
  Lock,
  Memo,
  Operation,
  SetUp,
  SwitchButton,
  Tickets,
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

const iconMap: Partial<Record<AppSection, object>> = {
  doctor: Grid,
  archive: Document,
  emr: Document,
  tasks: Memo,
  contacts: Operation,
  flow: FolderOpened,
  pharmacy: Tickets,
  coordination: Operation,
  insights: Grid,
  governance: FolderOpened,
  'data-quality': Document,
  'drug-management': Tickets,
  'drug-permission-management': Tickets,
  'model-dashboard': Grid,
  'training-center': Memo,
  'model-operations': Operation,
  'role-workspaces': Lock,
  system: SetUp,
}

const navItems = computed(() => ROLE_WORKSPACE_MENUS[props.doctor.role] ?? [])
const modeLabel = computed(() => `${String(props.health?.mode ?? 'demo').toUpperCase()} 模式`)
const modelLabel = computed(() => (props.health?.model_available ? '模型可用' : '模型降级'))
</script>

<template>
  <aside class="stitch-sidenav">
    <div class="sidenav-brand">
      <div class="brand-mark">
        <span>CT</span>
      </div>
      <div>
        <h1>慢性病辅疗</h1>
        <p>临床工作站</p>
      </div>
    </div>

    <div class="sidenav-meta">
      <span class="meta-pill">{{ modeLabel }}</span>
      <span class="meta-pill meta-pill-muted">{{ modelLabel }}</span>

      <div class="meta-user">
        <div class="meta-avatar">{{ doctor.name.slice(-1) }}</div>
        <div>
          <strong>{{ doctor.name }}</strong>
          <small>{{ doctor.department || '慢病管理中心' }}</small>
        </div>
      </div>

      <div class="meta-stats">
        <span>患者 {{ patientCount }}</span>
        <span>随访 {{ followupCount }}</span>
      </div>
    </div>

    <nav class="sidenav-menu">
      <button
        v-for="item in navItems"
        :key="item.section"
        class="sidenav-item"
        :class="{ active: item.section === activeSection }"
        type="button"
        @click="emit('select', item.section)"
      >
        <el-icon><component :is="iconMap[item.section]" /></el-icon>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <button class="sidenav-logout" type="button" @click="emit('logout')">
      <el-icon><SwitchButton /></el-icon>
      <span>退出登录</span>
    </button>
  </aside>
</template>

<style scoped>
.stitch-sidenav {
  position: sticky;
  top: 0;
  display: flex;
  min-height: 100vh;
  width: 256px;
  flex-direction: column;
  gap: 24px;
  padding: 24px 16px;
  border-right: 1px solid rgba(191, 200, 200, 0.7);
  background: #f5f7f8;
}

.sidenav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 12px;
}

.brand-mark {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border-radius: 12px;
  background: #004d4d;
  color: #fff;
  font-family: var(--ws-font-headline);
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.sidenav-brand h1 {
  margin: 0;
  color: #003434;
  font-family: var(--ws-font-headline);
  font-size: 20px;
  font-weight: 800;
}

.sidenav-brand p {
  margin: 4px 0 0;
  color: #526772;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.sidenav-meta {
  display: grid;
  gap: 12px;
  padding: 0 12px;
}

.meta-pill {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  background: #e8eeef;
  padding: 6px 12px;
  color: #3f4848;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.meta-pill-muted {
  background: rgba(0, 89, 187, 0.1);
  color: #0059bb;
}

.meta-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-avatar {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 999px;
  background: #005c61;
  color: #fff;
  font-family: var(--ws-font-headline);
  font-size: 18px;
  font-weight: 700;
}

.meta-user strong {
  display: block;
  color: #181c1e;
}

.meta-user small {
  color: #526772;
}

.meta-stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  color: #526772;
  font-size: 12px;
  font-weight: 700;
}

.sidenav-menu {
  display: grid;
  gap: 4px;
}

.sidenav-item {
  position: relative;
  display: flex;
  min-height: 48px;
  align-items: center;
  gap: 14px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  padding: 0 16px;
  color: #3f4848;
  font-family: var(--ws-font-headline);
  font-size: 14px;
  font-weight: 700;
  text-align: left;
}

.sidenav-item.active {
  background: rgba(235, 238, 240, 0.92);
  color: #003434;
}

.sidenav-item.active::after {
  content: '';
  position: absolute;
  top: 8px;
  right: -2px;
  bottom: 8px;
  width: 4px;
  border-radius: 999px;
  background: #003434;
}

.sidenav-logout {
  margin-top: auto;
  display: flex;
  min-height: 46px;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 0;
  border-radius: 12px;
  background: #f1f4f6;
  color: #3f4848;
  font-weight: 700;
}
</style>
