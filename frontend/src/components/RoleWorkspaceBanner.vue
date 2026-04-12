<script setup lang="ts">
import { computed } from 'vue'
import type { DoctorUser } from '../services/types'
import type { AppSection } from './AppSidebar.vue'

const props = defineProps<{
  doctor: DoctorUser
  section: AppSection
  patientCount: number
  followupCount: number
}>()

function sectionLabel(section: AppSection) {
  if (section === 'archive') return '档案联查'
  if (section === 'tasks') return '随访协同'
  if (section === 'governance') return '治理中心'
  return '临床工作台'
}

const bannerConfig = computed(() => {
  if (props.doctor.role === 'nurse') {
    return {
      theme: 'nurse',
      eyebrow: 'Nurse Station',
      title: '护理与随访工作台',
      description: '聚焦今日待随访患者、联系记录、复联安排和执行闭环，避免与医生工作台混合。',
      chips: [
        { label: '当前模块', value: sectionLabel(props.section) },
        { label: '待处理随访', value: props.followupCount },
        { label: '岗位焦点', value: '联系结果 / 复联提醒' },
      ],
    }
  }

  if (props.doctor.role === 'archivist') {
    return {
      theme: 'archivist',
      eyebrow: 'Archive Desk',
      title: '档案治理与主索引工作台',
      description: '聚焦患者主索引、建档完整性、导入治理、MRN 维护和档案质控，更接近病案管理场景。',
      chips: [
        { label: '当前模块', value: sectionLabel(props.section) },
        { label: '档案总量', value: props.patientCount },
        { label: '岗位焦点', value: 'MRN / 同意状态 / 资料治理' },
      ],
    }
  }

  return {
    theme: 'doctor',
    eyebrow: 'Doctor Console',
    title: '临床评估与门诊协同工作台',
    description: '保留临床评估、风险查看、预测建议、门诊任务与档案联查，同时补充治理中心用于系统总览。',
    chips: [
      { label: '当前模块', value: sectionLabel(props.section) },
      { label: '患者总量', value: props.patientCount },
      { label: '随访协同', value: props.followupCount },
    ],
  }
})
</script>

<template>
  <section class="role-banner card" :class="`role-banner-${bannerConfig.theme}`">
    <div>
      <p class="eyebrow">{{ bannerConfig.eyebrow }}</p>
      <h2>{{ bannerConfig.title }}</h2>
      <p class="role-banner-copy">{{ bannerConfig.description }}</p>
    </div>

    <div class="role-banner-chips">
      <article
        v-for="chip in bannerConfig.chips"
        :key="chip.label"
        class="role-banner-chip"
      >
        <span>{{ chip.label }}</span>
        <strong>{{ chip.value }}</strong>
      </article>
    </div>
  </section>
</template>
