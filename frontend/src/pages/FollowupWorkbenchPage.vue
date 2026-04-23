<script setup lang="ts">
import FollowupPage from './FollowupPage.vue'
import type { ContactLogCreatePayload, DoctorUser, FlowBoardRow, FollowupTaskRow, PatientCase } from '../services/types'

const props = defineProps<{
  loading: boolean
  loadingTaskAction: boolean
  followupItems: FollowupTaskRow[]
  flowBoardItems: FlowBoardRow[]
  selectedPatientId?: string
  selectedPatient?: PatientCase | null
  savingContactLog: boolean
  doctorRole?: DoctorUser['role']
  noPermission?: boolean
  modelUnavailable?: boolean
}>()

const emit = defineEmits<{
  (e: 'open-patient', patientId: string): void
  (e: 'open-archive', patientId: string): void
  (e: 'complete-task', payload: { patientId: string; taskId: string }): void
  (e: 'close-task', payload: { patientId: string; taskId: string }): void
  (e: 'submit-contact-log', patientId: string, payload: ContactLogCreatePayload): void
}>()
</script>

<template>
  <section v-if="props.noPermission" class="empty-state-card">
    <h3>当前账号无随访权限</h3>
    <p>请使用医生或护士账号进入随访工作区。</p>
  </section>

  <section v-else-if="props.loading" class="empty-state-card">
    <h3>随访工作台加载中</h3>
    <p>正在同步待随访任务、病程流转和联系记录，请稍后。</p>
  </section>

  <section v-else-if="!props.followupItems.length" class="empty-state-card">
    <h3>当前暂无待办随访任务</h3>
    <p>可以先从患者详情创建随访任务，或等待新的门诊任务进入工作台。</p>
  </section>

  <section v-else-if="props.modelUnavailable" class="empty-state-card">
    <h3>推理服务当前不可用</h3>
    <p>随访工作区仍可正常查看任务、录入联系记录和更新状态，预测相关内容会稍后恢复。</p>
  </section>

  <FollowupPage
    v-else
    :loading="props.loading"
    :loading-task-action="props.loadingTaskAction"
      :followup-items="props.followupItems"
      :flow-board-items="props.flowBoardItems"
      :selected-patient-id="props.selectedPatientId"
      :selected-patient="props.selectedPatient"
      :saving-contact-log="props.savingContactLog"
    :doctor-role="props.doctorRole"
    @open-patient="emit('open-patient', $event)"
    @open-archive="emit('open-archive', $event)"
    @complete-task="emit('complete-task', $event)"
    @close-task="emit('close-task', $event)"
    @submit-contact-log="(patientId, payload) => emit('submit-contact-log', patientId, payload)"
  />
</template>
