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
  'model-operations': '模型运营台',
  'training-center': '训练中心',
  governance: '治理看板',
  'data-quality': '数据质量',
  system: '系统中心',
}

const bannerConfig = computed(() => {
  if (props.doctor.role === 'nurse') {
    return {
      eyebrow: '随访工作台',
      title: '护士随访工作台',
      description: '聚焦待随访患者、联系记录和流程推进，不混入训练中心或治理看板。',
      role: '护士',
    }
  }

  if (props.doctor.role === 'archivist') {
    return {
      eyebrow: '档案治理',
      title: '患者档案与治理工作台',
      description: '聚焦档案归集、信息补全、电子附件和治理动作，保持与临床主流程边界清晰。',
      role: '档案员',
    }
  }

  return {
    eyebrow: '临床工作台',
    title: '医生慢病辅助诊疗工作台',
    description: '聚焦待处理患者、风险提示、真实预测入口和随访闭环，不把模型治理和训练堆进首页。',
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
