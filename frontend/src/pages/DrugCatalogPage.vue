<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  createDrugCatalogItem,
  getDrugCatalog,
  updateDrugCatalogItem,
} from '../services/api'
import type { DrugCatalogRecord, DrugCatalogStatus, DrugCatalogUpsertRequest } from '../services/types'

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const keyword = ref('')
const statusFilter = ref<'all' | DrugCatalogStatus>('all')
const dosageFormFilter = ref('')
const prescriptionFilter = ref<'all' | 'yes' | 'no'>('all')
const controlledFilter = ref<'all' | 'yes' | 'no'>('all')

const drugs = ref<DrugCatalogRecord[]>([])
const selectedDrugId = ref('')
const form = ref<DrugCatalogUpsertRequest>(createEmptyForm())

const selectedDrug = computed(() => drugs.value.find((item) => item.drug_id === selectedDrugId.value) ?? null)
const isEditing = computed(() => Boolean(selectedDrugId.value))

const filteredDrugs = computed(() => {
  const keywordValue = keyword.value.trim().toLowerCase()
  const dosageValue = dosageFormFilter.value.trim().toLowerCase()

  return drugs.value.filter((drug) => {
    if (statusFilter.value !== 'all' && drug.status !== statusFilter.value) return false
    if (dosageValue && drug.dosage_form.toLowerCase() !== dosageValue) return false
    if (prescriptionFilter.value === 'yes' && !drug.is_prescription) return false
    if (prescriptionFilter.value === 'no' && drug.is_prescription) return false
    if (controlledFilter.value === 'yes' && !drug.is_controlled) return false
    if (controlledFilter.value === 'no' && drug.is_controlled) return false
    if (!keywordValue) return true

    const haystack = [
      drug.drug_id,
      drug.generic_name,
      drug.brand_name,
      drug.dosage_form,
      drug.specification,
      drug.unit,
      drug.indication,
    ].join(' ').toLowerCase()

    return haystack.includes(keywordValue)
  })
})

function createEmptyForm(): DrugCatalogUpsertRequest {
  return {
    drug_id: '',
    generic_name: '',
    brand_name: '',
    dosage_form: '',
    specification: '',
    unit: 'box',
    is_prescription: true,
    is_controlled: false,
    status: 'active',
    indication: '',
  }
}

function resetEditor() {
  selectedDrugId.value = ''
  form.value = createEmptyForm()
  errorMessage.value = ''
  successMessage.value = ''
}

function openDrug(drug: DrugCatalogRecord) {
  selectedDrugId.value = drug.drug_id
  form.value = {
    drug_id: drug.drug_id,
    generic_name: drug.generic_name,
    brand_name: drug.brand_name,
    dosage_form: drug.dosage_form,
    specification: drug.specification,
    unit: drug.unit,
    is_prescription: drug.is_prescription,
    is_controlled: drug.is_controlled,
    status: drug.status,
    indication: drug.indication,
  }
  errorMessage.value = ''
  successMessage.value = ''
}

async function loadDrugs(selectDrugId = '') {
  loading.value = true
  errorMessage.value = ''
  try {
    drugs.value = await getDrugCatalog()
    if (selectDrugId) {
      const next = drugs.value.find((item) => item.drug_id === selectDrugId)
      if (next) openDrug(next)
    } else if (!selectedDrugId.value && drugs.value.length) {
      const firstDrug = drugs.value[0]
      if (firstDrug) openDrug(firstDrug)
    } else if (selectedDrugId.value) {
      const next = drugs.value.find((item) => item.drug_id === selectedDrugId.value)
      if (next) openDrug(next)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载药品目录失败。'
  } finally {
    loading.value = false
  }
}

async function saveDrug() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const payload = { ...form.value }
    if (selectedDrugId.value) {
      await updateDrugCatalogItem(selectedDrugId.value, payload)
      successMessage.value = '药品已更新。'
      await loadDrugs(selectedDrugId.value)
    } else {
      const created = await createDrugCatalogItem(payload)
      successMessage.value = '药品已新增。'
      await loadDrugs(created.drug_id)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存药品失败。'
  } finally {
    saving.value = false
  }
}

function clearFilters() {
  keyword.value = ''
  statusFilter.value = 'all'
  dosageFormFilter.value = ''
  prescriptionFilter.value = 'all'
  controlledFilter.value = 'all'
}

function statusText(status: DrugCatalogStatus) {
  return status === 'active' ? '启用' : '停用'
}

function formatBoolean(value: boolean) {
  return value ? '是' : '否'
}

onMounted(() => {
  void loadDrugs()
})
</script>

<template>
  <section class="workspace-page drug-catalog-page">
    <header class="card page-header">
      <div>
        <h2>药品管理</h2>
        <p>最小可用药品目录，仅负责目录维护，不包含库存、处方流或训练中心。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="resetEditor">新建药品</button>
        <button class="primary-button" type="button" :disabled="saving" @click="saveDrug">
          {{ saving ? '保存中...' : isEditing ? '保存修改' : '新增药品' }}
        </button>
      </div>
    </header>

    <section v-if="errorMessage" class="card empty-state">
      {{ errorMessage }}
    </section>

    <section v-else-if="successMessage" class="card empty-state success">
      {{ successMessage }}
    </section>

    <section class="drug-layout">
      <article class="card panel drug-list-panel">
        <div class="panel-head">
          <div>
            <h3>药品目录列表</h3>
            <p>{{ filteredDrugs.length }} 条记录</p>
          </div>
          <button class="secondary-button" type="button" :disabled="loading" @click="loadDrugs(selectedDrugId)">
            {{ loading ? '刷新中...' : '刷新列表' }}
          </button>
        </div>

        <div class="filter-grid">
          <label class="field">
            <span>关键词</span>
            <input v-model="keyword" type="text" placeholder="编号、通用名、商品名、适应症" />
          </label>
          <label class="field">
            <span>状态</span>
            <select v-model="statusFilter">
              <option value="all">全部</option>
              <option value="active">启用</option>
              <option value="inactive">停用</option>
            </select>
          </label>
          <label class="field">
            <span>剂型</span>
            <input v-model="dosageFormFilter" type="text" placeholder="tablet / capsule / injection" />
          </label>
          <label class="field">
            <span>处方药</span>
            <select v-model="prescriptionFilter">
              <option value="all">全部</option>
              <option value="yes">是</option>
              <option value="no">否</option>
            </select>
          </label>
          <label class="field">
            <span>管制药</span>
            <select v-model="controlledFilter">
              <option value="all">全部</option>
              <option value="yes">是</option>
              <option value="no">否</option>
            </select>
          </label>
          <div class="filter-actions">
            <button class="secondary-button" type="button" @click="clearFilters">清空筛选</button>
          </div>
        </div>

        <div v-if="loading" class="card empty-state compact">正在加载药品目录...</div>
        <div v-else-if="!filteredDrugs.length" class="card empty-state compact">暂无匹配的药品。</div>
        <div v-else class="drug-table">
          <table>
            <thead>
              <tr>
                <th>药品编号</th>
                <th>通用名</th>
                <th>商品名</th>
                <th>剂型</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="drug in filteredDrugs"
                :key="drug.drug_id"
                :class="{ active: selectedDrugId === drug.drug_id }"
                @click="openDrug(drug)"
              >
                <td>{{ drug.drug_id }}</td>
                <td>
                  <strong>{{ drug.generic_name }}</strong>
                  <p>{{ drug.indication }}</p>
                </td>
                <td>{{ drug.brand_name || '--' }}</td>
                <td>{{ drug.dosage_form }}</td>
                <td>
                  <span class="status-badge" :class="drug.status">{{ statusText(drug.status) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="card panel drug-detail-panel">
        <div class="panel-head">
          <div>
            <h3>{{ isEditing ? '药品详情 / 编辑' : '新增药品' }}</h3>
            <p>字段校验由后端统一执行。</p>
          </div>
          <div class="panel-meta">
            <span class="badge" :class="selectedDrug?.status ?? 'active'">{{ selectedDrug ? statusText(selectedDrug.status) : '新建' }}</span>
          </div>
        </div>

        <div class="detail-summary" v-if="selectedDrug">
          <p><span>最近更新</span><strong>{{ selectedDrug.updated_at }}</strong></p>
          <p><span>更新人</span><strong>{{ selectedDrug.updated_by }}</strong></p>
          <p><span>处方药</span><strong>{{ formatBoolean(selectedDrug.is_prescription) }}</strong></p>
          <p><span>管制药</span><strong>{{ formatBoolean(selectedDrug.is_controlled) }}</strong></p>
        </div>

        <div class="edit-grid">
          <label class="field">
            <span>药品编号</span>
            <input v-model="form.drug_id" :disabled="isEditing" type="text" placeholder="例如 drug-metformin" />
          </label>
          <label class="field">
            <span>通用名</span>
            <input v-model="form.generic_name" type="text" />
          </label>
          <label class="field">
            <span>商品名</span>
            <input v-model="form.brand_name" type="text" />
          </label>
          <label class="field">
            <span>剂型</span>
            <input v-model="form.dosage_form" type="text" />
          </label>
          <label class="field">
            <span>规格</span>
            <input v-model="form.specification" type="text" />
          </label>
          <label class="field">
            <span>单位</span>
            <input v-model="form.unit" type="text" />
          </label>
          <label class="field">
            <span>适应症</span>
            <input v-model="form.indication" type="text" />
          </label>
          <label class="field">
            <span>状态</span>
            <select v-model="form.status">
              <option value="active">启用</option>
              <option value="inactive">停用</option>
            </select>
          </label>
          <label class="field">
            <span>处方药</span>
            <select v-model="form.is_prescription">
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select>
          </label>
          <label class="field">
            <span>管制药</span>
            <select v-model="form.is_controlled">
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select>
          </label>
        </div>

        <div class="detail-actions">
          <button class="secondary-button" type="button" @click="resetEditor">重置</button>
          <button class="primary-button" type="button" :disabled="saving" @click="saveDrug">
            {{ saving ? '保存中...' : isEditing ? '保存修改' : '新增药品' }}
          </button>
        </div>

        <div v-if="selectedDrug" class="detail-footnote">
          <p>当前仅维护目录信息，不包含库存、调剂、处方开立或训练功能。</p>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.drug-layout {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 20px;
  align-items: start;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
  margin-bottom: 16px;
}

.panel-head h3 {
  margin: 0;
}

.panel-head p {
  margin: 4px 0 0;
  color: #64748b;
}

.filter-grid,
.edit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.filter-actions,
.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  grid-column: 1 / -1;
}

.field {
  display: grid;
  gap: 6px;
}

.field span {
  font-size: 13px;
  color: #64748b;
}

.field input,
.field select {
  width: 100%;
}

.drug-table {
  margin-top: 16px;
  overflow: auto;
}

.drug-table table {
  width: 100%;
  border-collapse: collapse;
}

.drug-table th,
.drug-table td {
  text-align: left;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  padding: 12px 10px;
  vertical-align: top;
}

.drug-table tbody tr {
  cursor: pointer;
}

.drug-table tbody tr.active {
  background: rgba(56, 189, 248, 0.08);
}

.drug-table td p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 12px;
}

.status-badge,
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.active,
.badge.active {
  background: rgba(34, 197, 94, 0.14);
  color: #15803d;
}

.status-badge.inactive,
.badge.inactive {
  background: rgba(248, 113, 113, 0.14);
  color: #b91c1c;
}

.detail-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.detail-summary p {
  margin: 0;
  display: grid;
  gap: 4px;
}

.detail-summary span,
.detail-footnote p {
  color: #64748b;
  font-size: 12px;
}

.detail-summary strong {
  font-size: 14px;
}

.detail-footnote {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
}

@media (max-width: 1100px) {
  .drug-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .filter-grid,
  .edit-grid,
  .detail-summary {
    grid-template-columns: 1fr;
  }
}
</style>
