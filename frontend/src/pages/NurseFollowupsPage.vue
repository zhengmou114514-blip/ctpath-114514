<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  addPatientContactLog,
  createPatientOutpatientTask,
  getFlowBoard,
  getFollowupWorklist,
  getPatientCase,
  getPatients,
  restoreAuthSession,
  updatePatientOutpatientTaskStatus,
} from '../services/api'
import type { ContactLog, FlowBoardRow, FollowupTaskRow, PatientSummary } from '../services/types'

type ContactLogRow = ContactLog & {
  patientId: string
  patientName: string
}

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const followups = ref<FollowupTaskRow[]>([])
const flowRows = ref<FlowBoardRow[]>([])
const contactLogs = ref<ContactLogRow[]>([])
const patients = ref<PatientSummary[]>([])
const selectedTaskKey = ref('')
const showCreateDialog = ref(false)
const showContactDialog = ref(false)
const showStatusDialog = ref(false)

const currentUser = computed(() => restoreAuthSession()?.doctor ?? null)
const today = new Date().toISOString().slice(0, 10)

const taskForm = reactive({
  patientId: '',
  taskType: '电话随访',
  dueDate: today,
  note: '',
  owner: currentUser.value?.name || '随访护士',
})

const contactForm = reactive({
  contactTime: new Date().toISOString().slice(0, 16),
  contactType: 'phone' as ContactLog['contactType'],
  contactTarget: 'patient' as ContactLog['contactTarget'],
  contactResult: 'reached' as ContactLog['contactResult'],
  note: '',
  nextContactDate: '',
})

const statusForm = reactive({
  status: 'Completed',
  note: '',
})

const selectedTask = computed(() => {
  if (!followups.value.length) return null
  return followups.value.find((item) => taskKey(item) === selectedTaskKey.value) ?? followups.value[0]
})

const selectedPatient = computed(() => patients.value.find((item) => item.patientId === selectedTask.value?.patientId) ?? null)
const selectedPatientLogs = computed(() =>
  contactLogs.value.filter((item) => item.patientId === selectedTask.value?.patientId).slice(0, 4)
)

const todayFollowups = computed(() =>
  followups.value.filter((item) => item.dueDate <= today && !isClosedStatus(item.status))
)
const missedContacts = computed(() => contactLogs.value.filter((item) => item.contactResult === 'missed'))
const doctorReviewRows = computed(() =>
  followups.value.filter((item) => normalizeStatus(item.status).includes('review')).concat(
    flowRows.value
      .filter((item) => item.flowStatus.toLowerCase().includes('review') || item.flowStatus.includes('复核'))
      .map((item) => ({
        taskId: null,
        patientId: item.patientId,
        patientName: item.patientName,
        primaryDisease: item.primaryDisease,
        riskLevel: item.riskLevel,
        dataSupport: item.dataSupport,
        dueDate: item.lastVisit,
        owner: '医生',
        priority: 'medium',
        taskType: '医生复核',
        status: item.flowStatus,
        source: 'followup',
        lastActionBy: null,
        lastActionAt: null,
      }) satisfies FollowupTaskRow)
  )
)
const completedTasks = computed(() => followups.value.filter((item) => isClosedStatus(item.status)))

function taskKey(item: FollowupTaskRow) {
  return item.taskId || `${item.patientId}-${item.taskType}-${item.dueDate}`
}

function normalizeStatus(value: string) {
  return String(value || '').trim().toLowerCase().replace(/\s+/g, '_')
}

function isClosedStatus(value: string) {
  const status = normalizeStatus(value)
  return ['completed', 'closed', 'done', '已完成', '已关闭'].includes(status)
}

function archiveNumber(patientId: string) {
  const patient = patients.value.find((item) => item.patientId === patientId)
  return patient?.medicalRecordNumber || `MRN-${patientId.replace(/\D/g, '').padStart(4, '0')}`
}

function riskLabel(value: string) {
  const raw = String(value || '').toLowerCase()
  if (raw.includes('high') || raw.includes('高')) return '高风险'
  if (raw.includes('medium') || raw.includes('中')) return '中风险'
  return '低风险'
}

function riskClass(value: string) {
  const label = riskLabel(value)
  if (label === '高风险') return 'risk-high'
  if (label === '中风险') return 'risk-medium'
  return 'risk-low'
}

function statusLabel(value: string) {
  const labels: Record<string, string> = {
    pending: '待随访',
    Pending: '待随访',
    completed: '已完成',
    Completed: '已完成',
    closed: '已关闭',
    Closed: '已关闭',
    pending_review: '待医生复核',
    Pending_Review: '待医生复核',
    review: '待医生复核',
  }
  return labels[value] ?? labels[normalizeStatus(value)] ?? value
}

function contactResultLabel(value: ContactLog['contactResult']) {
  const labels = {
    reached: '已接通',
    missed: '未接通',
    scheduled: '已预约',
    urgent: '需加急',
  }
  return labels[value] ?? value
}

function selectTask(item: FollowupTaskRow) {
  selectedTaskKey.value = taskKey(item)
}

async function loadContactLogs(items: FollowupTaskRow[]) {
  const uniquePatientIds = [...new Set(items.map((item) => item.patientId))].slice(0, 16)
  const cases = await Promise.all(
    uniquePatientIds.map(async (patientId) => {
      try {
        return await getPatientCase(patientId)
      } catch {
        return null
      }
    })
  )

  contactLogs.value = cases
    .filter((patient): patient is NonNullable<typeof patient> => patient !== null)
    .flatMap((patient) =>
      patient.contactLogs.map((log) => ({
        ...log,
        patientId: patient.patientId,
        patientName: patient.name,
      }))
    )
    .sort((left, right) => right.contactTime.localeCompare(left.contactTime))
}

async function reload() {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const [worklist, flowBoard, patientList] = await Promise.all([getFollowupWorklist(), getFlowBoard(), getPatients()])
    followups.value = worklist.items
    flowRows.value = flowBoard.items
    patients.value = patientList
    await loadContactLogs(worklist.items)
    const firstTask = worklist.items[0]
    if (!selectedTask.value && firstTask) {
      selectedTaskKey.value = taskKey(firstTask)
    }
  } catch {
    errorMessage.value = '当前随访任务加载失败，请检查后端服务或稍后刷新。'
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  taskForm.patientId = selectedTask.value?.patientId || patients.value[0]?.patientId || ''
  taskForm.taskType = '电话随访'
  taskForm.dueDate = today
  taskForm.note = ''
  taskForm.owner = currentUser.value?.name || '随访护士'
  showCreateDialog.value = true
}

function openContactDialog(task = selectedTask.value) {
  if (!task) return
  selectTask(task)
  contactForm.contactTime = new Date().toISOString().slice(0, 16)
  contactForm.contactType = 'phone'
  contactForm.contactTarget = 'patient'
  contactForm.contactResult = 'reached'
  contactForm.note = ''
  contactForm.nextContactDate = ''
  showContactDialog.value = true
}

function openStatusDialog(task = selectedTask.value, nextStatus = 'Completed') {
  if (!task) return
  selectTask(task)
  statusForm.status = nextStatus
  statusForm.note = ''
  showStatusDialog.value = true
}

async function submitCreateTask() {
  if (!taskForm.patientId) {
    errorMessage.value = '请选择患者后再新建随访任务。'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    const patient = patients.value.find((item) => item.patientId === taskForm.patientId)
    const updated = await createPatientOutpatientTask(taskForm.patientId, {
      category: 'recheck',
      title: taskForm.taskType,
      owner: taskForm.owner,
      dueDate: taskForm.dueDate,
      priority: patient?.riskLevel?.toLowerCase().includes('high') ? 'high' : 'medium',
      note: taskForm.note || '慢病患者随访任务',
      status: 'Pending',
      source: 'nurse-workstation',
      actorUsername: currentUser.value?.username,
      actorName: currentUser.value?.name,
    })
    showCreateDialog.value = false
    selectedTaskKey.value = `${updated.patientId}-${taskForm.taskType}-${taskForm.dueDate}`
    ElMessage.success('随访任务已创建')
    await reload()
  } catch {
    errorMessage.value = '随访任务保存失败，请检查后端服务或稍后重试。'
  } finally {
    saving.value = false
  }
}

async function submitContactLog() {
  const task = selectedTask.value
  if (!task) return
  saving.value = true
  errorMessage.value = ''
  try {
    await addPatientContactLog(task.patientId, {
      contactTime: contactForm.contactTime,
      contactType: contactForm.contactType,
      contactTarget: contactForm.contactTarget,
      contactResult: contactForm.contactResult,
      note: contactForm.note,
      nextContactDate: contactForm.nextContactDate || undefined,
      actorUsername: currentUser.value?.username,
      actorName: currentUser.value?.name,
    })
    showContactDialog.value = false
    ElMessage.success('联系记录已追加')
    await reload()
  } catch {
    errorMessage.value = '联系记录保存失败，请检查后端服务或稍后重试。'
  } finally {
    saving.value = false
  }
}

async function submitStatusUpdate() {
  const task = selectedTask.value
  if (!task?.taskId) {
    errorMessage.value = '该任务缺少任务编号，无法更新状态。'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    await updatePatientOutpatientTaskStatus(task.patientId, task.taskId, {
      status: statusForm.status,
      actorUsername: currentUser.value?.username,
      actorName: currentUser.value?.name,
    })
    showStatusDialog.value = false
    ElMessage.success('随访状态已更新')
    await reload()
  } catch {
    errorMessage.value = '随访状态更新失败，请检查后端服务或稍后重试。'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void reload()
})
</script>

<template>
  <section class="nurse-followups-page workstation-page">
    <header class="workstation-page-header followup-header">
      <div>
        <p class="eyebrow">随访管理模块</p>
        <h1>护士随访工作台</h1>
        <p>围绕今日随访、未接通、医生复核和联系记录完成慢病患者随访闭环管理。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" :disabled="loading" @click="reload">刷新</button>
        <button class="primary-button" type="button" @click="openCreateDialog">新建随访任务</button>
      </div>
    </header>

    <div v-if="errorMessage" class="inline-alert error">{{ errorMessage }}</div>
    <div v-else-if="successMessage" class="inline-alert success">{{ successMessage }}</div>

    <section class="followup-metrics">
      <article class="metric-card">
        <span>今日随访</span>
        <strong>{{ todayFollowups.length }}</strong>
      </article>
      <article class="metric-card">
        <span>未接通</span>
        <strong>{{ missedContacts.length }}</strong>
      </article>
      <article class="metric-card">
        <span>待医生复核</span>
        <strong>{{ doctorReviewRows.length }}</strong>
      </article>
      <article class="metric-card">
        <span>已完成</span>
        <strong>{{ completedTasks.length }}</strong>
      </article>
    </section>

    <section class="followup-layout">
      <main class="clinical-card task-list-card">
        <div class="section-header">
          <div>
            <h2>随访任务列表</h2>
            <p>今日任务、未接通任务和待医生复核任务统一在此处理。</p>
          </div>
        </div>

        <div v-if="loading" class="table-state">正在加载随访任务...</div>
        <div v-else-if="!followups.length" class="empty-state-card compact">
          <h3>暂无随访任务</h3>
          <p>可新建随访任务，或稍后刷新查看后端同步结果。</p>
          <button class="primary-button" type="button" @click="openCreateDialog">新建随访任务</button>
        </div>

        <table v-else class="followup-table">
          <thead>
            <tr>
              <th>任务编号</th>
              <th>患者姓名</th>
              <th>档案号</th>
              <th>随访类型</th>
              <th>风险等级</th>
              <th>负责人</th>
              <th>截止日期</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in followups"
              :key="taskKey(item)"
              :class="{ selected: taskKey(item) === taskKey(selectedTask || item) }"
              @click="selectTask(item)"
            >
              <td>{{ item.taskId || taskKey(item) }}</td>
              <td><strong>{{ item.patientName }}</strong></td>
              <td>{{ archiveNumber(item.patientId) }}</td>
              <td>{{ item.taskType }}</td>
              <td><span class="risk-pill" :class="riskClass(item.riskLevel)">{{ riskLabel(item.riskLevel) }}</span></td>
              <td>{{ item.owner }}</td>
              <td>{{ item.dueDate }}</td>
              <td>{{ statusLabel(item.status) }}</td>
              <td>
                <div class="row-actions">
                  <button class="text-action" type="button" @click.stop="openContactDialog(item)">联系记录</button>
                  <button class="text-action" type="button" @click.stop="openStatusDialog(item, 'Completed')">更新状态</button>
                  <button class="text-action" type="button" @click.stop="openStatusDialog(item, 'pending_review')">医生复核</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </main>

      <aside class="clinical-card task-detail-card">
        <div class="section-header">
          <div>
            <p class="eyebrow">任务详情</p>
            <h2>{{ selectedTask ? selectedTask.patientName : '请选择任务' }}</h2>
          </div>
          <button class="secondary-button" type="button" :disabled="!selectedTask" @click="openContactDialog()">追加联系</button>
        </div>

        <template v-if="selectedTask">
          <section class="detail-block patient-summary">
            <h3>患者摘要</h3>
            <dl>
              <div>
                <dt>档案号</dt>
                <dd>{{ archiveNumber(selectedTask.patientId) }}</dd>
              </div>
              <div>
                <dt>疾病</dt>
                <dd>{{ selectedTask.primaryDisease }}</dd>
              </div>
              <div>
                <dt>风险</dt>
                <dd>{{ riskLabel(selectedTask.riskLevel) }}</dd>
              </div>
              <div>
                <dt>联系电话</dt>
                <dd>{{ selectedPatient?.phone || '档案待补充' }}</dd>
              </div>
            </dl>
          </section>

          <section class="detail-block">
            <h3>任务说明</h3>
            <p>{{ selectedTask.taskType }}，由 {{ selectedTask.owner }} 负责，截止日期 {{ selectedTask.dueDate }}。</p>
          </section>

          <section class="detail-block">
            <h3>最近联系记录</h3>
            <div v-if="selectedPatientLogs.length" class="mini-record-list">
              <p v-for="item in selectedPatientLogs" :key="item.logId">
                <strong>{{ item.contactTime }}</strong>
                <span>{{ contactResultLabel(item.contactResult) }}：{{ item.note }}</span>
              </p>
            </div>
            <p v-else class="muted-line">暂无联系记录，可点击“追加联系”。</p>
          </section>

          <section class="detail-block">
            <h3>随访结果</h3>
            <p>{{ statusLabel(selectedTask.status) }}</p>
          </section>

          <section class="detail-block">
            <h3>下一步计划</h3>
            <p>{{ selectedTask.lastActionAt ? `最近更新：${selectedTask.lastActionAt}` : '根据本次联系结果安排复诊、再次联系或提交医生复核。' }}</p>
          </section>

          <section class="detail-block">
            <h3>状态更新时间线</h3>
            <div class="status-timeline">
              <p><strong>创建任务</strong><span>{{ selectedTask.dueDate }}</span></p>
              <p v-if="selectedTask.lastActionAt"><strong>{{ selectedTask.lastActionBy || '护士' }}</strong><span>{{ selectedTask.lastActionAt }}</span></p>
              <p><strong>当前状态</strong><span>{{ statusLabel(selectedTask.status) }}</span></p>
            </div>
          </section>
        </template>

        <div v-else class="empty-state-card compact">
          <h3>暂无选中任务</h3>
          <p>请从左侧任务列表选择一条随访任务。</p>
        </div>
      </aside>
    </section>

    <el-dialog v-model="showCreateDialog" title="新建随访任务" width="520px">
      <div class="dialog-form">
        <label class="field">
          <span>选择患者</span>
          <select v-model="taskForm.patientId">
            <option v-for="patient in patients" :key="patient.patientId" :value="patient.patientId">
              {{ patient.name }} / {{ archiveNumber(patient.patientId) }}
            </option>
          </select>
        </label>
        <label class="field">
          <span>随访类型</span>
          <select v-model="taskForm.taskType">
            <option>电话随访</option>
            <option>复诊提醒</option>
            <option>用药依从性随访</option>
            <option>异常指标回访</option>
          </select>
        </label>
        <label class="field">
          <span>计划日期</span>
          <input v-model="taskForm.dueDate" type="date" />
        </label>
        <label class="field">
          <span>负责人</span>
          <input v-model="taskForm.owner" type="text" />
        </label>
        <label class="field full-span">
          <span>说明</span>
          <textarea v-model="taskForm.note" rows="3" placeholder="填写随访原因、注意事项或医生交代内容"></textarea>
        </label>
      </div>
      <template #footer>
        <button class="secondary-button" type="button" @click="showCreateDialog = false">取消</button>
        <button class="primary-button" type="button" :disabled="saving" @click="submitCreateTask">保存</button>
      </template>
    </el-dialog>

    <el-dialog v-model="showContactDialog" title="追加联系记录" width="520px">
      <div class="dialog-form">
        <label class="field">
          <span>联系时间</span>
          <input v-model="contactForm.contactTime" type="datetime-local" />
        </label>
        <label class="field">
          <span>联系方式</span>
          <select v-model="contactForm.contactType">
            <option value="phone">电话</option>
            <option value="family">家属</option>
            <option value="wechat">微信</option>
            <option value="outpatient">门诊</option>
          </select>
        </label>
        <label class="field">
          <span>联系对象</span>
          <select v-model="contactForm.contactTarget">
            <option value="patient">患者本人</option>
            <option value="emergency_contact">紧急联系人</option>
          </select>
        </label>
        <label class="field">
          <span>联系结果</span>
          <select v-model="contactForm.contactResult">
            <option value="reached">已接通</option>
            <option value="missed">未接通</option>
            <option value="scheduled">已预约</option>
            <option value="urgent">需加急</option>
          </select>
        </label>
        <label class="field">
          <span>下次联系</span>
          <input v-model="contactForm.nextContactDate" type="date" />
        </label>
        <label class="field full-span">
          <span>随访结果</span>
          <textarea v-model="contactForm.note" rows="3" placeholder="记录患者反馈、用药情况、是否需要医生复核"></textarea>
        </label>
      </div>
      <template #footer>
        <button class="secondary-button" type="button" @click="showContactDialog = false">取消</button>
        <button class="primary-button" type="button" :disabled="saving" @click="submitContactLog">保存联系记录</button>
      </template>
    </el-dialog>

    <el-dialog v-model="showStatusDialog" title="更新随访状态" width="460px">
      <div class="dialog-form one-column">
        <label class="field">
          <span>状态</span>
          <select v-model="statusForm.status">
            <option value="Pending">待随访</option>
            <option value="Completed">已完成</option>
            <option value="Closed">已关闭</option>
            <option value="pending_review">待医生复核</option>
          </select>
        </label>
        <label class="field">
          <span>备注</span>
          <textarea v-model="statusForm.note" rows="3" placeholder="说明状态变化原因"></textarea>
        </label>
      </div>
      <template #footer>
        <button class="secondary-button" type="button" @click="showStatusDialog = false">取消</button>
        <button class="primary-button" type="button" :disabled="saving" @click="submitStatusUpdate">提交</button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.nurse-followups-page {
  display: grid;
  gap: 12px;
}

.followup-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.followup-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.followup-metrics .metric-card {
  min-height: 68px;
  padding: 12px 16px;
}

.followup-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 12px;
  align-items: start;
}

.task-list-card,
.task-detail-card {
  display: grid;
  gap: 12px;
}

.followup-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  border: 1px solid #d5e6ef;
  background: #fff;
}

.followup-table th,
.followup-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #d5e6ef;
  color: #243f4d;
  font-size: 13px;
  text-align: left;
  vertical-align: top;
  word-break: break-word;
}

.followup-table th {
  background: #edf7fc;
  color: #275d70;
  font-weight: 800;
}

.followup-table tr {
  cursor: pointer;
}

.followup-table tr.selected,
.followup-table tbody tr:hover {
  background: #f0fbfb;
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
}

.text-action {
  padding: 0;
  border: 0;
  background: transparent;
  color: #006f86;
  cursor: pointer;
  font-weight: 800;
}

.table-state {
  min-height: 180px;
  display: grid;
  place-items: center;
  border: 1px dashed #b7d1de;
  color: #527384;
}

.detail-block {
  display: grid;
  gap: 8px;
  padding: 10px;
  border: 1px solid #d5e6ef;
  border-radius: 4px;
  background: #fff;
}

.detail-block h3 {
  margin: 0;
  color: #003c43;
  font-size: 16px;
}

.detail-block p,
.muted-line {
  margin: 0;
  color: #526772;
  line-height: 1.6;
}

.patient-summary dl {
  display: grid;
  gap: 6px;
  margin: 0;
}

.patient-summary div {
  display: grid;
  grid-template-columns: 80px minmax(0, 1fr);
  gap: 8px;
}

.patient-summary dt,
.patient-summary dd {
  margin: 0;
  font-size: 13px;
}

.patient-summary dt {
  color: #527384;
  font-weight: 700;
}

.patient-summary dd {
  color: #243f4d;
  font-weight: 800;
}

.mini-record-list,
.status-timeline {
  display: grid;
  gap: 8px;
}

.mini-record-list p,
.status-timeline p {
  display: grid;
  gap: 2px;
  margin: 0;
  padding: 8px;
  border-radius: 3px;
  background: #f7fbfd;
}

.mini-record-list strong,
.status-timeline strong {
  color: #003c43;
}

.mini-record-list span,
.status-timeline span {
  color: #526772;
  font-size: 13px;
}

.dialog-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.dialog-form.one-column {
  grid-template-columns: 1fr;
}

.full-span {
  grid-column: 1 / -1;
}

.field {
  display: grid;
  gap: 6px;
}

.field span {
  color: #275d70;
  font-weight: 800;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  min-height: 34px;
  border: 1px solid #bfd4df;
  border-radius: 4px;
  padding: 7px 9px;
  background: #fff;
}

@media (max-width: 1180px) {
  .followup-layout {
    grid-template-columns: 1fr;
  }

  .followup-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .followup-header,
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .followup-metrics,
  .dialog-form {
    grid-template-columns: 1fr;
  }

  .full-span {
    grid-column: auto;
  }
}
</style>
