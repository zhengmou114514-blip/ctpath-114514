<script setup lang="ts">
import type { ContactLog, OutpatientTask, PatientCase } from '../../services/types'

defineProps<{
  patient: PatientCase
}>()

function sortedLogs(logs: ContactLog[]) {
  return [...logs].sort((a, b) => b.contactTime.localeCompare(a.contactTime))
}

function sortedTasks(tasks: OutpatientTask[]) {
  return [...tasks].sort((a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''))
}
</script>

<template>
  <section class="card footer-panel">
    <article class="pane">
      <h3>随访记录</h3>
      <div v-if="!patient.contactLogs.length" class="empty">暂无随访记录</div>
      <div v-else class="rows">
        <article v-for="log in sortedLogs(patient.contactLogs)" :key="log.logId" class="row">
          <div>
            <strong>{{ log.contactType }} / {{ log.contactResult }}</strong>
            <p>{{ log.note || '无备注' }}</p>
          </div>
          <span>{{ log.contactTime.replace('T', ' ') }}</span>
        </article>
      </div>
    </article>

    <article class="pane">
      <h3>下一步计划</h3>
      <div v-if="!patient.outpatientTasks.length" class="empty">暂无计划任务</div>
      <div v-else class="rows">
        <article v-for="task in sortedTasks(patient.outpatientTasks)" :key="task.taskId" class="row">
          <div>
            <strong>{{ task.title }}</strong>
            <p>{{ task.owner }} / {{ task.priority }}</p>
          </div>
          <span>{{ task.status }} · {{ task.dueDate }}</span>
        </article>
      </div>
    </article>
  </section>
</template>

<style scoped>
.footer-panel {
  padding: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.pane {
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #fbfdff;
  padding: 10px;
  display: grid;
  gap: 8px;
}

.pane h3 {
  margin: 0;
  color: var(--navy);
  font-size: 1rem;
}

.rows {
  display: grid;
  gap: 8px;
}

.row {
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #fff;
  padding: 8px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.row p {
  margin: 4px 0 0;
  color: var(--ink-soft);
  font-size: 0.84rem;
}

.row span {
  color: var(--ink-muted);
  font-size: 0.78rem;
}

.empty {
  border: 1px dashed var(--border-strong);
  border-radius: 8px;
  padding: 12px;
  color: var(--ink-muted);
  text-align: center;
  font-size: 0.84rem;
}

@media (max-width: 1000px) {
  .footer-panel {
    grid-template-columns: 1fr;
  }
}
</style>
