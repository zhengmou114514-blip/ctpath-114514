<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getRiskAssessments, refreshRiskAssessment } from '../../services/api'
import type { RiskAssessmentRecord } from '../../services/types'
import { useWorkspaceContext } from '../../composables/workspaceContext'

const workspace = useWorkspaceContext()
const route = useRoute()
const router = useRouter()
const patient = computed(() => workspace.selectedPatient)
const assessments = ref<RiskAssessmentRecord[]>([])
const loading = ref(false)
const refreshing = ref(false)
const error = ref('')
const message = ref('')

const current = computed(() => assessments.value.find((item) => item.isCurrent) ?? assessments.value[0] ?? null)
const topK = computed(() => current.value?.topk ?? patient.value?.predictions ?? [])
const advice = computed(() => current.value?.advice ?? patient.value?.careAdvice ?? [])
const evidence = computed(() => current.value?.supportSummary || patient.value?.summary || '当前展示演示推理结果和规则回退摘要。')
const generatedAt = computed(() => current.value?.generatedAt ?? patient.value?.latestAssessmentAt ?? '尚未刷新')
const sourceLabel = computed(() => {
  const item = current.value
  if (!item) return '演示推理结果'
  if (item.mode === 'model' && item.strategy === 'direct-model') return '模型推理结果'
  if (item.strategy === 'rules') return '规则回退结果'
  return '演示推理结果'
})
const activeTab = computed(() => {
  const tab = typeof route.query.tab === 'string' ? route.query.tab : 'current'
  return ['current', 'history', 'evidence', 'advice'].includes(tab) ? tab : 'current'
})

function setTab(tab: string) {
  void router.replace({ query: { ...route.query, tab } })
}

async function loadAssessments() {
  if (!patient.value) return
  loading.value = true
  error.value = ''
  try {
    assessments.value = (await getRiskAssessments(patient.value.patientId)).items
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '风险评估加载失败。'
  } finally {
    loading.value = false
  }
}

async function refreshRisk() {
  if (!patient.value) return
  refreshing.value = true
  error.value = ''
  message.value = ''
  try {
    const updated = await refreshRiskAssessment(patient.value.patientId)
    await loadAssessments()
    message.value = `风险评估已刷新：${updated.generatedAt.slice(0, 19).replace('T', ' ')}`
    setTab('current')
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '风险评估刷新失败。'
  } finally {
    refreshing.value = false
  }
}

watch(
  () => patient.value?.patientId,
  () => {
    assessments.value = []
    void loadAssessments()
  },
  { immediate: true }
)
</script>

<template>
  <section v-if="patient" class="patient-feature-grid">
    <article class="clinical-card risk-shell">
      <div class="section-header">
        <div>
          <p class="eyebrow">风险评估</p>
          <h2>风险评估与辅助建议</h2>
        </div>
        <button class="primary-button" type="button" :disabled="refreshing" @click="refreshRisk">
          {{ refreshing ? '正在评估...' : '刷新风险评估' }}
        </button>
      </div>

      <div class="risk-tabs">
        <button type="button" :class="{ active: activeTab === 'current' }" @click="setTab('current')">当前评估</button>
        <button type="button" :class="{ active: activeTab === 'history' }" @click="setTab('history')">历史评估</button>
        <button type="button" :class="{ active: activeTab === 'evidence' }" @click="setTab('evidence')">证据摘要</button>
        <button type="button" :class="{ active: activeTab === 'advice' }" @click="setTab('advice')">辅助建议</button>
      </div>

      <p v-if="message" class="success-line">{{ message }}</p>
      <p v-if="error" class="risk-error">{{ error }}</p>
      <p v-if="loading" class="muted-line">正在加载风险评估记录...</p>

      <div v-if="activeTab === 'current'" class="risk-current">
        <p>模型结果仅供医生诊疗参考，不能替代临床判断。</p>
        <div class="risk-meta">
          <span>评估时间：{{ generatedAt }}</span>
          <span>评估来源：{{ sourceLabel }}</span>
          <span>证据数量：{{ current?.evidence.eventCount ?? 0 }}</span>
        </div>
        <div class="risk-list">
          <p v-for="item in topK.slice(0, 3)" :key="item.label">
            <strong>{{ item.label }} {{ Math.round(item.score * 100) }}%</strong>
            <span>{{ item.reason }}</span>
          </p>
        </div>
      </div>

      <div v-else-if="activeTab === 'history'" class="history-table">
        <table>
          <thead>
            <tr>
              <th>评估编号</th>
              <th>评估时间</th>
              <th>风险提示</th>
              <th>证据</th>
              <th>来源</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in assessments" :key="item.resultId">
              <td>{{ item.resultId }}</td>
              <td>{{ item.generatedAt.slice(0, 19).replace('T', ' ') }}</td>
              <td>{{ item.topk[0]?.label || patient.riskLevel }}</td>
              <td>{{ item.evidence.eventCount }} 条</td>
              <td>{{ item.strategy === 'direct-model' ? '模型推理结果' : '演示/规则结果' }}</td>
            </tr>
            <tr v-if="!assessments.length && !loading">
              <td colspan="5">暂无历史评估，请点击“刷新风险评估”。</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else-if="activeTab === 'evidence'" class="clinical-section">
        <h3>证据摘要</h3>
        <p>{{ evidence }}</p>
        <ul v-if="current">
          <li>病程事件：{{ current.evidence.eventCount }} 条</li>
          <li>时间点：{{ current.evidence.timepointCount }} 个</li>
          <li>关系类型：{{ current.evidence.relationCount }} 类</li>
          <li>支持级别：{{ current.evidence.supportLevel }}</li>
        </ul>
      </div>

      <div v-else class="clinical-section">
        <h3>辅助建议</h3>
        <ol>
          <li v-for="item in advice.slice(0, 6)" :key="item">{{ item }}</li>
        </ol>
      </div>
    </article>
  </section>
</template>

<style scoped>
.patient-feature-grid { display: grid; grid-template-columns: 1fr; gap: 12px; }
.risk-shell { display: grid; gap: 12px; }
.risk-tabs { display: flex; flex-wrap: wrap; gap: 8px; border-bottom: 1px solid #d5e6ef; padding-bottom: 8px; }
.risk-tabs button { min-height: 34px; border: 1px solid #c9dce6; background: #f7fbfd; color: #003f43; font-weight: 700; cursor: pointer; }
.risk-tabs button.active { background: #00474b; color: #fff; border-color: #00474b; }
.risk-list { display: grid; gap: 8px; }
.risk-list p { display: grid; gap: 4px; margin: 0; padding: 10px; background: #f7fbfd; border: 1px solid #d5e6ef; }
.risk-meta { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; color: #526772; font-size: 12px; font-weight: 700; }
.history-table { overflow-x: auto; }
.history-table table { width: 100%; border-collapse: collapse; background: #fff; }
.history-table th,
.history-table td { border: 1px solid #d5e6ef; padding: 9px; text-align: left; vertical-align: top; }
.history-table th { background: #f0f7fa; color: #003f43; }
.clinical-section { display: grid; gap: 8px; }
.success-line { color: #027a48; font-weight: 700; }
.risk-error { color: #b42318; font-weight: 700; }
.muted-line { color: #526772; }
</style>
