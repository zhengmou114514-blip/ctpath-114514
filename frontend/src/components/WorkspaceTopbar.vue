<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
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
</script>

<template>
  <header class="stitch-topbar">
    <div class="topbar-system">
      <strong>{{ currentSystem.title }}</strong>
      <span v-for="item in breadcrumb" :key="item">{{ item }}</span>
    </div>

    <div class="topbar-search">
      <el-icon><Search /></el-icon>
      <input :placeholder="placeholderMap[section]" readonly type="text" />
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
  position: static;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  min-height: 54px;
  padding: 8px 14px;
  border-bottom: 1px solid rgba(191, 200, 200, 0.7);
  background: #f7fafb;
  box-shadow: 0 2px 10px rgba(24, 28, 30, 0.05);
}

.topbar-system {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
  color: #3f4848;
  white-space: nowrap;
}

.topbar-system strong {
  color: #003434;
  font-size: 15px;
}

.topbar-system span {
  border-left: 1px solid #d5dde0;
  padding-left: 10px;
  color: #526772;
  font-size: 12px;
  font-weight: 700;
}

.topbar-search {
  display: flex;
  width: min(390px, 100%);
  align-items: center;
  gap: 8px;
  border: 1px solid #d5dde0;
  border-radius: 999px;
  background: #fff;
  padding: 0 10px;
}

.topbar-search :deep(input) {
  min-height: 32px;
  border: 0;
  background: transparent;
  box-shadow: none;
  color: #181c1d;
  cursor: default;
  font-size: 12px;
  padding: 6px 0;
}

.topbar-search :deep(input):focus {
  box-shadow: none;
}

.topbar-search :deep(svg) {
  color: #6f797a;
}

.topbar-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.topbar-pill {
  border: 1px solid #d5dde0;
  border-radius: 999px;
  background: #fff;
  color: #3f4849;
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
  background: #005c61;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  padding: 0 9px;
}

@media (max-width: 900px) {
  .stitch-topbar {
    display: grid;
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
