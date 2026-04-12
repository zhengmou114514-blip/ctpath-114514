<script setup lang="ts">
import FollowupPage from './FollowupPage.vue'
import type { ContactLogCreatePayload, DoctorUser, FlowBoardRow, FollowupTaskRow } from '../services/types'

const props = defineProps<{
  loading: boolean
  loadingTaskAction: boolean
  followupItems: FollowupTaskRow[]
  flowBoardItems: FlowBoardRow[]
  selectedPatientId?: string
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
    <h3>无权限</h3>
    <p>当前账号无随访工作台访问权限。</p>
  </section>

  <section v-else-if="props.loading" class="empty-state-card">
    <h3>加载中</h3>
    <p>正在加载随访任务与流转看板。</p>
  </section>

  <section v-else-if="!props.followupItems.length" class="empty-state-card">
    <h3>无数据</h3>
    <p>当前暂无随访任务。</p>
  </section>

  <section v-else-if="props.modelUnavailable" class="empty-state-card">
    <h3>模型不可用</h3>
    <p>模型服务当前不可用，随访任务处理不受影响。</p>
  </section>

  <FollowupPage
    v-else
    :loading="props.loading"
    :loading-task-action="props.loadingTaskAction"
    :followup-items="props.followupItems"
    :flow-board-items="props.flowBoardItems"
    :selected-patient-id="props.selectedPatientId"
    :saving-contact-log="props.savingContactLog"
    :doctor-role="props.doctorRole"
    @open-patient="emit('open-patient', $event)"
    @open-archive="emit('open-archive', $event)"
    @complete-task="emit('complete-task', $event)"
    @close-task="emit('close-task', $event)"
    @submit-contact-log="(patientId, payload) => emit('submit-contact-log', patientId, payload)"
  />
</template>

