<script setup lang="ts">
import { computed, ref } from 'vue'
import Pagination from './Pagination.vue'
import type { FlowBoardRow, PatientSummary } from '../services/types'

interface AlertRow {
  patientId: string
  name: string
  title: string
  detail: string
  tone: 'risk-high' | 'risk-medium' | 'risk-low'
}

const props = defineProps<{
  patients: PatientSummary[]
  flowBoardItems: FlowBoardRow[]
}>()

const emit = defineEmits<{
  (e: 'open', patientId: string): void
}>()

// 分页状态
const page = ref(1)
const pageSize = ref(10)

function isHighRisk(level: string) {
  const value = level.toLowerCase()
  return level.includes('高') || value.includes('high')
}

const highRiskLowSupport = computed(() =>
  props.patients.filter((item) => isHighRisk(item.riskLevel) && item.dataSupport === 'low')
)

const lateStagePatients = computed(() => props.patients.filter((item) => item.currentStage === 'Late'))
const reviewRequired = computed(() => props.flowBoardItems.filter((item) => item.flowStatus.includes('复核')))
const supplementRequired = computed(() => props.flowBoardItems.filter((item) => item.flowStatus.includes('补录')))

const allAlertRows = computed<AlertRow[]>(() => {
  const rows: AlertRow[] = []

  for (const item of highRiskLowSupport.value) {
    rows.push({
      patientId: item.patientId,
      name: item.name,
      title: '高风险且数据支持不足',
      detail: `${item.primaryDisease}，建议先补录结构化事件，再复核模型结果。`,
      tone: 'risk-high',
    })
  }

  for (const item of reviewRequired.value) {
    rows.push({
      patientId: item.patientId,
      name: item.patientName,
      title: '待医生复核',
      detail: item.nextAction,
      tone: 'risk-medium',
    })
  }

  for (const item of lateStagePatients.value) {
    rows.push({
      patientId: item.patientId,
      name: item.name,
      title: '晚期患者重点关注',
      detail: `${item.primaryDisease} / 最近就诊 ${item.lastVisit}`,
      tone: 'risk-high',
    })
  }

  return rows
})

// 分页后的数据
const paginatedAlertRows = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return allAlertRows.value.slice(start, start + pageSize.value)
})

const total = computed(() => allAlertRows.value.length)

function handlePageChange(newPage: number, newPageSize: number) {
  page.value = newPage
  pageSize.value = newPageSize
}
</script>

<template>
  <section class="alert-board-grid">
    <article class="card alert-board-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Clinical Alerts</p>
          <h3>预警摘要</h3>
        </div>
      </div>

      <div class="alert-summary-grid">
        <article class="overview-metric tone-danger">
          <span>高风险且低支持</span>
          <strong>{{ highRiskLowSupport.length }}</strong>
          <small>建议先补录再评估</small>
        </article>
        <article class="overview-metric tone-warning">
          <span>待复核</span>
          <strong>{{ reviewRequired.length }}</strong>
          <small>需要医生优先查看</small>
        </article>
        <article class="overview-metric tone-warning">
          <span>待补录</span>
          <strong>{{ supplementRequired.length }}</strong>
          <small>需要补充结构化事件</small>
        </article>
        <article class="overview-metric">
          <span>晚期患者</span>
          <strong>{{ lateStagePatients.length }}</strong>
          <small>需要重点关注</small>
        </article>
      </div>
    </article>

    <article class="card alert-list-card">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Alert List</p>
          <h3>预警列表</h3>
        </div>
        <span class="panel-meta">共 {{ total }} 条预警</span>
      </div>

      <div class="alert-list">
        <button
          v-for="row in paginatedAlertRows"
          :key="row.patientId"
          class="alert-row"
          :class="row.tone"
          @click="emit('open', row.patientId)"
        >
          <div class="alert-icon">
            <span v-if="row.tone === 'risk-high'">⚠️</span>
            <span v-else-if="row.tone === 'risk-medium'">⚡</span>
            <span v-else>ℹ️</span>
          </div>
          <div class="alert-content">
            <div class="alert-title">{{ row.title }}</div>
            <div class="alert-patient">{{ row.name }}</div>
            <div class="alert-detail">{{ row.detail }}</div>
          </div>
        </button>

        <p v-if="paginatedAlertRows.length === 0" class="empty-state">
          暂无预警信息
        </p>
      </div>

      <!-- 分页器 -->
      <div v-if="total > pageSize" class="pagination-container">
        <Pagination
          :total="total"
          :page="page"
          :page-size="pageSize"
          @change="handlePageChange"
        />
      </div>
    </article>
  </section>
</template>

<style scoped>
.alert-board-grid {
  display: grid;
  gap: 16px;
}

.alert-board-card,
.alert-list-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.eyebrow {
  font-size: 12px;
  color: #8c8c8c;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 4px 0;
}

.panel-head h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.panel-meta {
  font-size: 13px;
  color: #8c8c8c;
}

.alert-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.overview-metric {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  border-left: 3px solid #d9d9d9;
}

.overview-metric span {
  display: block;
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.overview-metric strong {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #333;
  line-height: 1;
  margin-bottom: 4px;
}

.overview-metric small {
  display: block;
  font-size: 11px;
  color: #8c8c8c;
}

.overview-metric.tone-danger {
  border-left-color: #f5222d;
  background: #fff1f0;
}

.overview-metric.tone-warning {
  border-left-color: #fa8c16;
  background: #fff7e6;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.alert-row {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.alert-row:hover {
  background: #f5f7fa;
  border-color: #667eea;
  transform: translateX(4px);
}

.alert-row.risk-high {
  border-left: 3px solid #f5222d;
  background: #fff1f0;
}

.alert-row.risk-medium {
  border-left: 3px solid #fa8c16;
  background: #fff7e6;
}

.alert-row.risk-low {
  border-left: 3px solid #52c41a;
  background: #f6ffed;
}

.alert-icon {
  font-size: 24px;
  display: flex;
  align-items: center;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.alert-patient {
  font-size: 13px;
  color: #667eea;
  margin-bottom: 4px;
}

.alert-detail {
  font-size: 12px;
  color: #8c8c8c;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #8c8c8c;
  font-size: 14px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
