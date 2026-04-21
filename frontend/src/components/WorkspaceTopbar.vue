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

const placeholderMap: Record<AppSection, string> = {
  doctor: '搜索患者编号、姓名或主诊断...',
  archive: '搜索患者档案、病历号或建档来源...',
  tasks: '搜索随访任务...',
  contacts: '搜索联系记录...',
  flow: '搜索随访流程阶段...',
  insights: '搜索当前患者模型洞察...',
  'model-dashboard': '搜索模型版本、指标或运行状态...',
  'model-operations': '搜索用户信息、登录审计或模型状态...',
  'training-center': '搜索训练数据集、任务或模型名称...',
  governance: '搜索治理问题、冲突记录或待补全档案...',
  'data-quality': '搜索数据质量问题...',
  'drug-management': '搜索药品目录...',
  'drug-permission-management': '搜索药品权限映射...',
  system: '搜索系统审计或账号权限...',
}

const modeLabel = computed(() => `${String(props.health?.mode ?? 'demo').toUpperCase()} / MYSQL`)
const modelLabel = computed(() => {
  if (props.loading) return '加载中'
  if (props.health?.model_available) return '模型可用'
  if (props.health?.model_error) return '模型降级'
  return '模型不可用'
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
      <button class="topbar-icon" type="button" aria-label="连接状态">
        <el-icon><Connection /></el-icon>
      </button>
      <button class="topbar-icon" type="button" aria-label="通知">
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
