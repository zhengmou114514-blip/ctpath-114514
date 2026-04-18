<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PatientAttachmentPanel from '../components/archive/PatientAttachmentPanel.vue'
import MedicationAdequacyPanel from '../components/patient-workstation/MedicationAdequacyPanel.vue'
import { useWorkspaceContext } from '../composables/workspaceContext'

const workspace = useWorkspaceContext()
const route = useRoute()
const router = useRouter()

const routePatientId = computed(() => {
  const value = route.params.patientId
  return typeof value === 'string' ? value : ''
})

const selectedPatient = computed(() => workspace.selectedPatient)
const doctorRole = computed(() => workspace.currentDoctor?.role ?? 'doctor')
const topPrediction = computed(() => workspace.predictionResult?.topk?.[0] ?? selectedPatient.value?.predictions?.[0] ?? null)
const adviceList = computed(() => workspace.predictionResult?.advice ?? selectedPatient.value?.careAdvice ?? [])
const evidence = computed(() => {
  const prediction = workspace.predictionResult
  if (prediction?.evidence) {
    return {
      eventCount: prediction.evidence.eventCount,
      relationCount: prediction.evidence.relationCount,
      supportLevel: prediction.evidence.supportLevel,
      summary: prediction.supportSummary || '当前患者预测证据已生成。',
    }
  }

  return {
    eventCount: selectedPatient.value?.timeline.length ?? 0,
    relationCount: selectedPatient.value?.pathExplanation.length ?? 0,
    supportLevel: selectedPatient.value?.dataSupport ?? 'unknown',
    summary: selectedPatient.value?.summary || '当前患者尚未生成新的预测摘要。',
  }
})

const modelStatus = computed(() => {
  if (workspace.modelUnavailable) return '模型降级'
  if (workspace.health?.mode === 'demo') return 'Demo 模式'
  if (workspace.predictionResult?.mode === 'model') return '模型正常'
  if (workspace.predictionResult?.mode === 'similar-case') return '回退结果'
  return '待加载'
})

function labelForSupportLevel(value: string) {
  if (value === 'strong') return '强'
  if (value === 'limited') return '有限'
  if (value === 'minimal') return '较弱'
  return value || '--'
}

async function loadPatientDetail(patientId: string) {
  if (!patientId) return
  if (workspace.selectedPatientId === patientId && workspace.selectedPatient) return
  await workspace.openPatient(patientId, 'doctor')
}

function handleBack() {
  void router.push({ name: 'home' })
}

function handleOpenFollowup() {
  const patientId = selectedPatient.value?.patientId || routePatientId.value
  if (!patientId) return
  void workspace.openFollowupModule(patientId, 'tasks')
}

watch(
  routePatientId,
  (value) => {
    void loadPatientDetail(value)
  },
  { immediate: true }
)
</script>

<template>
  <section class="patient-detail-page">
    <header class="card page-header">
      <div>
        <h2>患者详情</h2>
        <p>独立承接患者主信息、时间线、当前用药、预测摘要、建议摘要和附件入口。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" @click="handleBack">返回医生首页</button>
        <button class="primary-button" :disabled="!selectedPatient" @click="handleOpenFollowup">进入随访</button>
      </div>
    </header>

    <section v-if="!selectedPatient" class="card empty-state">
      请先从医生首页选择患者，或者使用患者详情路由打开已选患者。
    </section>

    <template v-else>
      <section class="overview-grid">
        <article class="card info-card">
          <span>患者主信息</span>
          <strong>{{ selectedPatient.name }}</strong>
          <p>{{ selectedPatient.patientId }} · {{ selectedPatient.primaryDisease }}</p>
          <div class="meta-grid">
            <div><span>年龄</span><strong>{{ selectedPatient.age }}</strong></div>
            <div><span>性别</span><strong>{{ selectedPatient.gender }}</strong></div>
            <div><span>最近就诊</span><strong>{{ selectedPatient.lastVisit || '--' }}</strong></div>
            <div><span>病程阶段</span><strong>{{ selectedPatient.currentStage || '--' }}</strong></div>
          </div>
        </article>

        <article class="card info-card">
          <span>预测摘要</span>
          <strong>{{ modelStatus }}</strong>
          <p>{{ evidence.summary }}</p>
          <div v-if="topPrediction" class="prediction-box">
            <strong>{{ topPrediction.label }}</strong>
            <span>{{ Math.round(topPrediction.score * 100) }}%</span>
            <p>{{ topPrediction.reason }}</p>
          </div>
        </article>
      </section>

      <section class="detail-grid">
        <article class="card panel">
          <h3>病程时间线</h3>
          <div v-if="selectedPatient.timeline.length" class="timeline-list">
            <div v-for="item in selectedPatient.timeline.slice(0, 8)" :key="`${item.date}-${item.type}`" class="timeline-item">
              <span class="timeline-date">{{ item.date }}</span>
              <div>
                <strong>{{ item.title }}</strong>
                <p>{{ item.detail }}</p>
              </div>
            </div>
          </div>
          <p v-else class="empty-inline">暂无时间线数据。</p>
        </article>

        <article class="card panel medication-module">
          <MedicationAdequacyPanel :patient="selectedPatient" :model-advice="adviceList" :doctor-role="doctorRole" />
        </article>

        <article class="card panel">
          <h3>建议摘要</h3>
          <ul v-if="adviceList.length" class="simple-list">
            <li v-for="(item, index) in adviceList.slice(0, 5)" :key="`${index}-${item}`">{{ item }}</li>
          </ul>
          <p v-else class="empty-inline">暂无建议摘要。</p>
        </article>

        <article class="card panel attachment-module">
          <PatientAttachmentPanel :patient-id="selectedPatient.patientId" title="附件摘要入口" />
        </article>

        <article class="card panel">
          <h3>证据摘要</h3>
          <ul class="kv-list">
            <li><span>事件数</span><strong>{{ evidence.eventCount }}</strong></li>
            <li><span>关系数</span><strong>{{ evidence.relationCount }}</strong></li>
            <li><span>证据强度</span><strong>{{ labelForSupportLevel(evidence.supportLevel) }}</strong></li>
          </ul>
        </article>

        <article class="card panel">
          <h3>下一步动作</h3>
          <div class="action-row">
            <button class="primary-button" @click="handleBack">返回首页</button>
            <button class="secondary-button" @click="handleOpenFollowup">进入随访</button>
          </div>
        </article>
      </section>
    </template>
  </section>
</template>

<style scoped>
.patient-detail-page {
  padding: 20px;
  display: grid;
  gap: 14px;
  align-content: start;
}

.page-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  color: #17324d;
}

.page-header p {
  margin: 4px 0 0;
  color: #5f758b;
  font-size: 13px;
}

.header-actions,
.action-row {
  display: flex;
  gap: 8px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.medication-module,
.attachment-module {
  grid-column: 1 / -1;
}

.info-card,
.panel {
  padding: 14px;
  display: grid;
  gap: 10px;
}

.info-card span,
.panel h3 {
  color: #60778e;
  font-size: 12px;
  font-weight: 600;
}

.info-card strong {
  color: #17324d;
  font-size: 18px;
}

.info-card p,
.placeholder-text {
  margin: 0;
  color: #5f758b;
  font-size: 13px;
  line-height: 1.6;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.meta-grid div,
.prediction-box {
  border: 1px solid #d7e2ee;
  border-radius: 8px;
  background: #f9fbfd;
  padding: 10px;
}

.meta-grid span,
.prediction-box p {
  display: block;
  color: #6b7f92;
  font-size: 11px;
  margin-bottom: 2px;
}

.prediction-box strong {
  color: #17324d;
}

.timeline-list {
  display: grid;
  gap: 10px;
}

.timeline-item {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 10px;
  align-items: start;
  border-bottom: 1px solid #e4ebf2;
  padding-bottom: 10px;
}

.timeline-date {
  font-size: 12px;
  color: #60778e;
}

.timeline-item p,
.empty-inline {
  margin: 4px 0 0;
  color: #5f758b;
  font-size: 13px;
}

.simple-list,
.kv-list {
  margin: 0;
  padding-left: 18px;
}

.kv-list {
  list-style: none;
  padding-left: 0;
  display: grid;
  gap: 8px;
}

.kv-list li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid #d7e2ee;
  border-radius: 8px;
  padding: 8px 10px;
}

.kv-list span {
  color: #60778e;
  font-size: 12px;
}

.kv-list strong {
  color: #17324d;
}

.empty-state {
  padding: 16px;
  text-align: center;
  color: #5f758b;
}

@media (max-width: 900px) {
  .overview-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .medication-module,
  .attachment-module {
    grid-column: auto;
  }
}
</style>
