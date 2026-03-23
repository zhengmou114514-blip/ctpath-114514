<script setup lang="ts">
import type { FollowUpTask } from '../services/types'

defineProps<{
  tasks: FollowUpTask[]
  pathExplanation: string[]
}>()
</script>

<template>
  <section class="surface-card">
    <div class="surface-head">
      <div>
        <p class="surface-eyebrow">Care Plan</p>
        <h3>随访任务与路径解释</h3>
      </div>
      <span class="surface-note">答辩时可展示模型解释性</span>
    </div>

    <div class="task-list">
      <article v-for="task in tasks" :key="task.title" class="task-card">
        <div class="task-top">
          <h4>{{ task.title }}</h4>
          <span class="priority" :class="`priority-${task.priority}`">{{ task.priority }}</span>
        </div>
        <p>{{ task.owner }}</p>
        <small>截止时间：{{ task.dueDate }}</small>
      </article>
    </div>

    <div class="path-box">
      <div class="path-head">
        <span>关键路径</span>
        <strong>Graph Structure-Aware Path</strong>
      </div>
      <ol class="path-list">
        <li v-for="step in pathExplanation" :key="step">{{ step }}</li>
      </ol>
    </div>
  </section>
</template>
