<script setup lang="ts">
import { computed } from 'vue'
import { Bell, Connection, Search, UserFilled } from '@element-plus/icons-vue'
import type { DoctorUser, HealthResponse } from '../services/types'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  doctor: DoctorUser
  section: AppSection
  health: HealthResponse | null
  loading?: boolean
}>()

const placeholderMap: Partial<Record<AppSection, string>> = {
  doctor: '搜索待处理患者、病案号或风险标签',
  archive: '搜索患者档案、建档状态或联系方式',
  emr: '搜索患者一览、历史记录或管理任务',
  pharmacy: '搜索库存、复核队列或出入库记录',
  coordination: '搜索协同记录、负责人或下一步动作',
  tasks: '搜索待随访任务、计划时间或责任人',
  contacts: '搜索联系记录、拨打结果或备注',
  flow: '搜索病程流转节点、状态或责任医生',
  insights: '搜索当前患者预测结果、证据摘要或建议',
  governance: '搜索数据质量问题、缺失字段或治理动作',
  'role-workspaces': '搜索角色边界、权限矩阵或协同分工',
  'data-quality': '搜索数据质量记录',
  'drug-management': '搜索药品名称、规格或状态',
  'drug-permission-management': '搜索角色权限、药品范围或管制级别',
  system: '搜索系统状态、运行模式或健康检查',
}

const modeLabel = computed(() => `${String(props.health?.mode ?? 'demo').toUpperCase()} / CLINIC`)
const modelLabel = computed(() => {
  if (props.loading) return '模型状态检测中'
  if (props.health?.model_available) return '推理服务可用'
  if (props.health?.model_error) return '推理服务告警'
  return '推理服务离线'
})
</script>

<template>
  <header class="stitch-topbar">
    <div class="topbar-search">
      <el-icon><Search /></el-icon>
      <input :placeholder="placeholderMap[section]" readonly type="text" />
    </div>

    <div class="topbar-actions">
      <span class="topbar-pill">{{ modeLabel }}</span>
      <button class="topbar-icon" type="button" aria-label="接口连通状态">
        <el-icon><Connection /></el-icon>
      </button>
      <button class="topbar-icon" type="button" aria-label="系统通知">
        <el-icon><Bell /></el-icon>
      </button>
      <span class="topbar-pill">{{ modelLabel }}</span>
      <div class="topbar-avatar" :title="doctor.name">
        <el-icon><UserFilled /></el-icon>
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
  gap: 24px;
  min-height: 80px;
  padding: 0 40px;
  background: #f7fafb;
}

.topbar-search {
  display: flex;
  align-items: center;
  gap: 12px;
  width: min(420px, 100%);
  border-radius: 999px;
  background: #ebeeef;
  padding: 0 16px;
}

.topbar-search :deep(input) {
  border: 0;
  background: transparent;
  color: #181c1d;
  cursor: default;
  padding: 12px 0;
  box-shadow: none;
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
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.topbar-pill {
  border-radius: 999px;
  background: #ebeeef;
  padding: 6px 12px;
  color: #3f4849;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.topbar-icon {
  display: inline-grid;
  height: 40px;
  width: 40px;
  place-items: center;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #3f4849;
}

.topbar-avatar {
  display: grid;
  height: 40px;
  width: 40px;
  place-items: center;
  border-radius: 999px;
  background: #005c61;
  color: #fff;
}

@media (max-width: 900px) {
  .stitch-topbar {
    padding: 16px 20px;
    display: grid;
  }

  .topbar-search {
    width: 100%;
  }
}
</style>
