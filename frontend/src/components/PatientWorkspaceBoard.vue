<script setup lang="ts">
import type { PatientSummary } from '../services/types'

const props = defineProps<{
  patients: PatientSummary[]
  recentViewed: PatientSummary[]
  loadingPatients: boolean
  searchText: string
  riskFilter: string
  riskOptions: string[]
  hiddenCount: number
  showAllPending: boolean
}>()

const emit = defineEmits<{
  (e: 'update:search-text', value: string): void
  (e: 'update:risk-filter', value: string): void
  (e: 'toggle-show-all'): void
  (e: 'open', patientId: string): void
  (e: 'open-archive', patientId: string): void
}>()

function riskTone(level: string) {
  if (level.includes('高') || level.toLowerCase().includes('high')) return 'risk-high'
  if (level.includes('中') || level.toLowerCase().includes('medium')) return 'risk-medium'
  return 'risk-low'
}

function supportLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value
}

function stageLabel(value: string) {
  if (value === 'Early') return '早期'
  if (value === 'Mid') return '中期'
  if (value === 'Late') return '晚期'
  return value
}

function updateSearch(event: Event) {
  emit('update:search-text', (event.target as HTMLInputElement).value)
}

function updateRiskFilter(event: Event) {
  emit('update:risk-filter', (event.target as HTMLSelectElement).value)
}

function queueButtonText() {
  if (props.showAllPending) return '收起队列'
  return `查看其余 ${props.hiddenCount} 位患者`
}
</script>

<template>
  <section class="module-shell worklist-shell practical-worklist-shell card">
    <div class="worklist-toolbar">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Patient Queue</p>
          <h3>待处理患者</h3>
        </div>
        <button
          v-if="props.hiddenCount > 0 || props.showAllPending"
          class="secondary-button"
          @click="emit('toggle-show-all')"
        >
          {{ queueButtonText() }}
        </button>
      </div>

      <div class="workspace-filter-grid practical-filter-grid">
        <label class="field">
          <span>搜索患者</span>
          <input
            :value="props.searchText"
            type="text"
            placeholder="按编号、姓名或疾病搜索"
            @input="updateSearch"
          />
        </label>

        <label class="field">
          <span>风险筛选</span>
          <select :value="props.riskFilter" @change="updateRiskFilter">
            <option v-for="item in props.riskOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
      </div>
    </div>

    <div v-if="props.patients.length" class="worklist-list practical-worklist-list">
      <button
        v-for="patient in props.patients"
        :key="patient.patientId"
        class="worklist-item practical-patient-row"
        @click="emit('open', patient.patientId)"
      >
        <div class="worklist-main">
          <strong>{{ patient.name }}</strong>
          <span>{{ patient.patientId }} / {{ patient.primaryDisease }}</span>
          <small>{{ stageLabel(patient.currentStage) }} / 最近就诊 {{ patient.lastVisit }}</small>
        </div>
        <div class="worklist-side">
          <span class="risk-pill" :class="riskTone(patient.riskLevel)">{{ patient.riskLevel }}</span>
          <small>支持度 {{ supportLabel(patient.dataSupport) }}</small>
          <button class="text-button" type="button" @click.stop="emit('open-archive', patient.patientId)">档案</button>
        </div>
      </button>
    </div>

    <article v-else-if="!props.loadingPatients" class="empty-card compact">
      <p>没有符合筛选条件的患者。</p>
    </article>

    <section v-if="props.recentViewed.length" class="recent-inline-panel">
      <div class="mini-head">
        <h4>最近查看</h4>
        <span>便于快速回到刚才处理的患者详情。</span>
      </div>
      <div class="recent-list practical-recent-list">
        <button
          v-for="patient in props.recentViewed"
          :key="patient.patientId"
          class="recent-row"
          @click="emit('open', patient.patientId)"
        >
          <div class="queue-main">
            <strong>{{ patient.name }}</strong>
            <span>{{ patient.patientId }} / {{ patient.primaryDisease }}</span>
          </div>
          <div class="queue-side">
            <span class="risk-pill" :class="riskTone(patient.riskLevel)">{{ patient.riskLevel }}</span>
          </div>
        </button>
      </div>
    </section>
  </section>
</template>
