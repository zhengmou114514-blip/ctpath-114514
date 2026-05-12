<script setup lang="ts">
import { computed, ref } from 'vue'
import { addPatientContactLog, updatePatientOutpatientTaskStatus, createPatientOutpatientTask } from '../../services/api'
import type { OutpatientTask } from '../../services/types'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)
const tasks = computed(() => patient.value?.outpatientTasks ?? [])

const showContactDialog = ref(false)
const showStatusDialog = ref(false)
const showNewTaskDialog = ref(false)
const message = ref('')
const error = ref('')
const saving = ref(false)

const focusTask = ref<OutpatientTask | null>(null)
const contactForm = ref({
  contactType: 'phone' as 'phone' | 'family' | 'wechat' | 'outpatient',
  contactTarget: 'patient' as 'patient' | 'emergency_contact',
  contactResult: 'reached' as 'reached' | 'missed' | 'scheduled' | 'urgent',
  note: '',
  nextContactDate: '',
})
const statusForm = ref({ status: 'completed', note: '' })
const newTaskForm = ref({
  category: 'recheck' as 'exam' | 'recheck',
  title: '',
  owner: '',
  dueDate: '',
  priority: 'medium' as 'high' | 'medium' | 'low',
  note: '',
})

function openContactDialog() {
  contactForm.value = { contactType: 'phone', contactTarget: 'patient', contactResult: 'reached', note: '', nextContactDate: '' }
  showContactDialog.value = true
}

function openStatusDialog(task: OutpatientTask) {
  focusTask.value = task
  statusForm.value = { status: 'completed', note: '' }
  showStatusDialog.value = true
}

function openNewTaskDialog() {
  newTaskForm.value = { category: 'recheck', title: '', owner: '', dueDate: '', priority: 'medium', note: '' }
  showNewTaskDialog.value = true
}

function statusLabel(status: string) {
  if (status === 'completed') return '已完成'
  if (status === 'pending_review') return '待复核'
  if (status === 'in_progress') return '进行中'
  if (status === 'closed') return '已关闭'
  return status || '待执行'
}

function statusClass(status: string) {
  if (status === 'completed') return 'status-done'
  if (status === 'closed') return 'status-closed'
  if (status === 'pending_review') return 'status-review'
  return 'status-pending'
}

async function submitContactLog() {
  if (!patient.value) return
  saving.value = true
  error.value = ''
  try {
    const updated = await addPatientContactLog(patient.value.patientId, {
      contactTime: new Date().toISOString().slice(0, 19),
      contactType: contactForm.value.contactType,
      contactTarget: contactForm.value.contactTarget,
      contactResult: contactForm.value.contactResult,
      note: contactForm.value.note,
      nextContactDate: contactForm.value.nextContactDate || undefined,
    })
    workspace.selectedPatient = updated
    showContactDialog.value = false
    message.value = '联系记录已保存。'
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '保存联系记录失败。'
  } finally {
    saving.value = false
  }
}

async function submitStatusUpdate() {
  if (!patient.value || !focusTask.value) return
  saving.value = true
  error.value = ''
  try {
    const updated = await updatePatientOutpatientTaskStatus(
      patient.value.patientId,
      focusTask.value.taskId,
      { status: statusForm.value.status }
    )
    workspace.selectedPatient = updated
    showStatusDialog.value = false
    message.value = '任务状态已更新。'
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '更新状态失败。'
  } finally {
    saving.value = false
  }
}

async function submitNewTask() {
  if (!patient.value) return
  saving.value = true
  error.value = ''
  try {
    const updated = await createPatientOutpatientTask(patient.value.patientId, {
      category: newTaskForm.value.category,
      title: newTaskForm.value.title,
      owner: newTaskForm.value.owner,
      dueDate: newTaskForm.value.dueDate,
      priority: newTaskForm.value.priority,
      note: newTaskForm.value.note,
    })
    workspace.selectedPatient = updated
    showNewTaskDialog.value = false
    message.value = '随访任务已创建。'
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '创建任务失败。'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section v-if="patient" class="followups-page">
    <div class="section-header">
      <div>
        <p class="eyebrow">随访记录</p>
        <h2>患者随访闭环</h2>
      </div>
      <div class="action-row">
        <button class="secondary-button" type="button" @click="openContactDialog">追加联系记录</button>
        <button class="primary-button" type="button" @click="openNewTaskDialog">新建随访任务</button>
      </div>
    </div>

    <p v-if="message" class="success-line">{{ message }}</p>
    <p v-if="error" class="error-line">{{ error }}</p>

    <table class="followup-table">
      <thead>
        <tr>
          <th>任务</th>
          <th>类别</th>
          <th>负责人</th>
          <th>截止日期</th>
          <th>优先级</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in tasks" :key="item.taskId">
          <td><strong>{{ item.title }}</strong></td>
          <td>{{ item.category === 'exam' ? '检查' : '复诊' }}</td>
          <td>{{ item.owner }}</td>
          <td>{{ item.dueDate }}</td>
          <td>{{ item.priority === 'high' ? '高' : item.priority === 'low' ? '低' : '中' }}</td>
          <td><span class="status-pill" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span></td>
          <td>
            <button v-if="item.status !== 'completed' && item.status !== 'closed'" class="text-action" type="button" @click="openStatusDialog(item)">更新状态</button>
            <span v-else class="muted-text">-</span>
          </td>
        </tr>
      </tbody>
    </table>

    <article v-if="patient.contactLogs.length" class="clinical-card">
      <p class="eyebrow">最近联系记录</p>
      <h2>联系记录</h2>
      <div class="contact-list">
        <div v-for="log in patient.contactLogs.slice(0, 10)" :key="log.logId" class="contact-item">
          <strong>{{ log.contactTime }}</strong>
          <span>{{ log.contactType }} → {{ log.contactResult }}</span>
          <span>{{ log.note }}</span>
        </div>
      </div>
    </article>

    <dialog v-if="showContactDialog" class="dialog-overlay" open @click.self="showContactDialog = false">
      <form class="dialog-card" @submit.prevent="submitContactLog">
        <h2>追加联系记录</h2>
        <label>联系方式 <select v-model="contactForm.contactType">
          <option value="phone">电话</option>
          <option value="wechat">微信</option>
          <option value="family">家属</option>
          <option value="outpatient">门诊</option>
        </select></label>
        <label>联系对象 <select v-model="contactForm.contactTarget">
          <option value="patient">患者本人</option>
          <option value="emergency_contact">紧急联系人</option>
        </select></label>
        <label>联系结果 <select v-model="contactForm.contactResult">
          <option value="reached">已接通</option>
          <option value="missed">未接通</option>
          <option value="scheduled">已预约</option>
          <option value="urgent">需紧急处理</option>
        </select></label>
        <label>备注 <textarea v-model="contactForm.note" rows="3"></textarea></label>
        <label>下次联系日期 <input type="date" v-model="contactForm.nextContactDate" /></label>
        <div class="dialog-actions">
          <button type="button" class="secondary-button" @click="showContactDialog = false">取消</button>
          <button type="submit" class="primary-button" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
        </div>
      </form>
    </dialog>

    <dialog v-if="showStatusDialog && focusTask" class="dialog-overlay" open @click.self="showStatusDialog = false">
      <form class="dialog-card" @submit.prevent="submitStatusUpdate">
        <h2>更新任务状态</h2>
        <p>任务：{{ focusTask.title }}</p>
        <label>新状态 <select v-model="statusForm.status">
          <option value="completed">已完成</option>
          <option value="closed">已关闭</option>
          <option value="in_progress">进行中</option>
          <option value="pending_review">待复核</option>
        </select></label>
        <label>备注 <textarea v-model="statusForm.note" rows="2"></textarea></label>
        <div class="dialog-actions">
          <button type="button" class="secondary-button" @click="showStatusDialog = false">取消</button>
          <button type="submit" class="primary-button" :disabled="saving">{{ saving ? '更新中...' : '确认' }}</button>
        </div>
      </form>
    </dialog>

    <dialog v-if="showNewTaskDialog" class="dialog-overlay" open @click.self="showNewTaskDialog = false">
      <form class="dialog-card" @submit.prevent="submitNewTask">
        <h2>新建随访任务</h2>
        <label>类别 <select v-model="newTaskForm.category">
          <option value="recheck">复诊</option>
          <option value="exam">检查</option>
        </select></label>
        <label>任务名称 <input type="text" v-model="newTaskForm.title" required /></label>
        <label>负责人 <input type="text" v-model="newTaskForm.owner" /></label>
        <label>截止日期 <input type="date" v-model="newTaskForm.dueDate" /></label>
        <label>优先级 <select v-model="newTaskForm.priority">
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select></label>
        <label>备注 <textarea v-model="newTaskForm.note" rows="2"></textarea></label>
        <div class="dialog-actions">
          <button type="button" class="secondary-button" @click="showNewTaskDialog = false">取消</button>
          <button type="submit" class="primary-button" :disabled="saving">{{ saving ? '创建中...' : '创建' }}</button>
        </div>
      </form>
    </dialog>
  </section>
</template>

<style scoped>
.followups-page {
  display: grid;
  gap: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.action-row {
  display: flex;
  gap: 8px;
}

.followup-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #d5e6ef;
}

.followup-table th,
.followup-table td {
  padding: 10px;
  border-bottom: 1px solid #d5e6ef;
  text-align: left;
}

.followup-table th {
  background: #edf7fc;
}

.status-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 800;
}

.status-done {
  background: #e6f9f0;
  color: #007f65;
}

.status-closed {
  background: #f0f5f9;
  color: #526772;
}

.status-review {
  background: #fff7ed;
  color: #9a5b00;
}

.status-pending {
  background: #edf7fc;
  color: #275d70;
}

.text-action {
  min-height: 28px;
  border: 1px solid #b7d1de;
  border-radius: 4px;
  background: #f8fdff;
  color: #005c61;
  font-weight: 800;
  padding: 0 10px;
  cursor: pointer;
}

.muted-text {
  color: #9ab3c0;
}

.contact-list {
  display: grid;
  gap: 8px;
}

.contact-item {
  display: grid;
  grid-template-columns: 120px 160px minmax(0, 1fr);
  gap: 8px;
  padding: 8px;
  background: #f7fbfd;
  border: 1px solid #d5e6ef;
  font-size: 13px;
}

.contact-item strong {
  color: #003f43;
}

.contact-item span {
  color: #526772;
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 15, 30, 0.4);
  display: grid;
  place-items: center;
  z-index: 100;
  border: 0;
  padding: 0;
}

.dialog-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  min-width: min(480px, 90vw);
  display: grid;
  gap: 12px;
}

.dialog-card h2 {
  margin: 0;
  color: #003f43;
}

.dialog-card label {
  display: grid;
  gap: 4px;
  color: #526772;
  font-size: 13px;
  font-weight: 700;
}

.dialog-card select,
.dialog-card input,
.dialog-card textarea {
  min-height: 36px;
  border: 1px solid #c9dce6;
  border-radius: 4px;
  padding: 7px 9px;
  background: #fff;
  font-size: 14px;
}

.dialog-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.success-line {
  color: #027a48;
  font-weight: 700;
}

.error-line {
  color: #b42318;
  font-weight: 700;
}
</style>
