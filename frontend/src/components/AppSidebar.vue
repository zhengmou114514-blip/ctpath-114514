<script setup lang="ts">
import { computed } from 'vue'
import {
  DataAnalysis,
  Document,
  FolderOpened,
  Grid,
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

const iconMap: Record<AppSection, object> = {
  doctor: Grid,
  archive: Document,
  tasks: Memo,
  contacts: Operation,
  flow: FolderOpened,
  insights: DataAnalysis,
  'model-dashboard': DataAnalysis,
  'model-operations': DataAnalysis,
  'training-center': DataAnalysis,
  governance: FolderOpened,
  'data-quality': Document,
  'drug-management': Tickets,
  'drug-permission-management': Tickets,
  system: SetUp,
}

const navItems = computed(() => ROLE_WORKSPACE_MENUS[props.doctor.role] ?? [])
const modeLabel = computed(() => `${String(props.health?.mode ?? 'demo').toUpperCase()} / MYSQL`)
</script>

<template>
  <aside class="stitch-sidenav">
    <div class="sidenav-brand">
      <h1>CTPATH</h1>
      <p>慢病辅助诊疗工作站</p>
    </div>

    <div class="sidenav-meta">
      <span class="meta-pill">{{ modeLabel }}</span>
      <div class="meta-user">
        <div class="meta-avatar">{{ doctor.name.slice(-1) }}</div>
        <div>
          <strong>{{ doctor.name }}</strong>
          <small>{{ doctor.department }}</small>
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
  width: 288px;
  flex-direction: column;
  gap: 24px;
  padding: 32px 16px;
  background: #ebeeef;
}

.sidenav-brand {
  padding: 0 16px;
}

.sidenav-brand h1 {
  margin: 0;
  color: #004347;
  font-family: var(--ws-font-headline);
  font-size: 22px;
  font-weight: 900;
  letter-spacing: 0.2em;
}

.sidenav-brand p {
  margin: 6px 0 0;
  color: #004347;
  font-family: var(--ws-font-headline);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.sidenav-meta {
  display: grid;
  gap: 14px;
  padding: 0 16px;
}

.meta-pill {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  background: #f1f4f5;
  padding: 6px 12px;
  color: #3f4849;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.meta-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-avatar {
  display: grid;
  height: 42px;
  width: 42px;
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
  color: #181c1d;
}

.meta-user small {
  color: #526772;
}

.meta-stats {
  display: flex;
  gap: 12px;
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
  align-items: center;
  gap: 14px;
  min-height: 52px;
  border: 0;
  background: transparent;
  padding: 0 20px;
  color: #3f4849;
  font-family: var(--ws-font-headline);
  font-size: 14px;
  font-weight: 700;
  text-align: left;
}

.sidenav-item.active {
  background: rgba(241, 244, 245, 0.8);
  color: #004347;
}

.sidenav-item.active::after {
  content: '';
  position: absolute;
  top: 8px;
  right: 0;
  bottom: 8px;
  width: 4px;
  background: #004347;
}

.sidenav-logout {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 46px;
  border: 0;
  border-radius: 10px;
  background: #f1f4f5;
  color: #3f4849;
  font-weight: 700;
}
</style>
