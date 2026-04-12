<script setup lang="ts">
import { computed } from 'vue'
import { useAuditTrailStore } from '../../stores/auditTrailStore'

const props = withDefaults(
  defineProps<{
    title?: string
    limit?: number
    compact?: boolean
  }>(),
  {
    title: 'Recent Audit Trail',
    limit: 8,
    compact: false,
  }
)

const auditStore = useAuditTrailStore()

const rows = computed(() => auditStore.getRecent(props.limit))

function resultTone(result: string) {
  if (result === 'success') return 'tone-success'
  if (result === 'degraded') return 'tone-degraded'
  return 'tone-failed'
}

function formatTime(value: string): string {
  return value.replace('T', ' ').slice(0, 16)
}
</script>

<template>
  <section class="audit-panel card" :class="{ compact: props.compact }">
    <header class="panel-head">
      <h3>{{ props.title }}</h3>
      <button class="text-button" @click="auditStore.clearAuditLogs">Clear</button>
    </header>

    <div v-if="!rows.length" class="empty">No audit records yet.</div>

    <div v-else class="rows">
      <article v-for="item in rows" :key="item.id" class="row">
        <div class="row-main">
          <strong>{{ item.action }}</strong>
          <p>{{ item.detail }}</p>
          <small>
            {{ item.actor.name }} ({{ item.actor.role }}) | {{ item.target.type }}: {{ item.target.label || item.target.id }}
          </small>
        </div>
        <div class="row-side">
          <span class="result-pill" :class="resultTone(item.result)">{{ item.result }}</span>
          <small>{{ formatTime(item.time) }}</small>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.audit-panel {
  border: 1px solid #cfd9e5;
  border-radius: 10px;
  background: #fff;
  padding: 10px;
  display: grid;
  gap: 8px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.panel-head h3 {
  margin: 0;
  color: #10263c;
  font-size: 0.94rem;
}

.rows {
  display: grid;
  gap: 8px;
}

.row {
  border: 1px solid #d8e2ee;
  border-radius: 8px;
  padding: 8px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  background: #fbfdff;
}

.row-main {
  display: grid;
  gap: 3px;
}

.row-main p {
  margin: 0;
  color: #556f85;
  font-size: 0.8rem;
}

.row-main small,
.row-side small {
  color: #607b91;
  font-size: 0.74rem;
}

.row-side {
  display: grid;
  justify-items: end;
  gap: 4px;
}

.result-pill {
  border: 1px solid transparent;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 0.72rem;
  font-weight: 700;
}

.tone-success {
  background: #e9f8f1;
  border-color: #bde7d1;
  color: #1d7b5c;
}

.tone-degraded {
  background: #fff4e2;
  border-color: #efdbb2;
  color: #9b6518;
}

.tone-failed {
  background: #fdeced;
  border-color: #efc2c5;
  color: #a4383f;
}

.empty {
  border: 1px dashed #bfd0e2;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  color: #617c91;
  font-size: 0.82rem;
}

.audit-panel.compact .row {
  padding: 6px;
}
</style>
