<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { RouterLink } from 'vue-router'
import { Search, UserFilled } from '@element-plus/icons-vue'
import { roleSystemForRole, sectionLabel } from '../config/workspaceMenu'
import type { DoctorUser, HealthResponse } from '../services/types'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  doctor: DoctorUser
  section: AppSection
  health: HealthResponse | null
  loading?: boolean
}>()

const route = useRoute()

const placeholderMap: Partial<Record<AppSection, string>> = {
  doctor: '搜索待处理患者、档案号或风险标签',
  archive: '搜索患者姓名、档案号或联系方式',
  emr: '搜索患者姓名、病程记录或档案号',
  pharmacy: '搜索药品名称、剂型规格或当前用药',
  coordination: '搜索协同记录、负责人或下一步动作',
  tasks: '搜索随访患者、任务状态或负责人',
  contacts: '搜索联系记录、拨打结果或备注',
  flow: '搜索今日随访任务、状态或负责人',
  insights: '搜索当前患者预测结果、证据摘要或建议',
  governance: '搜索异常时间线、冲突记录或待补全档案',
  'role-workspaces': '搜索用户、角色或权限项',
  'data-quality': '搜索数据质量记录',
  'drug-management': '搜索药品名称、剂型规格或状态',
  'drug-permission-management': '搜索角色、药品范围或管制级别',
  'model-dashboard': '搜索模型版本、健康状态或调用记录',
  system: '搜索审计日志、操作人或异常记录',
}

const roleLabelMap: Record<DoctorUser['role'], string> = {
  doctor: '医生站',
  nurse: '护士站',
  pharmacist: '药房人员',
  archivist: '档案查看',
  admin: '管理员',
}

const currentSystem = computed(() => roleSystemForRole(props.doctor.role))
const serviceLabel = computed(() => (props.health?.status === 'ok' ? '业务服务正常' : '服务连接中'))
const breadcrumb = computed(() => {
  const routeBreadcrumb = route.meta.breadcrumb
  if (Array.isArray(routeBreadcrumb) && routeBreadcrumb.every((item) => typeof item === 'string')) {
    return routeBreadcrumb
  }
  return [props.doctor.department || '慢病管理门诊', roleLabelMap[props.doctor.role], sectionLabel(props.section)]
})

const homeRoute = computed(() => {
  if (props.doctor.role === 'doctor') return { name: 'doctor-workbench' }
  if (props.doctor.role === 'nurse') return { name: 'nurse-followups' }
  if (props.doctor.role === 'pharmacist') return { name: 'pharmacy-drug-catalog' }
  if (props.doctor.role === 'admin') return { name: 'admin-governance' }
  return { name: 'home' }
})

</script>

<template>
  <header class="stitch-topbar">
    <div class="topbar-system">
      <RouterLink class="topbar-link topbar-title" :to="homeRoute">{{ currentSystem.title }}</RouterLink>
      <template v-for="(item, index) in breadcrumb" :key="`${item}-${index}`">
        <span v-if="index === breadcrumb.length - 1" class="topbar-link topbar-current">
          {{ item }}
        </span>
        <RouterLink v-else class="topbar-link" :to="homeRoute">
          {{ item }}
        </RouterLink>
      </template>
    </div>

    <div class="topbar-search">
      <el-icon><Search /></el-icon>
      <input :placeholder="placeholderMap[section]" type="text" />
    </div>

    <div class="topbar-actions">
      <span class="topbar-pill">{{ serviceLabel }}</span>
      <div class="topbar-avatar" :title="doctor.name">
        <el-icon><UserFilled /></el-icon>
        <span>{{ doctor.name }} / {{ roleLabelMap[doctor.role] }}</span>
      </div>
    </div>
  </header>
</template>

<style scoped>
.stitch-topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  min-height: var(--ws-topbar-height);
  margin: 0 -24px;
  padding: 10px 24px;
  border-bottom: 1px solid var(--ws-outline);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 4px 20px rgba(23, 32, 51, 0.05);
  backdrop-filter: blur(14px);
}

.topbar-system {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
  color: #475569;
  white-space: nowrap;
}

.topbar-title {
  color: #172033;
  font-size: 15px;
}

.topbar-link {
  border-left: 1px solid #d5dde0;
  padding-left: 10px;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.topbar-link:first-child {
  border-left: 0;
  padding-left: 0;
}

.topbar-link:hover {
  color: #1d4ed8;
}

.topbar-search {
  display: flex;
  width: min(390px, 100%);
  align-items: center;
  gap: 8px;
  border: 1px solid var(--ws-outline);
  border-radius: 10px;
  background: #fff;
  padding: 0 10px;
}

.topbar-search :deep(input) {
  min-height: 32px;
  border: 0;
  background: transparent;
  box-shadow: none;
  color: #172033;
  font-size: 12px;
  padding: 6px 0;
}

.topbar-search :deep(input):focus {
  box-shadow: none;
}

.topbar-search :deep(svg) {
  color: #94a3b8;
}

.topbar-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.topbar-pill {
  border: 1px solid var(--ws-outline);
  border-radius: 999px;
  background: #f8fafc;
  color: #475569;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 8px;
}

.topbar-avatar {
  display: inline-flex;
  min-height: 30px;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  background: #1d4ed8;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  padding: 0 9px;
}

@media (max-width: 900px) {
  .stitch-topbar {
    display: grid;
    margin: 0;
    padding: 10px;
  }

  .topbar-system {
    flex-wrap: wrap;
  }

  .topbar-search {
    width: 100%;
  }
}
</style>
