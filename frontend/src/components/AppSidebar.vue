<script setup lang="ts">
import { computed } from 'vue'
import { ROLE_WORKSPACE_MENUS, sectionLabel } from '../config/workspaceMenu'
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

const menus = computed(() => ROLE_WORKSPACE_MENUS[props.doctor.role])

const roleLabel = computed(() => {
  if (props.doctor.role === 'archivist') return '档案员'
  if (props.doctor.role === 'nurse') return '护士'
  return '医生'
})
</script>

<template>
  <aside class="sidebar-shell workstation-sidebar" :class="`sidebar-role-${props.doctor.role}`">
    <div class="brand-panel">
      <div class="brand-mark">HIS</div>
      <div>
        <p class="eyebrow inverse">门诊工作站</p>
        <strong>慢病管理信息系统</strong>
      </div>
    </div>

    <section class="sidebar-card doctor-panel">
      <span class="sidebar-label">{{ props.doctor.department }}</span>
      <strong>{{ props.doctor.name }} / {{ props.doctor.title }}</strong>
      <small>
        角色：
        <span class="role-tag" :class="`role-tag-${props.doctor.role}`">{{ roleLabel }}</span>
      </small>
      <small>当前模块：{{ sectionLabel(props.activeSection) }}</small>
    </section>

    <section class="sidebar-card sidebar-kpi-card">
      <div class="sidebar-kpi-row">
        <span>患者总数</span>
        <strong>{{ props.patientCount }}</strong>
      </div>
      <div class="sidebar-kpi-row">
        <span>随访任务</span>
        <strong>{{ props.followupCount }}</strong>
      </div>
      <div class="sidebar-kpi-row">
        <span>系统模式</span>
        <strong>{{ props.health?.mode ?? '未知' }}</strong>
      </div>
    </section>

    <nav class="sidebar-nav">
      <button
        v-for="item in menus"
        :key="item.section"
        class="nav-item nav-item-detailed"
        :class="{ active: item.section === props.activeSection }"
        @click="emit('select', item.section)"
      >
        <strong>{{ item.label }}</strong>
        <span>{{ item.description }}</span>
      </button>
    </nav>

    <div class="sidebar-actions">
      <button class="sidebar-button ghost" @click="emit('logout')">退出登录</button>
    </div>
  </aside>
</template>
