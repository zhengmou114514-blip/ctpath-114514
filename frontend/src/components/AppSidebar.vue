<script setup lang="ts">
import { computed } from 'vue'
import type { DoctorUser, HealthResponse } from '../services/types'

export type AppSection = 'doctor' | 'archive' | 'tasks' | 'governance'

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

const visibleSections = computed<Array<{ key: AppSection; label: string; description: string }>>(() => {
  if (props.doctor.role === 'archivist') {
    return [
      {
        key: 'archive',
        label: '档案治理台',
        description: '建档、MRN 维护、知情同意核对、资料补录与档案质控。',
      },
      {
        key: 'governance',
        label: '治理中心',
        description: '查看系统状态、主索引治理、模块目录与医院化改造进展。',
      },
    ]
  }

  if (props.doctor.role === 'nurse') {
    return [
      {
        key: 'tasks',
        label: '随访工作台',
        description: '电话随访、联系记录、复联提醒与移动端协同录入。',
      },
    ]
  }

  return [
    {
      key: 'doctor',
      label: '临床工作台',
      description: '风险研判、预测建议、门诊任务与临床工作流。',
    },
    {
      key: 'archive',
      label: '档案联查台',
      description: '患者档案、结构化事件、病历补录与主数据联查。',
    },
    {
      key: 'tasks',
      label: '随访协同台',
      description: '随访任务、联系结果、流程状态与门诊协作闭环。',
    },
    {
      key: 'governance',
      label: '治理中心',
      description: '模块治理、系统状态、模型能力与主索引治理看板。',
    },
  ]
})

const roleLabel = computed(() => {
  if (props.doctor.role === 'archivist') return '档案员'
  if (props.doctor.role === 'nurse') return '护士 / 随访管理'
  return '医生'
})

const roleFocus = computed(() => {
  if (props.doctor.role === 'archivist') {
    return '重点关注患者主索引、MRN、知情同意、建档来源与资料完整性。'
  }
  if (props.doctor.role === 'nurse') {
    return '重点关注今日随访执行、联系结果登记、重点患者复联与提醒。'
  }
  return '重点关注临床评估、风险研判、预测建议、档案联查与门诊任务处置。'
})

const roleThemeClass = computed(() => `sidebar-role-${props.doctor.role}`)
</script>

<template>
  <aside class="sidebar-shell" :class="roleThemeClass">
    <div class="brand-panel">
      <div class="brand-mark">CT</div>
      <div>
        <p class="eyebrow inverse">Hospital HIS Prototype</p>
        <strong>慢病医院化协同系统</strong>
      </div>
    </div>

    <section class="sidebar-card doctor-panel">
      <span class="sidebar-label">{{ props.doctor.department }}</span>
      <strong>{{ props.doctor.name }} / {{ props.doctor.title }}</strong>
      <small>当前岗位：{{ roleLabel }}</small>
      <small>{{ roleFocus }}</small>
    </section>

    <section class="sidebar-card sidebar-kpi-card">
      <div class="sidebar-kpi-row">
        <span>患者总量</span>
        <strong>{{ props.patientCount }}</strong>
      </div>
      <div class="sidebar-kpi-row">
        <span>随访任务</span>
        <strong>{{ props.followupCount }}</strong>
      </div>
      <div class="sidebar-kpi-row">
        <span>系统模式</span>
        <strong>{{ props.health?.mode ?? 'unknown' }}</strong>
      </div>
    </section>

    <nav class="sidebar-nav">
      <button
        v-for="section in visibleSections"
        :key="section.key"
        class="nav-item nav-item-detailed"
        :class="{ active: section.key === props.activeSection }"
        @click="emit('select', section.key)"
      >
        <strong>{{ section.label }}</strong>
        <span>{{ section.description }}</span>
      </button>
    </nav>

    <div class="sidebar-actions">
      <button class="sidebar-button ghost" @click="emit('logout')">退出登录</button>
    </div>
  </aside>
</template>
