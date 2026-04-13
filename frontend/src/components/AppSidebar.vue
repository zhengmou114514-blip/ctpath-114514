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

    <!-- 优化后的医生信息区域 -->
    <section class="sidebar-user-section">
      <div class="user-info">
        <span class="user-department">{{ props.doctor.department }}</span>
        <strong class="user-name">{{ props.doctor.name }}</strong>
        <span class="user-title">{{ props.doctor.title }}</span>
      </div>
      <div class="user-meta">
        <span class="role-tag" :class="`role-tag-${props.doctor.role}`">{{ roleLabel }}</span>
        <span class="current-module">当前模块：{{ sectionLabel(props.activeSection) }}</span>
      </div>
    </section>

    <!-- 重构后的统计指标区域：参考门诊队列样式 -->
    <section class="sidebar-stats-section">
      <header class="stats-header">
        <p class="eyebrow">统计概览</p>
        <h3>关键指标</h3>
      </header>
      
      <div class="stats-grid">
        <!-- 患者总数 -->
        <div class="stat-item">
          <span class="stat-label">患者总数</span>
          <strong class="stat-value">{{ props.patientCount }}</strong>
        </div>
        
        <!-- 随访任务 -->
        <div class="stat-item">
          <span class="stat-label">随访任务</span>
          <strong class="stat-value">{{ props.followupCount }}</strong>
        </div>
        
        <!-- 系统模式 -->
        <div class="stat-item">
          <span class="stat-label">系统模式</span>
          <span class="stat-mode">{{ props.health?.mode ?? '未知' }}</span>
        </div>
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
