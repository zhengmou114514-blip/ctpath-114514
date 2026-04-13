<script setup lang="ts">
import { computed } from 'vue'
import PatientAttachmentPanel from '../../components/archive/PatientAttachmentPanel.vue'
import type { PatientCase, PatientEventPayload, PatientUpsertPayload, TimelineEvent } from '../../services/types'

type ArchiveFocusSection = 'overview' | 'events'

const props = defineProps<{
  patientForm: PatientUpsertPayload
  selectedPatientId: string
  eventForm: PatientEventPayload
  relationOptions: string[]
  savingPatient: boolean
  savingEvent: boolean
  timelineItems: TimelineEvent[]
  selectedPatient: PatientCase | null
  focusSection?: ArchiveFocusSection
}>()

const emit = defineEmits<{
  (e: 'submit-archive'): void
  (e: 'submit-event'): void
  (e: 'prepare-new'): void
  (e: 'back'): void
}>()

const patient = computed(() => props.selectedPatient)

const timeline = computed(() => {
  if (props.timelineItems.length) return props.timelineItems
  return patient.value?.timeline ?? []
})

const structuredEvents = computed(() =>
  timeline.value.map((item, idx) => ({
    eventId: `${item.date}-${item.type}-${idx}`,
    relation: item.type,
    objectValue: item.detail,
    eventTime: item.date,
    note: item.title,
  }))
)

const keyQuadruples = computed(() => {
  if (!patient.value) return []
  const base = [
    {
      subject: patient.value.patientId,
      relation: 'has_disease',
      object: patient.value.primaryDisease || '--',
      time: patient.value.lastVisit || '--',
    },
    {
      subject: patient.value.patientId,
      relation: 'stage',
      object: patient.value.currentStage || '--',
      time: patient.value.lastVisit || '--',
    },
    {
      subject: patient.value.patientId,
      relation: 'risk_level',
      object: patient.value.riskLevel || '--',
      time: patient.value.lastVisit || '--',
    },
  ]
  const eventQuads = timeline.value.slice(0, 5).map((item) => ({
    subject: patient.value?.patientId || '--',
    relation: item.type,
    object: item.detail,
    time: item.date,
  }))
  return [...base, ...eventQuads]
})

const topPrediction = computed(() => patient.value?.predictions?.[0] ?? null)
const evidenceSummary = computed(() => ({
  eventCount: timeline.value.length,
  relationCount: keyQuadruples.value.length,
  support: patient.value?.dataSupport || '--',
}))

function riskClass(level: string) {
  const normalized = level.toLowerCase()
  if (normalized.includes('high')) return 'risk-high'
  if (normalized.includes('medium')) return 'risk-medium'
  return 'risk-low'
}
</script>

<template>
  <section class="core-detail-page">
    <article class="card detail-master-card">
      <div class="master-header-main">
        <h2>{{ patient?.name || patientForm.name || '未选择患者' }}</h2>
        <p>
          {{ patient?.gender || patientForm.gender || '--' }} ·
          {{ patient?.age ?? patientForm.age ?? '--' }} 岁 ·
          最近就诊：{{ patient?.lastVisit || patientForm.lastVisit || '--' }}
        </p>
      </div>
      <div class="master-tags">
        <span>病案号：{{ patient?.medicalRecordNumber || patientForm.medicalRecordNumber || '--' }}</span>
        <span>主诊断：{{ patient?.primaryDisease || patientForm.primaryDisease || '--' }}</span>
        <span>当前阶段：{{ patient?.currentStage || patientForm.currentStage || '--' }}</span>
        <span class="risk-pill" :class="riskClass(patient?.riskLevel || patientForm.riskLevel || '')">
          风险：{{ patient?.riskLevel || patientForm.riskLevel || '--' }}
        </span>
        <span>最近就诊：{{ patient?.lastVisit || patientForm.lastVisit || '--' }}</span>
      </div>
      <div class="master-actions">
        <button class="secondary-button" @click="emit('back')">返回列表</button>
        <button class="primary-button" :disabled="savingPatient" @click="emit('submit-archive')">
          {{ savingPatient ? '保存中...' : '保存档案' }}
        </button>
      </div>
    </article>

    <section class="detail-3col">
      <aside class="card col left-col">
        <h3>基础身份信息</h3>
        <div class="field-grid">
          <p><span>姓名</span><strong>{{ patient?.name || patientForm.name || '--' }}</strong></p>
          <p><span>性别</span><strong>{{ patient?.gender || patientForm.gender || '--' }}</strong></p>
          <p><span>年龄</span><strong>{{ patient?.age ?? patientForm.age ?? '--' }}</strong></p>
          <p><span>最近就诊</span><strong>{{ patient?.lastVisit || patientForm.lastVisit || '--' }}</strong></p>
        </div>

        <h3>证件信息</h3>
        <div class="field-grid">
          <p><span>证件号</span><strong>{{ patient?.identityMasked || patientForm.identityMasked || '--' }}</strong></p>
          <p><span>证件类型</span><strong>居民身份证</strong></p>
          <p><span>医保类型</span><strong>{{ patient?.insuranceType || patientForm.insuranceType || '--' }}</strong></p>
          <p><span>知情同意</span><strong>{{ patient?.consentStatus || patientForm.consentStatus || '--' }}</strong></p>
        </div>

        <h3>联系方式</h3>
        <div class="field-grid">
          <p><span>手机号</span><strong>{{ patient?.phone || patientForm.phone || '--' }}</strong></p>
          <p><span>地址</span><strong>--</strong></p>
        </div>

        <h3>紧急联系人</h3>
        <div class="field-grid">
          <p><span>姓名</span><strong>{{ patient?.emergencyContactName || patientForm.emergencyContactName || '--' }}</strong></p>
          <p><span>关系</span><strong>{{ patient?.emergencyContactRelation || patientForm.emergencyContactRelation || '--' }}</strong></p>
          <p><span>电话</span><strong>{{ patient?.emergencyContactPhone || patientForm.emergencyContactPhone || '--' }}</strong></p>
        </div>

        <h3>照片与证件附件</h3>
        <div class="attachment-grid">
          <div class="attach-tile">
            <span>患者照片</span>
            <img v-if="patient?.avatarUrl" :src="patient.avatarUrl" alt="患者照片" />
            <p v-else>待上传</p>
          </div>
          <div class="attach-tile"><span>身份证附件</span><p>待上传</p></div>
          <div class="attach-tile"><span>医保卡附件</span><p>待上传</p></div>
          <div class="attach-tile"><span>转诊/检查单附件</span><p>待上传</p></div>
        </div>
        <PatientAttachmentPanel
          :patient-id="patient?.patientId || patientForm.patientId"
          title="档案附件区（患者照片/证件/单据）"
        />
      </aside>

      <main class="card col middle-col">
        <section class="panel">
          <div class="panel-head">
            <h3>病程时间线</h3>
            <button class="secondary-button" :disabled="savingEvent" @click="emit('submit-event')">
              {{ savingEvent ? '保存中...' : '保存事件' }}
            </button>
          </div>
          <div v-if="!timeline.length" class="empty-block">暂无病程数据</div>
          <div v-else class="timeline-list">
            <article v-for="(item, idx) in timeline" :key="`${item.date}-${item.type}-${idx}`" class="timeline-row">
              <span>{{ item.date }}</span>
              <div>
                <strong>{{ item.title }}</strong>
                <p>{{ item.detail }}</p>
              </div>
            </article>
          </div>
        </section>

        <section class="panel">
          <h3>结构化事件</h3>
          <div v-if="!structuredEvents.length" class="empty-block">暂无结构化事件</div>
          <table v-else>
            <thead>
              <tr>
                <th>事件时间</th>
                <th>关系</th>
                <th>值</th>
                <th>备注</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in structuredEvents" :key="item.eventId">
                <td>{{ item.eventTime }}</td>
                <td>{{ item.relation }}</td>
                <td>{{ item.objectValue }}</td>
                <td>{{ item.note }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="panel">
          <h3>关键四元组</h3>
          <div v-if="!keyQuadruples.length" class="empty-block">暂无四元组</div>
          <table v-else>
            <thead>
              <tr>
                <th>主语</th>
                <th>关系</th>
                <th>客体</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in keyQuadruples" :key="`${item.relation}-${idx}`">
                <td>{{ item.subject }}</td>
                <td>{{ item.relation }}</td>
                <td>{{ item.object }}</td>
                <td>{{ item.time }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </main>

      <aside class="card col right-col">
        <section class="panel">
          <h3>预测结果</h3>
          <div v-if="!topPrediction" class="empty-block">暂无预测结果</div>
          <div v-else class="plain-card">
            <strong>{{ topPrediction.label }}</strong>
            <p>置信度：{{ Math.round(topPrediction.score * 100) }}%</p>
            <p>{{ topPrediction.reason }}</p>
          </div>
        </section>

        <section class="panel">
          <h3>证据摘要</h3>
          <div class="field-grid">
            <p><span>病程事件数</span><strong>{{ evidenceSummary.eventCount }}</strong></p>
            <p><span>关系数</span><strong>{{ evidenceSummary.relationCount }}</strong></p>
            <p><span>数据支持度</span><strong>{{ evidenceSummary.support }}</strong></p>
          </div>
        </section>

        <section class="panel">
          <h3>建议审核</h3>
          <ul v-if="patient?.careAdvice?.length" class="simple-list">
            <li v-for="(item, idx) in patient.careAdvice" :key="`advice-${idx}`">{{ item }}</li>
          </ul>
          <div v-else class="empty-block">暂无建议</div>
        </section>

        <section class="panel">
          <h3>下一步计划</h3>
          <ul v-if="patient?.followUps?.length" class="simple-list">
            <li v-for="(item, idx) in patient.followUps" :key="`plan-${idx}`">
              {{ item.title }} / {{ item.owner }} / {{ item.dueDate }}
            </li>
          </ul>
          <div v-else class="empty-block">暂无随访计划</div>
        </section>
      </aside>
    </section>

    <section class="bottom-panels">
      <article class="card panel">
        <h3>最近操作留痕</h3>
        <div v-if="!patient?.auditLogs?.length" class="empty-block">暂无操作留痕</div>
        <div v-else class="record-list">
          <div v-for="item in patient.auditLogs" :key="item.logId" class="record-row">
            <strong>{{ item.action }}</strong>
            <p>{{ item.detail }}</p>
            <small>{{ item.createdAt }}</small>
          </div>
        </div>
      </article>

      <article class="card panel">
        <h3>随访记录</h3>
        <div v-if="!patient?.contactLogs?.length" class="empty-block">暂无随访记录</div>
        <div v-else class="record-list">
          <div v-for="item in patient.contactLogs" :key="item.logId" class="record-row">
            <strong>{{ item.contactType }} / {{ item.contactResult }}</strong>
            <p>{{ item.note || '--' }}</p>
            <small>{{ item.contactTime }}</small>
          </div>
        </div>
      </article>

      <article class="card panel">
        <h3>档案修改记录</h3>
        <div v-if="!patient?.outpatientTasks?.length" class="empty-block">暂无档案修改记录</div>
        <div v-else class="record-list">
          <div v-for="item in patient.outpatientTasks" :key="item.taskId" class="record-row">
            <strong>{{ item.title }} / {{ item.status }}</strong>
            <p>{{ item.note }}</p>
            <small>{{ item.updatedAt || '--' }}</small>
          </div>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.core-detail-page {
  display: grid;
  gap: 16px;
}

.detail-master-card {
  padding: 16px;
  display: grid;
  gap: 12px;
}

.master-header-main h2 {
  margin: 0;
}

.master-header-main p {
  margin: 4px 0 0;
  color: var(--ink-muted);
}

.master-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.master-tags span {
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px 10px;
  background: #f8fafc;
  font-size: 12px;
}

.master-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.detail-3col {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) 340px;
  gap: 16px;
  align-items: start;
}

.col {
  padding: 16px;
  display: grid;
  gap: 14px;
}

.panel {
  display: grid;
  gap: 10px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.field-grid {
  display: grid;
  gap: 8px;
}

.field-grid p {
  margin: 0;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  background: #fbfdff;
}

.field-grid span {
  color: var(--ink-muted);
}

.attachment-grid {
  display: grid;
  gap: 8px;
}

.attach-tile {
  border: 1px dashed var(--border-strong);
  border-radius: 8px;
  padding: 10px;
  display: grid;
  gap: 6px;
}

.attach-tile img {
  width: 100%;
  max-height: 120px;
  object-fit: cover;
  border-radius: 6px;
}

.timeline-list,
.record-list {
  display: grid;
  gap: 8px;
}

.timeline-row,
.record-row {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  display: grid;
  gap: 4px;
  background: #fff;
}

.timeline-row {
  grid-template-columns: 120px 1fr;
  align-items: start;
}

.timeline-row p,
.record-row p {
  margin: 0;
}

.plain-card {
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #f7fbff;
  padding: 10px;
}

.plain-card p {
  margin: 4px 0 0;
}

.simple-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
}

.bottom-panels {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.empty-block {
  border: 1px dashed var(--border-strong);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  color: var(--ink-muted);
}

.risk-pill.risk-high {
  background: #fdeced;
  color: #a4383f;
  border-color: #efc2c5;
}

.risk-pill.risk-medium {
  background: #fff4e2;
  color: #9b6518;
  border-color: #efdbb2;
}

.risk-pill.risk-low {
  background: #e9f8f1;
  color: #1d7b5c;
  border-color: #bde7d1;
}

@media (max-width: 1460px) {
  .detail-3col {
    grid-template-columns: 1fr;
  }

  .bottom-panels {
    grid-template-columns: 1fr;
  }
}
</style>
