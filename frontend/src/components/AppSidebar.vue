<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Document,
  FolderOpened,
  Grid,
  Memo,
  Operation,
  SetUp,
  SwitchButton,
  Tickets,
} from '@element-plus/icons-vue'
import { roleSystemForRole } from '../config/workspaceMenu'
import { visibleNavigationGroups, type NavigationItem } from '../config/navigation'
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

const route = useRoute()
const router = useRouter()

const iconMap: Record<string, object> = {
  Grid,
  Document,
  Memo,
  Operation,
  Tickets,
  SetUp,
  FolderOpened,
}

const navigation = computed(() => visibleNavigationGroups(props.doctor.role))
const currentSystem = computed(() => roleSystemForRole(props.doctor.role))
const modeLabel = computed(() => (props.health?.status === 'ok' ? '业务运行中' : '服务连接中'))

function isActive(item: NavigationItem) {
  if (!item.path) return false
  const basePath = item.path.split('?')[0]
  return route.path === basePath || route.fullPath === item.path
}

function openItem(item: NavigationItem) {
  if (item.section) {
    emit('select', item.section)
  }
  if (item.path) {
    void router.push(item.path)
  }
}
</script>

<template>
  <aside class="stitch-sidenav">
    <div class="sidenav-brand">
      <div class="brand-mark">
        <span>H</span>
      </div>
      <div>
        <h1>{{ currentSystem.title }}</h1>
        <p>{{ currentSystem.subtitle }}</p>
      </div>
    </div>

    <div class="sidenav-meta">
      <div class="meta-user">
        <div class="meta-avatar">{{ doctor.name.slice(-1) }}</div>
        <div>
          <strong>{{ doctor.name }}</strong>
          <small>{{ doctor.title }} / {{ doctor.department || '慢病管理中心' }}</small>
        </div>
      </div>

      <span class="meta-pill">{{ modeLabel }}</span>

      <div class="meta-stats">
        <span>患者 {{ patientCount }}</span>
        <span>随访 {{ followupCount }}</span>
      </div>
    </div>

    <nav class="sidenav-menu">
      <section v-for="group in navigation" :key="group.title" class="sidenav-group">
        <div class="sidenav-group-head">
          <el-icon><component :is="iconMap[group.icon || 'Grid']" /></el-icon>
          <p>{{ group.title }}</p>
        </div>
        <button
          v-for="item in group.children"
          :key="`${group.title}-${item.title}-${item.path}`"
          class="sidenav-item"
          :class="{ active: isActive(item) }"
          type="button"
          @click="openItem(item)"
        >
          <span>{{ item.title }}</span>
        </button>
      </section>
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
  width: 282px;
  flex-direction: column;
  gap: 14px;
  padding: 14px 10px;
  border-right: 1px solid rgba(191, 200, 200, 0.7);
  background: #f5f7f8;
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.82);
}

.sidenav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 58px;
  padding: 8px 10px;
  border: 1px solid #d8e0e2;
  border-radius: 6px;
  background: #ffffff;
}

.brand-mark {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #003434, #155e75);
  color: #fff;
  font-family: var(--ws-font-headline);
  font-size: 18px;
  font-weight: 800;
}

.sidenav-brand h1 {
  margin: 0;
  color: #003434;
  font-family: var(--ws-font-headline);
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0;
}

.sidenav-brand p {
  margin: 2px 0 0;
  color: #526772;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.sidenav-meta {
  display: grid;
  gap: 8px;
  padding: 10px;
  border: 1px solid #d8e0e2;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.8);
}

.meta-pill {
  display: inline-flex;
  width: fit-content;
  border: 1px solid #d5dde0;
  border-radius: 999px;
  background: #e8eeef;
  padding: 3px 7px;
  color: #3f4848;
  font-size: 11px;
  font-weight: 700;
}

.meta-user {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-avatar {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  border-radius: 50%;
  background: #005c61;
  color: #fff;
  font-family: var(--ws-font-headline);
  font-size: 16px;
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
  gap: 10px;
  overflow: auto;
}

.sidenav-group {
  display: grid;
  gap: 2px;
  border: 1px solid #d8e0e2;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.68);
  padding: 6px;
}

.sidenav-group-head {
  display: flex;
  align-items: center;
  gap: 7px;
  border-bottom: 1px solid #e1e7e9;
  padding: 2px 4px 5px;
  color: #003434;
}

.sidenav-group-head p {
  margin: 0;
  color: #003434;
  font-size: 12px;
  font-weight: 800;
}

.sidenav-item {
  position: relative;
  display: flex;
  min-height: 32px;
  align-items: center;
  border: 0;
  border-radius: 3px;
  background: transparent;
  padding: 0 8px 0 24px;
  color: #3f4848;
  font-family: var(--ws-font-headline);
  font-size: 13px;
  font-weight: 700;
  text-align: left;
}

.sidenav-item:hover {
  background: #e8eeef;
}

.sidenav-item.active {
  background: #003434;
  color: #fff;
}

.sidenav-item.active::after {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: #00a9a5;
}

.sidenav-logout {
  margin-top: auto;
  display: flex;
  min-height: 36px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid #d5dde0;
  border-radius: 6px;
  background: #f1f4f6;
  color: #3f4848;
  font-weight: 700;
}
</style>
