<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getPatientAttachments, getPatientMedications } from '../../services/api'
import type { PatientAttachmentRecord, PatientMedicationRecord } from '../../services/types'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const router = useRouter()
const patient = computed(() => workspace.selectedPatient)
const latestTimeline = computed(() => patient.value?.timeline.slice(0, 3) ?? [])
const firstAdvice = computed(() => workspace.predictionResult?.advice?.[0] ?? patient.value?.careAdvice?.[0] ?? '结合病程记录、当前用药和随访情况继续观察。')

const recentAttachments = ref<PatientAttachmentRecord[]>([])
const activeMedications = ref<PatientMedicationRecord[]>([])

function go(name: string) {
  if (!patient.value) return
  void router.push({ name, params: { patientId: patient.value.patientId } })
}

function startFollowup() {
  if (!patient.value) return
  void workspace.openFollowupModule(patient.value.patientId, 'tasks')
}

async function loadOverviewExtras() {
  if (!patient.value) return
  try {
    const [attachments, medications] = await Promise.all([
      getPatientAttachments(patient.value.patientId),
      getPatientMedications(patient.value.patientId),
    ])
    recentAttachments.value = attachments.slice(0, 4)
    activeMedications.value = medications.filter((m) => m.status === 'active').slice(0, 5)
  } catch {
    recentAttachments.value = []
    activeMedications.value = []
  }
}

watch(
  () => patient.value?.patientId,
  () => {
    recentAttachments.value = []
    activeMedications.value = []
    void loadOverviewExtras()
  },
  { immediate: true }
)
</script>

<template>
  <section v-if="patient" class="patient-feature-grid">
    <article class="clinical-card wide-card">
      <p class="eyebrow">患者总览</p>
      <h2>{{ patient.name }}慢病管理摘要</h2>
      <p>{{ patient.summary }}</p>
      <div class="action-row">
        <button class="primary-button" type="button" @click="go('patient-profile')">查看基本档案</button>
        <button class="secondary-button" type="button" @click="go('patient-timeline')">查看病程时间线</button>
        <button class="secondary-button" type="button" @click="go('patient-risk')">进入风险评估</button>
        <button class="secondary-button" type="button" @click="startFollowup">发起随访</button>
      </div>
    </article>
    <article class="clinical-card">
      <h2>最近病程</h2>
      <div class="mini-list">
        <p v-for="item in latestTimeline" :key="`${item.date}-${item.title}`"><strong>{{ item.date }}</strong><span>{{ item.title }}：{{ item.detail }}</span></p>
      </div>
    </article>
    <article class="clinical-card">
      <h2>当前风险</h2>
      <strong class="big-value">{{ patient.riskLevel }}</strong>
      <p>数据支持：{{ patient.dataSupport }}</p>
      <button class="text-action" type="button" @click="go('patient-risk')">查看评估详情</button>
    </article>
    <article class="clinical-card">
      <h2>当前用药摘要</h2>
      <p v-if="activeMedications.length" class="med-count">活跃用药 {{ activeMedications.length }} 项</p>
      <ul v-if="activeMedications.length" class="med-mini-list">
        <li v-for="med in activeMedications" :key="med.medication_id">{{ med.drug_name_snapshot }} {{ med.dosage }} {{ med.frequency }}</li>
      </ul>
      <p v-else class="muted-line">暂无活跃用药记录。</p>
      <button class="text-action" type="button" @click="go('patient-medications')">查看当前用药</button>
    </article>
    <article class="clinical-card">
      <h2>附件资料</h2>
      <p v-if="recentAttachments.length" class="med-count">最近 {{ recentAttachments.length }} 份</p>
      <ul v-if="recentAttachments.length" class="med-mini-list">
        <li v-for="att in recentAttachments" :key="att.attachmentId">{{ att.fileName }}</li>
      </ul>
      <p v-else class="muted-line">暂无附件。</p>
      <button class="text-action" type="button" @click="go('patient-attachments')">查看附件资料</button>
    </article>
    <article class="clinical-card">
      <h2>下一步动作</h2>
      <p>{{ firstAdvice }}</p>
      <div class="action-row compact">
        <button class="text-action" type="button" @click="go('patient-medications')">查看当前用药</button>
        <button class="text-action" type="button" @click="startFollowup">安排随访</button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.patient-feature-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.wide-card { grid-column: 1 / -1; }
.mini-list { display: grid; gap: 8px; }
.mini-list p { display: grid; gap: 4px; margin: 0; padding: 10px; background: #f7fbfd; border: 1px solid #d5e6ef; }
.big-value { color: #0f6f99; font-size: 32px; }
.action-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.action-row.compact { margin-top: 8px; }
.text-action {
  min-height: 30px;
  border: 1px solid #b7d1de;
  border-radius: 4px;
  background: #f8fdff;
  color: #005c61;
  font-weight: 800;
  padding: 0 10px;
  cursor: pointer;
}
.med-count { color: #275d70; font-weight: 800; margin: 0 0 4px; }
.med-mini-list { display: grid; gap: 4px; padding: 0; margin: 0; list-style: none; }
.med-mini-list li { padding: 4px 8px; background: #f7fbfd; border: 1px solid #d5e6ef; font-size: 13px; color: #243f4d; }
.muted-line { color: #526772; }
@media (max-width: 900px) { .patient-feature-grid { grid-template-columns: 1fr; } }
</style>
