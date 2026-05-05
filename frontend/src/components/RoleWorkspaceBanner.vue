<script setup lang="ts">
import { computed } from 'vue'
import { allowedSectionsForRole, sectionLabel } from '../config/workspaceMenu'
import type { DoctorUser } from '../services/types'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  doctor: DoctorUser
  section: AppSection
  patientCount: number
  followupCount: number
}>()

const sectionLabels: Partial<Record<AppSection, string>> = {
  doctor: '医生工作台',
  archive: '患者档案',
  emr: '电子病历',
  pharmacy: '药房药库',
  'drug-management': '药品目录',
  'drug-permission-management': '药品权限',
  tasks: '随访任务',
  contacts: '联系记录',
  flow: '随访流程',
  coordination: '医护协调',
  insights: '模型洞察',
  governance: '治理看板',
  'data-quality': '数据质量',
  system: '系统中心',
}

const bannerConfig = computed(() => {
  if (props.doctor.role === 'nurse') {
    return {
      eyebrow: '随访工作台',
      title: '护士随访工作台',
      description: '待随访患者、联系记录、病程流转和协同事项。',
      role: '护士',
    }
  }

  if (props.doctor.role === 'archivist') {
    return {
      eyebrow: '档案治理',
      title: '患者档案与治理工作台',
      description: '聚焦档案归集、信息补全、电子附件和数据质量，保持与临床主流程边界清晰。',
      role: '档案员',
    }
  }

  if (props.doctor.role === 'pharmacist') {
    return {
      eyebrow: '药事工作台',
      title: '药房与药品管理工作台',
      description: '药房库存、药品目录、处方审核和药品权限。',
      role: '药师',
    }
  }

  if (props.doctor.role === 'admin') {
    return {
      eyebrow: '系统管理',
      title: '管理员工作台',
      description: '聚焦多角色入口、模型治理、数据质量和系统状态，作为全局协调与管理中心。',
      role: '管理员',
    }
  }

  return {
    eyebrow: '临床工作台',
    title: '医生慢病辅助诊疗工作台',
    description: '待处理患者、风险提示、预测入口和随访闭环。',
    role: '医生',
  }
})

const roleSections = computed(() => allowedSectionsForRole(props.doctor.role))
const roleSectionLabels = computed(() => roleSections.value.slice(0, 5).map((item) => sectionLabel(item)))
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
        <span>可见模块</span>
        <strong>{{ roleSections.length }} 个</strong>
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

    <div class="role-banner-links">
      <span class="role-banner-link-label">该角色常用入口</span>
      <div class="role-banner-link-list">
        <span v-for="item in roleSectionLabels" :key="item" class="role-banner-link-chip">{{ item }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.role-banner-links {
  display: grid;
  gap: 10px;
}

.role-banner-link-label {
  color: rgba(24, 28, 29, 0.64);
  font-family: var(--ws-font-headline);
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.role-banner-link-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.role-banner-link-chip {
  border: 1px solid rgba(190, 200, 201, 0.68);
  border-radius: 999px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.6);
  color: rgba(24, 28, 29, 0.84);
  font-size: 13px;
}
</style>
