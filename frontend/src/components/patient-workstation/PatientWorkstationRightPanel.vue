<script setup lang="ts">
import { computed } from 'vue'
import ClinicalAdviceCardBoard from '../clinical/ClinicalAdviceCardBoard.vue'
import type { ClinicalAdviceCard } from '../clinical/ClinicalAdviceCardBoard.vue'
import type { PatientCase, PredictResponse } from '../../services/types'

const props = defineProps<{
  patient: PatientCase
  predictionResult: PredictResponse | null
  loadingPredict: boolean
  predictError: string
  loadingAction: boolean
  watched: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh-predict'): void
  (e: 'create-followup'): void
  (e: 'toggle-watch'): void
  (e: 'mark-review'): void
  (e: 'copy-to-followup', actionTitle: string): void
}>()

const topk = computed(() => props.predictionResult?.topk ?? props.patient.predictions)

const evidence = computed(() => {
  if (props.predictionResult?.evidence) return props.predictionResult.evidence
  return {
    eventCount: props.patient.timeline.length,
    timepointCount: props.patient.timeline.length,
    relationCount: Math.max(1, props.patient.pathExplanation.length),
    supportLevel:
      props.patient.dataSupport === 'high'
        ? 'strong'
        : props.patient.dataSupport === 'medium'
          ? 'limited'
          : 'minimal',
  }
})

function inferRiskFromText(text: string, fallbackLevel: string): 'high' | 'medium' | 'low' {
  const normalized = text.toLowerCase()
  const fallback = fallbackLevel.toLowerCase()
  if (normalized.includes('high') || fallback.includes('high')) return 'high'
  if (normalized.includes('medium') || fallback.includes('medium')) return 'medium'
  return 'low'
}

function buildSourceTags(): string[] {
  const tags: string[] = []
  if (props.predictionResult) {
    tags.push(`strategy:${props.predictionResult.strategy}`)
    tags.push(`mode:${props.predictionResult.mode}`)
    tags.push(`source:${props.predictionResult.adviceMeta.source}`)
    tags.push(`provider:${props.predictionResult.adviceMeta.provider}`)
  } else {
    tags.push(`strategy:${props.patient.recommendationMode}`)
    tags.push('source:patient-history')
  }
  return tags
}

const adviceCards = computed<ClinicalAdviceCard[]>(() => {
  const adviceItems = props.predictionResult?.advice ?? props.patient.careAdvice
  const evidenceSourceBase =
    topk.value[0]?.reason || props.predictionResult?.supportSummary || 'Patient timeline and structured quadruples.'
  const supportLabel = props.predictionResult?.evidence.supportLevel ?? props.patient.dataSupport

  return adviceItems.map((item, index) => {
    const riskLevel = inferRiskFromText(item, props.patient.riskLevel)
    return {
      id: `${props.patient.patientId}-advice-${index + 1}`,
      title: `Clinical Suggestion #${index + 1}`,
      riskLevel,
      recommendedAction: item,
      evidenceSource: evidenceSourceBase,
      dataSupport: supportLabel,
      sourceTags: buildSourceTags(),
      needsHumanConfirm: riskLevel !== 'low' || supportLabel === 'minimal' || supportLabel === 'low',
    }
  })
})

function onCopyToFollowup(card: ClinicalAdviceCard) {
  emit('copy-to-followup', card.recommendedAction)
}

function onConfirm() {
  // Keep behavior local-first. Escalate to explicit review action if needed later.
}

function onReject() {
  // Keep behavior local-first. Escalate to explicit review action if needed later.
}

function onMarkReview() {
  emit('mark-review')
}
</script>

<template>
  <section class="card right-panel">
    <div class="head-row">
      <h3>Prediction and Clinical Advice</h3>
      <button class="secondary-button" :disabled="loadingPredict" @click="emit('refresh-predict')">
        {{ loadingPredict ? 'Predicting...' : 'Refresh Prediction' }}
      </button>
    </div>

    <article class="block">
      <h4>Top-K Prediction</h4>
      <div v-if="!topk.length" class="empty">No prediction results.</div>
      <div v-else class="list">
        <article v-for="(item, idx) in topk" :key="`${item.label}-${idx}`" class="list-item">
          <div class="row">
            <strong>{{ idx + 1 }}. {{ item.label }}</strong>
            <span>{{ Math.round(item.score * 100) }}%</span>
          </div>
          <p>{{ item.reason }}</p>
        </article>
      </div>
    </article>

    <article class="block">
      <h4>Evidence Summary</h4>
      <div class="evidence-grid">
        <article><span>Event Count</span><strong>{{ evidence.eventCount }}</strong></article>
        <article><span>Timepoints</span><strong>{{ evidence.timepointCount }}</strong></article>
        <article><span>Relations</span><strong>{{ evidence.relationCount }}</strong></article>
        <article><span>Support</span><strong>{{ evidence.supportLevel }}</strong></article>
      </div>
      <p class="summary-line">{{ predictionResult?.supportSummary || 'Displaying history-based evidence summary.' }}</p>
      <p v-if="predictError" class="warn-line">{{ predictError }}</p>
    </article>

    <article class="block">
      <h4>Auditable Clinical Advice Cards</h4>
      <ClinicalAdviceCardBoard
        :cards="adviceCards"
        :loading="loadingPredict"
        @confirm="onConfirm"
        @reject="onReject"
        @mark-review="onMarkReview"
        @copy-to-followup="onCopyToFollowup"
      />
    </article>

    <article class="block">
      <h4>Next Actions</h4>
      <div class="next-actions">
        <button class="primary-button" :disabled="loadingAction" @click="emit('create-followup')">Create Follow-up</button>
        <button class="secondary-button" :disabled="loadingAction" @click="emit('toggle-watch')">
          {{ watched ? 'Remove Watch' : 'Add Watch' }}
        </button>
        <button class="secondary-button" :disabled="loadingAction" @click="emit('mark-review')">Mark Review</button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.right-panel {
  padding: 12px;
  display: grid;
  gap: 10px;
  align-content: start;
}

.head-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
}

.head-row h3,
.block h4 {
  margin: 0;
  color: var(--ws-title, #10263c);
}

.block {
  border: 1px solid var(--ws-border, #cfd9e5);
  border-radius: 10px;
  padding: 10px;
  background: #fbfdff;
  display: grid;
  gap: 8px;
}

.list {
  display: grid;
  gap: 8px;
}

.list-item {
  border: 1px solid var(--ws-border, #cfd9e5);
  border-radius: 8px;
  padding: 8px;
  background: #fff;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.list-item p {
  margin: 4px 0 0;
  color: var(--ws-text-muted, #617385);
  font-size: 0.84rem;
}

.evidence-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.evidence-grid article {
  border: 1px solid var(--ws-border, #cfd9e5);
  border-radius: 8px;
  padding: 8px;
  background: #fff;
  display: grid;
  gap: 4px;
}

.evidence-grid span {
  color: var(--ws-text-muted, #617385);
  font-size: 0.78rem;
}

.summary-line {
  margin: 0;
  color: var(--ws-text-muted, #617385);
  font-size: 0.84rem;
}

.warn-line {
  margin: 0;
  color: #a4383f;
  font-size: 0.84rem;
}

.next-actions {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.empty {
  border: 1px dashed var(--ws-border-strong, #b8c7d8);
  border-radius: 8px;
  padding: 12px;
  color: var(--ws-text-muted, #617385);
  text-align: center;
  font-size: 0.84rem;
}
</style>