<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useModelWorkspace } from '../composables/useModelWorkspace'

const workspace = useModelWorkspace()
const route = useRoute()
const router = useRouter()

const title = computed(() => 'CTpath 模型治理与训练平台')

function redirectAfterLogin() {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  void router.replace(redirect || '/')
}

onMounted(async () => {
  await workspace.initialize()
  if (workspace.isAuthenticated) redirectAfterLogin()
})

watch(
  () => workspace.currentUser,
  (user) => {
    if (user) redirectAfterLogin()
  }
)
</script>

<template>
  <section class="login-shell">
    <div class="login-card clinical-card">
      <p class="eyebrow">Model Center</p>
      <h1>{{ title }}</h1>
      <p class="login-lead">
        面向模型管理员与算法工程师，集中管理训练数据集、训练任务、模型版本发布与回滚，以及推理服务状态。
      </p>

      <div class="metric-grid compact-grid">
        <article class="record-item">
          <strong>服务状态</strong>
          <p>{{ workspace.health?.model_available ? '推理服务可用' : '推理服务异常' }}</p>
        </article>
        <article class="record-item">
          <strong>当前模式</strong>
          <p>{{ workspace.health?.mode?.toUpperCase() ?? 'MODEL' }}</p>
        </article>
      </div>

      <form class="login-form" @submit.prevent="workspace.submitLogin">
        <label>
          <span>账号</span>
          <input v-model="workspace.username" autocomplete="username" />
        </label>
        <label>
          <span>密码</span>
          <input v-model="workspace.password" autocomplete="current-password" type="password" />
        </label>
        <p class="login-hint">演示账号：`model_admin / model123456` 或 `ml_engineer / ml123456`</p>
        <p v-if="workspace.loginError" class="error-text">{{ workspace.loginError }}</p>
        <button class="primary-button" type="submit" :disabled="workspace.loadingLogin">
          {{ workspace.loadingLogin ? '正在登录...' : '登录模型平台' }}
        </button>
      </form>
    </div>
  </section>
</template>
