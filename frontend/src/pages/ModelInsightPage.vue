<script setup lang="ts">
import { computed } from 'vue'
import type { PatientCase, PredictResponse } from '../services/types'

const props = defineProps<{
  selectedPatient: PatientCase | null
  predictionResult: PredictResponse | null
  loadingPredict: boolean
  modelUnavailable: boolean
  systemMode: string
}>()

const emit = defineEmits<{
  refresh: []
  runPredict: []
  openPatientDetail: []
  openFollowup: []
}>()

const topK = computed(() => props.predictionResult?.topk ?? props.selectedPatient?.predictions ?? [])
const topKEvents = computed(() => topK.value.slice(0, 3))

const evidenceSummary = computed(() => {
  if (props.predictionResult?.evidence) {
    return {
      eventCount: props.predictionResult.evidence.eventCount,
      relationCount: props.predictionResult.evidence.relationCount,
      supportLevel: props.predictionResult.evidence.supportLevel,
      summary: props.predictionResult.supportSummary || '来自模型推理证据摘要。',
    }
  }

  const patient = props.selectedPatient
  return {
    eventCount: patient?.timeline.length ?? 0,
    relationCount: Math.max(0, patient?.pathExplanation.length ?? 0),
    supportLevel: patient?.dataSupport ?? 'unknown',
    summary: '当前为患者历史证据摘要（无新推理结果）。',
  }
})

const adviceList = computed(() => props.predictionResult?.advice ?? props.selectedPatient?.careAdvice ?? [])

const adviceSource = computed(() => {
  const meta = props.predictionResult?.adviceMeta
  if (!meta) {
    return {
      provider: 'patient-history',
      model: '--',
      source: 'history',
      note: '当前建议来自患者历史记录与默认规则。',
    }
  }

  return {
    provider: meta.provider || '--',
    model: meta.model || '--',
    source: meta.source,
    note: meta.note || '--',
  }
})

const modelStatus = computed(() => {
  if (props.modelUnavailable) return '降级中'
  if (props.systemMode === 'demo') return '演示模式'
  return '可用'
})

const hasPatient = computed(() => Boolean(props.selectedPatient))
</script>

<template>
  <section class="insight-page">
    <header class="page-header card">
      <div>
        <h2>模型洞察</h2>
        <p>当前患者预测、证据与处置建议</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" @click="emit('refresh')">刷新数据</button>
        <button class="primary-button" :disabled="!hasPatient || loadingPredict" @click="emit('runPredict')">
          {{ loadingPredict ? '推理中...' : '更新患者推理' }}
        </button>
      </div>
    </header>

    <section v-if="!hasPatient" class="card empty-state">
      请先在诊疗工作台选择一位患者，再查看模型洞察。
    </section>

    <template v-else>
      <section class="grid-top">
        <article class="card stat-card">
          <span>当前患者</span>
          <strong>{{ selectedPatient!.name }} / {{ selectedPatient!.patientId }}</strong>
        </article>
        <article class="card stat-card">
          <span>模型状态</span>
          <strong>{{ modelStatus }}</strong>
        </article>
        <article class="card stat-card">
          <span>支持度</span>
          <strong>{{ evidenceSummary.supportLevel }}</strong>
        </article>
      </section>

      <section class="content-grid">
        <article class="card panel">
          <h3>Top-K 风险事件</h3>
          <div v-if="!topKEvents.length" class="empty-mini">暂无推理结果</div>
          <div v-else class="list">
            <article v-for="(item, idx) in topKEvents" :key="`${item.label}-${idx}`" class="list-item">
              <div class="row">
                <strong>{{ idx + 1 }}. {{ item.label }}</strong>
                <span>{{ Math.round(item.score * 100) }}%</span>
              </div>
              <p>{{ item.reason }}</p>
            </article>
          </div>
        </article>

        <article class="card panel">
          <h3>证据摘要</h3>
          <div class="kv-grid">
            <p><span>事件数</span><strong>{{ evidenceSummary.eventCount }}</strong></p>
            <p><span>关系数</span><strong>{{ evidenceSummary.relationCount }}</strong></p>
            <p><span>支持度</span><strong>{{ evidenceSummary.supportLevel }}</strong></p>
          </div>
          <p class="summary-text">{{ evidenceSummary.summary }}</p>
        </article>

        <article class="card panel">
          <h3>建议来源</h3>
          <div class="kv-grid">
            <p><span>Provider</span><strong>{{ adviceSource.provider }}</strong></p>
            <p><span>Model</span><strong>{{ adviceSource.model }}</strong></p>
            <p><span>Source</span><strong>{{ adviceSource.source }}</strong></p>
          </div>
          <p class="summary-text">{{ adviceSource.note }}</p>
        </article>

        <article class="card panel">
          <h3>当前患者建议</h3>
          <ul v-if="adviceList.length" class="simple-list">
            <li v-for="(item, idx) in adviceList.slice(0, 5)" :key="`advice-${idx}`">{{ item }}</li>
          </ul>
          <div v-else class="empty-mini">暂无建议</div>
        </article>
      </section>

      <section class="card panel next-actions">
        <h3>下一步动作（当前患者）</h3>
        <div class="actions">
          <button class="secondary-button" @click="emit('openPatientDetail')">进入患者工作区</button>
          <button class="primary-button" @click="emit('openFollowup')">进入随访任务</button>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.insight-page {
  padding: 20px;
  display: grid;
  gap: 14px;
}

.page-header {
  padding: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.page-header h2 {
  margin: 0;
  color: #16324d;
}

.page-header p {
  margin: 4px 0 0;
  color: #5f7488;
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.grid-top {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.stat-card {
  padding: 12px;
  display: grid;
  gap: 4px;
}

.stat-card span {
  color: #60768b;
  font-size: 12px;
}

.stat-card strong {
  color: #17324d;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.panel {
  padding: 12px;
  display: grid;
  gap: 8px;
}

.panel h3 {
  margin: 0;
  color: #17324d;
  font-size: 15px;
}

.list {
  display: grid;
  gap: 8px;
}

.list-item {
  border: 1px solid #d5dfeb;
  border-radius: 8px;
  padding: 8px;
  background: #fbfdff;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.list-item p,
.summary-text {
  margin: 4px 0 0;
  color: #5f7488;
  font-size: 13px;
}

.kv-grid {
  display: grid;
  gap: 6px;
}

.kv-grid p {
  margin: 0;
  border: 1px solid #d5dfeb;
  border-radius: 8px;
  padding: 6px 8px;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  background: #f9fbfd;
}

.kv-grid span {
  color: #60768b;
  font-size: 12px;
}

.simple-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
}

.next-actions .actions {
  display: flex;
  gap: 8px;
}

.empty-state,
.empty-mini {
  border: 1px dashed #c3d1e0;
  border-radius: 8px;
  padding: 12px;
  color: #60768b;
  text-align: center;
}

@media (max-width: 1280px) {
  .grid-top,
  .content-grid,
  .next-actions .actions {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>
