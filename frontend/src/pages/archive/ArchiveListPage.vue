<script setup lang="ts">
import { computed } from 'vue'
import ArchiveManagementBoard from '../../components/ArchiveManagementBoard.vue'
import type { PatientSummary } from '../../services/types'

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

const highRiskCount = computed(() =>
  props.patients.filter((item) => item.riskLevel.includes('高') || item.riskLevel.toLowerCase().includes('high')).length
)
const lowSupportCount = computed(() => props.patients.filter((item) => item.dataSupport === 'low').length)
</script>

<template>
  <section class="role-page-stack archive-overview-shell">
    <article class="card archive-page-hero archive-page-hero-practical">
      <div>
        <p class="eyebrow">Archive Registry</p>
        <h3>患者档案总览</h3>
        <p class="page-copy">
          用于完成患者建档、主索引维护、档案筛查、详情查看，以及外院或门诊资料的批量导入。
        </p>
      </div>
      <div class="archive-page-metrics">
        <div class="summary-chip">
          <span>本页患者</span>
          <strong>{{ props.patients.length }}</strong>
        </div>
        <div class="summary-chip">
          <span>高风险患者</span>
          <strong>{{ highRiskCount }}</strong>
        </div>
        <div class="summary-chip">
          <span>低支持度</span>
          <strong>{{ lowSupportCount }}</strong>
        </div>
      </div>
    </article>

    <ArchiveManagementBoard
      :patients="props.patients"
      :loading-patients="props.loadingPatients"
      :current-page="props.currentPage"
      :total-pages="props.totalPages"
      :patient-count="props.patientCount"
      @open="emit('open', $event)"
      @create="emit('create')"
      @import="emit('import')"
      @prev-page="emit('prev-page')"
      @next-page="emit('next-page')"
    />
  </section>
</template>
