<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkspaceContext } from '../composables/workspaceContext'
import type { PatientSummary } from '../services/types'

const workspace = useWorkspaceContext()
const route = useRoute()
const router = useRouter()

const selectedPatient = computed(() => workspace.selectedPatient)
const patientOptions = computed<PatientSummary[]>(() => workspace.allPatients ?? [])
const selectedPatientId = computed(() => selectedPatient.value?.patientId ?? '')

const topK = computed(() => workspace.predictionResult?.topk ?? selectedPatient.value?.predictions ?? [])
const adviceList = computed(() => workspace.predictionResult?.advice ?? selectedPatient.value?.careAdvice ?? [])
const pathList = computed(() => (workspace.predictionResult?.pathExplanation ?? selectedPatient.value?.pathExplanation ?? []).slice(0, 3))

const evidence = computed(() => {
  if (workspace.predictionResult?.evidence) {
    return {
      eventCount: workspace.predictionResult.evidence.eventCount,
      relationCount: workspace.predictionResult.evidence.relationCount,
      supportLevel: workspace.predictionResult.evidence.supportLevel,
      summary: workspace.predictionResult.supportSummary || '系统根据当前患者病程事件、慢病阶段和关系证据生成了证据摘要。',
    }
  }

  return {
    eventCount: selectedPatient.value?.timeline.length ?? 0,
    relationCount: selectedPatient.value?.pathExplanation.length ?? 0,
    supportLevel: selectedPatient.value?.dataSupport ?? 'unknown',
    summary: selectedPatient.value?.summary || '当前展示患者历史摘要，选择患者并运行预测后可查看新的风险结果。',
  }
})

const adviceSource = computed(() => {
  const meta = workspace.predictionResult?.adviceMeta
  if (meta) {
    return `${meta.provider || '辅助诊疗服务'} / ${meta.model || '慢病风险预测模型'}`
  }
  if (selectedPatient.value?.recommendationMode === 'similar-case') return '相似病例辅助建议'
  return '患者历史病程与规则摘要'
})

const suggestFollowup = computed(() => {
  const highRisk = selectedPatient.value?.riskLevel?.toLowerCase().includes('high') || selectedPatient.value?.riskLevel?.includes('高')
  const hasUrgentAdvice = adviceList.value.some((item) => /随访|复诊|联系|监测|血压|血糖/.test(item))
  return Boolean(highRisk || hasUrgentAdvice)
})

const needDoctorReview = computed(() => {
  const highScore = topK.value.some((item) => item.score >= 0.75)
  const highRisk = selectedPatient.value?.riskLevel?.toLowerCase().includes('high') || selectedPatient.value?.riskLevel?.includes('高')
  return Boolean(highScore || highRisk)
})

const hasPatient = computed(() => Boolean(selectedPatient.value))
const activeTab = computed(() => {
  const tab = typeof route.query.tab === 'string' ? route.query.tab : 'current'
  return tab === 'evidence' || tab === 'advice' ? tab : 'current'
})

const tabItems = [
  { key: 'current', label: '风险评估' },
  { key: 'evidence', label: '证据摘要' },
  { key: 'advice', label: '辅助建议' },
]

function supportLabel(value: string) {
  if (value === 'strong' || value === 'high') return '高'
  if (value === 'limited' || value === 'medium') return '中'
  if (value === 'minimal' || value === 'low') return '低'
  return value || '待评估'
}

function riskLabel(value: string) {
  const raw = String(value || '').toLowerCase()
  if (raw.includes('high') || raw.includes('高')) return '高风险'
  if (raw.includes('medium') || raw.includes('中')) return '中风险'
  if (raw.includes('low') || raw.includes('低')) return '低风险'
  return value || '待评估'
}

function riskClass(value: string) {
  const label = riskLabel(value)
  if (label === '高风险') return 'risk-high'
  if (label === '中风险') return 'risk-medium'
  return 'risk-low'
}

async function handlePatientChange(event: Event) {
  const patientId = (event.target as HTMLSelectElement).value
  if (!patientId) return
  await workspace.openPatient(patientId, 'doctor')
}

async function handlePickAndPredict(patientId: string) {
  if (!patientId) return
  await workspace.openPatient(patientId, 'doctor')
  await workspace.runPrediction(true)
}

function handleRunPrediction() {
  if (!hasPatient.value) return
  void workspace.runPrediction(true)
}

function handleOpenDetail() {
  if (!selectedPatient.value) return
  void router.push({ name: 'patient-overview', params: { patientId: selectedPatient.value.patientId } })
}

function handleOpenFollowup() {
  if (!selectedPatient.value) return
  void router.push({ name: 'patient-followups', params: { patientId: selectedPatient.value.patientId } })
}

function switchTab(tab: string) {
  void router.push({ name: 'doctor-risk', query: { tab } })
}
</script>

<template>
  <section class="model-insight-page workstation-page">
    <header class="workstation-page-header insight-header">
      <div>
        <p class="eyebrow">模型辅助模块</p>
        <h1>模型洞察</h1>
        <p>围绕当前患者展示风险预测、证据摘要和辅助建议，结果仅供医生诊疗参考。</p>
      </div>
      <div class="header-actions">
        <select class="patient-select" :value="selectedPatientId" @change="handlePatientChange">
          <option value="">选择患者</option>
          <option v-for="patient in patientOptions" :key="patient.patientId" :value="patient.patientId">
            {{ patient.name }} / {{ patient.patientId }} / {{ patient.primaryDisease }}
          </option>
        </select>
        <button class="primary-button" type="button" :disabled="!hasPatient || workspace.loadingPredict" @click="handleRunPrediction">
          {{ workspace.loadingPredict ? '预测中...' : '运行风险预测' }}
        </button>
      </div>
    </header>

    <aside v-if="workspace.health?.model_error" class="model-status-banner tone-warning">
      <strong>模型降级运行</strong>
      <span>{{ workspace.health.model_error }}</span>
    </aside>
    <aside v-else-if="workspace.health && !workspace.health.model_available" class="model-status-banner tone-danger">
      <strong>模型不可用</strong>
      <span>当前模型服务未就绪，预测结果可能为规则回退。</span>
    </aside>
    <aside v-if="workspace.health?.mode === 'demo'" class="model-status-banner tone-notice">
      <strong>演示模式</strong>
      <span>当前运行为演示数据，非真实临床数据。</span>
    </aside>

    <section v-if="!hasPatient" class="clinical-card patient-picker-card">
      <div>
        <p class="eyebrow">未选择患者</p>
        <h2>请选择患者查看模型洞察</h2>
        <p>选择后可查看当前患者摘要、Top-K 风险、证据摘要和辅助建议。</p>
      </div>
      <div class="patient-pick-grid">
        <button
          v-for="patient in patientOptions.slice(0, 8)"
          :key="patient.patientId"
          class="patient-pick-card"
          type="button"
          @click="handlePickAndPredict(patient.patientId)"
        >
          <strong>{{ patient.name }}</strong>
          <span>{{ patient.patientId }} / {{ patient.primaryDisease }}</span>
          <em>{{ riskLabel(patient.riskLevel) }}</em>
        </button>
      </div>
    </section>

    <template v-else>
      <section class="patient-summary-band clinical-card">
        <div>
          <p class="eyebrow">当前患者摘要</p>
          <h2>{{ selectedPatient?.name }}</h2>
          <p>
            {{ selectedPatient?.patientId }} / {{ selectedPatient?.gender }} / {{ selectedPatient?.age }} 岁 /
            {{ selectedPatient?.primaryDisease }}
          </p>
        </div>
        <dl>
          <div>
            <dt>当前阶段</dt>
            <dd>{{ selectedPatient?.currentStage || '待维护' }}</dd>
          </div>
          <div>
            <dt>风险等级</dt>
            <dd><span class="risk-pill" :class="riskClass(selectedPatient?.riskLevel || '')">{{ riskLabel(selectedPatient?.riskLevel || '') }}</span></dd>
          </div>
          <div>
            <dt>最近就诊</dt>
            <dd>{{ selectedPatient?.lastVisit || '待补录' }}</dd>
          </div>
        </dl>
      </section>

      <nav class="insight-tabs" aria-label="辅助诊疗功能切换">
        <button
          v-for="item in tabItems"
          :key="item.key"
          class="insight-tab"
          :class="{ active: activeTab === item.key }"
          type="button"
          @click="switchTab(item.key)"
        >
          {{ item.label }}
        </button>
      </nav>

      <section v-if="activeTab === 'current'" class="insight-layout">
        <main class="clinical-card prediction-card">
          <div class="section-header">
            <div>
              <p class="eyebrow">风险预测结果</p>
              <h2>Top-K 风险</h2>
            </div>
          </div>
          <div v-if="topK.length" class="risk-list">
            <article v-for="(item, index) in topK.slice(0, 3)" :key="`${item.label}-${index}`" class="risk-item">
              <div class="risk-head">
                <strong>{{ index + 1 }}. {{ item.label }}</strong>
                <span>{{ Math.round(item.score * 100) }}%</span>
              </div>
              <el-progress :percentage="Math.round(item.score * 100)" :stroke-width="8" />
              <p>{{ item.reason }}</p>
            </article>
          </div>
          <p v-else class="empty-inline">当前暂无预测结果，请点击“运行风险预测”。</p>
        </main>

        <aside class="clinical-card decision-card">
          <p class="eyebrow">临床参考结论</p>
          <h2>下一步判断</h2>
          <dl class="decision-list">
            <div>
              <dt>是否建议随访</dt>
              <dd>{{ suggestFollowup ? '建议随访' : '暂不强制随访' }}</dd>
            </div>
            <div>
              <dt>是否需要医生复核</dt>
              <dd>{{ needDoctorReview ? '需要复核' : '常规观察' }}</dd>
            </div>
            <div>
              <dt>建议来源</dt>
              <dd>{{ adviceSource }}</dd>
            </div>
          </dl>
          <p class="medical-disclaimer">模型预测结果仅作为辅助参考，最终诊疗决策应由医生结合临床情况判断。</p>
        </aside>
      </section>

      <section v-else-if="activeTab === 'evidence'" class="insight-grid single-panel">
        <article class="clinical-card evidence-card">
          <p class="eyebrow">模型辅助证据</p>
          <h2>证据摘要</h2>
          <ul class="kv-list">
            <li><span>病程事件</span><strong>{{ evidence.eventCount }}</strong></li>
            <li><span>证据关系</span><strong>{{ evidence.relationCount }}</strong></li>
            <li><span>支撑等级</span><strong>{{ supportLabel(evidence.supportLevel) }}</strong></li>
          </ul>
          <p class="panel-note">{{ evidence.summary }}</p>
          <div v-if="pathList.length" class="path-list">
            <p v-for="item in pathList" :key="item">{{ item }}</p>
          </div>
        </article>
      </section>

      <section v-else class="insight-grid single-panel">
        <article class="clinical-card advice-card">
          <p class="eyebrow">医生诊疗参考</p>
          <h2>辅助建议</h2>
          <ol v-if="adviceList.length" class="advice-list">
            <li v-for="(item, index) in adviceList.slice(0, 5)" :key="`${index}-${item}`">{{ item }}</li>
          </ol>
          <p v-else class="empty-inline">当前没有可展示的建议内容。</p>
          <div class="action-row">
            <button class="secondary-button" type="button" @click="handleOpenDetail">打开患者详情</button>
            <button class="primary-button" type="button" @click="handleOpenFollowup">进入随访工作台</button>
          </div>
        </article>
      </section>
    </template>
  </section>
</template>

<style scoped>
.model-insight-page {
  display: grid;
  gap: 12px;
}

.insight-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 112px;
}

.insight-header h1 {
  margin: 2px 0 4px;
  font-size: 30px;
  line-height: 1.15;
}

.insight-header p {
  margin: 0;
  color: #526772;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.patient-select {
  width: min(460px, 48vw);
  min-height: 36px;
  border: 1px solid #bfd4df;
  border-radius: 4px;
  padding: 7px 9px;
  background: #fff;
}

.patient-picker-card {
  gap: 16px;
}

.patient-pick-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.patient-pick-card {
  display: grid;
  gap: 5px;
  border: 1px solid #d5e6ef;
  border-radius: 4px;
  background: #fff;
  padding: 10px;
  text-align: left;
}

.patient-pick-card span,
.patient-pick-card em {
  color: #526772;
  font-size: 12px;
}

.patient-pick-card em {
  font-style: normal;
  font-weight: 800;
}

.patient-summary-band {
  grid-template-columns: minmax(260px, 0.8fr) minmax(420px, 1.2fr);
  align-items: center;
  min-height: 126px;
}

.patient-summary-band h2 {
  margin: 2px 0 4px;
  font-size: 28px;
}

.patient-summary-band p {
  margin: 0;
  color: #526772;
}

.patient-summary-band dl,
.decision-list {
  display: grid;
  gap: 8px;
  margin: 0;
}

.patient-summary-band dl {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: stretch;
}

.patient-summary-band dl div {
  border-left: 1px solid #d5e6ef;
  padding-left: 14px;
}

.insight-tabs {
  display: flex;
  gap: 6px;
  border-bottom: 1px solid #cfdde5;
}

.insight-tab {
  min-height: 36px;
  border: 1px solid #cfdde5;
  border-bottom: 0;
  border-radius: 4px 4px 0 0;
  background: #f7fbfd;
  color: #275d70;
  padding: 0 16px;
  font-weight: 900;
}

.insight-tab.active {
  background: #008bbf;
  border-color: #008bbf;
  color: #fff;
}

.patient-summary-band dt,
.decision-list dt {
  color: #527384;
  font-size: 12px;
  font-weight: 800;
}

.patient-summary-band dd,
.decision-list dd {
  margin: 2px 0 0;
  color: #243f4d;
  font-weight: 900;
}

.insight-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 12px;
}

.prediction-card,
.decision-card,
.insight-grid .clinical-card {
  display: grid;
  gap: 12px;
}

.risk-list {
  display: grid;
  gap: 10px;
}

.risk-item {
  display: grid;
  gap: 8px;
  border: 1px solid #d5e6ef;
  border-radius: 4px;
  background: #fff;
  padding: 10px 12px;
}

.risk-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.risk-head span {
  color: #0f6f99;
  font-size: 20px;
  font-weight: 900;
}

.risk-item p,
.panel-note,
.medical-disclaimer {
  margin: 0;
  color: #526772;
  line-height: 1.65;
}

.medical-disclaimer {
  padding: 10px;
  border-left: 3px solid #008bbf;
  background: #edf7fc;
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.insight-grid.single-panel {
  grid-template-columns: minmax(0, 1fr);
}

.evidence-card,
.advice-card {
  min-height: 340px;
}

.kv-list,
.advice-list,
.path-list {
  display: grid;
  gap: 8px;
  margin: 0;
}

.kv-list {
  padding: 0;
  list-style: none;
}

.advice-list {
  padding-left: 20px;
}

.kv-list li,
.path-list {
  border: 1px solid #d5e6ef;
  border-radius: 4px;
  background: #f7fbfd;
  padding: 10px;
}

.kv-list li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.path-list p {
  margin: 0;
  color: #526772;
  font-size: 13px;
}

.empty-inline {
  margin: 0;
  border: 1px dashed #b7d1de;
  border-radius: 4px;
  padding: 12px;
  color: #526772;
  text-align: center;
}

.action-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.model-status-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 4px;
  font-size: 13px;
}

.model-status-banner.tone-warning {
  background: #fff7ed;
  border: 1px solid #f9d4b0;
  color: #9a5b00;
}

.model-status-banner.tone-danger {
  background: #fff5f5;
  border: 1px solid #f3b8b8;
  color: #b42318;
}

.model-status-banner.tone-notice {
  background: #edf7fc;
  border: 1px solid #b7d1de;
  color: #275d70;
}

@media (max-width: 1100px) {
  .patient-pick-grid,
  .patient-summary-band,
  .patient-summary-band dl,
  .insight-layout,
  .insight-grid {
    grid-template-columns: 1fr;
  }

  .patient-summary-band dl div {
    border-left: 0;
    border-top: 1px solid #d5e6ef;
    padding: 10px 0 0;
  }

  .patient-select {
    width: 100%;
  }
}
</style>
