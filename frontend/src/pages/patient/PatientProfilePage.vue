<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { updatePatient } from '../../services/api'
import type { PatientCase } from '../../services/types'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const router = useRouter()
const patient = computed(() => workspace.selectedPatient)

const editing = ref(false)
const saving = ref(false)
const error = ref('')
const message = ref('')

const editForm = ref({
  phone: '',
  emergencyContactName: '',
  emergencyContactPhone: '',
  emergencyContactRelation: '',
  archiveStatus: '',
  consentStatus: '',
})

function archiveStatus(value: string) {
  if (value === 'active') return '已建档'
  if (value === 'draft') return '待补全'
  return value || '待维护'
}

function consentStatus(value: string) {
  if (value === 'signed') return '已签署'
  if (value === 'family_authorized') return '家属授权'
  return '待签署'
}

function startEdit() {
  if (!patient.value) return
  editForm.value = {
    phone: patient.value.phone || '',
    emergencyContactName: patient.value.emergencyContactName || '',
    emergencyContactPhone: patient.value.emergencyContactPhone || '',
    emergencyContactRelation: patient.value.emergencyContactRelation || '',
    archiveStatus: patient.value.archiveStatus || 'draft',
    consentStatus: patient.value.consentStatus || 'pending',
  }
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  error.value = ''
}

async function saveProfile() {
  if (!patient.value) return
  saving.value = true
  error.value = ''
  try {
    const p = patient.value
    const updated = await updatePatient(p.patientId, {
      patientId: p.patientId,
      name: p.name,
      age: p.age,
      gender: p.gender,
      avatarUrl: p.avatarUrl || '',
      phone: editForm.value.phone,
      emergencyContactName: editForm.value.emergencyContactName,
      emergencyContactPhone: editForm.value.emergencyContactPhone,
      emergencyContactRelation: editForm.value.emergencyContactRelation,
      identityMasked: p.identityMasked || '',
      insuranceType: p.insuranceType || '',
      department: p.department || '',
      primaryDoctor: p.primaryDoctor || '',
      caseManager: p.caseManager || '',
      medicalRecordNumber: p.medicalRecordNumber || '',
      archiveSource: p.archiveSource || '',
      archiveStatus: editForm.value.archiveStatus,
      consentStatus: editForm.value.consentStatus,
      allergyHistory: p.allergyHistory || '',
      familyHistory: p.familyHistory || '',
      primaryDisease: p.primaryDisease,
      currentStage: p.currentStage,
      riskLevel: p.riskLevel,
      lastVisit: p.lastVisit || '',
      summary: p.summary || '',
      dataSupport: p.dataSupport || 'medium',
    })
    workspace.selectedPatient = updated as PatientCase
    editing.value = false
    message.value = '档案已更新。'
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '保存失败。'
  } finally {
    saving.value = false
  }
}

function goAttachments() {
  if (!patient.value) return
  void router.push({ name: 'patient-attachments', params: { patientId: patient.value.patientId } })
}
</script>

<template>
  <section v-if="patient" class="clinical-card">
    <div class="section-header">
      <div>
        <p class="eyebrow">基本档案</p>
        <h2>患者基础信息</h2>
      </div>
      <div class="action-row">
        <button class="secondary-button" type="button" @click="goAttachments">电子档案</button>
        <button v-if="!editing" class="secondary-button" type="button" @click="startEdit">补全档案</button>
        <template v-else>
          <button class="secondary-button" type="button" @click="cancelEdit">取消</button>
          <button class="primary-button" type="button" :disabled="saving" @click="saveProfile">{{ saving ? '保存中...' : '保存' }}</button>
        </template>
      </div>
    </div>

    <p v-if="message" class="success-line">{{ message }}</p>
    <p v-if="error" class="error-line">{{ error }}</p>

    <template v-if="!editing">
      <dl class="profile-grid">
        <div><dt>姓名</dt><dd>{{ patient.name }}</dd></div>
        <div><dt>性别</dt><dd>{{ patient.gender }}</dd></div>
        <div><dt>年龄</dt><dd>{{ patient.age }}岁</dd></div>
        <div><dt>联系方式</dt><dd>{{ patient.phone || '待补充' }}</dd></div>
        <div><dt>病历号</dt><dd>{{ patient.medicalRecordNumber || patient.patientId }}</dd></div>
        <div><dt>主治医生</dt><dd>{{ patient.primaryDoctor || '待分配' }}</dd></div>
        <div><dt>档案状态</dt><dd>{{ archiveStatus(patient.archiveStatus) }}</dd></div>
        <div><dt>知情同意</dt><dd>{{ consentStatus(patient.consentStatus) }}</dd></div>
      </dl>
      <dl class="profile-grid emergency-grid">
        <div><dt>紧急联系人</dt><dd>{{ patient.emergencyContactName || '待补充' }}</dd></div>
        <div><dt>紧急联系人电话</dt><dd>{{ patient.emergencyContactPhone || '待补充' }}</dd></div>
        <div><dt>紧急联系人关系</dt><dd>{{ patient.emergencyContactRelation || '待补充' }}</dd></div>
      </dl>
    </template>

    <template v-else>
      <dl class="profile-grid">
        <div><dt>姓名</dt><dd>{{ patient.name }}</dd></div>
        <div><dt>性别</dt><dd>{{ patient.gender }}</dd></div>
        <div><dt>年龄</dt><dd>{{ patient.age }}岁</dd></div>
        <div><dt>联系方式</dt><dd><input type="text" v-model="editForm.phone" class="edit-input" /></dd></div>
        <div><dt>病历号</dt><dd>{{ patient.medicalRecordNumber || patient.patientId }}</dd></div>
        <div><dt>主治医生</dt><dd>{{ patient.primaryDoctor || '待分配' }}</dd></div>
        <div><dt>档案状态</dt><dd>
          <select v-model="editForm.archiveStatus" class="edit-input">
            <option value="active">已建档</option>
            <option value="draft">待补全</option>
          </select>
        </dd></div>
        <div><dt>知情同意</dt><dd>
          <select v-model="editForm.consentStatus" class="edit-input">
            <option value="signed">已签署</option>
            <option value="family_authorized">家属授权</option>
            <option value="pending">待签署</option>
          </select>
        </dd></div>
      </dl>
      <dl class="profile-grid emergency-grid">
        <div><dt>紧急联系人</dt><dd><input type="text" v-model="editForm.emergencyContactName" class="edit-input" placeholder="姓名" /></dd></div>
        <div><dt>紧急联系人电话</dt><dd><input type="text" v-model="editForm.emergencyContactPhone" class="edit-input" placeholder="电话" /></dd></div>
        <div><dt>紧急联系人关系</dt><dd><input type="text" v-model="editForm.emergencyContactRelation" class="edit-input" placeholder="关系" /></dd></div>
      </dl>
    </template>
  </section>
</template>

<style scoped>
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

.profile-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
}

.emergency-grid {
  margin-top: 8px;
}

.profile-grid div {
  border: 1px solid #d5e6ef;
  background: #fff;
  padding: 10px;
}

.profile-grid dt {
  color: #527384;
  font-weight: 800;
}

.profile-grid dd {
  margin: 4px 0 0;
  color: #243f4d;
  font-weight: 900;
}

.edit-input {
  width: 100%;
  min-height: 32px;
  border: 1px solid #c9dce6;
  border-radius: 4px;
  padding: 4px 8px;
  background: #f7fbfd;
  font-size: 14px;
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
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
