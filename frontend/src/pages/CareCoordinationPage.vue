<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  appendCoordinationNote,
  createCoordinationItem,
  getCoordinationBoard,
  updateCoordinationItem,
  updateCoordinationItemStatus,
} from '../services/api'
import type {
  CoordinationBoardResponse,
  CoordinationCategory,
  CoordinationItem,
  CoordinationItemUpsertRequest,
  CoordinationNoteCreateRequest,
  CoordinationParticipant,
  CoordinationParticipantRole,
  CoordinationStatus,
  CoordinationStatusUpdateRequest,
  CoordinationSummaryItem,
} from '../services/types'

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const selectedId = ref('')
const board = ref<CoordinationBoardResponse | null>(null)
const items = ref<CoordinationItem[]>([])

const keyword = ref('')
const statusFilter = ref<'all' | CoordinationStatus>('all')
const categoryFilter = ref<'all' | CoordinationCategory>('all')

const noteForm = reactive<CoordinationNoteCreateRequest>({
  action: '备注',
  note: '',
  operatorUsername: '',
  operatorName: '',
  operatorRole: 'doctor',
})

const statusForm = reactive<CoordinationStatusUpdateRequest>({
  status: 'open',
  note: '',
  operatorUsername: '',
  operatorName: '',
  operatorRole: 'doctor',
})

const itemForm = reactive<CoordinationItemUpsertRequest>(createEmptyItemForm())

const summaryItems = computed<CoordinationSummaryItem[]>(() => board.value?.summary ?? [])
const selectedItem = computed(() => items.value.find((item) => item.coordinationId === selectedId.value) ?? null)

const filteredItems = computed(() => {
  const keywordValue = keyword.value.trim().toLowerCase()
  return items.value.filter((item) => {
    if (statusFilter.value !== 'all' && item.status !== statusFilter.value) return false
    if (categoryFilter.value !== 'all' && item.category !== categoryFilter.value) return false
    if (!keywordValue) return true
    return [
      item.coordinationId,
      item.patientId,
      item.patientName,
      item.primaryDisease,
      item.currentStage,
      item.ownerName,
      item.summary,
      item.nextAction,
    ]
      .join(' ')
      .toLowerCase()
      .includes(keywordValue)
  })
})

function createEmptyItemForm(): CoordinationItemUpsertRequest {
  return {
    coordinationId: '',
    patientId: '',
    patientName: '',
    primaryDisease: '',
    currentStage: '',
    riskLevel: 'Medium Risk',
    category: 'followup',
    status: 'open',
    ownerRole: 'nurse',
    ownerName: '',
    nextAction: '',
    dueDate: new Date().toISOString().slice(0, 10),
    summary: '',
    participants: defaultParticipantsArray(),
  }
}

function defaultParticipantsArray(): CoordinationParticipant[] {
  return [
    { role: 'doctor', name: '', relation: '责任医生', phone: '' },
    { role: 'nurse', name: '', relation: '个案管理师', phone: '' },
    { role: 'pharmacist', name: '', relation: '药师', phone: '' },
    { role: 'archivist', name: '', relation: '档案员', phone: '' },
  ]
}

function formatTime(value: string) {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function statusLabel(value: CoordinationStatus) {
  const map: Record<CoordinationStatus, string> = {
    open: '待处理',
    in_progress: '处理中',
    blocked: '阻塞',
    done: '已完成',
    closed: '已关闭',
  }
  return map[value]
}

function categoryLabel(value: CoordinationCategory) {
  const map: Record<CoordinationCategory, string> = {
    handoff: '交接',
    medication_review: '药物复核',
    followup: '随访',
    referral: '转诊',
    family_contact: '家属联系',
    case_review: '病例复核',
  }
  return map[value]
}

function roleLabel(value: CoordinationParticipantRole) {
  const map: Record<CoordinationParticipantRole, string> = {
    doctor: '医生',
    nurse: '护士',
    pharmacist: '药师',
    archivist: '档案员',
    admin: '管理员',
  }
  return map[value]
}

function fillItemForm(item: CoordinationItem) {
  selectedId.value = item.coordinationId
  itemForm.coordinationId = item.coordinationId
  itemForm.patientId = item.patientId
  itemForm.patientName = item.patientName
  itemForm.primaryDisease = item.primaryDisease
  itemForm.currentStage = item.currentStage
  itemForm.riskLevel = item.riskLevel
  itemForm.category = item.category
  itemForm.status = item.status
  itemForm.ownerRole = item.ownerRole
  itemForm.ownerName = item.ownerName
  itemForm.nextAction = item.nextAction
  itemForm.dueDate = item.dueDate
  itemForm.summary = item.summary
  itemForm.participants = item.participants.length ? item.participants.map((participant) => ({ ...participant })) : defaultParticipantsArray()

  statusForm.status = item.status
  statusForm.note = ''
  statusForm.operatorUsername = ''
  statusForm.operatorName = ''
  statusForm.operatorRole = item.ownerRole

  noteForm.action = '备注'
  noteForm.note = ''
  noteForm.operatorUsername = ''
  noteForm.operatorName = ''
  noteForm.operatorRole = item.ownerRole
}

function resetItemForm() {
  selectedId.value = ''
  Object.assign(itemForm, createEmptyItemForm())
  noteForm.action = '备注'
  noteForm.note = ''
  noteForm.operatorUsername = ''
  noteForm.operatorName = ''
  noteForm.operatorRole = 'doctor'
  statusForm.status = 'open'
  statusForm.note = ''
  statusForm.operatorUsername = ''
  statusForm.operatorName = ''
  statusForm.operatorRole = 'doctor'
  successMessage.value = ''
  errorMessage.value = ''
}

function openItem(item: CoordinationItem) {
  fillItemForm(item)
  successMessage.value = ''
  errorMessage.value = ''
}

async function loadBoard(selectId = selectedId.value) {
  loading.value = true
  errorMessage.value = ''
  try {
    const result = await getCoordinationBoard()
    board.value = result
    items.value = result.items
    const next = result.items.find((item) => item.coordinationId === selectId) ?? result.items[0]
    if (next) {
      fillItemForm(next)
      selectedId.value = next.coordinationId
    } else {
      resetItemForm()
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '医护协调数据加载失败。'
  } finally {
    loading.value = false
  }
}

async function saveItem() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const payload = {
      ...itemForm,
      participants: (itemForm.participants || []).map((participant) => ({
        ...participant,
        name: participant.name.trim(),
        relation: participant.relation.trim(),
        phone: participant.phone.trim(),
      })),
    }

    if (!payload.coordinationId) {
      errorMessage.value = '协同编号不能为空。'
      return
    }

    if (selectedId.value) {
      await updateCoordinationItem(selectedId.value, payload)
      successMessage.value = '协同任务已更新。'
      await loadBoard(selectedId.value)
    } else {
      const created = await createCoordinationItem(payload)
      successMessage.value = '协同任务已创建。'
      await loadBoard(created.coordinationId)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存协同任务失败。'
  } finally {
    saving.value = false
  }
}

async function saveStatus() {
  if (!selectedItem.value) {
    errorMessage.value = '请先选择一个协同任务。'
    return
  }

  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await updateCoordinationItemStatus(selectedItem.value.coordinationId, statusForm)
    successMessage.value = '协同状态已更新。'
    await loadBoard(selectedItem.value.coordinationId)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新协同状态失败。'
  } finally {
    saving.value = false
  }
}

async function addNote() {
  if (!selectedItem.value) {
    errorMessage.value = '请先选择一个协同任务。'
    return
  }

  if (!noteForm.note.trim()) {
    errorMessage.value = '备注内容不能为空。'
    return
  }

  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await appendCoordinationNote(selectedItem.value.coordinationId, noteForm)
    successMessage.value = '备注已追加。'
    await loadBoard(selectedItem.value.coordinationId)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '追加备注失败。'
  } finally {
    saving.value = false
  }
}

function clearFilters() {
  keyword.value = ''
  statusFilter.value = 'all'
  categoryFilter.value = 'all'
}

onMounted(() => {
  void loadBoard()
})
</script>

<template>
  <section class="workspace-page coordination-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">医护协调</p>
        <h1>医护协同工作台</h1>
        <p>参考 openhis 的协同交接方式，把患者联系人、责任人、下一步动作和流转备注放到同一页里。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="clearFilters">清空筛选</button>
        <button class="primary-button" type="button" @click="resetItemForm">新建协同</button>
      </div>
    </header>

    <section class="metric-grid four">
      <article v-for="item in summaryItems" :key="item.label" class="metric-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.trend }}</small>
      </article>
    </section>

    <div v-if="errorMessage" class="inline-alert error">{{ errorMessage }}</div>
    <div v-else-if="successMessage" class="inline-alert success">{{ successMessage }}</div>

    <section class="coordination-layout">
      <article class="clinical-card coordination-list-card">
        <div class="section-header">
          <div>
            <h2>协同列表</h2>
            <p>左侧显示待处理、处理中、已完成的协同流转，点击后在右侧查看详情。</p>
          </div>
          <button class="secondary-button" type="button" :disabled="loading" @click="loadBoard()">刷新</button>
        </div>

        <div class="filter-grid">
          <label class="field">
            <span>关键词</span>
            <input v-model="keyword" type="text" placeholder="患者、责任人、病种、备注" />
          </label>
          <label class="field">
            <span>状态</span>
            <select v-model="statusFilter">
              <option value="all">全部</option>
              <option value="open">待处理</option>
              <option value="in_progress">处理中</option>
              <option value="blocked">阻塞</option>
              <option value="done">已完成</option>
              <option value="closed">已关闭</option>
            </select>
          </label>
          <label class="field">
            <span>分类</span>
            <select v-model="categoryFilter">
              <option value="all">全部</option>
              <option value="handoff">交接</option>
              <option value="medication_review">药物复核</option>
              <option value="followup">随访</option>
              <option value="referral">转诊</option>
              <option value="family_contact">家属联系</option>
              <option value="case_review">病例复核</option>
            </select>
          </label>
        </div>

        <div v-if="!filteredItems.length && !loading" class="empty-state-card compact">
          <h3>暂无协同记录</h3>
          <p>请调整筛选条件，或点击“新建协同”创建一条患者协同任务。</p>
        </div>

        <div v-else class="coordination-table">
          <div class="coordination-head">
            <span>患者</span>
            <span>分类 / 责任人</span>
            <span>状态</span>
            <span>下一步动作</span>
          </div>
          <button
            v-for="item in filteredItems"
            :key="item.coordinationId"
            class="coordination-row"
            :class="{ selected: item.coordinationId === selectedId }"
            type="button"
            @click="openItem(item)"
          >
            <div class="coordination-cell">
              <strong>{{ item.patientName }}</strong>
              <span>{{ item.patientId }} / {{ item.primaryDisease }}</span>
            </div>
            <div class="coordination-cell">
              <strong>{{ categoryLabel(item.category) }}</strong>
              <span>{{ roleLabel(item.ownerRole) }} · {{ item.ownerName }}</span>
            </div>
            <div class="coordination-cell">
              <span class="status-pill" :class="item.status === 'in_progress' ? 'warning' : item.status === 'blocked' ? 'danger' : item.status === 'done' || item.status === 'closed' ? 'muted' : 'success'">
                {{ statusLabel(item.status) }}
              </span>
            </div>
            <div class="coordination-cell">
              <strong>{{ item.nextAction }}</strong>
              <span>{{ formatTime(item.dueDate) }}</span>
            </div>
          </button>
        </div>
      </article>

      <aside class="coordination-side">
        <article class="clinical-card coordination-detail-card">
          <div class="section-header">
            <div>
              <h2>协同详情</h2>
              <p>患者联系人、责任医生、药师和档案员的协同关系都集中在这里。</p>
            </div>
          </div>

          <div v-if="selectedItem" class="detail-summary">
            <div class="info-item">
              <span>患者</span>
              <strong>{{ selectedItem.patientName }}</strong>
            </div>
            <div class="info-item">
              <span>病种</span>
              <strong>{{ selectedItem.primaryDisease }}</strong>
            </div>
            <div class="info-item">
              <span>阶段</span>
              <strong>{{ selectedItem.currentStage }}</strong>
            </div>
            <div class="info-item">
              <span>负责人</span>
              <strong>{{ roleLabel(selectedItem.ownerRole) }} / {{ selectedItem.ownerName }}</strong>
            </div>
          </div>

          <div class="editor-grid">
            <label class="field full-span">
              <span>协同编号</span>
              <input v-model="itemForm.coordinationId" type="text" placeholder="coord-PID1001" />
            </label>
            <label class="field">
              <span>患者编号</span>
              <input v-model="itemForm.patientId" type="text" placeholder="PID1001" />
            </label>
            <label class="field">
              <span>患者姓名</span>
              <input v-model="itemForm.patientName" type="text" />
            </label>
            <label class="field">
              <span>病种</span>
              <input v-model="itemForm.primaryDisease" type="text" />
            </label>
            <label class="field">
              <span>阶段</span>
              <input v-model="itemForm.currentStage" type="text" />
            </label>
            <label class="field">
              <span>风险</span>
              <input v-model="itemForm.riskLevel" type="text" />
            </label>
            <label class="field">
              <span>分类</span>
              <select v-model="itemForm.category">
                <option value="handoff">交接</option>
                <option value="medication_review">药物复核</option>
                <option value="followup">随访</option>
                <option value="referral">转诊</option>
                <option value="family_contact">家属联系</option>
                <option value="case_review">病例复核</option>
              </select>
            </label>
            <label class="field">
              <span>状态</span>
              <select v-model="itemForm.status">
                <option value="open">待处理</option>
                <option value="in_progress">处理中</option>
                <option value="blocked">阻塞</option>
                <option value="done">已完成</option>
                <option value="closed">已关闭</option>
              </select>
            </label>
            <label class="field">
              <span>负责人角色</span>
              <select v-model="itemForm.ownerRole">
                <option value="doctor">医生</option>
                <option value="nurse">护士</option>
                <option value="pharmacist">药师</option>
                <option value="archivist">档案员</option>
                <option value="admin">管理员</option>
              </select>
            </label>
            <label class="field">
              <span>负责人姓名</span>
              <input v-model="itemForm.ownerName" type="text" />
            </label>
            <label class="field">
              <span>下一步动作</span>
              <input v-model="itemForm.nextAction" type="text" />
            </label>
            <label class="field">
              <span>计划日期</span>
              <input v-model="itemForm.dueDate" type="date" />
            </label>
            <label class="field full-span">
              <span>概要说明</span>
              <textarea v-model="itemForm.summary" rows="3"></textarea>
            </label>
          </div>

          <div class="participant-grid">
            <div class="section-header compact">
              <h3>协同参与人</h3>
              <p>与 openhis 类似，直接展示责任医生、护士、药师和档案员的关系。</p>
            </div>
            <div class="participant-card" v-for="participant in itemForm.participants" :key="participant.role">
              <strong>{{ roleLabel(participant.role) }}</strong>
              <input v-model="participant.name" type="text" placeholder="姓名" />
              <input v-model="participant.relation" type="text" placeholder="关系" />
              <input v-model="participant.phone" type="text" placeholder="联系方式" />
            </div>
          </div>

          <div class="form-actions">
            <button class="secondary-button" type="button" @click="resetItemForm">新建</button>
            <button class="primary-button" type="button" :disabled="saving" @click="saveItem">
              {{ saving ? '保存中...' : selectedId ? '更新协同' : '创建协同' }}
            </button>
          </div>
        </article>

        <article class="clinical-card coordination-status-card">
          <div class="section-header">
            <div>
              <h2>状态更新</h2>
              <p>协同状态变化后会进入审计流转。</p>
            </div>
          </div>
          <div class="editor-grid compact">
            <label class="field">
              <span>状态</span>
              <select v-model="statusForm.status">
                <option value="open">待处理</option>
                <option value="in_progress">处理中</option>
                <option value="blocked">阻塞</option>
                <option value="done">已完成</option>
                <option value="closed">已关闭</option>
              </select>
            </label>
            <label class="field full-span">
              <span>备注</span>
              <textarea v-model="statusForm.note" rows="3"></textarea>
            </label>
          </div>
          <div class="form-actions">
            <button class="primary-button" type="button" :disabled="saving || !selectedItem" @click="saveStatus">提交状态</button>
          </div>
        </article>

        <article class="clinical-card coordination-note-card">
          <div class="section-header">
            <div>
              <h2>协同备注</h2>
              <p>支持护士、药师、医生围绕同一患者追加沟通记录。</p>
            </div>
          </div>
          <div class="editor-grid compact">
            <label class="field">
              <span>动作</span>
              <input v-model="noteForm.action" type="text" />
            </label>
            <label class="field full-span">
              <span>备注内容</span>
              <textarea v-model="noteForm.note" rows="4"></textarea>
            </label>
          </div>
          <div class="form-actions">
            <button class="secondary-button" type="button" @click="noteForm.note = ''">清空</button>
            <button class="primary-button" type="button" :disabled="saving || !selectedItem" @click="addNote">追加备注</button>
          </div>
          <ul class="note-list" v-if="selectedItem">
            <li v-for="note in selectedItem.notes" :key="note.noteId">
              <span>{{ formatTime(note.createdAt) }} · {{ note.createdBy }}</span>
              <strong>{{ note.action }}</strong>
              <p>{{ note.note }}</p>
            </li>
          </ul>
        </article>
      </aside>
    </section>
  </section>
</template>

<style scoped>
.coordination-page,
.coordination-layout,
.coordination-side,
.coordination-table,
.filter-grid,
.editor-grid,
.participant-grid,
.note-list,
.detail-summary {
  display: grid;
  gap: 20px;
}

.coordination-layout {
  grid-template-columns: minmax(0, 1.4fr) minmax(360px, 0.92fr);
  align-items: start;
}

.coordination-side {
  position: sticky;
  top: 24px;
}

.coordination-list-card,
.coordination-detail-card,
.coordination-status-card,
.coordination-note-card {
  display: grid;
  gap: 16px;
}

.coordination-head,
.coordination-row {
  display: grid;
  grid-template-columns: 1.2fr 1.2fr 0.7fr 1.5fr;
  gap: 12px;
  align-items: center;
}

.coordination-head {
  padding: 0 8px;
  color: rgba(17, 24, 39, 0.62);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.coordination-row {
  width: 100%;
  text-align: left;
  padding: 14px 16px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
}

.coordination-row.selected,
.coordination-row:hover {
  border-color: rgba(15, 118, 110, 0.28);
  background: rgba(240, 253, 250, 0.9);
}

.coordination-cell {
  display: grid;
  gap: 4px;
}

.coordination-cell span {
  color: rgba(17, 24, 39, 0.58);
  font-size: 12px;
}

.detail-summary {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.section-header.compact {
  margin-bottom: 0;
}

.participant-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.participant-card {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(148, 163, 184, 0.14);
  display: grid;
  gap: 8px;
}

.note-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.note-list li {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.14);
  display: grid;
  gap: 4px;
}

.note-list span,
.note-list p {
  color: rgba(17, 24, 39, 0.58);
  font-size: 12px;
}

@media (max-width: 1200px) {
  .coordination-layout {
    grid-template-columns: 1fr;
  }

  .coordination-side {
    position: static;
  }
}

@media (max-width: 720px) {
  .coordination-head,
  .coordination-row,
  .detail-summary,
  .participant-grid {
    grid-template-columns: 1fr;
  }
}
</style>
