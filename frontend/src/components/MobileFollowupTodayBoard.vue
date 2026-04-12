<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ContactLogCreatePayload, FollowupTaskRow } from '../services/types'
import FollowupQuickContactCard from './FollowupQuickContactCard.vue'

interface MobileCandidate {
  patientId: string
  patientName: string
  primaryDisease: string
  riskLevel: string
  dueDate: string
  owner: string
  status: string
  source: FollowupTaskRow['source']
}

type MobileFilter = 'all' | 'high' | 'todo' | 'outpatient'

const props = defineProps<{
  loading: boolean
  loadingTaskAction: boolean
  followupItems: FollowupTaskRow[]
  selectedPatientId?: string
  savingContactLog: boolean
}>()

const emit = defineEmits<{
  (e: 'open-patient', patientId: string): void
  (e: 'open-archive', patientId: string): void
  (e: 'submit-contact-log', payload: { patientId: string; payload: ContactLogCreatePayload }): void
}>()

const activePatientId = ref('')
const activeFilter = ref<MobileFilter>('all')

function priorityRank(value: string) {
  if (value === 'high') return 0
  if (value === 'medium') return 1
  return 2
}

const todayPatients = computed<MobileCandidate[]>(() => {
  const map = new Map<string, MobileCandidate>()
  for (const item of [...props.followupItems].sort((left, right) => {
    const priorityDiff = priorityRank(left.priority) - priorityRank(right.priority)
    if (priorityDiff !== 0) return priorityDiff
    return left.dueDate.localeCompare(right.dueDate)
  })) {
    if (!map.has(item.patientId)) {
      map.set(item.patientId, {
        patientId: item.patientId,
        patientName: item.patientName,
        primaryDisease: item.primaryDisease,
        riskLevel: item.riskLevel,
        dueDate: item.dueDate,
        owner: item.owner,
        status: item.status,
        source: item.source,
      })
    }
  }
  return [...map.values()].slice(0, 8)
})

const filteredPatients = computed(() => {
  if (activeFilter.value === 'high') return todayPatients.value.filter((item) => item.riskLevel.toLowerCase().includes('high'))
  if (activeFilter.value === 'todo') return todayPatients.value.filter((item) => !item.status.toLowerCase().includes('completed') && !item.status.toLowerCase().includes('closed'))
  if (activeFilter.value === 'outpatient') return todayPatients.value.filter((item) => item.source === 'outpatient-task')
  return todayPatients.value
})

const quickCandidates = computed(() =>
  filteredPatients.value.map((item) => ({
    patientId: item.patientId,
    label: `${item.patientName} / ${item.primaryDisease}`,
  }))
)

const activePatient = computed(() => filteredPatients.value.find((item) => item.patientId === activePatientId.value) ?? null)

function riskTone(value: string) {
  const normalized = value.toLowerCase()
  if (normalized.includes('high')) return 'risk-high'
  if (normalized.includes('medium')) return 'risk-medium'
  return 'risk-low'
}

watch(
  () => [props.selectedPatientId, filteredPatients.value.length] as const,
  () => {
    if (props.selectedPatientId && filteredPatients.value.some((item) => item.patientId === props.selectedPatientId)) {
      activePatientId.value = props.selectedPatientId
      return
    }
    if (!activePatientId.value && filteredPatients.value.length) {
      activePatientId.value = filteredPatients.value[0]?.patientId ?? ''
    }
  },
  { immediate: true }
)
</script>

<template>
  <section class="mobile-followup-shell">
    <article class="card mobile-followup-hero">
      <div>
        <p class="eyebrow">移动随访工作台</p>
        <h3>今日随访</h3>
        <p class="page-copy">用于快速筛选患者、打开详情/档案和提交联系记录。</p>
      </div>
    </article>

    <div class="mobile-followup-grid">
      <section class="mobile-followup-list">
        <div class="mobile-followup-filterbar">
          <button class="secondary-button" :class="{ active: activeFilter === 'all' }" @click="activeFilter = 'all'">全部</button>
          <button class="secondary-button" :class="{ active: activeFilter === 'high' }" @click="activeFilter = 'high'">高风险</button>
          <button class="secondary-button" :class="{ active: activeFilter === 'todo' }" @click="activeFilter = 'todo'">待处理</button>
          <button class="secondary-button" :class="{ active: activeFilter === 'outpatient' }" @click="activeFilter = 'outpatient'">门诊任务</button>
        </div>

        <article v-if="activePatient" class="card mobile-followup-focus-card">
          <div class="mobile-followup-focus-head">
            <div>
              <p class="eyebrow">当前患者</p>
              <h4>{{ activePatient.patientName }}</h4>
            </div>
            <span class="risk-pill" :class="riskTone(activePatient.riskLevel)">{{ activePatient.riskLevel }}</span>
          </div>
          <p>{{ activePatient.patientId }} / {{ activePatient.primaryDisease }}</p>
          <p>任务状态：{{ activePatient.status }}</p>
          <p>截止：{{ activePatient.dueDate }} / 负责人：{{ activePatient.owner }}</p>
          <div class="mobile-followup-actions">
            <button class="primary-button" :disabled="props.loadingTaskAction" @click="emit('open-patient', activePatient.patientId)">打开患者</button>
            <button class="secondary-button" :disabled="props.loadingTaskAction" @click="emit('open-archive', activePatient.patientId)">打开档案</button>
          </div>
        </article>

        <article
          v-for="item in filteredPatients"
          :key="`${item.patientId}-${item.dueDate}`"
          class="card mobile-followup-patient-card"
          :class="{ 'is-highlighted': activePatientId === item.patientId }"
        >
          <div class="mobile-followup-patient-head">
            <div>
              <strong>{{ item.patientName }}</strong>
              <span>{{ item.patientId }} / {{ item.primaryDisease }}</span>
            </div>
            <span class="risk-pill" :class="riskTone(item.riskLevel)">{{ item.riskLevel }}</span>
          </div>
          <p>状态：{{ item.status }}</p>
          <p>截止：{{ item.dueDate }} / 负责人：{{ item.owner }}</p>
          <div class="mobile-followup-actions">
            <button class="primary-button" @click="activePatientId = item.patientId">设为当前</button>
            <button class="secondary-button" :disabled="props.loadingTaskAction" @click="emit('open-patient', item.patientId)">患者详情</button>
            <button class="secondary-button" :disabled="props.loadingTaskAction" @click="emit('open-archive', item.patientId)">档案</button>
          </div>
        </article>

        <article v-if="!filteredPatients.length && !props.loading" class="empty-card compact">
          <p>无数据</p>
        </article>
      </section>

      <FollowupQuickContactCard
        :candidates="quickCandidates"
        :selected-patient-id="activePatientId"
        :saving="props.savingContactLog"
        @submit="emit('submit-contact-log', $event)"
        @open-patient="emit('open-patient', $event)"
      />
    </div>
  </section>
</template>
