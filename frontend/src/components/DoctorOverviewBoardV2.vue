<script setup lang="ts">
import { ref, computed } from 'vue'
import Pagination from './Pagination.vue'

type OverviewView = 'summary' | 'reminders' | 'queue'

interface OverviewMetric {
  label: string
  value: string | number
  note: string
  tone?: 'danger' | 'warning' | 'normal'
}

interface ReminderItem {
  id: string
  title: string
  detail: string
  patientId: string
  priority: 'high' | 'medium' | 'low'
}

interface QueueItem {
  patientId: string
  name: string
  primaryDisease: string
  riskLevel: string
  dataSupport: string
  dueLabel: string
}

const props = defineProps<{
  metrics: OverviewMetric[]
  reminders: ReminderItem[]
  queue: QueueItem[]
  view?: OverviewView
}>()

const emit = defineEmits<{
  (e: 'open', patientId: string): void
}>()

// 分页状态
const remindersPage = ref(1)
const remindersPageSize = ref(10)
const queuePage = ref(1)
const queuePageSize = ref(10)

// 分页后的待办提醒
const paginatedReminders = computed(() => {
  const start = (remindersPage.value - 1) * remindersPageSize.value
  return props.reminders.slice(start, start + remindersPageSize.value)
})

// 分页后的风险队列
const paginatedQueue = computed(() => {
  const start = (queuePage.value - 1) * queuePageSize.value
  return props.queue.slice(start, start + queuePageSize.value)
})

function handleRemindersPageChange(page: number, pageSize: number) {
  remindersPage.value = page
  remindersPageSize.value = pageSize
}

function handleQueuePageChange(page: number, pageSize: number) {
  queuePage.value = page
  queuePageSize.value = pageSize
}

function priorityLabel(priority: string) {
  if (priority === 'high') return '优先'
  if (priority === 'medium') return '尽快'
  return '常规'
}

function riskTone(level: string) {
  if (level.includes('高') || level.toLowerCase().includes('high')) return 'risk-high'
  if (level.includes('中') || level.toLowerCase().includes('medium')) return 'risk-medium'
  return 'risk-low'
}
</script>

<template>
  <section class="overview-shell practical-overview-shell single-view-overview">
    <!-- 工作摘要 -->
    <article v-if="props.view === 'summary'" class="card overview-summary">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Work Summary</p>
          <h3>当前门诊概况</h3>
        </div>
      </div>

      <div class="overview-metrics">
        <article
          v-for="item in props.metrics"
          :key="item.label"
          class="overview-metric"
          :class="item.tone ? `tone-${item.tone}` : ''"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.note }}</small>
        </article>
      </div>
    </article>

    <!-- 待办提醒（带分页） -->
    <article v-else-if="props.view === 'reminders'" class="card reminder-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Pending Actions</p>
          <h3>当前重点事项</h3>
        </div>
        <span class="panel-meta">共 {{ props.reminders.length }} 条待办</span>
      </div>

      <div v-if="props.reminders.length" class="reminder-list">
        <article v-for="item in paginatedReminders" :key="item.id" class="reminder-card">
          <div class="reminder-top">
            <strong>{{ item.title }}</strong>
            <span class="status-badge" :class="item.priority === 'high' ? 'todo' : 'done'">
              {{ priorityLabel(item.priority) }}
            </span>
          </div>
          <p>{{ item.detail }}</p>
          <button class="text-button" @click="emit('open', item.patientId)">打开患者</button>
        </article>
      </div>

      <article v-else class="empty-card compact">
        <p>当前没有待处理提醒。</p>
      </article>

      <!-- 分页器 -->
      <div v-if="props.reminders.length > remindersPageSize" class="pagination-container">
        <Pagination
          :total="props.reminders.length"
          :page="remindersPage"
          :page-size="remindersPageSize"
          @change="handleRemindersPageChange"
        />
      </div>
    </article>

    <!-- 风险队列（带分页） -->
    <article v-else class="card queue-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Risk Queue</p>
          <h3>风险优先队列</h3>
        </div>
        <span class="panel-meta">共 {{ props.queue.length }} 位患者</span>
      </div>

      <div v-if="props.queue.length" class="queue-list">
        <button
          v-for="item in paginatedQueue"
          :key="item.patientId"
          class="queue-row"
          :class="riskTone(item.riskLevel)"
          @click="emit('open', item.patientId)"
        >
          <div class="queue-main">
            <strong>{{ item.name }}</strong>
            <span class="queue-disease">{{ item.primaryDisease }}</span>
          </div>
          <div class="queue-meta">
            <span class="risk-badge" :class="riskTone(item.riskLevel)">{{ item.riskLevel }}</span>
            <span class="support-badge">{{ item.dataSupport }}</span>
            <span class="due-label">{{ item.dueLabel }}</span>
          </div>
        </button>
      </div>

      <article v-else class="empty-card compact">
        <p>当前没有患者队列。</p>
      </article>

      <!-- 分页器 -->
      <div v-if="props.queue.length > queuePageSize" class="pagination-container">
        <Pagination
          :total="props.queue.length"
          :page="queuePage"
          :page-size="queuePageSize"
          @change="handleQueuePageChange"
        />
      </div>
    </article>
  </section>
</template>

<style scoped>
.overview-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.eyebrow {
  font-size: 12px;
  color: #8c8c8c;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 4px 0;
}

.panel-head h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.panel-meta {
  font-size: 13px;
  color: #8c8c8c;
}

/* 工作摘要 */
.overview-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.overview-metric {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
  border-left: 3px solid #d9d9d9;
}

.overview-metric span {
  display: block;
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.overview-metric strong {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: #333;
  line-height: 1;
  margin-bottom: 4px;
}

.overview-metric small {
  display: block;
  font-size: 11px;
  color: #8c8c8c;
}

.overview-metric.tone-danger {
  border-left-color: #f5222d;
  background: #fff1f0;
}

.overview-metric.tone-warning {
  border-left-color: #fa8c16;
  background: #fff7e6;
}

/* 待办提醒 */
.reminder-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.reminder-card {
  padding: 12px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
}

.reminder-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.reminder-top strong {
  font-size: 14px;
  color: #333;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.status-badge.todo {
  background: #fff1f0;
  color: #f5222d;
}

.status-badge.done {
  background: #f6ffed;
  color: #52c41a;
}

.reminder-card p {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #666;
}

.text-button {
  padding: 0;
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-size: 13px;
  text-decoration: underline;
}

.text-button:hover {
  color: #5a6fd8;
}

/* 风险队列 */
.queue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.queue-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.queue-row:hover {
  background: #f5f7fa;
  border-color: #667eea;
  transform: translateX(4px);
}

.queue-row.risk-high {
  border-left: 3px solid #f5222d;
}

.queue-row.risk-medium {
  border-left: 3px solid #fa8c16;
}

.queue-row.risk-low {
  border-left: 3px solid #52c41a;
}

.queue-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.queue-main strong {
  font-size: 14px;
  color: #333;
}

.queue-disease {
  font-size: 12px;
  color: #8c8c8c;
}

.queue-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.risk-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.risk-badge.risk-high {
  background: #fff1f0;
  color: #f5222d;
}

.risk-badge.risk-medium {
  background: #fff7e6;
  color: #fa8c16;
}

.risk-badge.risk-low {
  background: #f6ffed;
  color: #52c41a;
}

.support-badge {
  padding: 2px 6px;
  background: #e6f7ff;
  color: #1890ff;
  border-radius: 3px;
  font-size: 11px;
}

.due-label {
  font-size: 11px;
  color: #8c8c8c;
}

.empty-card {
  text-align: center;
  padding: 40px 20px;
  color: #8c8c8c;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
