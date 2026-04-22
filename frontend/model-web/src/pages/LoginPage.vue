<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useModelWorkspace } from '../composables/useModelWorkspace'

const workspace = useModelWorkspace()
const route = useRoute()
const router = useRouter()

const title = computed(() => 'CTpath 模型管理端')

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
      <p class="eyebrow">模型管理端</p>
      <h1>{{ title }}</h1>
      <p class="login-lead">数据集、训练任务、模型版本和推理服务状态独立管理。</p>

      <form class="login-form" @submit.prevent="workspace.submitLogin">
        <label>
          <span>账号</span>
          <input v-model="workspace.username" autocomplete="username" />
        </label>
        <label>
          <span>密码</span>
          <input v-model="workspace.password" autocomplete="current-password" type="password" />
        </label>
        <p v-if="workspace.loginError" class="error-text">{{ workspace.loginError }}</p>
        <button class="primary-button" type="submit" :disabled="workspace.loadingLogin">
          {{ workspace.loadingLogin ? '登录中...' : '登录模型端' }}
        </button>
      </form>
    </div>
  </section>
</template>
