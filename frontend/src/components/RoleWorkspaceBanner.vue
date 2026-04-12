<script setup lang="ts">
import { computed } from 'vue'
import type { DoctorUser } from '../services/types'
import { sectionLabel } from '../config/workspaceMenu'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  doctor: DoctorUser
  section: AppSection
  patientCount: number
  followupCount: number
}>()

const bannerConfig = computed(() => {
  if (props.doctor.role === 'nurse') {
    return {
      eyebrow: '护理工作区',
      title: '随访与联络协同',
      description: '聚焦随访任务进度、联系结果与患者流转，保障连续护理闭环。',
    }
  }

  if (props.doctor.role === 'archivist') {
    return {
      eyebrow: '档案工作区',
      title: '档案与数据质量管理',
      description: '聚焦档案完整性、记录一致性与治理留痕，保障病历质量可追溯。',
    }
  }

  return {
    eyebrow: '医生工作区',
    title: '慢病门诊诊疗工作台',
    description: '结合病程轨迹、模型证据与处置建议，支持门诊诊疗决策。',
  }
})

const roleLabel = computed(() => {
  if (props.doctor.role === 'archivist') return '档案员'
  if (props.doctor.role === 'nurse') return '护士'
  return '医生'
})
</script>

<template>
  <section class="role-banner card">
    <div>
      <p class="eyebrow">{{ bannerConfig.eyebrow }}</p>
      <h2 class="page-title">{{ bannerConfig.title }}</h2>
      <p class="role-banner-copy page-description">{{ bannerConfig.description }}</p>
      <span class="role-tag" :class="`role-tag-${props.doctor.role}`">{{ roleLabel }}</span>
    </div>

    <div class="role-banner-chips">
      <article class="role-banner-chip">
        <span>当前模块</span>
        <strong>{{ sectionLabel(props.section) }}</strong>
      </article>
      <article class="role-banner-chip">
        <span>患者总数</span>
        <strong>{{ props.patientCount }}</strong>
      </article>
      <article class="role-banner-chip">
        <span>随访任务</span>
        <strong>{{ props.followupCount }}</strong>
      </article>
    </div>
  </section>
</template>
