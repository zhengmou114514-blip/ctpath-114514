<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useWorkspaceContext } from '../composables/workspaceContext'

const workspace = useWorkspaceContext()

const selectedPatient = computed(() => workspace.selectedPatient)
const topK = computed(() => workspace.predictionResult?.topk ?? selectedPatient.value?.predictions ?? [])
const evidence = computed(() => {
  if (workspace.predictionResult?.evidence) {
    return {
      eventCount: workspace.predictionResult.evidence.eventCount,
      relationCount: workspace.predictionResult.evidence.relationCount,
      supportLevel: workspace.predictionResult.evidence.supportLevel,
      summary: workspace.predictionResult.supportSummary || '已加载当前患者证据摘要。',
    }
  }

  return {
    eventCount: selectedPatient.value?.timeline.length ?? 0,
    relationCount: selectedPatient.value?.pathExplanation.length ?? 0,
    supportLevel: selectedPatient.value?.dataSupport ?? 'unknown',
    summary: selectedPatient.value?.summary || '暂无当前患者证据摘要。',
  }
})

const adviceList = computed(() => workspace.predictionResult?.advice ?? selectedPatient.value?.careAdvice ?? [])
const adviceSource = computed(() => {
  const meta = workspace.predictionResult?.adviceMeta
  if (meta) {
    return {
      provider: meta.provider || '--',
      model: meta.model || '--',
      source: meta.source,
      note: meta.note || '--',
    }
  }

  return {
    provider: selectedPatient.value?.recommendationMode || '--',
    model: workspace.health?.mode || '--',
    source: workspace.modelUnavailable ? 'fallback' : 'history',
    note: selectedPatient.value?.summary || '暂无建议来源说明。',
  }
})

const modelStatus = computed(() => {
  if (workspace.modelUnavailable) return '模型不可用'
  if (workspace.health?.mode === 'demo') return 'Demo 模式'
  if (workspace.predictionResult?.mode === 'model') return '模型结果'
  if (workspace.predictionResult?.mode === 'similar-case') return '相似病例回退'
  return '待预测'
})

const hasPatient = computed(() => Boolean(selectedPatient.value))

function supportLabel(value: string) {
  if (value === 'strong' || value === 'high') return '高'
  if (value === 'limited' || value === 'medium') return '中'
  if (value === 'minimal' || value === 'low') return '低'
  return value || '--'
}

function handleRefresh() {
  void workspace.refreshGovernanceWorkspace()
}

function handleRunPrediction() {
  if (!hasPatient.value) return
  void workspace.runPrediction()
}

function handleOpenDetail() {
  if (!selectedPatient.value) return
  void workspace.openPatient(selectedPatient.value.patientId, 'doctor')
}

function handleOpenFollowup() {
  if (!selectedPatient.value) return
  void workspace.openFollowupModule(selectedPatient.value.patientId, 'tasks')
}

onMounted(() => {
  if (!workspace.currentDoctor) return
  if (!workspace.modelMetrics || !workspace.maintenanceOverview) {
    void workspace.refreshGovernanceWorkspace()
  }
})
</script>

<template>
  <section class="model-insight-page workstation-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">Model insight</p>
        <h1>模型洞察</h1>
        <p>当前患者预测结果、Top-K 风险事件、证据摘要、建议来源和下一步动作。</p>
      </div>
      <div class="header-actions">
        <el-button @click="handleRefresh">刷新上下文</el-button>
        <el-button type="primary" :disabled="!hasPatient || workspace.loadingPredict" :loading="workspace.loadingPredict" @click="handleRunPrediction">
          运行预测
        </el-button>
      </div>
    </header>

    <section v-if="!hasPatient" class="empty-state-card">
      <h3>未选择患者</h3>
      <p>请先从医生工作台选择患者，再查看当前患者模型洞察。</p>
    </section>

    <template v-else>
      <section class="metric-grid three">
        <article class="metric-card">
          <span>当前患者</span>
          <strong>{{ selectedPatient?.name }}</strong>
          <p>{{ selectedPatient?.patientId }} / {{ selectedPatient?.primaryDisease }}</p>
        </article>
        <article class="metric-card">
          <span>模型状态</span>
          <strong>{{ modelStatus }}</strong>
          <p>运行模式 {{ workspace.health?.mode ?? '--' }}</p>
        </article>
        <article class="metric-card">
          <span>证据支持</span>
          <strong>{{ supportLabel(evidence.supportLevel) }}</strong>
          <p>事件 {{ evidence.eventCount }} / 关系 {{ evidence.relationCount }}</p>
        </article>
      </section>

      <section class="insight-grid">
        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>Top-K 风险事件</h2>
              <p>当前患者相关预测。</p>
            </div>
          </div>
          <div v-if="topK.length" class="risk-list">
            <div v-for="(item, index) in topK.slice(0, 3)" :key="`${item.label}-${index}`" class="risk-item">
              <div class="risk-head">
                <strong>{{ index + 1 }}. {{ item.label }}</strong>
                <span>{{ Math.round(item.score * 100) }}%</span>
              </div>
              <p>{{ item.reason }}</p>
            </div>
          </div>
          <p v-else class="empty-inline">暂无预测结果。</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>证据摘要</h2>
              <p>模型可解释证据和当前数据支持水平。</p>
            </div>
          </div>
          <ul class="kv-list">
            <li><span>事件数</span><strong>{{ evidence.eventCount }}</strong></li>
            <li><span>关系数</span><strong>{{ evidence.relationCount }}</strong></li>
            <li><span>支持水平</span><strong>{{ supportLabel(evidence.supportLevel) }}</strong></li>
          </ul>
          <p class="panel-note">{{ evidence.summary }}</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>建议来源</h2>
              <p>区分模型、相似病例和回退来源。</p>
            </div>
          </div>
          <ul class="kv-list">
            <li><span>Provider</span><strong>{{ adviceSource.provider }}</strong></li>
            <li><span>Model</span><strong>{{ adviceSource.model }}</strong></li>
            <li><span>Source</span><strong>{{ adviceSource.source }}</strong></li>
          </ul>
          <p class="panel-note">{{ adviceSource.note }}</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>建议摘要</h2>
              <p>{{ adviceList.length }} 条</p>
            </div>
          </div>
          <ol v-if="adviceList.length" class="advice-list">
            <li v-for="(item, index) in adviceList.slice(0, 5)" :key="`${index}-${item}`">{{ item }}</li>
          </ol>
          <p v-else class="empty-inline">暂无建议。</p>
        </article>
      </section>

      <section class="clinical-card actions-panel">
        <div class="section-header">
          <div>
            <h2>下一步动作</h2>
            <p>进入当前患者详情或随访闭环。</p>
          </div>
        </div>
        <div class="action-row">
          <el-button @click="handleOpenDetail">打开患者详情</el-button>
          <el-button type="primary" @click="handleOpenFollowup">打开随访任务</el-button>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.model-insight-page {
  display: grid;
  gap: 24px;
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.risk-list,
.kv-list,
.advice-list {
  display: grid;
  gap: 10px;
  margin: 0;
}

.kv-list {
  padding: 0;
}

.advice-list {
  padding-left: 20px;
}

.risk-item,
.kv-list li {
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: var(--ws-surface-soft);
  padding: 12px;
}

.kv-list li {
  list-style: none;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.risk-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.risk-head span,
.kv-list strong {
  color: var(--ws-title);
  font-weight: 800;
}

.risk-item p,
.panel-note {
  margin: 6px 0 0;
  color: var(--ws-text-muted);
  line-height: 1.6;
}

.kv-list span {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.empty-inline {
  margin: 0;
  border: 1px dashed var(--ws-border-strong);
  border-radius: 8px;
  padding: 12px;
  color: var(--ws-text-muted);
  text-align: center;
}

.actions-panel {
  display: grid;
  gap: 16px;
}

.action-row {
  display: flex;
  gap: 10px;
}

@media (max-width: 1100px) {
  .insight-grid {
    grid-template-columns: 1fr;
  }
}
</style>
