<script setup lang="ts">
import { reactive } from 'vue'
import { useAuditTrailStore } from '../../stores/auditTrailStore'

type AdviceRiskLevel = 'high' | 'medium' | 'low'
type AdviceAuditStatus = 'unreviewed' | 'confirmed' | 'rejected' | 'needs_review'

export interface ClinicalAdviceCard {
  id: string
  title: string
  riskLevel: AdviceRiskLevel
  recommendedAction: string
  evidenceSource: string
  dataSupport: string
  sourceTags: string[]
  needsHumanConfirm: boolean
}

interface LocalAuditState {
  status: AdviceAuditStatus
  reviewer: string
  reviewedAt: string
}

const props = defineProps<{
  cards: ClinicalAdviceCard[]
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'confirm', card: ClinicalAdviceCard): void
  (e: 'reject', card: ClinicalAdviceCard): void
  (e: 'mark-review', card: ClinicalAdviceCard): void
  (e: 'copy-to-followup', card: ClinicalAdviceCard): void
}>()

const audits = reactive<Record<string, LocalAuditState>>({})
const auditTrail = useAuditTrailStore()

function statusLabel(status: AdviceAuditStatus): string {
  if (status === 'confirmed') return 'Confirmed'
  if (status === 'rejected') return 'Rejected'
  if (status === 'needs_review') return 'Needs Review'
  return 'Unreviewed'
}

function supportTone(value: string): AdviceRiskLevel {
  const normalized = value.toLowerCase()
  if (normalized.includes('strong') || normalized.includes('high')) return 'low'
  if (normalized.includes('limited') || normalized.includes('medium')) return 'medium'
  return 'high'
}

function ensureAudit(cardId: string): LocalAuditState {
  if (!audits[cardId]) {
    audits[cardId] = {
      status: 'unreviewed',
      reviewer: '--',
      reviewedAt: '--',
    }
  }
  return audits[cardId]
}

function review(card: ClinicalAdviceCard, status: AdviceAuditStatus) {
  const current = ensureAudit(card.id)
  current.status = status
  current.reviewer = 'Current User'
  current.reviewedAt = new Date().toISOString().replace('T', ' ').slice(0, 16)
}

function onConfirm(card: ClinicalAdviceCard) {
  review(card, 'confirmed')
  auditTrail.addAuditLog({
    action: 'confirm_advice',
    target: { type: 'advice_card', id: card.id, label: card.title },
    result: 'success',
    detail: `Advice confirmed: ${card.recommendedAction}`,
  })
  emit('confirm', card)
}

function onReject(card: ClinicalAdviceCard) {
  review(card, 'rejected')
  auditTrail.addAuditLog({
    action: 'reject_advice',
    target: { type: 'advice_card', id: card.id, label: card.title },
    result: 'success',
    detail: `Advice rejected: ${card.recommendedAction}`,
  })
  emit('reject', card)
}

function onNeedsReview(card: ClinicalAdviceCard) {
  review(card, 'needs_review')
  emit('mark-review', card)
}
</script>

<template>
  <section class="advice-board">
    <div v-if="loading" class="empty-card">Generating advice cards...</div>
    <div v-else-if="!props.cards.length" class="empty-card">No clinical advice generated yet.</div>

    <article v-for="card in props.cards" :key="card.id" class="advice-card" :class="`risk-${card.riskLevel}`">
      <header class="advice-head">
        <h5>{{ card.title }}</h5>
        <span class="risk-pill" :class="`risk-${card.riskLevel}`">{{ card.riskLevel.toUpperCase() }}</span>
      </header>

      <div class="advice-row">
        <span class="field-label">Recommended Action</span>
        <p>{{ card.recommendedAction }}</p>
      </div>

      <div class="grid-two">
        <div class="meta-item">
          <span class="field-label">Evidence Source</span>
          <p>{{ card.evidenceSource }}</p>
        </div>
        <div class="meta-item">
          <span class="field-label">Data Support</span>
          <span class="support-pill" :class="`risk-${supportTone(card.dataSupport)}`">{{ card.dataSupport }}</span>
        </div>
      </div>

      <div class="meta-item">
        <span class="field-label">Source Labels</span>
        <div class="tag-list">
          <span v-for="tag in card.sourceTags" :key="`${card.id}-${tag}`" class="source-tag">{{ tag }}</span>
        </div>
      </div>

      <div class="grid-two">
        <div class="meta-item">
          <span class="field-label">Manual Confirmation</span>
          <span>{{ card.needsHumanConfirm ? 'Required' : 'Optional' }}</span>
        </div>
        <div class="meta-item">
          <span class="field-label">Audit Status</span>
          <span class="audit-pill" :class="`status-${ensureAudit(card.id).status}`">
            {{ statusLabel(ensureAudit(card.id).status) }}
          </span>
        </div>
      </div>

      <div class="grid-two">
        <div class="meta-item">
          <span class="field-label">Reviewer</span>
          <span>{{ ensureAudit(card.id).reviewer }}</span>
        </div>
        <div class="meta-item">
          <span class="field-label">Reviewed At</span>
          <span>{{ ensureAudit(card.id).reviewedAt }}</span>
        </div>
      </div>

      <div class="actions">
        <button class="secondary-button" @click="onConfirm(card)">Confirm</button>
        <button class="secondary-button" @click="onReject(card)">Reject</button>
        <button class="secondary-button" @click="onNeedsReview(card)">Needs Review</button>
        <button class="primary-button" @click="emit('copy-to-followup', card)">Copy to Follow-up</button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.advice-board {
  display: grid;
  gap: 10px;
}

.empty-card {
  border: 1px dashed var(--ws-border-strong, #b8c7d8);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  color: var(--ws-text-muted, #617385);
}

.advice-card {
  border: 1px solid var(--ws-border, #cfd9e5);
  border-left: 4px solid var(--ws-border-strong, #b8c7d8);
  border-radius: 10px;
  background: #fff;
  padding: 10px;
  display: grid;
  gap: 10px;
}

.advice-card.risk-high {
  border-left-color: #a4383f;
}

.advice-card.risk-medium {
  border-left-color: #9b6518;
}

.advice-card.risk-low {
  border-left-color: #1d7b5c;
}

.advice-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.advice-head h5 {
  margin: 0;
  font-size: 0.94rem;
  color: var(--ws-title, #10263c);
}

.field-label {
  font-size: 0.75rem;
  color: var(--ws-text-muted, #617385);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.advice-row p,
.meta-item p {
  margin: 4px 0 0;
  color: var(--ws-text, #1b2b3a);
  font-size: 0.84rem;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.meta-item {
  display: grid;
  gap: 4px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.source-tag {
  border: 1px solid var(--ws-border, #cfd9e5);
  border-radius: 999px;
  background: #f7fafd;
  color: var(--ws-title, #10263c);
  padding: 2px 8px;
  font-size: 0.74rem;
}

.support-pill,
.audit-pill,
.risk-pill {
  border-radius: 999px;
  border: 1px solid transparent;
  padding: 2px 8px;
  font-size: 0.74rem;
  width: fit-content;
  font-weight: 700;
}

.risk-high {
  background: #fdeced;
  border-color: #efc2c5;
  color: #a4383f;
}

.risk-medium {
  background: #fff4e2;
  border-color: #efdbb2;
  color: #9b6518;
}

.risk-low {
  background: #e9f8f1;
  border-color: #bde7d1;
  color: #1d7b5c;
}

.status-unreviewed {
  background: #eaf2fb;
  border-color: #c7d8ec;
  color: #2f5f8f;
}

.status-confirmed {
  background: #e9f8f1;
  border-color: #bde7d1;
  color: #1d7b5c;
}

.status-rejected {
  background: #fdeced;
  border-color: #efc2c5;
  color: #a4383f;
}

.status-needs_review {
  background: #fff4e2;
  border-color: #efdbb2;
  color: #9b6518;
}

.actions {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

@media (max-width: 980px) {
  .grid-two,
  .actions {
    grid-template-columns: 1fr;
  }
}
</style>
