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
        <p class="eyebrow">Operations & Audit</p>
        <h1>模型运营与审计</h1>
        <p>查看模型端登录次数、当前操作人、模型用户清单与关键运营事件，便于演示管理闭环。</p>
      </div>
    </header>

    <section class="metric-grid compact-grid">
      <article class="clinical-card metric-card">
        <span>累计登录次数</span>
        <strong>{{ workspace.operations?.loginCount ?? 0 }}</strong>
      </article>
      <article class="clinical-card metric-card">
        <span>当前操作人</span>
        <strong>{{ workspace.operations?.currentUser?.name ?? '--' }}</strong>
        <small>{{ workspace.operations?.currentUser?.department ?? '' }}</small>
      </article>
      <article class="clinical-card metric-card">
        <span>服务状态</span>
        <strong>{{ workspace.health?.model_available ? '可用' : '异常' }}</strong>
      </article>
    </section>

    <p v-if="workspace.opsError" class="error-text">{{ workspace.opsError }}</p>

    <section class="training-grid">
      <article class="clinical-card">
        <h2>模型中心用户</h2>
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
