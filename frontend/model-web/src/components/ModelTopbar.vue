<script setup lang="ts">
import { computed } from 'vue'
import { Bell, Refresh, UserFilled } from '@element-plus/icons-vue'
import type { ModelHealthResponse, ModelUser } from '../services/modelApi'

const props = defineProps<{
  health: ModelHealthResponse | null
  user: ModelUser | null
  loading?: boolean
}>()
const emit = defineEmits<{ (e: 'refresh'): void }>()

const statusLabel = computed(() => {
  if (!props.health) return '状态加载中'
  if (props.health.model_available) return '推理服务可用'
  return '推理服务异常'
})
</script>

<template>
  <header class="stitch-topbar">
    <div class="topbar-search">
      <input
        placeholder="模型中心只管理训练、版本、部署与运营审计，不进入临床患者流程"
        readonly
        type="text"
      />
    </div>
    <div class="topbar-actions">
      <span class="topbar-pill">{{ statusLabel }}</span>
      <button class="topbar-icon" type="button" aria-label="刷新模型中心数据" @click="emit('refresh')">
        <el-icon><Refresh /></el-icon>
      </button>
      <button class="topbar-icon" type="button" aria-label="提醒中心">
        <el-icon><Bell /></el-icon>
      </button>
      <span class="topbar-pill">{{ props.health?.mode?.toUpperCase() ?? 'MODEL' }}</span>
      <span v-if="loading" class="topbar-pill">同步中</span>
      <div class="topbar-avatar" :title="user?.name || ''">
        <el-icon><UserFilled /></el-icon>
      </div>
    </div>
  </header>
</template>
