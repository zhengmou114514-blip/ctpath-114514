<script setup lang="ts">
import { computed } from 'vue'
import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  doctor: DoctorUser
  section: AppSection
  patientCount: number
  followupCount: number
}>()

const sectionLabels: Record<AppSection, string> = {
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

const bannerConfig = computed(() => {
  if (props.doctor.role === 'nurse') {
    return {
      eyebrow: '随访闭环',
      title: '护士随访工作台',
      description: '随访任务、联系记录、随访状态和下一次计划集中处理。',
      role: '护士',
    }
  }

  if (props.doctor.role === 'archivist') {
    return {
      eyebrow: '档案治理',
      title: '患者档案与治理工作区',
      description: '聚焦患者身份信息、建档状态、电子档案入口、缺失字段与冲突记录。',
      role: '档案员',
    }
  }

  return {
    eyebrow: '临床工作',
    title: '医生慢病辅助诊疗工作台',
    description: '待处理患者、风险摘要和主要临床动作集中处理。',
    role: '医生',
  }
})
</script>

<template>
  <section class="role-banner">
    <div class="role-banner-copy">
      <p class="eyebrow">{{ bannerConfig.eyebrow }}</p>
      <h2>{{ bannerConfig.title }}</h2>
      <p>{{ bannerConfig.description }}</p>
      <span class="role-tag" :class="`role-tag-${doctor.role}`">{{ bannerConfig.role }}</span>
    </div>

    <div class="role-banner-chips">
      <article class="role-banner-chip">
        <span>当前模块</span>
        <strong>{{ sectionLabels[section] }}</strong>
      </article>
      <article class="role-banner-chip">
        <span>患者档案</span>
        <strong>{{ patientCount }}</strong>
      </article>
      <article class="role-banner-chip">
        <span>随访任务</span>
        <strong>{{ followupCount }}</strong>
      </article>
    </div>
  </section>
</template>
