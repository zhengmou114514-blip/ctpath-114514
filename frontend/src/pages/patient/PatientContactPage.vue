<script setup lang="ts">
import { computed, ref } from 'vue'
import { addPatientContactLog } from '../../services/api'
import type { PatientCase } from '../../services/types'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const patient = computed(() => workspace.selectedPatient)
const logs = computed(() => patient.value?.contactLogs.slice(0, 12) ?? [])

const showDialog = ref(false)
const saving = ref(false)
const error = ref('')
const message = ref('')

const form = ref({
  contactType: 'phone' as 'phone' | 'family' | 'wechat' | 'outpatient',
  contactTarget: 'patient' as 'patient' | 'emergency_contact',
  contactResult: 'reached' as 'reached' | 'missed' | 'scheduled' | 'urgent',
  note: '',
  nextContactDate: '',
})

function openDialog() {
  form.value = { contactType: 'phone', contactTarget: 'patient', contactResult: 'reached', note: '', nextContactDate: '' }
  showDialog.value = true
}

async function submitContactLog() {
  if (!patient.value) return
  saving.value = true
  error.value = ''
  try {
    const updated = await addPatientContactLog(patient.value.patientId, {
      contactTime: new Date().toISOString().slice(0, 19),
      contactType: form.value.contactType,
      contactTarget: form.value.contactTarget,
      contactResult: form.value.contactResult,
      note: form.value.note,
      nextContactDate: form.value.nextContactDate || undefined,
    })
    workspace.selectedPatient = updated as PatientCase
    showDialog.value = false
    message.value = '联系记录已保存。'
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '保存联系记录失败。'
  } finally {
    saving.value = false
  }
}

function contactTypeLabel(type: string) {
  if (type === 'phone') return '电话'
  if (type === 'wechat') return '微信'
  if (type === 'family') return '家属'
  if (type === 'outpatient') return '门诊'
  return type
}

function contactResultLabel(result: string) {
  if (result === 'reached') return '已接通'
  if (result === 'missed') return '未接通'
  if (result === 'scheduled') return '已预约'
  if (result === 'urgent') return '需紧急处理'
  return result
}
</script>

<template>
  <section v-if="patient" class="patient-feature-grid">
    <article class="clinical-card">
      <h2>联系方式</h2>
      <dl class="contact-info-grid">
        <div><dt>患者电话</dt><dd>{{ patient.phone || '待补充' }}</dd></div>
        <div><dt>紧急联系人</dt><dd>{{ patient.emergencyContactName || '待补充' }}</dd></div>
        <div><dt>紧急联系人电话</dt><dd>{{ patient.emergencyContactPhone || '待补充' }}</dd></div>
        <div><dt>紧急联系人关系</dt><dd>{{ patient.emergencyContactRelation || '待补充' }}</dd></div>
      </dl>
      <button class="secondary-button" type="button" @click="openDialog">追加联系记录</button>
    </article>
    <article class="clinical-card">
      <h2>最近联系记录</h2>
      <p v-if="message" class="success-line">{{ message }}</p>
      <p v-if="error" class="error-line">{{ error }}</p>
      <div class="mini-list">
        <div v-for="item in logs" :key="item.logId" class="contact-row">
          <strong>{{ item.contactTime }}</strong>
          <span class="type-tag">{{ contactTypeLabel(item.contactType) }}</span>
          <span :class="item.contactResult === 'reached' ? 'result-ok' : item.contactResult === 'urgent' ? 'result-warn' : 'result-muted'">
            {{ contactResultLabel(item.contactResult) }}
          </span>
          <span class="note-text">{{ item.note }}</span>
        </div>
      </div>
      <p v-if="!logs.length" class="muted-line">暂无联系记录。</p>
    </article>

    <dialog v-if="showDialog" class="dialog-overlay" open @click.self="showDialog = false">
      <form class="dialog-card" @submit.prevent="submitContactLog">
        <h2>追加联系记录</h2>
        <label>联系方式 <select v-model="form.contactType">
          <option value="phone">电话</option>
          <option value="wechat">微信</option>
          <option value="family">家属</option>
          <option value="outpatient">门诊</option>
        </select></label>
        <label>联系对象 <select v-model="form.contactTarget">
          <option value="patient">患者本人</option>
          <option value="emergency_contact">紧急联系人</option>
        </select></label>
        <label>联系结果 <select v-model="form.contactResult">
          <option value="reached">已接通</option>
          <option value="missed">未接通</option>
          <option value="scheduled">已预约</option>
          <option value="urgent">需紧急处理</option>
        </select></label>
        <label>备注 <textarea v-model="form.note" rows="3"></textarea></label>
        <label>下次联系日期 <input type="date" v-model="form.nextContactDate" /></label>
        <div class="dialog-actions">
          <button type="button" class="secondary-button" @click="showDialog = false">取消</button>
          <button type="submit" class="primary-button" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
        </div>
      </form>
    </dialog>
  </section>
</template>

<style scoped>
.patient-feature-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 12px;
}

.contact-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 0 0 12px;
}

.contact-info-grid div {
  border: 1px solid #d5e6ef;
  background: #f7fbfd;
  padding: 8px;
}

.contact-info-grid dt {
  color: #527384;
  font-size: 12px;
  font-weight: 800;
}

.contact-info-grid dd {
  margin: 2px 0 0;
  color: #243f4d;
  font-weight: 900;
}

.mini-list {
  display: grid;
  gap: 8px;
}

.contact-row {
  display: grid;
  grid-template-columns: 120px 60px 80px minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  padding: 8px;
  background: #f7fbfd;
  border: 1px solid #d5e6ef;
  font-size: 13px;
}

.contact-row strong {
  color: #003f43;
}

.type-tag {
  color: #275d70;
  font-weight: 800;
}

.result-ok {
  color: #007f65;
  font-weight: 800;
}

.result-warn {
  color: #b42318;
  font-weight: 800;
}

.result-muted {
  color: #9a5b00;
  font-weight: 800;
}

.note-text {
  color: #526772;
}

.muted-line {
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

@media (max-width: 900px) {
  .patient-feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>
