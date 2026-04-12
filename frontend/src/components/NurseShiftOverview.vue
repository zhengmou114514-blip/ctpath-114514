<script setup lang="ts">
import { computed } from 'vue'
import type { FollowupTaskRow } from '../services/types'

const props = defineProps<{
  followupItems: FollowupTaskRow[]
}>()

const emit = defineEmits<{
  (e: 'open-patient', patientId: string): void
}>()

function isPending(status: string) {
  const normalized = status.toLowerCase()
  return !normalized.includes('completed') &&
    !normalized.includes('closed') &&
    !status.includes('已完成') &&
    !status.includes('已关闭')
}

const summary = computed(() => ({
  total: props.followupItems.length,
  high: props.followupItems.filter((item) => item.priority === 'high').length,
  outpatient: props.followupItems.filter((item) => item.source === 'outpatient-task').length,
  pending: props.followupItems.filter((item) => isPending(item.status)).length,
}))

const priorityPatients = computed(() => {
  const seen = new Set<string>()
  return props.followupItems
    .filter((item) => item.priority === 'high')
    .filter((item) => {
      if (seen.has(item.patientId)) return false
      seen.add(item.patientId)
      return true
    })
    .slice(0, 4)
})
</script>

<template>
  <section class="card role-focus-board nurse-focus-board">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Nurse Shift</p>
        <h3>护士班次总览</h3>
      </div>
      <span class="panel-meta">聚焦今日随访执行、重点联系患者和待回写结果。</span>
    </div>

    <div class="role-focus-metrics">
      <article class="role-focus-metric">
        <span>今日任务</span>
        <strong>{{ summary.total }}</strong>
      </article>
      <article class="role-focus-metric">
        <span>高优先级</span>
        <strong>{{ summary.high }}</strong>
      </article>
      <article class="role-focus-metric">
        <span>门诊联动</span>
        <strong>{{ summary.outpatient }}</strong>
      </article>
      <article class="role-focus-metric">
        <span>待处理</span>
        <strong>{{ summary.pending }}</strong>
      </article>
    </div>

    <div class="role-focus-grid">
      <article class="role-focus-section">
        <strong>重点联系患者</strong>
        <button
          v-for="item in priorityPatients"
          :key="`${item.patientId}-${item.taskType}`"
          class="role-focus-row"
          @click="emit('open-patient', item.patientId)"
        >
          <span>{{ item.patientName }} / {{ item.patientId }}</span>
          <small>{{ item.taskType }} / {{ item.dueDate }}</small>
        </button>
        <p v-if="!priorityPatients.length" class="risk-group-empty">当前没有高优先级患者，可优先处理常规随访任务。</p>
      </article>

      <article class="role-focus-section">
        <strong>本班次建议</strong>
        <p class="role-focus-note">
          优先处理高风险和门诊联动患者，联系后立即回写结果，避免只完成电话但未同步档案。
        </p>
        <p class="role-focus-note">
          若患者未接通，建议同步填写下次联系日期，形成连续随访节奏，方便下一班次接续处理。
        </p>
      </article>
    </div>
  </section>
</template>
