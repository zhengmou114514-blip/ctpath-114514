<script setup lang="ts">
import { computed } from 'vue'
import type { FlowBoardRow, PatientSummary } from '../services/types'

const props = defineProps<{
  patients: PatientSummary[]
  flowBoardItems: FlowBoardRow[]
  recentViewed: PatientSummary[]
}>()

const emit = defineEmits<{
  (e: 'open', patientId: string): void
}>()

function riskRank(level: string) {
  const value = level.toLowerCase()
  if (level.includes('高') || value.includes('high')) return 0
  if (level.includes('中') || value.includes('medium')) return 1
  return 2
}

function stageLabel(value: string) {
  if (value === 'Early') return '早期'
  if (value === 'Mid') return '中期'
  if (value === 'Late') return '晚期'
  return value
}

const clinicQueue = computed(() =>
  [...props.patients]
    .sort((left, right) => {
      const riskCompare = riskRank(left.riskLevel) - riskRank(right.riskLevel)
      if (riskCompare !== 0) return riskCompare
      return right.lastVisit.localeCompare(left.lastVisit)
    })
    .slice(0, 6)
)

const revisitQueue = computed(() =>
  [...props.flowBoardItems]
    .filter((item) => item.flowStatus.includes('复核') || item.flowStatus.includes('随访') || item.flowStatus.includes('补录'))
    .slice(0, 6)
)
</script>

<template>
  <section class="clinic-session-grid">
    <article class="card clinic-session-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Clinic Queue</p>
          <h3>当前接诊队列</h3>
        </div>
        <span class="panel-meta">按风险和最近就诊时间排序，便于先处理重点患者。</span>
      </div>

      <div v-if="clinicQueue.length" class="clinic-queue-list">
        <button
          v-for="item in clinicQueue"
          :key="item.patientId"
          class="clinic-queue-row"
          @click="emit('open', item.patientId)"
        >
          <div class="queue-main">
            <strong>{{ item.name }} / {{ item.patientId }}</strong>
            <span>{{ item.primaryDisease }} / {{ stageLabel(item.currentStage) }}</span>
            <small>最近就诊 {{ item.lastVisit }}</small>
          </div>
          <div class="queue-side">
            <span
              class="risk-pill"
              :class="riskRank(item.riskLevel) === 0 ? 'risk-high' : riskRank(item.riskLevel) === 1 ? 'risk-medium' : 'risk-low'"
            >
              {{ item.riskLevel }}
            </span>
          </div>
        </button>
      </div>

      <article v-else class="empty-card compact">
        <p>当前没有可展示的接诊队列。</p>
      </article>
    </article>

    <article class="card clinic-session-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Follow-up Return</p>
          <h3>重点复诊与复核</h3>
        </div>
        <span class="panel-meta">从流程状态板提取需要回到临床端继续处理的患者。</span>
      </div>

      <div v-if="revisitQueue.length" class="clinic-queue-list">
        <button
          v-for="item in revisitQueue"
          :key="`${item.patientId}-${item.flowStatus}`"
          class="clinic-queue-row"
          @click="emit('open', item.patientId)"
        >
          <div class="queue-main">
            <strong>{{ item.patientName }} / {{ item.patientId }}</strong>
            <span>{{ item.primaryDisease }} / {{ stageLabel(item.currentStage) }}</span>
            <small>{{ item.nextAction }}</small>
          </div>
          <div class="queue-side">
            <span
              class="risk-pill"
              :class="riskRank(item.riskLevel) === 0 ? 'risk-high' : riskRank(item.riskLevel) === 1 ? 'risk-medium' : 'risk-low'"
            >
              {{ item.flowStatus }}
            </span>
          </div>
        </button>
      </div>

      <article v-else class="empty-card compact">
        <p>当前没有重点复诊或复核患者。</p>
      </article>
    </article>

    <article class="card clinic-session-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Recent Access</p>
          <h3>最近查看患者</h3>
        </div>
        <span class="panel-meta">方便快速回到刚处理过的患者详情。</span>
      </div>

      <div v-if="props.recentViewed.length" class="clinic-queue-list">
        <button
          v-for="item in props.recentViewed"
          :key="item.patientId"
          class="clinic-queue-row"
          @click="emit('open', item.patientId)"
        >
          <div class="queue-main">
            <strong>{{ item.name }} / {{ item.patientId }}</strong>
            <span>{{ item.primaryDisease }}</span>
            <small>最近就诊 {{ item.lastVisit }}</small>
          </div>
          <div class="queue-side">
            <span
              class="risk-pill"
              :class="riskRank(item.riskLevel) === 0 ? 'risk-high' : riskRank(item.riskLevel) === 1 ? 'risk-medium' : 'risk-low'"
            >
              {{ item.riskLevel }}
            </span>
          </div>
        </button>
      </div>

      <article v-else class="empty-card compact">
        <p>当前还没有最近查看记录。</p>
      </article>
    </article>
  </section>
</template>
