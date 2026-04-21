<script setup lang="ts">
import { computed } from 'vue'
import { Bell, Connection, Search, SwitchButton, UserFilled } from '@element-plus/icons-vue'
import type { DoctorUser, HealthResponse } from '../services/types'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  doctor: DoctorUser
  section: AppSection
  health: HealthResponse | null
  loading?: boolean
}>()

const sectionLabelMap: Record<AppSection, string> = {
  doctor: '搜索患者、风险事件或模型摘要...',
  archive: '搜索患者档案、病案号或主病种...',
  tasks: '搜索随访任务...',
  contacts: '搜索联系记录...',
  flow: '搜索随访流程看板...',
  insights: '搜索当前患者洞察...',
  'model-dashboard': '搜索模型版本与指标...',
  'training-center': '搜索数据集、训练任务或模型名称...',
  governance: '搜索治理记录...',
  'data-quality': '搜索数据质量问题...',
  'drug-management': '搜索药品目录...',
  'drug-permission-management': '搜索权限配置...',
  system: '搜索系统配置与日志...',
}

const modeLabel = computed(() => `${(props.health?.mode ?? 'demo').toUpperCase()}/MYSQL 模式`)
const modelLabel = computed(() => {
  if (props.health?.model_available) return '模型正常'
  if (props.health?.model_error) return '模型降级'
  return '模型状态未知'
})
</script>

<template>
  <section class="workspace-topbar">
    <div class="stitch-search-shell">
      <el-icon><Search /></el-icon>
      <input :value="''" type="text" :placeholder="sectionLabelMap[section]" readonly />
    </div>

    <div class="stitch-topbar-right">
      <span class="workspace-status-pill">{{ modeLabel }}</span>
      <button class="topbar-icon-button" type="button" aria-label="连接状态">
        <el-icon><Connection /></el-icon>
      </button>
      <button class="topbar-icon-button" type="button" aria-label="消息通知">
        <el-icon><Bell /></el-icon>
      </button>
      <button class="topbar-icon-button" type="button" aria-label="会话状态">
        <el-icon><SwitchButton /></el-icon>
      </button>
      <span class="workspace-status-pill" :class="props.health?.model_available ? 'status-success' : 'status-warning'">
        {{ loading ? '同步中...' : modelLabel }}
      </span>
      <div class="topbar-avatar">
        <el-icon><UserFilled /></el-icon>
      </div>
    </div>
  </section>
</template>

<style scoped>
.stitch-search-shell {
  min-width: min(420px, 100%);
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 18px;
  border-radius: 18px;
  background: rgba(241, 244, 245, 0.95);
  box-shadow: inset 0 0 0 1px rgba(190, 200, 201, 0.45);
}

.stitch-search-shell :deep(input) {
  border: 0;
  background: transparent;
  box-shadow: none;
  color: rgba(24, 28, 29, 0.72);
  cursor: default;
}

.stitch-search-shell :deep(input):focus {
  box-shadow: none;
}

.stitch-search-shell :deep(svg) {
  color: rgba(24, 28, 29, 0.6);
}

.stitch-topbar-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.topbar-icon-button {
  width: 42px;
  height: 42px;
  display: inline-grid;
  place-items: center;
  border: 0;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.74);
  box-shadow: inset 0 0 0 1px rgba(190, 200, 201, 0.56);
  color: var(--ws-on-surface);
}

.topbar-avatar {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--ws-primary), var(--ws-primary-container));
  color: white;
}

@media (max-width: 900px) {
  .stitch-search-shell {
    min-width: 100%;
  }
}
</style>
