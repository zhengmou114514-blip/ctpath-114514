<script setup lang="ts">
import type { DoctorUser, HealthResponse } from '../services/types'
import type { AppSection } from './AppSidebar.vue'

defineProps<{
  doctor: DoctorUser
  section: AppSection
  health: HealthResponse | null
}>()

function sectionLabel(section: AppSection) {
  if (section === 'archive') return '档案治理域'
  if (section === 'tasks') return '随访协同域'
  if (section === 'governance') return '治理中心'
  return '临床工作域'
}

function roleLabel(role: DoctorUser['role']) {
  if (role === 'archivist') return '档案员'
  if (role === 'nurse') return '护士 / 随访管理'
  return '医生'
}
</script>

<template>
  <section class="workspace-topbar card">
    <div class="workspace-topbar-main">
      <p class="eyebrow">Workspace</p>
      <strong>{{ sectionLabel(section) }}</strong>
      <small>{{ doctor.department }} / {{ roleLabel(doctor.role) }}</small>
    </div>

    <div class="workspace-topbar-status">
      <span class="workspace-status-pill">系统：{{ health?.status ?? 'unknown' }}</span>
      <span class="workspace-status-pill">模式：{{ health?.mode ?? 'unknown' }}</span>
      <span class="workspace-status-pill">
        模型：{{ health?.model_available ? '可用' : '回退模式' }}
      </span>
    </div>
  </section>
</template>
