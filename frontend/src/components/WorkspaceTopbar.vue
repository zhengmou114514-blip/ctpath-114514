<script setup lang="ts">
import type { DoctorUser, HealthResponse } from '../services/types'
import type { AppSection } from '../types/workspace'

defineProps<{
  doctor: DoctorUser
  section: AppSection
  health: HealthResponse | null
  loading?: boolean
}>()

const sectionLabelMap: Record<AppSection, string> = {
  doctor: '医生工作台',
  archive: '患者档案',
  'drug-management': '药品管理',
  'drug-permission-management': '药品权限管理',
  tasks: '护士随访工作台',
  contacts: '联系记录',
  flow: '随访流转',
  insights: '模型洞察',
  'model-dashboard': '模型看板',
  governance: '治理中心',
  'data-quality': '数据质量',
  system: '系统状态',
}

const roleLabelMap: Record<DoctorUser['role'], string> = {
  doctor: '医生',
  nurse: '护士',
  archivist: '档案员',
}

function healthLabel(health: HealthResponse | null) {
  if (!health) return '未连接'
  if (health.status === 'ok') return '正常'
  return health.status
}

function modelLabel(health: HealthResponse | null) {
  if (!health) return '未知'
  if (health.model_available) return '可用'
  if (health.model_error) return '降级'
  return '不可用'
}
</script>

<template>
  <section class="workspace-topbar">
    <div class="workspace-topbar-main">
      <p class="eyebrow">慢病辅助诊疗业务系统</p>
      <strong class="page-title">{{ sectionLabelMap[section] }}</strong>
      <small class="page-subtitle">
        {{ doctor.department }} / {{ doctor.name }}
        <span class="role-tag" :class="`role-tag-${doctor.role}`">{{ roleLabelMap[doctor.role] }}</span>
      </small>
    </div>

    <div class="workspace-topbar-status">
      <span v-if="loading" class="workspace-status-pill status-info">加载中</span>
      <span class="workspace-status-pill">服务：{{ healthLabel(health) }}</span>
      <span class="workspace-status-pill">模式：{{ health?.mode ?? 'unknown' }}</span>
      <span
        class="workspace-status-pill"
        :class="{
          'status-success': health?.model_available,
          'status-warning': health && !health.model_available && health.model_error,
          'status-danger': health && !health.model_available && !health.model_error,
        }"
      >
        模型：{{ modelLabel(health) }}
      </span>
    </div>
  </section>
</template>
