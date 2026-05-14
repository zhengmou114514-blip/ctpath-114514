<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { getPharmacyReviewQueue, reviewPharmacyOrder } from '../services/api'
import type { PharmacyReviewOrder } from '../services/types'

const items = ref<PharmacyReviewOrder[]>([])
const loading = ref(false)
const error = ref('')
const noteById = ref<Record<string, string>>({})
const busyId = ref('')
let refreshTimer: number | undefined

const pendingItems = computed(() => items.value.filter((item) => item.reviewStatus === 'pending'))
const completedItems = computed(() => items.value.filter((item) => item.reviewStatus !== 'pending'))

function rowKey(item: PharmacyReviewOrder) {
  return `${item.patientId}:${item.medicationId}`
}

async function loadQueue() {
  loading.value = true
  error.value = ''
  try {
    items.value = await getPharmacyReviewQueue()
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '用药复核队列加载失败。'
  } finally {
    loading.value = false
  }
}

async function submitReview(item: PharmacyReviewOrder, reviewStatus: 'approved' | 'rejected') {
  const key = rowKey(item)
  busyId.value = key
  error.value = ''
  try {
    await reviewPharmacyOrder(item.patientId, item.medicationId, {
      reviewStatus,
      note: noteById.value[key] || (reviewStatus === 'approved' ? '药师审核通过。' : '药师审核驳回。'),
    })
    await loadQueue()
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '用药复核提交失败。'
  } finally {
    busyId.value = ''
  }
}

onMounted(() => {
  void loadQueue()
  refreshTimer = window.setInterval(() => {
    void loadQueue()
  }, 5000)
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    window.clearInterval(refreshTimer)
  }
})
</script>

<template>
  <section class="review-page">
    <div class="section-header">
      <div>
        <p class="eyebrow">药师用药复核</p>
        <h2>待复核用药</h2>
        <p class="muted-line">仅展示医生提交的患者用药审核，不包含库存、采购、入库、出库或交易流水。</p>
      </div>
      <button class="secondary-button" type="button" :disabled="loading" @click="loadQueue">刷新</button>
    </div>

    <div class="metric-row">
      <article class="clinical-card metric-card">
        <span>待复核</span>
        <strong>{{ pendingItems.length }}</strong>
      </article>
      <article class="clinical-card metric-card">
        <span>已处理</span>
        <strong>{{ completedItems.length }}</strong>
      </article>
    </div>

    <p v-if="loading" class="muted-line">正在加载用药复核队列...</p>
    <p v-if="error" class="error-line">{{ error }}</p>

    <article class="clinical-card table-card">
      <table class="review-table">
        <thead>
          <tr>
            <th>患者</th>
            <th>药品</th>
            <th>用法</th>
            <th>状态</th>
            <th>复核备注</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="rowKey(item)">
            <td>{{ item.patientName }}</td>
            <td>
              <strong>{{ item.drugNameSnapshot }}</strong>
              <small>{{ item.prescribedBy }}</small>
            </td>
            <td>{{ item.dosage }} / {{ item.frequency }} / {{ item.route }}</td>
            <td>
              <span class="status-pill" :class="`status-${item.reviewStatus}`">{{ item.reviewStatus }}</span>
            </td>
            <td>
              <input
                v-model="noteById[rowKey(item)]"
                :disabled="item.reviewStatus !== 'pending'"
                placeholder="填写审核备注"
              />
            </td>
            <td>
              <div class="action-row">
                <button
                  type="button"
                  class="primary-button"
                  :disabled="item.reviewStatus !== 'pending' || busyId === rowKey(item)"
                  @click="submitReview(item, 'approved')"
                >
                  批准
                </button>
                <button
                  type="button"
                  class="danger-button"
                  :disabled="item.reviewStatus !== 'pending' || busyId === rowKey(item)"
                  @click="submitReview(item, 'rejected')"
                >
                  驳回
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!items.length && !loading">
            <td colspan="6" class="empty-cell">暂无待复核用药。</td>
          </tr>
        </tbody>
      </table>
    </article>
  </section>
</template>

<style scoped>
.review-page {
  display: grid;
  gap: 14px;
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 180px));
  gap: 10px;
}

.metric-card {
  display: grid;
  gap: 6px;
}

.metric-card span,
.muted-line {
  color: #526772;
  font-size: 13px;
}

.metric-card strong {
  color: #0f6f99;
  font-size: 26px;
}

.review-table {
  width: 100%;
  border-collapse: collapse;
}

.review-table th,
.review-table td {
  padding: 10px;
  border-bottom: 1px solid #d5e6ef;
  text-align: left;
  vertical-align: middle;
}

.review-table th {
  background: #edf7fc;
  color: #275d70;
  font-weight: 800;
}

.review-table small {
  display: block;
  color: #6b7f8c;
  margin-top: 3px;
}

.review-table input {
  width: 100%;
  min-width: 180px;
  box-sizing: border-box;
  border: 1px solid #c9dbe5;
  border-radius: 6px;
  padding: 8px;
}

.action-row {
  display: flex;
  gap: 8px;
}

.status-pill {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 800;
}

.status-approved {
  background: #e6f9f0;
  color: #007f65;
}

.status-rejected {
  background: #fff5f5;
  color: #b42318;
}

.status-pending {
  background: #fff7ed;
  color: #9a5b00;
}

.danger-button {
  border: 1px solid #d92d20;
  background: #fff5f5;
  color: #b42318;
  border-radius: 6px;
  padding: 8px 12px;
  font-weight: 800;
}

.empty-cell {
  color: #526772;
  text-align: center;
}

.error-line {
  color: #b42318;
  font-weight: 700;
}
</style>
