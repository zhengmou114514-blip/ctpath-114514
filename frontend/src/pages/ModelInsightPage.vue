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
      summary: workspace.predictionResult.supportSummary || '当前患者的预测证据已生成。',
    }
  }

  return {
    eventCount: selectedPatient.value?.timeline.length ?? 0,
    relationCount: selectedPatient.value?.pathExplanation.length ?? 0,
    supportLevel: selectedPatient.value?.dataSupport ?? 'unknown',
    summary: selectedPatient.value?.summary || '当前患者尚未生成新的预测结果。',
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
    note: selectedPatient.value?.summary || '当前患者尚未触发新的建议生成。',
  }
})

const modelStatus = computed(() => {
  if (workspace.modelUnavailable) return '模型降级'
  if (workspace.health?.mode === 'demo') return 'Demo 模式'
  if (workspace.predictionResult?.mode === 'model') return '模型正常'
  if (workspace.predictionResult?.mode === 'similar-case') return '回退模式'
  return '待预测'
})

const hasPatient = computed(() => Boolean(selectedPatient.value))

function labelForSupportLevel(value: string) {
  if (value === 'strong') return '强'
  if (value === 'limited') return '有限'
  if (value === 'minimal') return '较弱'
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
  <section class="workspace-page model-insight-page">
    <header class="card page-header">
      <div>
        <h2>模型洞察</h2>
        <p>只展示当前患者相关的预测结果、证据和建议来源。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" @click="handleRefresh">刷新</button>
        <button class="primary-button" :disabled="!hasPatient || workspace.loadingPredict" @click="handleRunPrediction">
          {{ workspace.loadingPredict ? '预测中...' : '重新预测' }}
        </button>
      </div>
    </header>

    <section v-if="!hasPatient" class="card empty-state">
      请先在医生首页选择一位患者，再查看模型洞察。
    </section>

    <template v-else>
      <section class="overview-grid">
        <article class="card summary-card">
          <span>当前患者</span>
          <strong>{{ selectedPatient!.name }}</strong>
          <p>{{ selectedPatient!.patientId }} · {{ selectedPatient!.primaryDisease }}</p>
        </article>

        <article class="card summary-card">
          <span>模型状态</span>
          <strong>{{ modelStatus }}</strong>
          <p>当前模式：{{ workspace.health?.mode ?? '--' }}</p>
        </article>

        <article class="card summary-card">
          <span>证据强度</span>
          <strong>{{ labelForSupportLevel(evidence.supportLevel) }}</strong>
          <p>事件 {{ evidence.eventCount }} · 关系 {{ evidence.relationCount }}</p>
        </article>
      </section>

      <section class="detail-grid">
        <article class="card panel">
          <h3>当前患者预测结果</h3>
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

        <article class="card panel">
          <h3>证据摘要</h3>
          <ul class="kv-list">
            <li><span>事件数</span><strong>{{ evidence.eventCount }}</strong></li>
            <li><span>关系数</span><strong>{{ evidence.relationCount }}</strong></li>
            <li><span>证据强度</span><strong>{{ labelForSupportLevel(evidence.supportLevel) }}</strong></li>
          </ul>
          <p class="panel-note">{{ evidence.summary }}</p>
        </article>

        <article class="card panel">
          <h3>建议来源</h3>
          <ul class="kv-list">
            <li><span>Provider</span><strong>{{ adviceSource.provider }}</strong></li>
            <li><span>Model</span><strong>{{ adviceSource.model }}</strong></li>
            <li><span>Source</span><strong>{{ adviceSource.source }}</strong></li>
          </ul>
          <p class="panel-note">{{ adviceSource.note }}</p>
        </article>

        <article class="card panel">
          <h3>建议清单</h3>
          <ul v-if="adviceList.length" class="simple-list">
            <li v-for="(item, index) in adviceList.slice(0, 5)" :key="`${index}-${item}`">{{ item }}</li>
          </ul>
          <p v-else class="empty-inline">暂无建议。</p>
        </article>
      </section>

      <section class="card panel actions-panel">
        <h3>下一步操作</h3>
        <div class="action-row">
          <button class="secondary-button" @click="handleOpenDetail">查看患者详情</button>
          <button class="primary-button" @click="handleOpenFollowup">进入随访工作台</button>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.model-insight-page {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.summary-card,
.panel {
  padding: 14px;
  display: grid;
  gap: 8px;
}

.summary-card span {
  color: #60778e;
  font-size: 12px;
}

.summary-card strong {
  color: #17324d;
  font-size: 18px;
}

.summary-card p {
  margin: 0;
  color: #60778e;
  font-size: 12px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.panel h3 {
  margin: 0;
  color: #17324d;
  font-size: 15px;
}

.risk-list,
.simple-list {
  display: grid;
  gap: 8px;
}

.risk-item {
  border: 1px solid #d7e2ee;
  border-radius: 8px;
  padding: 10px;
  background: #fbfdff;
}

.risk-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.risk-head span {
  color: #4a7ab7;
  font-weight: 600;
}

.risk-item p,
.panel-note {
  margin: 0;
  color: #5f758b;
  font-size: 13px;
  line-height: 1.5;
}

.kv-list {
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.kv-list li {
  list-style: none;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid #d7e2ee;
  border-radius: 8px;
  padding: 8px 10px;
  background: #f9fbfd;
}

.kv-list span {
  color: #60778e;
  font-size: 12px;
}

.kv-list strong {
  color: #17324d;
}

.empty-inline,
.empty-state {
  border: 1px dashed #bfd0e1;
  border-radius: 8px;
  padding: 12px;
  color: #60778e;
  text-align: center;
}

.actions-panel {
  display: grid;
  gap: 12px;
}

.action-row {
  display: flex;
  gap: 8px;
}

@media (max-width: 1200px) {
  .overview-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .page-header,
  .action-row {
    flex-direction: column;
  }
}
</style>
