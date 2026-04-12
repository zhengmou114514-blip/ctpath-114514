<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { ContactLogCreatePayload, FlowBoardRow, FollowupTaskRow } from '../services/types'

type RiskFilter = 'all' | 'high' | 'medium' | 'low'
type DateFilter = 'all' | 'today' | 'overdue' | 'next7'

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
const filterUnreachedOnly = ref(false)
const filterReviewOnly = ref(false)
const keyword = ref('')

const selectedTaskKey = ref('')
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
          label: 'Task Loaded',
          status: item.status,
          at: initialAt,
          note: `Source: ${item.source}`,
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

    if (filterUnreachedOnly.value && !item.unreached) return false
    if (filterReviewOnly.value && !item.needsReview) return false

    const kw = keyword.value.trim().toLowerCase()
    if (kw) {
      const haystack = `${item.patientId} ${item.patientName} ${item.primaryDisease} ${item.taskType}`.toLowerCase()
      if (!haystack.includes(kw)) return false
    }

    return true
  })
})

const selectedTask = computed(() => filteredTasks.value.find((item) => taskKey(item) === selectedTaskKey.value) || null)

const todaySummary = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  const all = mergedTasks.value
  return {
    todayPending: all.filter((item) => item.dueDate === today && !item.completed).length,
    highRisk: all.filter((item) => item.riskKey === 'high' && !item.completed).length,
    completed: all.filter((item) => item.completed).length,
    unreached: all.filter((item) => item.unreached).length,
  }
})

const recentAdvice = computed(() => {
  if (!selectedTask.value) return []
  const flowAdvice = selectedTask.value.flow?.nextAction || ''
  return [
    flowAdvice,
    `Task recommendation: ${selectedTask.value.taskType}`,
    `Owner: ${selectedTask.value.owner}`,
  ].filter(Boolean)
})

const predictionChange = computed(() => {
  if (!selectedTask.value) return []
  const row = selectedTask.value
  return [
    `Current flow status: ${row.flow?.flowStatus || row.localStatus}`,
    `Risk level: ${row.riskLevel}`,
    `Data support: ${row.dataSupport}`,
  ]
})

const rightPanelHistory = computed(() => {
  if (!selectedTask.value) return []
  return [...selectedTask.value.history].sort((a, b) => b.at.localeCompare(a.at))
})

function riskToneClass(level: string): string {
  const key = riskLevelKey(level)
  return `risk-${key}`
}

function statusToneClass(status: string): string {
  const normalized = status.toLowerCase()
  if (normalized.includes('completed')) return 'status-completed'
  if (normalized.includes('review')) return 'status-review'
  if (normalized.includes('unreached') || normalized.includes('missed')) return 'status-unreached'
  if (normalized.includes('contacted')) return 'status-contacted'
  return 'status-pending'
}

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
    contactType: 'phone',
    contactTarget: 'patient',
    contactResult: result,
    note,
    nextContactDate: nextDate,
  }
  emit('submit-contact-log', { patientId: item.patientId, payload })
}

function markReached(item: FollowupTaskRow) {
  const state = ensureState(item)
  state.unreached = false
  state.needsReview = false
  appendHistory(item, 'Marked Contacted', 'Contacted', 'Patient reached by phone follow-up.')
  submitContact(item, 'reached', 'Reached during follow-up call.', state.nextFollowupDate)
}

function markUnreached(item: FollowupTaskRow) {
  const state = ensureState(item)
  state.unreached = true
  appendHistory(item, 'Marked Unreached', 'Unreached', 'No answer from patient contact.')
  submitContact(item, 'missed', 'No answer. Retry needed.', state.nextFollowupDate)
}

function markNeedReview(item: FollowupTaskRow) {
  const state = ensureState(item)
  state.needsReview = true
  appendHistory(item, 'Marked Need Review', 'Need Review', 'Nurse requested physician review.')
  submitContact(item, 'urgent', 'Need physician review based on follow-up findings.', state.nextFollowupDate)
}

function markCompleted(item: FollowupTaskRow) {
  appendHistory(item, 'Marked Completed', 'Completed', 'Follow-up cycle completed.')
  const key = taskKey(item)
  const current = localState[key]
  if (current) {
    current.unreached = false
    current.needsReview = false
  }
  if (item.source === 'outpatient-task' && item.taskId) {
    emit('complete-task', { patientId: item.patientId, taskId: item.taskId })
  }
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
</script>

<template>
  <section class="followup-workbench">
    <header class="top-metrics card">
      <article>
        <span>Today's Pending Follow-ups</span>
        <strong>{{ todaySummary.todayPending }}</strong>
        <p>Tasks due today and not completed.</p>
      </article>
      <article class="metric-high">
        <span>High-risk Priority</span>
        <strong>{{ todaySummary.highRisk }}</strong>
        <p>High-risk patients with unfinished tasks.</p>
      </article>
      <article class="metric-ok">
        <span>Completed</span>
        <strong>{{ todaySummary.completed }}</strong>
        <p>Current status is completed or closed.</p>
      </article>
      <article class="metric-warn">
        <span>Unreached</span>
        <strong>{{ todaySummary.unreached }}</strong>
        <p>Locally marked as not reached.</p>
      </article>
    </header>

    <section class="workbench-grid">
      <aside class="left-pane card">
        <h3>Todo Filters</h3>
        <label class="field">
          <span>Risk Level</span>
          <select v-model="riskFilter">
            <option value="all">All</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>

        <label class="field">
          <span>Date</span>
          <select v-model="dateFilter">
            <option value="all">All dates</option>
            <option value="today">Today</option>
            <option value="overdue">Overdue</option>
            <option value="next7">Next 7 days</option>
          </select>
        </label>

        <label class="field inline">
          <input v-model="filterUnreachedOnly" type="checkbox" />
          <span>Unreached only</span>
        </label>

        <label class="field inline">
          <input v-model="filterReviewOnly" type="checkbox" />
          <span>Needs review only</span>
        </label>

        <label class="field">
          <span>Search Patient</span>
          <input v-model="keyword" type="text" placeholder="patientId/name/disease" />
        </label>

        <div class="patient-list">
          <article
            v-for="item in filteredTasks"
            :key="taskKey(item)"
            class="patient-item"
            :class="{ active: selectedTaskKey === taskKey(item) }"
            @click="selectedTaskKey = taskKey(item)"
          >
            <div>
              <strong>{{ item.patientName }}</strong>
              <p>{{ item.patientId }} / {{ item.primaryDisease }}</p>
            </div>
            <div class="patient-item-right">
              <span class="risk-pill" :class="riskToneClass(item.riskLevel)">{{ item.riskLevel }}</span>
              <small>{{ item.dueDate }}</small>
            </div>
          </article>

          <p v-if="!filteredTasks.length" class="empty">No tasks under current filter.</p>
        </div>
      </aside>

      <main class="middle-pane card">
        <template v-if="selectedTask">
          <header class="panel-head">
            <div>
              <h3>Current Follow-up Summary</h3>
              <p>{{ selectedTask.patientName }} / {{ selectedTask.patientId }} / {{ selectedTask.primaryDisease }}</p>
            </div>
            <span class="status-pill" :class="statusToneClass(selectedTask.localStatus)">
              {{ selectedTask.localStatus }}
            </span>
          </header>

          <section class="summary-grid">
            <article>
              <span>Task Type</span>
              <strong>{{ selectedTask.taskType }}</strong>
            </article>
            <article>
              <span>Owner</span>
              <strong>{{ selectedTask.owner }}</strong>
            </article>
            <article>
              <span>Last Updated</span>
              <strong>{{ formatDateTime(selectedTask.localUpdatedAt) }}</strong>
            </article>
            <article>
              <span>Data Support</span>
              <strong>{{ selectedTask.dataSupport }}</strong>
            </article>
          </section>

          <section class="middle-block">
            <h4>Recent Advice</h4>
            <ul>
              <li v-for="(text, idx) in recentAdvice" :key="`advice-${idx}`">{{ text }}</li>
              <li v-if="!recentAdvice.length">No advice available.</li>
            </ul>
          </section>

          <section class="middle-block">
            <h4>Recent Prediction Change</h4>
            <ul>
              <li v-for="(text, idx) in predictionChange" :key="`pred-${idx}`">{{ text }}</li>
            </ul>
            <p class="todo-note">TODO(api): currently adapted from /api/worklists/followups + flow-board snapshot only.</p>
          </section>

          <section class="middle-block">
            <h4>Status Flow and Timestamps</h4>
            <div class="timeline">
              <article v-for="record in rightPanelHistory" :key="record.id" class="timeline-row">
                <div>
                  <strong>{{ record.label }}</strong>
                  <p>{{ record.status }} - {{ record.note }}</p>
                </div>
                <span>{{ formatDateTime(record.at) }}</span>
              </article>
            </div>
          </section>
        </template>

        <div v-else class="empty">Select one follow-up task on the left.</div>
      </main>

      <aside class="right-pane card">
        <template v-if="selectedTask">
          <section class="right-block">
            <h4>Contact Records</h4>
            <div class="timeline">
              <article v-for="record in rightPanelHistory.slice(0, 5)" :key="`contact-${record.id}`" class="timeline-row">
                <div>
                  <strong>{{ record.status }}</strong>
                  <p>{{ record.note }}</p>
                </div>
                <span>{{ formatDateTime(record.at) }}</span>
              </article>
            </div>
          </section>

          <section class="right-block">
            <h4>Next Follow-up Plan</h4>
            <label class="field">
              <span>Planned Date</span>
              <input
                type="date"
                :value="selectedTask.nextFollowupDate"
                @input="ensureState(selectedTask).nextFollowupDate = ($event.target as HTMLInputElement).value"
              />
            </label>
            <p class="plan-note">Owner: {{ selectedTask.owner }}, source: {{ selectedTask.source }}</p>
          </section>

          <section class="right-block">
            <h4>Quick Actions</h4>
            <div class="actions">
              <button class="secondary-button" :disabled="savingContactLog" @click="markReached(selectedTask)">Reached</button>
              <button class="secondary-button" :disabled="savingContactLog" @click="markUnreached(selectedTask)">Unreached</button>
              <button class="secondary-button" :disabled="savingContactLog" @click="markNeedReview(selectedTask)">Need Doctor Review</button>
              <button class="primary-button" :disabled="savingContactLog" @click="markCompleted(selectedTask)">Complete</button>
            </div>
            <div class="actions secondary">
              <button class="text-button" @click="emit('open-patient', selectedTask.patientId)">Open Patient Detail</button>
              <button class="text-button" @click="emit('open-archive', selectedTask.patientId)">Open Patient Archive</button>
            </div>
          </section>
        </template>

        <div v-else class="empty">Select a task before action.</div>
      </aside>
    </section>
  </section>
</template>

<style scoped>
.followup-workbench {
  display: grid;
  gap: 12px;
}

.card {
  border: 1px solid #cfd9e5;
  border-radius: 10px;
  background: #fff;
}

.top-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  padding: 12px;
}

.top-metrics article {
  border: 1px solid #d4dee9;
  border-radius: 8px;
  background: #f8fbff;
  padding: 10px;
  display: grid;
  gap: 4px;
}

.top-metrics span {
  color: #5b7388;
  font-size: 0.78rem;
}

.top-metrics strong {
  color: #10263c;
  font-size: 1.35rem;
}

.top-metrics p {
  margin: 0;
  color: #6b8195;
  font-size: 0.75rem;
}

.metric-high {
  background: #fff4f5 !important;
  border-color: #efc2c5 !important;
}

.metric-ok {
  background: #eef9f3 !important;
  border-color: #bde7d1 !important;
}

.metric-warn {
  background: #fff8eb !important;
  border-color: #efdbb2 !important;
}

.workbench-grid {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr) 360px;
  gap: 12px;
}

.left-pane,
.middle-pane,
.right-pane {
  padding: 12px;
  display: grid;
  gap: 10px;
  align-content: start;
}

.left-pane h3,
.middle-pane h3,
.right-pane h4 {
  margin: 0;
  color: #10263c;
}

.field {
  display: grid;
  gap: 4px;
}

.field span {
  color: #5f788d;
  font-size: 0.76rem;
}

.field input,
.field select {
  border: 1px solid #cfd9e5;
  border-radius: 8px;
  padding: 8px;
  font-size: 0.82rem;
  background: #fff;
}

.field.inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.patient-list {
  display: grid;
  gap: 8px;
}

.patient-item {
  border: 1px solid #d6e0eb;
  border-radius: 8px;
  padding: 8px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  cursor: pointer;
  background: #fbfdff;
}

.patient-item.active {
  border-color: #8fb3d6;
  background: #edf5fc;
}

.patient-item p {
  margin: 2px 0 0;
  color: #617a8f;
  font-size: 0.78rem;
}

.patient-item-right {
  display: grid;
  justify-items: end;
  gap: 4px;
}

.patient-item-right small {
  color: #617a8f;
  font-size: 0.74rem;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.panel-head p {
  margin: 4px 0 0;
  color: #617a8f;
  font-size: 0.82rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.summary-grid article {
  border: 1px solid #d6e0eb;
  border-radius: 8px;
  padding: 8px;
  background: #fbfdff;
  display: grid;
  gap: 4px;
}

.summary-grid span {
  color: #60798d;
  font-size: 0.76rem;
}

.summary-grid strong {
  color: #10263c;
  font-size: 0.86rem;
}

.middle-block,
.right-block {
  border: 1px solid #d6e0eb;
  border-radius: 8px;
  padding: 10px;
  background: #fbfdff;
  display: grid;
  gap: 8px;
}

.middle-block h4,
.right-block h4 {
  margin: 0;
  color: #14314a;
}

.middle-block ul {
  margin: 0;
  padding-left: 18px;
  color: #24445f;
  display: grid;
  gap: 4px;
  font-size: 0.82rem;
}

.todo-note {
  margin: 0;
  color: #8a641f;
  font-size: 0.76rem;
}

.timeline {
  display: grid;
  gap: 6px;
}

.timeline-row {
  border: 1px solid #d9e3ee;
  border-radius: 8px;
  padding: 8px;
  background: #fff;
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.timeline-row p {
  margin: 3px 0 0;
  color: #617a8f;
  font-size: 0.78rem;
}

.timeline-row span {
  color: #60798d;
  font-size: 0.75rem;
  white-space: nowrap;
}

.actions {
  display: grid;
  gap: 8px;
}

.actions.secondary {
  grid-template-columns: 1fr 1fr;
}

.plan-note {
  margin: 0;
  color: #60798d;
  font-size: 0.78rem;
}

.risk-pill,
.status-pill {
  display: inline-flex;
  border-radius: 999px;
  border: 1px solid transparent;
  padding: 2px 8px;
  font-size: 0.72rem;
  font-weight: 700;
  width: fit-content;
}

.risk-high {
  background: #fdeced;
  border-color: #efc2c5;
  color: #a4383f;
}

.risk-medium {
  background: #fff4e2;
  border-color: #efdbb2;
  color: #9b6518;
}

.risk-low {
  background: #e9f8f1;
  border-color: #bde7d1;
  color: #1d7b5c;
}

.status-pending {
  background: #eef3f9;
  border-color: #cfdae7;
  color: #3f6283;
}

.status-contacted {
  background: #e9f8f1;
  border-color: #bde7d1;
  color: #1d7b5c;
}

.status-unreached {
  background: #fff4e2;
  border-color: #efdbb2;
  color: #9b6518;
}

.status-review {
  background: #fdeced;
  border-color: #efc2c5;
  color: #a4383f;
}

.status-completed {
  background: #eaf2fb;
  border-color: #c7d8ec;
  color: #2f5f8f;
}

.empty {
  border: 1px dashed #c2d4e6;
  border-radius: 8px;
  padding: 14px;
  color: #627b90;
  text-align: center;
  font-size: 0.84rem;
}

@media (max-width: 1480px) {
  .workbench-grid {
    grid-template-columns: 1fr;
  }

  .top-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 840px) {
  .top-metrics {
    grid-template-columns: 1fr;
  }

  .summary-grid,
  .actions.secondary {
    grid-template-columns: 1fr;
  }
}
</style>