<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { ContactLogCreatePayload, FlowBoardRow, FollowupTaskRow } from '../services/types'

type RiskFilter = 'all' | 'high' | 'medium' | 'low'
type DateFilter = 'all' | 'today' | 'overdue' | 'next7'
type ContactMethod = 'call' | 'message'
type ContactOutcome = 'reached' | 'scheduled' | 'missed' | 'urgent'

interface LocalActionRecord {
  id: string
  label: string
  status: string
  at: string
  note: string
}

interface LocalTaskState {
  status: string
  updatedAt: string
  unreached: boolean
  needsReview: boolean
  nextFollowupDate: string
  history: LocalActionRecord[]
}

const props = defineProps<{
  loading: boolean
  loadingTaskAction: boolean
  followupItems: FollowupTaskRow[]
  flowBoardItems: FlowBoardRow[]
  selectedPatientId?: string
  savingContactLog: boolean
}>()

const emit = defineEmits<{
  (e: 'open-patient', patientId: string): void
  (e: 'open-archive', patientId: string): void
  (e: 'complete-task', payload: { patientId: string; taskId: string }): void
  (e: 'close-task', payload: { patientId: string; taskId: string }): void
  (e: 'submit-contact-log', payload: { patientId: string; payload: ContactLogCreatePayload }): void
}>()

const riskFilter = ref<RiskFilter>('all')
const dateFilter = ref<DateFilter>('all')
const keyword = ref('')
const selectedTaskKey = ref('')
const contactMethod = ref<ContactMethod>('call')
const contactOutcome = ref<ContactOutcome>('reached')
const clinicalNotes = ref('已在随访工作台记录本次患者联系情况。')
const localState = reactive<Record<string, LocalTaskState>>({})

function taskKey(item: FollowupTaskRow): string {
  return `${item.patientId}::${item.taskId || item.taskType}`
}

function nowIso(): string {
  return new Date().toISOString()
}

function formatDateTime(value: string): string {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function riskLevelKey(value: string): 'high' | 'medium' | 'low' {
  const normalized = value.toLowerCase()
  if (normalized.includes('high')) return 'high'
  if (normalized.includes('medium')) return 'medium'
  return 'low'
}

function isCompletedStatus(status: string): boolean {
  const normalized = status.toLowerCase()
  return normalized.includes('completed') || normalized.includes('closed')
}

function isOverdue(dueDate: string): boolean {
  if (!dueDate) return false
  const today = new Date().toISOString().slice(0, 10)
  return dueDate < today
}

function inNext7Days(dueDate: string): boolean {
  if (!dueDate) return false
  const now = new Date()
  const end = new Date(now.getTime() + 7 * 86400000)
  const due = new Date(`${dueDate}T00:00:00`)
  return due >= new Date(now.toISOString().slice(0, 10)) && due <= end
}

function ensureState(item: FollowupTaskRow): LocalTaskState {
  const key = taskKey(item)
  if (!localState[key]) {
    const initialAt = item.lastActionAt || `${item.dueDate}T09:00:00`
    localState[key] = {
      status: item.status,
      updatedAt: initialAt,
      unreached: false,
      needsReview: false,
      nextFollowupDate: item.dueDate,
      history: [
        {
          id: `${key}-init`,
          label: '任务加载',
          status: item.status,
          at: initialAt,
          note: `来源：${item.source}`,
        },
      ],
    }
  }
  return localState[key]
}

const mergedTasks = computed(() =>
  props.followupItems.map((item) => {
    const state = ensureState(item)
    const flow = props.flowBoardItems.find((row) => row.patientId === item.patientId) || null
    return {
      ...item,
      localStatus: state.status,
      localUpdatedAt: state.updatedAt,
      unreached: state.unreached,
      needsReview: state.needsReview,
      nextFollowupDate: state.nextFollowupDate,
      history: state.history,
      flow,
      riskKey: riskLevelKey(item.riskLevel),
      completed: isCompletedStatus(state.status),
      overdue: isOverdue(item.dueDate),
    }
  })
)

const filteredTasks = computed(() => {
  return mergedTasks.value.filter((item) => {
    if (riskFilter.value !== 'all' && item.riskKey !== riskFilter.value) return false
    if (dateFilter.value === 'today' && item.dueDate !== new Date().toISOString().slice(0, 10)) return false
    if (dateFilter.value === 'overdue' && !item.overdue) return false
    if (dateFilter.value === 'next7' && !inNext7Days(item.dueDate)) return false

    const kw = keyword.value.trim().toLowerCase()
    if (!kw) return true
    const haystack = `${item.patientId} ${item.patientName} ${item.primaryDisease} ${item.taskType}`.toLowerCase()
    return haystack.includes(kw)
  })
})

const selectedTask = computed(() => filteredTasks.value.find((item) => taskKey(item) === selectedTaskKey.value) || null)

const boardColumns = computed(() => {
  const pending = filteredTasks.value.filter((item) => item.localStatus.toLowerCase().includes('pending') || item.unreached)
  const inProgress = filteredTasks.value.filter(
    (item) =>
      item.localStatus.toLowerCase().includes('contacted') ||
      item.localStatus.toLowerCase().includes('review') ||
      item.flow?.flowStatus.toLowerCase().includes('progress')
  )
  const completed = filteredTasks.value.filter((item) => item.completed)

  return [
    { key: 'pending', label: '待处理', accent: 'accent-danger', items: pending },
    { key: 'progress', label: '处理中', accent: 'accent-info', items: inProgress },
    { key: 'completed', label: '已完成', accent: 'accent-success', items: completed },
  ]
})

function appendHistory(item: FollowupTaskRow, label: string, nextStatus: string, note: string) {
  const state = ensureState(item)
  const at = nowIso()
  state.status = nextStatus
  state.updatedAt = at
  state.history.unshift({
    id: `${taskKey(item)}-${at}`,
    label,
    status: nextStatus,
    at,
    note,
  })
}

function submitContact(item: FollowupTaskRow, result: ContactLogCreatePayload['contactResult'], note: string, nextDate?: string) {
  const payload: ContactLogCreatePayload = {
    contactTime: nowIso().slice(0, 16),
    contactType: contactMethod.value === 'call' ? 'phone' : 'wechat',
    contactTarget: 'patient',
    contactResult: result,
    note,
    nextContactDate: nextDate,
  }
  emit('submit-contact-log', { patientId: item.patientId, payload })
}

function markReached(item: FollowupTaskRow, note = '本次随访已联系到患者。') {
  const state = ensureState(item)
  state.unreached = false
  state.needsReview = false
  appendHistory(item, '已联系患者', 'Contacted', note)
  submitContact(item, 'reached', note, state.nextFollowupDate)
}

function markUnreached(item: FollowupTaskRow, note = '本次未接通，需再次联系。') {
  const state = ensureState(item)
  state.unreached = true
  appendHistory(item, '联系未果', 'Unreached', note)
  submitContact(item, 'missed', note, state.nextFollowupDate)
}

function markNeedReview(item: FollowupTaskRow, note = '根据随访情况需医生进一步复核。') {
  const state = ensureState(item)
  state.needsReview = true
  appendHistory(item, '需要医生复核', 'Need Review', note)
  submitContact(item, 'urgent', note, state.nextFollowupDate)
}

function markCompleted(item: FollowupTaskRow) {
  appendHistory(item, '已完成任务', 'Completed', '本轮随访已完成。')
  const current = localState[taskKey(item)]
  if (current) {
    current.unreached = false
    current.needsReview = false
  }
  if (item.source === 'outpatient-task' && item.taskId) {
    emit('complete-task', { patientId: item.patientId, taskId: item.taskId })
  }
}

function markClosed(item: FollowupTaskRow) {
  appendHistory(item, '已关闭任务', 'Closed', '任务已由随访人员关闭。')
  const current = localState[taskKey(item)]
  if (current) {
    current.unreached = false
    current.needsReview = false
  }
  if (item.source === 'outpatient-task' && item.taskId) {
    emit('close-task', { patientId: item.patientId, taskId: item.taskId })
  }
}

function saveContactEntry() {
  if (!selectedTask.value) return
  const note = clinicalNotes.value.trim() || '已在慢病随访工作台保存联系记录。'

  if (contactOutcome.value === 'missed') {
    markUnreached(selectedTask.value, note)
    return
  }

  if (contactOutcome.value === 'urgent') {
    markNeedReview(selectedTask.value, note)
    return
  }

  markReached(selectedTask.value, note)
}

watch(
  () => [props.selectedPatientId, filteredTasks.value.length] as const,
  () => {
    if (props.selectedPatientId) {
      const found = filteredTasks.value.find((item) => item.patientId === props.selectedPatientId)
      if (found) {
        selectedTaskKey.value = taskKey(found)
        return
      }
    }

    if (!selectedTask.value && filteredTasks.value.length) {
      const first = filteredTasks.value[0]
      if (first) selectedTaskKey.value = taskKey(first)
    }
  },
  { immediate: true }
)

watch(selectedTask, (task) => {
  if (!task) return
  clinicalNotes.value = `${task.patientName}：${task.taskType}。`
  contactOutcome.value = task.unreached ? 'missed' : task.needsReview ? 'urgent' : 'reached'
})
</script>

<template>
  <section class="followup-workbench">
    <div class="followup-header">
      <div>
        <p class="eyebrow">随访工作台</p>
        <h2>随访账本</h2>
        <p>集中处理当前患者联系、记录与任务闭环。</p>
      </div>

      <div class="followup-filters">
        <input v-model="keyword" type="text" placeholder="搜索患者姓名或主病种..." />
        <select v-model="riskFilter">
          <option value="all">全部风险等级</option>
          <option value="high">高风险</option>
          <option value="medium">中风险</option>
          <option value="low">低风险</option>
        </select>
        <select v-model="dateFilter">
          <option value="all">全部日期</option>
          <option value="today">今日到期</option>
          <option value="overdue">已逾期</option>
          <option value="next7">未来 7 天</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="empty-state-card">正在加载随访账本...</div>
    <div v-else-if="!filteredTasks.length" class="empty-state-card">当前筛选条件下没有随访任务。</div>

    <section v-else class="followup-ledger-layout">
      <section class="ledger-board">
        <article v-for="column in boardColumns" :key="column.key" class="ledger-column">
          <div class="ledger-column-head">
            <span class="ledger-dot" :class="column.accent"></span>
            <strong>{{ column.label }}</strong>
            <span class="ledger-count">{{ column.items.length }}</span>
          </div>

          <div class="ledger-stack">
            <article
              v-for="item in column.items"
              :key="taskKey(item)"
              class="clinical-card ledger-card"
              :class="{ active: selectedTaskKey === taskKey(item) }"
              @click="selectedTaskKey = taskKey(item)"
            >
              <div class="ledger-card-head">
                <div>
                  <strong>{{ item.patientName }}</strong>
                  <p>{{ item.taskType }}</p>
                </div>
                <span class="risk-pill" :class="`risk-${item.riskKey}`">{{ item.riskLevel }}</span>
              </div>
              <p class="ledger-card-copy">{{ item.primaryDisease }} / {{ item.patientId }}</p>
              <div class="ledger-card-meta">
                <span>最近联系</span>
                <strong>{{ item.lastActionAt ? formatDateTime(item.lastActionAt) : '暂无记录' }}</strong>
              </div>
              <div class="ledger-card-meta">
                <span>下次计划</span>
                <strong>{{ item.nextFollowupDate || item.dueDate }}</strong>
              </div>
            </article>
          </div>
        </article>
      </section>

      <aside class="clinical-card contact-entry-panel">
        <div class="contact-entry-head">
          <p class="eyebrow">联系记录</p>
          <h3>联系记录录入</h3>
        </div>

        <template v-if="selectedTask">
          <label class="entry-field">
            <span>患者</span>
            <input :value="selectedTask.patientName" type="text" readonly />
          </label>

          <div class="entry-field">
            <span>联系方式</span>
            <div class="method-row">
              <button
                class="secondary-button"
                :class="{ active: contactMethod === 'call' }"
                type="button"
                @click="contactMethod = 'call'"
              >
                电话
              </button>
              <button
                class="secondary-button"
                :class="{ active: contactMethod === 'message' }"
                type="button"
                @click="contactMethod = 'message'"
              >
                消息
              </button>
            </div>
          </div>

          <label class="entry-field">
            <span>联系结果</span>
            <select v-model="contactOutcome">
              <option value="reached">已联系患者</option>
              <option value="scheduled">已约定随访</option>
              <option value="missed">无人接听</option>
              <option value="urgent">需要医生复核</option>
            </select>
          </label>

          <label class="entry-field">
            <span>临床备注</span>
            <textarea v-model="clinicalNotes" placeholder="请输入联系情况、症状变化或后续安排..." />
          </label>

          <div class="contact-entry-footer">
            <button class="secondary-button" type="button" @click="emit('open-archive', selectedTask.patientId)">打开档案</button>
            <button class="primary-button" type="button" :disabled="savingContactLog || loadingTaskAction" @click="saveContactEntry">
              {{ savingContactLog || loadingTaskAction ? '保存中...' : '保存记录' }}
            </button>
          </div>

          <div class="contact-entry-actions">
            <button class="text-link" type="button" @click="emit('open-patient', selectedTask.patientId)">打开患者详情</button>
            <button class="text-link" type="button" @click="markCompleted(selectedTask)">完成任务</button>
            <button class="text-link" type="button" @click="markClosed(selectedTask)">关闭任务</button>
          </div>
        </template>

        <div v-else class="empty-state-card compact-empty">请选择一条随访任务后再录入联系记录。</div>
      </aside>
    </section>
  </section>
</template>

<style scoped>
.followup-workbench {
  display: grid;
  gap: 22px;
}

.followup-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.followup-header p {
  margin: 8px 0 0;
  color: rgba(63, 72, 73, 0.84);
}

.followup-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.followup-filters input {
  min-width: 260px;
}

.followup-ledger-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) 480px;
  gap: 18px;
  align-items: start;
}

.ledger-board {
  min-width: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.ledger-column {
  min-width: 0;
  display: grid;
  gap: 14px;
  padding: 8px 0 0;
}

.ledger-column-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px;
  font-family: var(--ws-font-headline);
  font-size: 13px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.ledger-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.accent-danger {
  background: var(--ws-error);
}

.accent-info {
  background: #8cd2d7;
}

.accent-success {
  background: var(--ws-primary);
}

.ledger-count {
  margin-left: auto;
  min-width: 28px;
  height: 28px;
  display: inline-grid;
  place-items: center;
  border-radius: 999px;
  background: rgba(224, 227, 228, 0.88);
  font-size: 13px;
  letter-spacing: 0;
}

.ledger-stack {
  display: grid;
  gap: 14px;
}

.ledger-card {
  display: grid;
  gap: 12px;
  cursor: pointer;
}

.ledger-card.active {
  box-shadow:
    var(--ws-shadow-card),
    inset 4px 0 0 var(--ws-primary);
}

.ledger-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.ledger-card-head p,
.ledger-card-copy {
  margin: 0;
  color: rgba(63, 72, 73, 0.82);
  line-height: 1.5;
}

.ledger-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: rgba(63, 72, 73, 0.72);
}

.ledger-card-meta strong {
  color: var(--ws-on-surface);
}

.contact-entry-panel {
  display: grid;
  gap: 18px;
  padding: 26px 28px;
}

.contact-entry-head {
  display: grid;
  gap: 10px;
}

.entry-field {
  display: grid;
  gap: 8px;
}

.entry-field span {
  font-family: var(--ws-font-headline);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.method-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.method-row .secondary-button.active {
  background: linear-gradient(135deg, var(--ws-primary), var(--ws-primary-container));
  color: white;
  box-shadow: 0 16px 24px rgba(0, 67, 71, 0.16);
}

.contact-entry-footer,
.contact-entry-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.contact-entry-actions {
  padding-top: 4px;
}

.compact-empty {
  min-height: 220px;
}

@media (max-width: 1320px) {
  .followup-ledger-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1100px) {
  .ledger-board {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .followup-header {
    display: grid;
  }

  .followup-filters {
    display: grid;
  }

  .followup-filters input {
    min-width: 0;
  }
}
</style>
