<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  adjustPharmacyInventoryItem,
  createPharmacyInventoryItem,
  getPharmacyDashboard,
  getPharmacyInventoryItem,
  reviewPharmacyOrder,
  updatePharmacyInventoryItem,
} from '../services/api'
import type {
  PharmacyDashboardResponse,
  PharmacyInventoryRecord,
  PharmacyInventoryStatus,
  PharmacyInventoryUpsertRequest,
  PharmacyReviewDecisionRequest,
  PharmacyReviewOrder,
  PharmacyStockAdjustRequest,
  PharmacyTransactionRecord,
} from '../services/types'

type PanelMode = 'inventory' | 'review'
type AdjustDirection = PharmacyStockAdjustRequest['direction']
type ReviewStatus = PharmacyReviewDecisionRequest['reviewStatus']

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const panelMode = ref<PanelMode>('inventory')
const selectedInventoryId = ref('')
const selectedReviewKey = ref('')

const dashboard = ref<PharmacyDashboardResponse | null>(null)
const inventoryItems = ref<PharmacyInventoryRecord[]>([])
const reviewQueue = ref<PharmacyReviewOrder[]>([])
const transactions = ref<PharmacyTransactionRecord[]>([])

const keyword = ref('')
const warehouseFilter = ref('')
const statusFilter = ref<'all' | PharmacyInventoryStatus>('all')
const lowStockOnly = ref(false)

const inventoryForm = ref<PharmacyInventoryUpsertRequest>(createEmptyInventoryForm())
const adjustForm = ref<PharmacyStockAdjustRequest>({
  quantity: 1,
  direction: 'adjust',
  note: '',
  operatorUsername: '',
  operatorName: '',
})
const reviewForm = ref<PharmacyReviewDecisionRequest>({
  reviewStatus: 'pending',
  note: '',
  operatorUsername: '',
  operatorName: '',
})

const summaryItems = computed(() => dashboard.value?.summary ?? [])
const selectedInventory = computed(
  () => inventoryItems.value.find((item) => item.itemId === selectedInventoryId.value) ?? null
)
const selectedReview = computed(() => {
  if (!selectedReviewKey.value) return null
  return reviewQueue.value.find((item) => `${item.patientId}:${item.medicationId}` === selectedReviewKey.value) ?? null
})

const filteredInventory = computed(() => {
  const keywordValue = keyword.value.trim().toLowerCase()
  const warehouseValue = warehouseFilter.value.trim().toLowerCase()
  return inventoryItems.value.filter((item) => {
    if (statusFilter.value !== 'all' && item.status !== statusFilter.value) return false
    if (lowStockOnly.value && item.currentStock > item.minStock) return false
    if (warehouseValue && item.warehouse.toLowerCase() !== warehouseValue) return false
    if (!keywordValue) return true
    return [item.itemId, item.drugId, item.drugName, item.warehouse, item.batchNo, item.lotNo, item.supplier]
      .join(' ')
      .toLowerCase()
      .includes(keywordValue)
  })
})

const lowStockCount = computed(() => inventoryItems.value.filter((item) => item.status === 'low' || item.currentStock <= item.minStock).length)
const expiredCount = computed(() => inventoryItems.value.filter((item) => item.status === 'expired').length)
const reviewCount = computed(() => reviewQueue.value.filter((item) => item.reviewStatus === 'pending').length)
const transactionCount = computed(() => transactions.value.length)

function createEmptyInventoryForm(): PharmacyInventoryUpsertRequest {
  return {
    itemId: '',
    drugId: '',
    drugName: '',
    warehouse: 'A库',
    batchNo: '',
    lotNo: '',
    unit: 'box',
    currentStock: 0,
    reservedStock: 0,
    minStock: 0,
    expiryDate: new Date().toISOString().slice(0, 10),
    status: 'active',
    supplier: '',
  }
}

function formatTime(value: string) {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function statusLabel(status: PharmacyInventoryStatus) {
  const map: Record<PharmacyInventoryStatus, string> = {
    active: '正常',
    low: '低库存',
    out_of_stock: '缺货',
    expired: '过期',
    inactive: '停用',
  }
  return map[status]
}

function reviewLabel(value: ReviewStatus) {
  const map: Record<ReviewStatus, string> = {
    pending: '待处理',
    approved: '已通过',
    rejected: '已拒绝',
    not_required: '无需审核',
  }
  return map[value]
}

function directionLabel(value: AdjustDirection) {
  const map: Record<AdjustDirection, string> = {
    inbound: '入库',
    outbound: '出库',
    transfer: '调拨',
    adjust: '盘点调整',
    discard: '报损',
  }
  return map[value]
}

function fillInventoryForm(item: PharmacyInventoryRecord) {
  selectedInventoryId.value = item.itemId
  inventoryForm.value = {
    itemId: item.itemId,
    drugId: item.drugId,
    drugName: item.drugName,
    warehouse: item.warehouse,
    batchNo: item.batchNo,
    lotNo: item.lotNo,
    unit: item.unit,
    currentStock: item.currentStock,
    reservedStock: item.reservedStock,
    minStock: item.minStock,
    expiryDate: item.expiryDate,
    status: item.status,
    supplier: item.supplier,
  }
  panelMode.value = 'inventory'
}

function fillReviewForm(item: PharmacyReviewOrder) {
  selectedReviewKey.value = `${item.patientId}:${item.medicationId}`
  reviewForm.value = {
    reviewStatus: item.reviewStatus,
    note: item.note || '',
    operatorUsername: '',
    operatorName: '',
  }
  panelMode.value = 'review'
}

function resetInventoryForm() {
  selectedInventoryId.value = ''
  inventoryForm.value = createEmptyInventoryForm()
  panelMode.value = 'inventory'
  successMessage.value = ''
  errorMessage.value = ''
}

function resetReviewForm() {
  if (selectedReview.value) {
    fillReviewForm(selectedReview.value)
    return
  }
  reviewForm.value = {
    reviewStatus: 'pending',
    note: '',
    operatorUsername: '',
    operatorName: '',
  }
}

async function loadDashboard(selectInventoryId = selectedInventoryId.value, selectReviewKey = selectedReviewKey.value) {
  loading.value = true
  errorMessage.value = ''
  try {
    const result = await getPharmacyDashboard()
    dashboard.value = result
    inventoryItems.value = result.inventory
    reviewQueue.value = result.reviewQueue
    transactions.value = result.transactions

    const nextInventory = result.inventory.find((item) => item.itemId === selectInventoryId) ?? result.inventory[0]
    if (nextInventory) {
      fillInventoryForm(nextInventory)
      selectedInventoryId.value = nextInventory.itemId
    } else {
      resetInventoryForm()
    }

    const nextReview = result.reviewQueue.find((item) => `${item.patientId}:${item.medicationId}` === selectReviewKey) ?? result.reviewQueue[0]
    if (nextReview) {
      selectedReviewKey.value = `${nextReview.patientId}:${nextReview.medicationId}`
      reviewForm.value = {
        reviewStatus: nextReview.reviewStatus,
        note: nextReview.note || '',
        operatorUsername: '',
        operatorName: '',
      }
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '药房数据加载失败。'
  } finally {
    loading.value = false
  }
}

async function openInventory(item: PharmacyInventoryRecord) {
  try {
    const detail = await getPharmacyInventoryItem(item.itemId)
    fillInventoryForm(detail)
    successMessage.value = ''
    errorMessage.value = ''
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '无法打开库存明细。'
  }
}

function openReview(item: PharmacyReviewOrder) {
  fillReviewForm(item)
  successMessage.value = ''
  errorMessage.value = ''
}

async function saveInventory() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const payload = { ...inventoryForm.value }
    if (selectedInventoryId.value) {
      await updatePharmacyInventoryItem(selectedInventoryId.value, payload)
      successMessage.value = '库存记录已更新。'
      await loadDashboard(selectedInventoryId.value, selectedReviewKey.value)
    } else {
      const nextItemId = payload.itemId.trim() || (payload.drugId ? `stock-${payload.drugId}` : '')
      if (!nextItemId) {
        errorMessage.value = '请先填写药品编码或库存编号。'
        saving.value = false
        return
      }
      const created = await createPharmacyInventoryItem({ ...payload, itemId: nextItemId })
      successMessage.value = '库存记录已新增。'
      await loadDashboard(created.itemId, selectedReviewKey.value)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存库存失败。'
  } finally {
    saving.value = false
  }
}

async function adjustInventory(direction: AdjustDirection) {
  if (!selectedInventoryId.value) {
    errorMessage.value = '请先选择一条库存记录。'
    return
  }

  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await adjustPharmacyInventoryItem(selectedInventoryId.value, {
      ...adjustForm.value,
      direction,
    })
    successMessage.value = `${directionLabel(direction)}已记录。`
    await loadDashboard(selectedInventoryId.value, selectedReviewKey.value)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '库存调整失败。'
  } finally {
    saving.value = false
  }
}

async function saveReviewDecision() {
  if (!selectedReview.value) {
    errorMessage.value = '请先选择一条审核队列。'
    return
  }

  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await reviewPharmacyOrder(selectedReview.value.patientId, selectedReview.value.medicationId, reviewForm.value)
    successMessage.value = '审核结果已提交。'
    await loadDashboard(selectedInventoryId.value, selectedReviewKey.value)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '提交审核失败。'
  } finally {
    saving.value = false
  }
}

function setKeyword(value: string) {
  keyword.value = value
}

function clearFilters() {
  keyword.value = ''
  warehouseFilter.value = ''
  statusFilter.value = 'all'
  lowStockOnly.value = false
}

onMounted(() => {
  void loadDashboard()
})
</script>

<template>
  <section class="workspace-page pharmacy-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">药房 / 药库</p>
        <h1>药房药库工作台</h1>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="clearFilters">清空筛选</button>
        <button class="primary-button" type="button" @click="resetInventoryForm">新增库存</button>
      </div>
    </header>

    <section class="metric-grid four">
      <article v-for="item in summaryItems" :key="item.label" class="metric-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.trend }}</small>
      </article>
      <article class="metric-card">
        <span>低库存</span>
        <strong>{{ lowStockCount }}</strong>
        <small>需要补货</small>
      </article>
      <article class="metric-card">
        <span>过期</span>
        <strong>{{ expiredCount }}</strong>
        <small>需处理</small>
      </article>
      <article class="metric-card">
        <span>待审核</span>
        <strong>{{ reviewCount }}</strong>
        <small>处方审核队列</small>
      </article>
      <article class="metric-card">
        <span>出入库记录</span>
        <strong>{{ transactionCount }}</strong>
        <small>最近操作</small>
      </article>
    </section>

    <div v-if="errorMessage" class="inline-alert error">{{ errorMessage }}</div>
    <div v-else-if="successMessage" class="inline-alert success">{{ successMessage }}</div>

    <section class="pharmacy-layout">
      <article class="clinical-card pharmacy-list-card">
        <div class="section-header">
          <div>
            <h2>库存总览</h2>
            <p>库存浏览、批次筛选与详情维护。</p>
          </div>
          <button class="secondary-button" type="button" :disabled="loading" @click="loadDashboard()">刷新</button>
        </div>

        <div class="filter-grid">
          <label class="field">
            <span>关键词</span>
            <input :value="keyword" type="text" placeholder="药品、批号、仓库、供应商" @input="setKeyword(($event.target as HTMLInputElement).value)" />
          </label>
          <label class="field">
            <span>仓库</span>
            <input v-model="warehouseFilter" type="text" placeholder="A库 / B库 / 冷链库" />
          </label>
          <label class="field">
            <span>状态</span>
            <select v-model="statusFilter">
              <option value="all">全部</option>
              <option value="active">正常</option>
              <option value="low">低库存</option>
              <option value="out_of_stock">缺货</option>
              <option value="expired">过期</option>
              <option value="inactive">停用</option>
            </select>
          </label>
          <label class="field toggle-field">
            <span>仅看低库存</span>
            <input v-model="lowStockOnly" type="checkbox" />
          </label>
        </div>

        <div v-if="!filteredInventory.length && !loading" class="empty-state-card compact">
          <h3>暂无库存记录</h3>
          <p>请调整筛选条件，或通过右侧新增库存录入一条药房记录。</p>
        </div>

        <div v-else class="pharmacy-table">
          <div class="pharmacy-head">
            <span>药品</span>
            <span>仓库 / 批号</span>
            <span>库存</span>
            <span>状态</span>
          </div>
          <button
            v-for="item in filteredInventory"
            :key="item.itemId"
            class="pharmacy-row"
            :class="{ selected: item.itemId === selectedInventoryId }"
            type="button"
            @click="openInventory(item)"
          >
            <div class="pharmacy-cell">
              <strong>{{ item.drugName }}</strong>
              <span>{{ item.drugId }} / {{ item.unit }}</span>
            </div>
            <div class="pharmacy-cell">
              <strong>{{ item.warehouse }}</strong>
              <span>{{ item.batchNo }} / {{ item.lotNo }}</span>
            </div>
            <div class="pharmacy-cell">
              <strong>{{ item.currentStock }}</strong>
              <span>预留 {{ item.reservedStock }} / 最低 {{ item.minStock }}</span>
            </div>
            <div class="pharmacy-cell">
              <span class="status-pill" :class="item.status === 'active' ? 'success' : item.status === 'low' ? 'warning' : 'muted'">
                {{ statusLabel(item.status) }}
              </span>
            </div>
          </button>
        </div>

        <div class="section-block">
          <h3>处方审核队列</h3>
          <div class="compact-list">
            <button
              v-for="item in reviewQueue"
              :key="`${item.patientId}:${item.medicationId}`"
              class="compact-list-item"
              :class="{ selected: `${item.patientId}:${item.medicationId}` === selectedReviewKey }"
              type="button"
              @click="openReview(item)"
            >
              <strong>{{ item.patientName }}</strong>
              <span>{{ item.drugNameSnapshot }} / {{ reviewLabel(item.reviewStatus) }}</span>
              <small>{{ item.dosage }} · {{ item.frequency }} · {{ item.route }}</small>
            </button>
          </div>
        </div>

        <div class="section-block">
          <h3>出入库记录</h3>
          <ul class="timeline-list">
            <li v-for="tx in transactions.slice(0, 8)" :key="tx.transactionId">
              <span>{{ formatTime(tx.createdAt) }}</span>
              <strong>{{ directionLabel(tx.direction) }}</strong>
              <p>{{ tx.note || tx.itemId }}</p>
            </li>
          </ul>
        </div>
      </article>

      <aside class="pharmacy-side">
        <article class="clinical-card pharmacy-detail-card">
          <div class="section-header">
            <div>
              <h2>{{ panelMode === 'review' ? '审核处理' : '库存详情' }}</h2>
              <p>{{ panelMode === 'review' ? '药师按照处方审核队列完成复核、通过或拒绝。' : '维护药房库存、批次、仓库和有效期。' }}</p>
            </div>
          </div>

          <div v-if="panelMode === 'review' && selectedReview" class="detail-summary">
            <div class="info-item">
              <span>患者</span>
              <strong>{{ selectedReview.patientName }}</strong>
            </div>
            <div class="info-item">
              <span>药品</span>
              <strong>{{ selectedReview.drugNameSnapshot }}</strong>
            </div>
            <div class="info-item">
              <span>处方状态</span>
              <strong>{{ reviewLabel(selectedReview.reviewStatus) }}</strong>
            </div>
            <div class="info-item">
              <span>当前状态</span>
              <strong>{{ selectedReview.status }}</strong>
            </div>
          </div>

          <div v-else-if="selectedInventory" class="detail-summary">
            <div class="info-item">
              <span>药品</span>
              <strong>{{ selectedInventory.drugName }}</strong>
            </div>
            <div class="info-item">
              <span>仓库</span>
              <strong>{{ selectedInventory.warehouse }}</strong>
            </div>
            <div class="info-item">
              <span>批号</span>
              <strong>{{ selectedInventory.batchNo }}</strong>
            </div>
            <div class="info-item">
              <span>有效期</span>
              <strong>{{ selectedInventory.expiryDate }}</strong>
            </div>
          </div>

          <div class="editor-grid">
            <label class="field full-span">
              <span>药品名称</span>
              <input v-model="inventoryForm.drugName" type="text" />
            </label>
            <label class="field">
              <span>药品编码</span>
              <input v-model="inventoryForm.drugId" type="text" />
            </label>
            <label class="field">
              <span>仓库</span>
              <input v-model="inventoryForm.warehouse" type="text" />
            </label>
            <label class="field">
              <span>批号</span>
              <input v-model="inventoryForm.batchNo" type="text" />
            </label>
            <label class="field">
              <span>库位号</span>
              <input v-model="inventoryForm.lotNo" type="text" />
            </label>
            <label class="field">
              <span>单位</span>
              <input v-model="inventoryForm.unit" type="text" />
            </label>
            <label class="field">
              <span>当前库存</span>
              <input v-model.number="inventoryForm.currentStock" type="number" min="0" />
            </label>
            <label class="field">
              <span>预留库存</span>
              <input v-model.number="inventoryForm.reservedStock" type="number" min="0" />
            </label>
            <label class="field">
              <span>最低库存</span>
              <input v-model.number="inventoryForm.minStock" type="number" min="0" />
            </label>
            <label class="field">
              <span>有效期</span>
              <input v-model="inventoryForm.expiryDate" type="date" />
            </label>
            <label class="field">
              <span>供应商</span>
              <input v-model="inventoryForm.supplier" type="text" />
            </label>
            <label class="field">
              <span>状态</span>
              <select v-model="inventoryForm.status">
                <option value="active">正常</option>
                <option value="low">低库存</option>
                <option value="out_of_stock">缺货</option>
                <option value="expired">过期</option>
                <option value="inactive">停用</option>
              </select>
            </label>
          </div>

          <div class="form-actions">
            <button class="secondary-button" type="button" @click="resetInventoryForm">新建库存</button>
            <button class="primary-button" type="button" :disabled="saving" @click="saveInventory">
              {{ saving ? '保存中...' : selectedInventoryId ? '更新库存' : '创建库存' }}
            </button>
          </div>
        </article>

        <article class="clinical-card pharmacy-adjust-card">
          <div class="section-header">
          <div>
            <h2>库存出入库</h2>
              <p>后台登记、补货、调拨和盘点调整。</p>
            </div>
          </div>
          <div class="editor-grid compact">
            <label class="field">
              <span>数量</span>
              <input v-model.number="adjustForm.quantity" type="number" min="1" />
            </label>
            <label class="field">
              <span>备注</span>
              <input v-model="adjustForm.note" type="text" placeholder="入库、调拨、报损说明" />
            </label>
            <label class="field">
              <span>操作人</span>
              <input v-model="adjustForm.operatorName" type="text" placeholder="可留空，自动使用当前用户" />
            </label>
          </div>
          <div class="form-actions wrap">
            <button class="secondary-button" type="button" :disabled="saving || !selectedInventoryId" @click="adjustInventory('inbound')">入库</button>
            <button class="secondary-button" type="button" :disabled="saving || !selectedInventoryId" @click="adjustInventory('outbound')">出库</button>
            <button class="secondary-button" type="button" :disabled="saving || !selectedInventoryId" @click="adjustInventory('transfer')">调拨</button>
            <button class="secondary-button" type="button" :disabled="saving || !selectedInventoryId" @click="adjustInventory('discard')">报损</button>
            <button class="secondary-button" type="button" :disabled="saving || !selectedInventoryId" @click="adjustInventory('adjust')">盘点</button>
          </div>
        </article>

        <article class="clinical-card pharmacy-review-card">
          <div class="section-header">
            <div>
              <h2>处方审核</h2>
              <p>审核通过后回写药房记录与医护协调轨迹。</p>
            </div>
          </div>
          <div v-if="selectedReview" class="review-summary">
            <p><strong>{{ selectedReview.patientName }}</strong> · {{ selectedReview.drugNameSnapshot }}</p>
            <small>{{ selectedReview.dosage }} / {{ selectedReview.frequency }} / {{ selectedReview.route }}</small>
          </div>
          <div class="editor-grid compact">
            <label class="field">
              <span>审核结果</span>
              <select v-model="reviewForm.reviewStatus">
                <option value="pending">待处理</option>
                <option value="approved">通过</option>
                <option value="rejected">拒绝</option>
                <option value="not_required">无需审核</option>
              </select>
            </label>
            <label class="field full-span">
              <span>审核说明</span>
              <textarea v-model="reviewForm.note" rows="3" placeholder="审核说明、补充建议或拒绝原因"></textarea>
            </label>
          </div>
          <div class="form-actions">
            <button class="secondary-button" type="button" @click="resetReviewForm">重置审核</button>
            <button class="primary-button" type="button" :disabled="saving || !selectedReview" @click="saveReviewDecision">
              {{ saving ? '提交中...' : '提交审核' }}
            </button>
          </div>
        </article>
      </aside>
    </section>
  </section>
</template>

<style scoped>
.pharmacy-page,
.pharmacy-layout,
.pharmacy-side,
.pharmacy-table,
.filter-grid,
.editor-grid,
.detail-summary {
  display: grid;
  gap: 20px;
}

.pharmacy-layout {
  grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.95fr);
  align-items: start;
}

.pharmacy-side {
  position: sticky;
  top: 24px;
}

.pharmacy-list-card,
.pharmacy-detail-card,
.pharmacy-adjust-card,
.pharmacy-review-card {
  display: grid;
  gap: 16px;
}

.pharmacy-table {
  gap: 10px;
}

.pharmacy-head,
.pharmacy-row {
  display: grid;
  grid-template-columns: 1.6fr 1.2fr 0.8fr 0.5fr;
  gap: 12px;
  align-items: center;
}

.pharmacy-head {
  padding: 0 8px;
  color: rgba(17, 24, 39, 0.62);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.pharmacy-row {
  width: 100%;
  text-align: left;
  padding: 14px 16px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  transition: border-color 0.18s ease, transform 0.18s ease, background 0.18s ease;
}

.pharmacy-row.selected,
.pharmacy-row:hover {
  border-color: rgba(15, 118, 110, 0.28);
  background: rgba(240, 253, 250, 0.9);
  transform: translateY(-1px);
}

.pharmacy-cell {
  display: grid;
  gap: 4px;
}

.pharmacy-cell span {
  color: rgba(17, 24, 39, 0.58);
  font-size: 12px;
}

.compact-list {
  display: grid;
  gap: 10px;
}

.compact-list-item {
  text-align: left;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.84);
  display: grid;
  gap: 4px;
}

.compact-list-item.selected {
  border-color: rgba(15, 118, 110, 0.34);
  background: rgba(236, 253, 245, 0.92);
}

.timeline-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 10px;
}

.timeline-list li {
  display: grid;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.timeline-list span,
.timeline-list p {
  color: rgba(17, 24, 39, 0.62);
  font-size: 12px;
}

.detail-summary {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.review-summary {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(15, 118, 110, 0.06);
  border: 1px solid rgba(15, 118, 110, 0.12);
  display: grid;
  gap: 4px;
}

.form-actions.wrap {
  flex-wrap: wrap;
}

@media (max-width: 1200px) {
  .pharmacy-layout {
    grid-template-columns: 1fr;
  }

  .pharmacy-side {
    position: static;
  }
}

@media (max-width: 720px) {
  .pharmacy-head,
  .pharmacy-row,
  .detail-summary {
    grid-template-columns: 1fr;
  }
}
</style>

