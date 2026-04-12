<script setup lang="ts">
import type { PatientSummary } from '../services/types'

const props = defineProps<{
  patients: PatientSummary[]
  loadingPatients: boolean
  currentPage: number
  totalPages: number
  patientCount: number
}>()

const emit = defineEmits<{
  (e: 'open', patientId: string): void
  (e: 'create'): void
  (e: 'import'): void
  (e: 'prev-page'): void
  (e: 'next-page'): void
}>()

function stageLabel(value: string) {
  if (value === 'Early') return '早期'
  if (value === 'Mid') return '中期'
  if (value === 'Late') return '晚期'
  return value
}

function supportLabel(value: string) {
  if (value === 'high') return '高'
  if (value === 'medium') return '中'
  if (value === 'low') return '低'
  return value
}
</script>

<template>
  <section class="card archive-table-card">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Patient Registry</p>
        <h3>患者档案列表</h3>
      </div>
      <div class="module-hero-actions">
        <span class="panel-meta">当前共 {{ props.patientCount }} 份患者档案</span>
        <button class="secondary-button" @click="emit('import')">导入档案</button>
        <button class="primary-button" @click="emit('create')">新建档案</button>
      </div>
    </div>

    <div class="archive-table-head archive-table-head-wide">
      <span>患者编号</span>
      <span>姓名</span>
      <span>年龄</span>
      <span>主要疾病</span>
      <span>阶段</span>
      <span>风险</span>
      <span>支持度</span>
      <span>最近就诊</span>
      <span>病情摘要</span>
    </div>

    <div v-if="props.patients.length" class="archive-table-body">
      <button
        v-for="patient in props.patients"
        :key="patient.patientId"
        class="archive-table-row archive-table-row-wide"
        @click="emit('open', patient.patientId)"
      >
        <span>{{ patient.patientId }}</span>
        <span :title="patient.name">{{ patient.name }}</span>
        <span>{{ patient.age }}</span>
        <span :title="patient.primaryDisease">{{ patient.primaryDisease }}</span>
        <span>{{ stageLabel(patient.currentStage) }}</span>
        <span>{{ patient.riskLevel }}</span>
        <span>{{ supportLabel(patient.dataSupport) }}</span>
        <span>{{ patient.lastVisit }}</span>
        <span :title="patient.summary">{{ patient.summary || '暂无摘要' }}</span>
      </button>
    </div>

    <div v-else-if="!props.loadingPatients" class="empty-card">
      <p class="eyebrow">Patient Registry</p>
      <h3>当前暂无患者档案</h3>
      <p>可以先新建建档，或从外院、门诊导出的数据表中批量导入患者基础资料。</p>
    </div>

    <div class="archive-footer">
      <span class="panel-meta">第 {{ props.currentPage }} / {{ props.totalPages }} 页</span>
      <div class="archive-footer-actions">
        <button class="secondary-button" :disabled="props.currentPage <= 1" @click="emit('prev-page')">上一页</button>
        <button class="secondary-button" :disabled="props.currentPage >= props.totalPages" @click="emit('next-page')">下一页</button>
      </div>
    </div>
  </section>
</template>
