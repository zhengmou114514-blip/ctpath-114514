<script setup lang="ts">
import { computed } from 'vue'
import { DataAnalysis, Dataset, SwitchButton, Tickets } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import type { ModelUser } from '../services/modelApi'

const props = defineProps<{ currentUser: ModelUser | null }>()
const emit = defineEmits<{ (e: 'logout'): void }>()

const route = useRoute()
const router = useRouter()

const items = [
  { name: 'model-home', label: '模型总览', icon: DataAnalysis },
  { name: 'model-datasets', label: '数据集管理', icon: Dataset },
  { name: 'model-training', label: '训练任务', icon: Tickets },
  { name: 'model-versions', label: '模型版本', icon: Tickets },
  { name: 'model-operations', label: '模型运营台', icon: DataAnalysis },
]

const currentName = computed(() => route.name?.toString() ?? 'model-home')
</script>

<template>
  <aside class="stitch-sidenav">
    <div class="sidenav-brand">
      <h1>CTpath</h1>
      <p>模型管理端</p>
    </div>

    <div class="sidenav-meta" v-if="currentUser">
      <div class="meta-user">
        <div class="meta-avatar">{{ currentUser.name.slice(-1) }}</div>
        <div>
          <strong>{{ currentUser.name }}</strong>
          <small>{{ currentUser.department }}</small>
        </div>
      </div>
      <div class="meta-stats">
        <span>{{ currentUser.title }}</span>
      </div>
    </div>

    <nav class="sidenav-menu">
      <button
        v-for="item in items"
        :key="item.name"
        class="sidenav-item"
        :class="{ active: currentName === item.name }"
        type="button"
        @click="router.push({ name: item.name })"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </button>
    </nav>

    <button class="sidenav-logout" type="button" @click="emit('logout')">
      <el-icon><SwitchButton /></el-icon>
      <span>退出登录</span>
    </button>
  </aside>
</template>
