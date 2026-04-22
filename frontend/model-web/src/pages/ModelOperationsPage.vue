<script setup lang="ts">
import { onMounted } from 'vue'
import { useModelWorkspace } from '../composables/useModelWorkspace'

const workspace = useModelWorkspace()

onMounted(() => {
  void workspace.refreshOperations()
})
</script>

<template>
  <section class="workspace-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">模型运营台</p>
        <h1>登录次数、用户信息与模型状态</h1>
        <p>用于模型侧的审计、运营和健康状态查看。</p>
      </div>
    </header>

    <section class="metric-grid">
      <article class="clinical-card metric-card">
        <span>登录次数</span>
        <strong>{{ workspace.operations?.loginCount ?? 0 }}</strong>
      </article>
      <article class="clinical-card metric-card">
        <span>当前用户</span>
        <strong>{{ workspace.operations?.currentUser?.name ?? '--' }}</strong>
        <small>{{ workspace.operations?.currentUser?.department ?? '' }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>模型状态</span>
        <strong>{{ workspace.health?.model_available ? '可用' : '降级' }}</strong>
      </article>
    </section>

    <p v-if="workspace.opsError" class="error-text">{{ workspace.opsError }}</p>

    <section class="training-grid">
      <article class="clinical-card">
        <h2>模型用户</h2>
        <div class="record-list">
          <article v-for="user in workspace.operations?.modelUsers ?? []" :key="user.username" class="record-item">
            <strong>{{ user.name }}</strong>
            <p>{{ user.title }} · {{ user.department }}</p>
          </article>
        </div>
      </article>

      <article class="clinical-card">
        <h2>操作日志</h2>
        <div class="record-list">
          <article v-for="item in workspace.operations?.activityLog ?? []" :key="item.id" class="record-item">
            <strong>{{ item.action }}</strong>
            <p>{{ item.detail }} · {{ item.operator }}</p>
            <small>{{ item.createdAt }}</small>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>
