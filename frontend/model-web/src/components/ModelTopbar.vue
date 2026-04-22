<script setup lang="ts">
import { computed } from 'vue'
import { Bell, Refresh, UserFilled } from '@element-plus/icons-vue'
import type { ModelHealthResponse, ModelUser } from '../services/modelApi'

const props = defineProps<{ health: ModelHealthResponse | null; user: ModelUser | null }>()
const emit = defineEmits<{ (e: 'refresh'): void }>()

const statusLabel = computed(() => {
  if (!props.health) return '连接中'
  if (props.health.model_available) return '模型可用'
  return '模型降级'
})
</script>

<template>
  <header class="stitch-topbar">
    <div class="topbar-search">
      <input placeholder="搜索数据集、任务、版本或状态..." readonly type="text" />
    </div>
    <div class="topbar-actions">
      <span class="topbar-pill">{{ statusLabel }}</span>
      <button class="topbar-icon" type="button" aria-label="刷新" @click="emit('refresh')">
        <el-icon><Refresh /></el-icon>
      </button>
      <button class="topbar-icon" type="button" aria-label="通知">
        <el-icon><Bell /></el-icon>
      </button>
      <span class="topbar-pill">{{ props.health?.mode?.toUpperCase() ?? 'MODEL' }}</span>
      <div class="topbar-avatar" :title="user?.name || ''">
        <el-icon><UserFilled /></el-icon>
      </div>
    </div>
  </header>
</template>
