<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { ContactLogCreatePayload, FlowBoardRow, FollowupTaskRow, PatientCase } from '../services/types'

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
  selectedPatient?: PatientCase | null
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
const clinicalNotes = ref('已完成首次电话联系，待补充患者反馈与下一次随访计划。')
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

function riskLabel(key: 'high' | 'medium' | 'low') {
  if (key === 'high') return '高风险'
  if (key === 'medium') return '中风险'
  return '低风险'
}

function archiveSourceLabel(value?: string) {
  if (value === 'community_referral') return '社区转诊'
  if (value === 'outpatient') return '门诊建档'
  if (value === 'discharge_followup') return '出院随访'
  if (value === 'manual') return '手工录入'
  return value || '--'
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
          label: '任务进入工作台',
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
const selectedPatientContact = computed(() => props.selectedPatient ?? null)
const selectedFlowSnapshot = computed(() => {
  const patientId = selectedTask.value?.patientId || selectedPatientContact.value?.patientId
  if (!patientId) return null
  return props.flowBoardItems.find((item) => item.patientId === patientId) || null
})

const pendingCount = computed(() => filteredTasks.value.filter((item) => !item.completed).length)
const urgentCount = computed(() => filteredTasks.value.filter((item) => item.riskKey === 'high' || item.needsReview).length)
const completedCount = computed(() => filteredTasks.value.filter((item) => item.completed).length)

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
    { key: 'pending', label: '待联系', accent: 'accent-danger', items: pending },
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

function markReached(item: FollowupTaskRow, note = '已联系到患者，并完成本次随访沟通。') {
  const state = ensureState(item)
  state.unreached = false
  state.needsReview = false
  appendHistory(item, '联系成功', 'Contacted', note)
  submitContact(item, 'reached', note, state.nextFollowupDate)
}

function markUnreached(item: FollowupTaskRow, note = '本次未联系到患者，建议按计划再次随访。') {
  const state = ensureState(item)
  state.unreached = true
  appendHistory(item, '联系未果', 'Unreached', note)
  submitContact(item, 'missed', note, state.nextFollowupDate)
}

function markNeedReview(item: FollowupTaskRow, note = '患者反馈存在异常，已转入医生复核。') {
  const state = ensureState(item)
  state.needsReview = true
  appendHistory(item, '转医生复核', 'Need Review', note)
  submitContact(item, 'urgent', note, state.nextFollowupDate)
}

function markCompleted(item: FollowupTaskRow) {
  appendHistory(item, '随访完成', 'Completed', '本次随访任务已完成。')
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
  appendHistory(item, '任务关闭', 'Closed', '该随访任务已关闭。')
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
  const note = clinicalNotes.value.trim() || '已记录本次联系结果。'

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
  clinicalNotes.value = `${task.patientName}：${task.taskType}`
  contactOutcome.value = task.unreached ? 'missed' : task.needsReview ? 'urgent' : 'reached'
})
</script>

<template>
  <section class="followup-workbench">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">随访工作台 / 联系闭环</p>
        <h1>随访账本与联系记录</h1>
        <p>集中处理待联系患者、病程流转、联系记录与任务状态更新，不把模型治理或档案管理内容混进本工作区。</p>
      </div>
      <div class="header-actions">
        <label class="field compact">
          <span>关键词</span>
          <input v-model="keyword" type="text" placeholder="患者姓名 / 编号 / 任务类型" />
        </label>
        <label class="field compact">
          <span>风险</span>
          <select v-model="riskFilter">
            <option value="all">全部</option>
            <option value="high">高风险</option>
            <option value="medium">中风险</option>
            <option value="low">低风险</option>
          </select>
        </label>
        <label class="field compact">
          <span>时间</span>
          <select v-model="dateFilter">
            <option value="all">全部</option>
            <option value="today">今日</option>
            <option value="overdue">逾期</option>
            <option value="next7">未来 7 天</option>
          </select>
        </label>
      </div>
    </header>

    <section class="metric-grid three">
      <article class="metric-card">
        <span>待办任务</span>
        <strong>{{ pendingCount }}</strong>
      </article>
      <article class="metric-card">
        <span>需优先处理</span>
        <strong>{{ urgentCount }}</strong>
      </article>
      <article class="metric-card">
        <span>已完成</span>
        <strong>{{ completedCount }}</strong>
      </article>
    </section>

    <section class="followup-ledger-layout">
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
                <span class="risk-pill" :class="`risk-${item.riskKey}`">{{ riskLabel(item.riskKey) }}</span>
              </div>
              <p class="ledger-card-copy">{{ item.primaryDisease }} / {{ item.patientId }}</p>
              <div class="ledger-card-meta">
                <span>负责人</span>
                <strong>{{ item.owner }}</strong>
              </div>
              <div class="ledger-card-meta">
                <span>下次随访</span>
                <strong>{{ item.nextFollowupDate || item.dueDate }}</strong>
              </div>
              <div class="ledger-card-meta">
                <span>病程流转</span>
                <strong>{{ item.flow?.flowStatus || '待同步' }}</strong>
              </div>
            </article>
          </div>
        </article>
      </section>

      <aside class="clinical-card contact-entry-panel">
        <div class="contact-entry-head">
          <p class="eyebrow">联系记录录入</p>
          <h3>随访联系表单</h3>
        </div>

        <template v-if="selectedTask">
          <section class="contact-relationship-card">
            <div class="contact-relationship-head">
              <p class="eyebrow">联系方式关系</p>
              <h4>患者本人 / 紧急联系人 / 个案管理</h4>
            </div>

            <div class="relationship-grid">
              <div class="relationship-item">
                <span>患者本人</span>
                <strong>{{ selectedPatientContact?.name || selectedTask.patientName }}</strong>
                <small>{{ selectedPatientContact?.phone || '未登记' }}</small>
              </div>
              <div class="relationship-item">
                <span>紧急联系人</span>
                <strong>{{ selectedPatientContact?.emergencyContactName || '--' }}</strong>
                <small>{{ selectedPatientContact?.emergencyContactRelation || '--' }}</small>
              </div>
              <div class="relationship-item">
                <span>联系人电话</span>
                <strong>{{ selectedPatientContact?.emergencyContactPhone || '--' }}</strong>
                <small>档案来源：{{ archiveSourceLabel(selectedPatientContact?.archiveSource) }}</small>
              </div>
              <div class="relationship-item">
                <span>责任医生 / 管理师</span>
                <strong>{{ selectedPatientContact?.primaryDoctor || selectedTask.owner }}</strong>
                <small>{{ selectedPatientContact?.caseManager || '随访工作台' }}</small>
              </div>
            </div>
          </section>

          <section class="contact-flow-card">
            <div class="contact-relationship-head">
              <p class="eyebrow">病情流转</p>
              <h4>当前阶段与下一步动作</h4>
            </div>

            <div class="relationship-grid single-row">
              <div class="relationship-item">
                <span>当前阶段</span>
                <strong>{{ selectedFlowSnapshot?.currentStage || selectedPatientContact?.currentStage || '--' }}</strong>
                <small>最后就诊：{{ selectedFlowSnapshot?.lastVisit || selectedPatientContact?.lastVisit || '--' }}</small>
              </div>
              <div class="relationship-item">
                <span>病程状态</span>
                <strong>{{ selectedFlowSnapshot?.flowStatus || selectedTask.flow?.flowStatus || '--' }}</strong>
                <small>风险：{{ selectedFlowSnapshot?.riskLevel || selectedTask.riskLevel || '--' }}</small>
              </div>
              <div class="relationship-item">
                <span>下一步动作</span>
                <strong>{{ selectedFlowSnapshot?.nextAction || selectedTask.flow?.nextAction || '待医生确认' }}</strong>
                <small>数据支持：{{ selectedFlowSnapshot?.dataSupport || selectedTask.dataSupport || '--' }}</small>
              </div>
            </div>
          </section>

          <label class="entry-field">
            <span>患者</span>
            <input :value="selectedTask.patientName" type="text" readonly />
          </label>

          <label class="entry-field">
            <span>任务类型</span>
            <input :value="selectedTask.taskType" type="text" readonly />
          </label>

          <div class="entry-field">
            <span>联系方式</span>
            <div class="method-row">
              <button class="secondary-button" :class="{ active: contactMethod === 'call' }" type="button" @click="contactMethod = 'call'">
                电话
              </button>
              <button class="secondary-button" :class="{ active: contactMethod === 'message' }" type="button" @click="contactMethod = 'message'">
                微信
              </button>
            </div>
          </div>

          <label class="entry-field">
            <span>联系结果</span>
            <select v-model="contactOutcome">
              <option value="reached">联系成功</option>
              <option value="scheduled">已约定复诊</option>
              <option value="missed">未联系到</option>
              <option value="urgent">需医生复核</option>
            </select>
          </label>

          <label class="entry-field">
            <span>随访说明</span>
            <textarea v-model="clinicalNotes" placeholder="记录患者反馈、复诊计划、用药依从性与下一步动作。" />
          </label>

          <div class="contact-entry-footer">
            <button class="secondary-button" type="button" @click="emit('open-archive', selectedTask.patientId)">打开档案</button>
            <button class="primary-button" type="button" :disabled="savingContactLog || loadingTaskAction" @click="saveContactEntry">
              {{ savingContactLog || loadingTaskAction ? '保存中...' : '保存联系记录' }}
            </button>
          </div>

          <div class="contact-entry-actions">
            <button class="text-link" type="button" @click="emit('open-patient', selectedTask.patientId)">打开患者详情</button>
            <button class="text-link" type="button" @click="markCompleted(selectedTask)">完成任务</button>
            <button class="text-link" type="button" @click="markClosed(selectedTask)">关闭任务</button>
          </div>

          <div class="history-list">
            <article v-for="history in selectedTask.history.slice(0, 5)" :key="history.id" class="history-row">
              <strong>{{ history.label }}</strong>
              <span>{{ formatDateTime(history.at) }}</span>
              <p>{{ history.note }}</p>
            </article>
          </div>
        </template>

        <div v-else class="empty-state-card compact-empty">请先从左侧账本选择一个随访任务，再录入联系记录。</div>
      </aside>
    </section>
  </section>
</template>

<style scoped>
.followup-workbench,
.followup-ledger-layout,
.ledger-board,
.ledger-stack,
.history-list {
  display: grid;
  gap: 22px;
}

.followup-ledger-layout {
  grid-template-columns: minmax(0, 1.4fr) 480px;
  align-items: start;
}

.ledger-board {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.ledger-column {
  display: grid;
  gap: 14px;
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

.ledger-card {
  display: grid;
  gap: 12px;
  cursor: pointer;
}

.ledger-card.active {
  box-shadow: var(--ws-shadow-card), inset 4px 0 0 var(--ws-primary);
}

.ledger-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.ledger-card-head p,
.ledger-card-copy,
.ledger-card-meta span,
.history-row p {
  margin: 0;
  color: rgba(63, 72, 73, 0.82);
  line-height: 1.5;
}

.ledger-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.ledger-card-meta strong {
  color: var(--ws-on-surface);
}

.contact-entry-panel {
  display: grid;
  gap: 18px;
  padding: 26px 28px;
}

.contact-relationship-card,
.contact-flow-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 20px;
  background: rgba(246, 248, 248, 0.95);
  border: 1px solid rgba(198, 208, 210, 0.85);
}

.contact-relationship-head {
  display: grid;
  gap: 4px;
}

.contact-relationship-head h4 {
  margin: 0;
  font-size: 16px;
  color: var(--ws-on-surface);
}

.relationship-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.relationship-grid.single-row {
  grid-template-columns: 1fr;
}

.relationship-item {
  display: grid;
  gap: 6px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(210, 217, 219, 0.95);
}

.relationship-item span,
.relationship-item small {
  color: rgba(63, 72, 73, 0.82);
}

.relationship-item strong {
  color: var(--ws-on-surface);
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

.entry-field input,
.entry-field select,
.entry-field textarea {
  width: 100%;
  min-height: 48px;
  border: 1px solid #d5dde0;
  border-radius: 14px;
  background: #fff;
  padding: 0 14px;
  font: inherit;
  color: #181c1e;
}

.entry-field textarea {
  min-height: 120px;
  padding: 14px;
  resize: vertical;
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

.history-row {
  display: grid;
  gap: 6px;
  border-radius: 14px;
  background: rgba(241, 244, 245, 0.92);
  padding: 14px 16px;
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
</style>
