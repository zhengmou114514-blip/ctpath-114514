<script setup lang="ts">
import type { DoctorUser, HealthResponse } from '../services/types'
import { sectionLabel } from '../config/workspaceMenu'
import type { AppSection } from '../types/workspace'

defineProps<{
  doctor: DoctorUser
  section: AppSection
  health: HealthResponse | null
}>()

function roleLabel(role: DoctorUser['role']) {
  if (role === 'archivist') return '档案员'
  if (role === 'nurse') return '护士'
  return '医生'
}
</script>

<template>
  <section class="workspace-topbar card">
    <div class="workspace-topbar-main">
      <p class="eyebrow">医疗工作台</p>
      <strong class="page-title">{{ sectionLabel(section) }}</strong>
      <small class="page-subtitle">
        {{ doctor.department }}
        <span class="role-tag" :class="`role-tag-${doctor.role}`">{{ roleLabel(doctor.role) }}</span>
      </small>
    </div>

    <div class="workspace-topbar-status">
      <span class="workspace-status-pill">系统状态：{{ health?.status ?? '未知' }}</span>
      <span class="workspace-status-pill">运行模式：{{ health?.mode ?? '未知' }}</span>
      <span class="workspace-status-pill">模型服务：{{ health?.model_available ? '可用' : '不可用' }}</span>
    </div>
  </section>
</template>
