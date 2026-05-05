<script setup lang="ts">
import { computed } from 'vue'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)
const tasks = computed(() => patient.value?.outpatientTasks ?? [])
</script>

<template>
  <section v-if="patient" class="clinical-card">
    <div class="section-header">
      <div><p class="eyebrow">随访记录</p><h2>患者随访闭环</h2></div>
      <button class="primary-button" type="button" @click="workspace.openFollowupModule(patient.patientId, 'tasks')">发起随访</button>
    </div>
    <table class="followup-table">
      <thead><tr><th>任务</th><th>负责人</th><th>截止日期</th><th>状态</th></tr></thead>
      <tbody>
        <tr v-for="item in tasks" :key="item.taskId">
          <td>{{ item.title }}</td><td>{{ item.owner }}</td><td>{{ item.dueDate }}</td><td>{{ item.status }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<style scoped>
.followup-table { width: 100%; border-collapse: collapse; border: 1px solid #d5e6ef; }
.followup-table th, .followup-table td { padding: 10px; border-bottom: 1px solid #d5e6ef; text-align: left; }
.followup-table th { background: #edf7fc; }
</style>
