<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
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
  selectedPatientId?: string
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
const currentPatientId = computed(() => {
  const routePatientId = route.params.patientId
  const storedPatientId =
    typeof window !== 'undefined' ? window.sessionStorage.getItem('ctpath:selectedPatientId') || '' : ''
  return typeof routePatientId === 'string' && routePatientId
    ? routePatientId
    : props.selectedPatientId || storedPatientId
})

function isActive(item: NavigationItem) {
  if (item.routeName) {
    const sameRoute = route.name === item.routeName
    const sameQuery = Object.entries(item.query ?? {}).every(([key, value]) => route.query[key] === value)
    return sameRoute && sameQuery
  }
  if (!item.path) return false
  const basePath = item.path.split('?')[0]
  return route.path === basePath || route.fullPath === item.path
}

function openItem(item: NavigationItem) {
  if (item.requirePatient && !currentPatientId.value) {
    ElMessage.info('请先选择患者')
    void router.push({ name: 'doctor-patients' })
    return
  }

  if (item.routeName) {
    void router.push({
      name: item.routeName,
      params: item.requirePatient ? { patientId: currentPatientId.value } : undefined,
      query: item.query,
    })
    return
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
          :key="`${group.title}-${item.title}-${item.routeName || item.path}`"
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
  width: var(--ws-sidebar-width);
  flex-direction: column;
  gap: 12px;
  padding: 16px 12px;
  border-right: 1px solid var(--ws-outline);
  background: #ffffff;
  box-shadow: 4px 0 20px rgba(23, 32, 51, 0.04);
}

.sidenav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 56px;
  padding: 8px;
  border: 1px solid var(--ws-outline);
  border-radius: 12px;
  background: #f8fafc;
}

.brand-mark {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 10px;
  background: #1d4ed8;
  color: #fff;
  font-family: var(--ws-font-headline);
  font-size: 18px;
  font-weight: 800;
}

.sidenav-brand h1 {
  margin: 0;
  color: #172033;
  font-family: var(--ws-font-headline);
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0;
}

.sidenav-brand p {
  margin: 2px 0 0;
  color: #64748b;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.sidenav-meta {
  display: grid;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--ws-outline);
  border-radius: 12px;
  background: #ffffff;
}

.meta-pill {
  display: inline-flex;
  width: fit-content;
  border: 1px solid var(--ws-outline);
  border-radius: 999px;
  background: #eff6ff;
  padding: 3px 8px;
  color: #1d4ed8;
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
  background: #1d4ed8;
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
  color: #64748b;
}

.meta-stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.sidenav-menu {
  display: grid;
  gap: 8px;
  overflow: auto;
}

.sidenav-group {
  display: grid;
  gap: 2px;
  border: 0;
  border-radius: 0;
  background: transparent;
  padding: 2px 0;
}

.sidenav-group-head {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 8px 5px;
  color: #64748b;
}

.sidenav-group-head p {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  font-weight: 800;
}

.sidenav-item {
  position: relative;
  display: flex;
  min-height: 36px;
  align-items: center;
  border: 0;
  border-radius: 10px;
  background: transparent;
  padding: 0 10px 0 28px;
  color: #475569;
  font-family: var(--ws-font-headline);
  font-size: 13px;
  font-weight: 700;
  text-align: left;
}

.sidenav-item:hover {
  background: #f1f5f9;
}

.sidenav-item.active {
  background: #eff6ff;
  box-shadow: inset 3px 0 0 #2563eb;
  color: #1d4ed8;
}

.sidenav-item.active span {
  color: #1d4ed8;
}

.sidenav-item.active {
  color: #1d4ed8;
}

.sidenav-item.active::after {
  content: none;
}

.sidenav-logout {
  margin-top: auto;
  display: flex;
  min-height: 36px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--ws-outline);
  border-radius: 10px;
  background: #f8fafc;
  color: #475569;
  font-weight: 700;
}
</style>
