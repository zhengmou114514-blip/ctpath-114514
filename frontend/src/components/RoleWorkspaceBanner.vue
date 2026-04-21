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
  'drug-management': '药品目录',
  'drug-permission-management': '药品权限',
  tasks: '随访任务',
  contacts: '联系记录',
  flow: '随访流程',
  insights: '模型洞察',
  'model-dashboard': '模型看板',
  'training-center': '训练中心',
  governance: '治理看板',
  'data-quality': '数据质量',
  system: '系统中心',
}

const bannerConfig = computed(() => {
  if (props.doctor.role === 'nurse') {
    return {
      eyebrow: '随访工作域',
      title: '护士随访工作台',
      description: '聚焦待随访任务、联系记录与流程推进，确保患者回访闭环能够稳定落地。',
      role: '护士',
    }
  }

  if (props.doctor.role === 'archivist') {
    return {
      eyebrow: '档案治理域',
      title: '患者档案与治理工作台',
      description: '聚焦档案主数据、建档状态、数据质量与治理巡检，不混入临床主流程。',
      role: '档案员',
    }
  }

  return {
    eyebrow: '临床工作域',
    title: '医生慢病工作台',
    description: '聚焦待处理患者、风险识别、预测触发与随访入口，服务慢病辅助诊疗主闭环。',
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
        <span>患者数</span>
        <strong>{{ patientCount }}</strong>
      </article>
      <article class="role-banner-chip">
        <span>随访任务</span>
        <strong>{{ followupCount }}</strong>
      </article>
    </div>
  </section>
</template>
