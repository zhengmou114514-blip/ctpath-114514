<script setup lang="ts">
import { computed } from 'vue'
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
      summary: workspace.predictionResult.supportSummary || '当前模型已给出基于病程事件与关系证据的支持摘要。',
    }
  }

  return {
    eventCount: selectedPatient.value?.timeline.length ?? 0,
    relationCount: selectedPatient.value?.pathExplanation.length ?? 0,
    supportLevel: selectedPatient.value?.dataSupport ?? 'unknown',
    summary: selectedPatient.value?.summary || '当前仅展示患者历史摘要，尚未触发新的实时预测。',
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
    note: selectedPatient.value?.summary || '当前展示的是患者已有建议摘要。',
  }
})

const modelStatus = computed(() => {
  if (workspace.modelUnavailable) return '模型不可用'
  if (workspace.health?.mode === 'demo') return 'Demo 模式'
  if (workspace.predictionResult?.mode === 'model') return '模型直推'
  if (workspace.predictionResult?.mode === 'similar-case') return '相似病例回退'
  return '历史摘要模式'
})

const hasPatient = computed(() => Boolean(selectedPatient.value))

function supportLabel(value: string) {
  if (value === 'strong' || value === 'high') return '高'
  if (value === 'limited' || value === 'medium') return '中'
  if (value === 'minimal' || value === 'low') return '低'
  return value || '--'
}

async function handleRefresh() {
  if (!selectedPatient.value) return
  await workspace.openPatient(selectedPatient.value.patientId, 'doctor')
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
</script>

<template>
  <section class="model-insight-page workstation-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">模型中心</p>
        <h1>模型洞察</h1>
        <p>这里只面向当前患者，展示风险预测、证据摘要与建议来源，不承接训练任务、全局指标或治理缺陷列表。</p>
      </div>
      <div class="header-actions">
        <el-button @click="handleRefresh">刷新当前患者</el-button>
        <el-button type="primary" :disabled="!hasPatient || workspace.loadingPredict" :loading="workspace.loadingPredict" @click="handleRunPrediction">
          重算洞察
        </el-button>
      </div>
    </header>

    <section v-if="!hasPatient" class="empty-state-card">
      <h3>当前没有选中的患者</h3>
      <p>请先从医生工作台或患者详情页进入一个具体患者，再查看该患者对应的模型洞察。</p>
    </section>

    <template v-else>
      <section class="metric-grid three">
        <article class="metric-card">
          <span>当前患者</span>
          <strong>{{ selectedPatient?.name }}</strong>
          <p>{{ selectedPatient?.patientId }} / {{ selectedPatient?.primaryDisease }}</p>
        </article>
        <article class="metric-card">
          <span>预测模式</span>
          <strong>{{ modelStatus }}</strong>
          <p>当前运行模式：{{ workspace.health?.mode ?? '--' }}</p>
        </article>
        <article class="metric-card">
          <span>证据支持等级</span>
          <strong>{{ supportLabel(evidence.supportLevel) }}</strong>
          <p>事件数 {{ evidence.eventCount }} / 关系数 {{ evidence.relationCount }}</p>
        </article>
      </section>

      <section class="insight-grid">
        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>Top-K 风险事件</h2>
              <p>仅展示当前患者最需要关注的风险事件及其分数与原因。</p>
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
          <p v-else class="empty-inline">当前没有可展示的风险预测结果。</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>证据摘要</h2>
              <p>汇总病程事件、关系数量与支撑等级，帮助理解当前患者的洞察来源。</p>
            </div>
          </div>
          <ul class="kv-list">
            <li><span>事件数</span><strong>{{ evidence.eventCount }}</strong></li>
            <li><span>关系数</span><strong>{{ evidence.relationCount }}</strong></li>
            <li><span>支撑等级</span><strong>{{ supportLabel(evidence.supportLevel) }}</strong></li>
          </ul>
          <p class="panel-note">{{ evidence.summary }}</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>建议来源</h2>
              <p>说明当前建议来自模型、回退逻辑还是患者历史摘要，避免和治理或训练信息混淆。</p>
            </div>
          </div>
          <ul class="kv-list">
            <li><span>提供方</span><strong>{{ adviceSource.provider }}</strong></li>
            <li><span>模型</span><strong>{{ adviceSource.model }}</strong></li>
            <li><span>来源</span><strong>{{ adviceSource.source }}</strong></li>
          </ul>
          <p class="panel-note">{{ adviceSource.note }}</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>建议清单</h2>
              <p>只显示当前患者的诊疗建议摘要，不承接训练结果或全局治理动作。</p>
            </div>
          </div>
          <ol v-if="adviceList.length" class="advice-list">
            <li v-for="(item, index) in adviceList.slice(0, 5)" :key="`${index}-${item}`">{{ item }}</li>
          </ol>
          <p v-else class="empty-inline">当前没有可展示的建议内容。</p>
        </article>
      </section>

      <section class="clinical-card actions-panel">
        <div class="section-header">
          <div>
            <h2>下一步动作</h2>
            <p>回到患者详情或进入随访模块，保持模型洞察和临床工作流的闭环。</p>
          </div>
        </div>
        <div class="action-row">
          <el-button @click="handleOpenDetail">打开患者详情</el-button>
          <el-button type="primary" @click="handleOpenFollowup">进入随访工作台</el-button>
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
