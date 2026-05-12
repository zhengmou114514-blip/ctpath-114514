<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getBusinessClosureSummary,
  getFlowBoard,
  getFollowupWorklist,
  getPatientAttachments,
  getPatientCase,
  getPatientMedications,
  getTimeline,
} from '../services/api'
import type {
  BusinessClosureSummary,
  FlowBoardRow,
  FollowupTaskRow,
  PatientAttachmentRecord,
  PatientCase,
  PatientMedicationRecord,
  TimelineEvent,
} from '../services/types'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref('')
const patient = ref<PatientCase | null>(null)
const timeline = ref<TimelineEvent[]>([])
const attachments = ref<PatientAttachmentRecord[]>([])
const medications = ref<PatientMedicationRecord[]>([])
const followups = ref<FollowupTaskRow[]>([])
const flowRow = ref<FlowBoardRow | null>(null)
const closureSummary = ref<BusinessClosureSummary | null>(null)

const patientId = computed(() => String(route.params.patientId || route.query.patientId || ''))

function fmt(value?: string | null) {
  if (!value) return '--'
  return value.slice(0, 10)
}

function datetime(value?: string | null) {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function medStatusLabel(value: string) {
  if (value === 'active') return '在用'
  if (value === 'paused') return '暂停'
  if (value === 'stopped') return '停用'
  return value || '--'
}

function reviewLabel(value: string) {
  if (value === 'pending') return '待审核'
  if (value === 'approved') return '已审核'
  if (value === 'rejected') return '已驳回'
  if (value === 'not_required') return '无需审核'
  return value || '--'
}

function attachmentLabel(value: string) {
  if (value === 'patient_photo') return '患者照片'
  if (value === 'id_card') return '身份证照片'
  if (value === 'insurance_card') return '医保卡照片'
  if (value === 'referral_note') return '转诊单'
  if (value === 'exam_report') return '检查报告'
  if (value === 'informed_consent') return '知情同意书'
  return value || '--'
}

function actorLabel(value?: string | null) {
  if (!value) return '--'
  const labels: Record<string, string> = {
    demo_clinic: '门诊医生',
    demo_nurse: '主管护士',
    demo_pharmacist: '主管药师',
    demo_admin: '系统管理员',
    demo_archivist: '档案管理员',
    demo_specialist: '专科医生',
  }
  return labels[value] ?? value
}

async function load() {
  if (!patientId.value) {
    error.value = '缺少患者编号，无法打开档案打印页。'
    return
  }

  loading.value = true
  error.value = ''
  try {
    const [patientResp, timelineResp, attachmentsResp, medsResp, closureResp, followupResp, flowResp] = await Promise.all([
      getPatientCase(patientId.value),
      getTimeline(patientId.value),
      getPatientAttachments(patientId.value),
      getPatientMedications(patientId.value),
      getBusinessClosureSummary(patientId.value),
      getFollowupWorklist(),
      getFlowBoard(),
    ])
    patient.value = patientResp
    timeline.value = timelineResp
    attachments.value = attachmentsResp
    medications.value = medsResp
    closureSummary.value = closureResp
    followups.value = followupResp.items.filter((item) => item.patientId === patientId.value)
    flowRow.value = flowResp.items.find((item) => item.patientId === patientId.value) || null
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '加载档案打印页失败。'
  } finally {
    loading.value = false
  }
}

function printPage() {
  window.print()
}

function backToArchive() {
  void router.push({ name: 'doctor-patients' })
}

onMounted(load)

watch(patientId, () => {
  void load()
})
</script>

<template>
  <section class="archive-print-shell">
    <header class="print-toolbar no-print">
      <div>
        <p class="eyebrow">电子档案 / 可打印文档</p>
        <h1>患者档案打印页</h1>
        <p>患者身份、联系方式、病程、附件、用药和随访闭环信息。</p>
      </div>
      <div class="toolbar-actions">
        <button class="secondary-button" type="button" @click="backToArchive">返回档案</button>
        <button class="primary-button" type="button" @click="printPage">打印此页</button>
      </div>
    </header>

    <section v-if="loading" class="empty-state-card">
      <h3>档案打印页加载中</h3>
      <p>正在同步患者档案、病程、附件与随访闭环信息。</p>
    </section>

    <section v-else-if="error" class="empty-state-card">
      <h3>档案加载失败</h3>
      <p>{{ error }}</p>
    </section>

    <article v-else-if="patient" class="print-document">
      <header class="document-header">
        <div>
          <p class="document-eyebrow">重庆邮电大学慢病辅助诊疗业务系统</p>
          <h2>{{ patient.name }} 患者档案打印单</h2>
          <p>档案号 {{ patient.medicalRecordNumber || '--' }} · 患者编号 {{ patient.patientId }} · 最近就诊 {{ fmt(patient.lastVisit) }}</p>
        </div>
        <div class="document-stamp">
          <span>档案状态</span>
          <strong>{{ patient.archiveStatus || '--' }}</strong>
          <small>{{ patient.department || '--' }}</small>
        </div>
      </header>

      <section class="document-grid">
        <article class="document-card">
          <h3>患者摘要</h3>
          <dl class="document-dl">
            <div><dt>姓名</dt><dd>{{ patient.name }}</dd></div>
            <div><dt>性别 / 年龄</dt><dd>{{ patient.gender }} / {{ patient.age }}</dd></div>
            <div><dt>联系电话</dt><dd>{{ patient.phone || '--' }}</dd></div>
            <div><dt>身份证脱敏</dt><dd>{{ patient.identityMasked || '--' }}</dd></div>
            <div><dt>主要疾病</dt><dd>{{ patient.primaryDisease || '--' }}</dd></div>
            <div><dt>当前阶段</dt><dd>{{ patient.currentStage || '--' }}</dd></div>
            <div><dt>风险等级</dt><dd>{{ patient.riskLevel || '--' }}</dd></div>
            <div><dt>数据支持</dt><dd>{{ patient.dataSupport || '--' }}</dd></div>
          </dl>
        </article>

        <article class="document-card">
          <h3>联系方式关系</h3>
          <dl class="document-dl">
            <div><dt>患者本人</dt><dd>{{ patient.name }} / {{ patient.phone || '--' }}</dd></div>
            <div><dt>紧急联系人</dt><dd>{{ patient.emergencyContactName || '--' }}</dd></div>
            <div><dt>联系人关系</dt><dd>{{ patient.emergencyContactRelation || '--' }}</dd></div>
            <div><dt>联系人电话</dt><dd>{{ patient.emergencyContactPhone || '--' }}</dd></div>
            <div><dt>责任医生</dt><dd>{{ patient.primaryDoctor || '--' }}</dd></div>
            <div><dt>个案管理师</dt><dd>{{ patient.caseManager || '--' }}</dd></div>
          </dl>
        </article>
      </section>

      <section class="document-card block-section">
        <h3>病程时间线</h3>
        <table class="document-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>类型</th>
              <th>标题</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
              <tr v-for="item in timeline" :key="`${item.date}-${item.type}-${item.title}`">
                <td>{{ fmt(item.date) }}</td>
                <td>{{ item.type }}</td>
                <td>{{ item.title }}</td>
                <td>{{ item.detail || '--' }}</td>
              </tr>
            </tbody>
          </table>
      </section>

      <section class="document-grid">
        <article class="document-card block-section">
          <h3>当前用药</h3>
          <table class="document-table compact">
            <thead>
              <tr>
                <th>药品</th>
                <th>剂量</th>
                <th>频次</th>
                <th>途径</th>
                <th>状态</th>
                <th>审核</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in medications" :key="item.medication_id">
                <td>{{ item.drug_name_snapshot }}</td>
                <td>{{ item.dosage }}</td>
                <td>{{ item.frequency }}</td>
                <td>{{ item.route }}</td>
                <td>{{ medStatusLabel(item.status) }}</td>
                <td>{{ reviewLabel(item.review_status) }}</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article class="document-card block-section">
          <h3>附件清单</h3>
          <table class="document-table compact">
            <thead>
              <tr>
                <th>类型</th>
                <th>文件</th>
                <th>上传人</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in attachments" :key="item.attachmentId">
                <td>{{ attachmentLabel(item.type) }}</td>
                <td>{{ item.fileName }}</td>
                <td>{{ actorLabel(item.uploadedBy) }}</td>
                <td>{{ datetime(item.uploadedAt) }}</td>
              </tr>
            </tbody>
          </table>
        </article>
      </section>

      <section class="document-grid">
        <article class="document-card block-section">
          <h3>随访与病情流转</h3>
          <table class="document-table compact">
            <thead>
              <tr>
                <th>任务</th>
                <th>负责人</th>
                <th>到期</th>
                <th>病情流转</th>
                <th>下一步</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in followups" :key="item.taskId || `${item.patientId}-${item.taskType}`">
                <td>{{ item.taskType }}</td>
                <td>{{ item.owner }}</td>
                <td>{{ item.dueDate }}</td>
                <td>{{ flowRow?.flowStatus || item.status }}</td>
                <td>{{ flowRow?.nextAction || item.lastActionBy || '--' }}</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article class="document-card block-section">
          <h3>闭环评估</h3>
          <div class="summary-grid">
            <div class="summary-item">
              <span>附件数量</span>
              <strong>{{ closureSummary?.attachmentCount ?? attachments.length }}</strong>
            </div>
            <div class="summary-item">
              <span>当前用药数</span>
              <strong>{{ closureSummary?.currentMedicationCount ?? medications.length }}</strong>
            </div>
            <div class="summary-item">
              <span>需药师复核</span>
              <strong>{{ closureSummary?.needsPharmacistReview ? '是' : '否' }}</strong>
            </div>
            <div class="summary-item">
              <span>建议对齐</span>
              <strong>{{ closureSummary?.medicationAssessment.alignsWithModelAdvice ? '一致' : '待补充' }}</strong>
            </div>
          </div>
          <ul v-if="closureSummary?.medicationAssessment.notes?.length" class="bullet-list">
            <li v-for="(note, index) in closureSummary.medicationAssessment.notes" :key="`${index}-${note}`">{{ note }}</li>
          </ul>
          <p v-if="flowRow" class="print-note">
            {{ flowRow.patientName }} 当前阶段 {{ flowRow.currentStage }}，状态 {{ flowRow.flowStatus }}，下一步动作：{{ flowRow.nextAction }}。
          </p>
        </article>
      </section>
    </article>
  </section>
</template>

<style scoped>
.archive-print-shell {
  display: grid;
  gap: 24px;
}

.print-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.print-document {
  width: min(210mm, 100%);
  margin: 0 auto;
  padding: 18mm 16mm;
  background: #fff;
  color: #1d2326;
  border-radius: 24px;
  border: 1px solid #d6dce0;
  box-shadow: 0 14px 34px rgba(14, 30, 32, 0.08);
  display: grid;
  gap: 18px;
}

.document-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 14px;
  border-bottom: 2px solid #dfe6e8;
}

.document-eyebrow,
.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: #547178;
  font-size: 12px;
}

.document-header h2 {
  margin: 8px 0 6px;
  font-size: 28px;
}

.document-header p {
  margin: 0;
  color: rgba(29, 35, 38, 0.78);
}

.document-stamp {
  display: grid;
  gap: 6px;
  min-width: 170px;
  padding: 14px 16px;
  border: 1px solid #d6dce0;
  border-radius: 18px;
  background: #f8fafb;
}

.document-stamp strong {
  font-size: 20px;
}

.document-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.document-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid #e0e6e8;
  border-radius: 18px;
  background: #fbfcfd;
}

.document-card h3 {
  margin: 0;
  font-size: 18px;
}

.document-dl {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.document-dl > div {
  display: grid;
  gap: 4px;
}

.document-dl dt {
  color: rgba(29, 35, 38, 0.66);
  font-size: 12px;
}

.document-dl dd {
  margin: 0;
  font-weight: 600;
}

.document-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.document-table th,
.document-table td {
  padding: 10px 8px;
  border-bottom: 1px solid #e4eaed;
  text-align: left;
  vertical-align: top;
}

.document-table thead th {
  background: #f4f7f8;
  color: rgba(29, 35, 38, 0.75);
}

.document-table.compact th,
.document-table.compact td {
  padding: 8px 6px;
}

.block-section {
  grid-column: 1 / -1;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.summary-item {
  padding: 14px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #e4eaed;
  display: grid;
  gap: 4px;
}

.summary-item span {
  color: rgba(29, 35, 38, 0.66);
  font-size: 12px;
}

.summary-item strong {
  font-size: 20px;
}

.bullet-list {
  margin: 0;
  padding-left: 20px;
  display: grid;
  gap: 8px;
}

.print-note {
  margin: 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: #f4f7f8;
}

@media print {
  .no-print {
    display: none !important;
  }

  .archive-print-shell {
    gap: 0;
  }

  .print-document {
    width: 100%;
    margin: 0;
    border: none;
    box-shadow: none;
    border-radius: 0;
    padding: 12mm 10mm;
  }

  .document-card,
  .summary-item,
  .document-stamp {
    break-inside: avoid;
  }

  body {
    background: #fff;
  }
}

@media (max-width: 960px) {
  .document-grid,
  .summary-grid,
  .document-dl {
    grid-template-columns: 1fr;
  }
}
</style>
