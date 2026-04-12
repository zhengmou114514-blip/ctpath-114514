<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ContactLogCreatePayload, FlowBoardRow, FollowupTaskRow } from '../services/types'
import FollowupQuickContactCard from './FollowupQuickContactCard.vue'

type FollowupView = 'tasks' | 'flow' | 'quick'

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

const activeView = ref<FollowupView>('tasks')
const taskPage = ref(1)
const flowPage = ref(1)
const quickPage = ref(1)
const pageSize = 5
const priorityFilter = ref<'全部优先级' | 'high' | 'medium' | 'low'>('全部优先级')
const statusFilter = ref('全部状态')

const statusOptions = computed(() => {
  const values = Array.from(new Set(props.followupItems.map((item) => item.status)))
  return ['全部状态', ...values]
})

const filteredFollowups = computed(() =>
  props.followupItems.filter((item) => {
    const matchPriority = priorityFilter.value === '全部优先级' || item.priority === priorityFilter.value
    const matchStatus = statusFilter.value === '全部状态' || item.status === statusFilter.value
    return matchPriority && matchStatus
  })
)

function flowStatusRank(value: string) {
  const lowered = value.toLowerCase()
  if (value.includes('接诊中') || lowered.includes('progress')) return 0
  if (value.includes('待复核') || lowered.includes('review')) return 1
  if (value.includes('候诊') || lowered.includes('waiting')) return 2
  if (value.includes('已完成') || lowered.includes('completed')) return 3
  return 4
}

const sortedFlowBoard = computed(() =>
  [...props.flowBoardItems].sort((left, right) => {
    const byStatus = flowStatusRank(left.flowStatus) - flowStatusRank(right.flowStatus)
    if (byStatus !== 0) return byStatus
    return left.lastVisit.localeCompare(right.lastVisit)
  })
)

const quickPatients = computed(() => sortedFlowBoard.value.slice(0, 12))

const quickContactCandidates = computed(() => {
  const map = new Map<string, { patientId: string; label: string }>()
  for (const item of props.followupItems) {
    if (!map.has(item.patientId)) {
      map.set(item.patientId, {
        patientId: item.patientId,
        label: `${item.patientName} / ${item.primaryDisease}`,
      })
    }
  }
  for (const item of props.flowBoardItems) {
    if (!map.has(item.patientId)) {
      map.set(item.patientId, {
        patientId: item.patientId,
        label: `${item.patientName} / ${item.primaryDisease}`,
      })
    }
  }
  return [...map.values()]
})

const summary = computed(() => {
  const items = props.followupItems
  return {
    total: items.length,
    high: items.filter((item) => item.priority === 'high').length,
    overdue: items.filter((item) => item.status.includes('逾期') || item.status.toLowerCase().includes('overdue')).length,
    review: props.flowBoardItems.filter((item) => item.flowStatus.includes('待复核')).length,
  }
})

const taskTotalPages = computed(() => Math.max(1, Math.ceil(filteredFollowups.value.length / pageSize)))
const flowTotalPages = computed(() => Math.max(1, Math.ceil(sortedFlowBoard.value.length / pageSize)))
const quickTotalPages = computed(() => Math.max(1, Math.ceil(quickPatients.value.length / pageSize)))

const pagedTasks = computed(() => {
  const start = (taskPage.value - 1) * pageSize
  return filteredFollowups.value.slice(start, start + pageSize)
})

const pagedFlowBoard = computed(() => {
  const start = (flowPage.value - 1) * pageSize
  return sortedFlowBoard.value.slice(start, start + pageSize)
})

const pagedQuickPatients = computed(() => {
  const start = (quickPage.value - 1) * pageSize
  return quickPatients.value.slice(start, start + pageSize)
})

function priorityTone(level: string) {
  if (level === 'high') return 'risk-high'
  if (level === 'medium') return 'risk-medium'
  return 'risk-low'
}

function priorityLabel(level: string) {
  if (level === 'high') return '高优先'
  if (level === 'medium') return '中优先'
  if (level === 'low') return '低优先'
  return level
}

function supportLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value
}

function stageLabel(value: string) {
  if (value === 'Early') return '早期'
  if (value === 'Mid') return '中期'
  if (value === 'Late') return '晚期'
  return value
}

function isSelected(patientId: string) {
  return Boolean(props.selectedPatientId) && props.selectedPatientId === patientId
}

function canOperateTask(item: FollowupTaskRow) {
  return item.source === 'outpatient-task' && Boolean(item.taskId) && item.status !== '已完成' && item.status !== '已关闭'
}

function switchView(next: FollowupView) {
  activeView.value = next
}

function prevTaskPage() {
  taskPage.value = Math.max(1, taskPage.value - 1)
}

function nextTaskPage() {
  taskPage.value = Math.min(taskTotalPages.value, taskPage.value + 1)
}

function prevFlowPage() {
  flowPage.value = Math.max(1, flowPage.value - 1)
}

function nextFlowPage() {
  flowPage.value = Math.min(flowTotalPages.value, flowPage.value + 1)
}

function prevQuickPage() {
  quickPage.value = Math.max(1, quickPage.value - 1)
}

function nextQuickPage() {
  quickPage.value = Math.min(quickTotalPages.value, quickPage.value + 1)
}
</script>

<template>
  <section class="module-shell followup-dashboard">
    <article class="card module-hero">
      <div>
        <p class="eyebrow">随访任务</p>
        <h3>慢病门诊随访工作台</h3>
        <p class="page-copy">集中查看检查申请、复查计划、流程状态和重点患者入口，避免在多个页面之间来回切换。</p>
      </div>
      <div class="module-hero-meta">
        <div class="summary-chip">
          <span>任务总数</span>
          <strong>{{ summary.total }}</strong>
        </div>
        <div class="summary-chip">
          <span>高优先任务</span>
          <strong>{{ summary.high }}</strong>
        </div>
        <div v-if="selectedPatientId" class="summary-chip summary-chip-accent">
          <span>当前定位患者</span>
          <strong>{{ selectedPatientId }}</strong>
        </div>
      </div>
    </article>

    <section class="followup-summary-grid">
      <article class="card summary-tile">
        <span>待处理任务</span>
        <strong>{{ summary.total }}</strong>
        <small>当前随访和门诊任务总量</small>
      </article>
      <article class="card summary-tile danger">
        <span>逾期任务</span>
        <strong>{{ summary.overdue }}</strong>
        <small>建议优先处理已逾期任务</small>
      </article>
      <article class="card summary-tile">
        <span>待复核患者</span>
        <strong>{{ summary.review }}</strong>
        <small>流程状态已进入待复核的患者</small>
      </article>
      <article class="card summary-tile">
        <span>快捷入口</span>
        <strong>{{ quickPatients.length }}</strong>
        <small>按流程状态排序后的重点患者</small>
      </article>
    </section>

    <FollowupQuickContactCard
      :candidates="quickContactCandidates"
      :selected-patient-id="props.selectedPatientId"
      :saving="props.savingContactLog"
      @submit="emit('submit-contact-log', $event)"
      @open-patient="emit('open-patient', $event)"
    />

    <article class="card followup-tab-card">
      <div class="followup-tabbar">
        <button class="secondary-button" :class="{ active: activeView === 'tasks' }" @click="switchView('tasks')">任务列表</button>
        <button class="secondary-button" :class="{ active: activeView === 'flow' }" @click="switchView('flow')">流程状态板</button>
        <button class="secondary-button" :class="{ active: activeView === 'quick' }" @click="switchView('quick')">患者快捷入口</button>
      </div>

      <section v-if="activeView === 'tasks'" class="followup-tab-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">任务列表</p>
            <h3>随访与门诊任务</h3>
          </div>
          <span class="panel-meta">第 {{ taskPage }} / {{ taskTotalPages }} 页</span>
        </div>

        <div class="followup-filter-grid">
          <label class="field">
            <span>优先级</span>
            <select v-model="priorityFilter">
              <option value="全部优先级">全部优先级</option>
              <option value="high">高优先</option>
              <option value="medium">中优先</option>
              <option value="low">低优先</option>
            </select>
          </label>

          <label class="field">
            <span>任务状态</span>
            <select v-model="statusFilter">
              <option v-for="item in statusOptions" :key="item" :value="item">{{ item }}</option>
            </select>
          </label>
        </div>

        <div v-if="pagedTasks.length" class="followup-list">
          <article
            v-for="item in pagedTasks"
            :key="`${item.patientId}-${item.taskId ?? item.taskType}-${item.dueDate}`"
            class="followup-task-card"
            :class="{ 'is-highlighted': isSelected(item.patientId) }"
          >
            <div class="followup-task-main">
              <strong>{{ item.patientName }} / {{ item.patientId }}</strong>
              <span>{{ item.primaryDisease }} / {{ item.taskType }}</span>
              <small>责任人：{{ item.owner }} / 截止：{{ item.dueDate }}</small>
            </div>

            <div class="followup-task-side">
              <span class="risk-pill" :class="priorityTone(item.priority)">{{ item.status }}</span>
              <small>{{ priorityLabel(item.priority) }} / 数据支持：{{ supportLabel(item.dataSupport) }}</small>
              <small v-if="item.lastActionBy || item.lastActionAt">
                最近操作：{{ item.lastActionBy || '系统' }}<span v-if="item.lastActionAt"> / {{ item.lastActionAt }}</span>
              </small>
              <div class="card-actions followup-actions">
                <button class="text-button" @click="emit('open-patient', item.patientId)">打开患者</button>
                <button class="text-button" @click="emit('open-archive', item.patientId)">打开档案</button>
                <button
                  v-if="canOperateTask(item)"
                  class="text-button"
                  @click="emit('complete-task', { patientId: item.patientId, taskId: item.taskId! })"
                >
                  标记完成
                </button>
                <button
                  v-if="canOperateTask(item)"
                  class="text-button"
                  @click="emit('close-task', { patientId: item.patientId, taskId: item.taskId! })"
                >
                  关闭任务
                </button>
              </div>
            </div>
          </article>
        </div>

        <article v-else-if="!loading" class="empty-card compact">
          <p>当前筛选条件下没有匹配的任务。</p>
        </article>

        <div class="pagination-bar">
          <span class="panel-meta">每页 {{ pageSize }} 条</span>
          <div class="archive-footer-actions">
            <button class="secondary-button" :disabled="taskPage <= 1" @click="prevTaskPage">上一页</button>
            <button class="secondary-button" :disabled="taskPage >= taskTotalPages" @click="nextTaskPage">下一页</button>
          </div>
        </div>
      </section>

      <section v-else-if="activeView === 'flow'" class="followup-tab-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">流程状态板</p>
            <h3>患者处理进度</h3>
          </div>
          <span class="panel-meta">第 {{ flowPage }} / {{ flowTotalPages }} 页</span>
        </div>

        <div v-if="pagedFlowBoard.length" class="flow-board-list">
          <article
            v-for="item in pagedFlowBoard"
            :key="`${item.patientId}-${item.flowStatus}`"
            class="flow-board-row"
            :class="{ 'is-highlighted': isSelected(item.patientId) }"
          >
            <div class="queue-main">
              <strong>{{ item.patientName }} / {{ item.patientId }}</strong>
              <span>{{ item.primaryDisease }} / {{ stageLabel(item.currentStage) }}</span>
              <small>最近就诊：{{ item.lastVisit }} / 数据支持：{{ supportLabel(item.dataSupport) }}</small>
            </div>
            <div class="queue-side">
              <span class="risk-pill" :class="priorityTone(item.riskLevel)">{{ item.flowStatus }}</span>
              <small>{{ item.nextAction }}</small>
            </div>
          </article>
        </div>

        <article v-else-if="!loading" class="empty-card compact">
          <p>当前没有可展示的流程状态数据。</p>
        </article>

        <div class="pagination-bar">
          <span class="panel-meta">每页 {{ pageSize }} 条</span>
          <div class="archive-footer-actions">
            <button class="secondary-button" :disabled="flowPage <= 1" @click="prevFlowPage">上一页</button>
            <button class="secondary-button" :disabled="flowPage >= flowTotalPages" @click="nextFlowPage">下一页</button>
          </div>
        </div>
      </section>

      <section v-else class="followup-tab-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">快捷入口</p>
            <h3>重点患者快捷访问</h3>
          </div>
          <span class="panel-meta">第 {{ quickPage }} / {{ quickTotalPages }} 页</span>
        </div>

        <div v-if="pagedQuickPatients.length" class="quick-entry-list">
          <button
            v-for="item in pagedQuickPatients"
            :key="`${item.patientId}-${item.flowStatus}`"
            class="quick-entry-row"
            :class="{ 'is-highlighted': isSelected(item.patientId) }"
            @click="emit('open-patient', item.patientId)"
          >
            <div class="queue-main">
              <strong>{{ item.patientName }}</strong>
              <span>{{ item.patientId }} / {{ item.primaryDisease }}</span>
              <small>{{ item.nextAction }}</small>
            </div>
            <div class="queue-side">
              <span class="risk-pill" :class="priorityTone(item.riskLevel)">{{ item.flowStatus }}</span>
              <small>{{ item.lastVisit }}</small>
            </div>
          </button>
        </div>

        <article v-else-if="!loading" class="empty-card compact">
          <p>当前没有可用的患者快捷入口。</p>
        </article>

        <div class="pagination-bar">
          <span class="panel-meta">每页 {{ pageSize }} 条</span>
          <div class="archive-footer-actions">
            <button class="secondary-button" :disabled="quickPage <= 1" @click="prevQuickPage">上一页</button>
            <button class="secondary-button" :disabled="quickPage >= quickTotalPages" @click="nextQuickPage">下一页</button>
          </div>
        </div>
      </section>
    </article>
  </section>
</template>
