<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { createDrugCatalogItem, getDrugCatalog, updateDrugCatalogItem } from '../../services/api'
import type { DrugCatalogRecord, DrugCatalogStatus, DrugCatalogUpsertRequest } from '../../services/types'

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const editorVisible = ref(false)

const keyword = ref('')
const statusFilter = ref<'all' | DrugCatalogStatus>('all')
const controlledFilter = ref<'all' | 'yes' | 'no'>('all')
const prescriptionFilter = ref<'all' | 'yes' | 'no'>('all')
const dosageFormFilter = ref('')

const drugs = ref<DrugCatalogRecord[]>([])
const selectedDrugId = ref('')
const form = ref<DrugCatalogUpsertRequest>(createEmptyForm())

const selectedDrug = computed(() => drugs.value.find((item) => item.drug_id === selectedDrugId.value) ?? null)
const isEditing = computed(() => Boolean(selectedDrugId.value))
const activeCount = computed(() => drugs.value.filter((item) => item.status === 'active').length)
const controlledCount = computed(() => drugs.value.filter((item) => item.is_controlled).length)
const prescriptionCount = computed(() => drugs.value.filter((item) => item.is_prescription).length)

const filteredDrugs = computed(() => {
  const keywordValue = keyword.value.trim().toLowerCase()
  const dosageValue = dosageFormFilter.value.trim().toLowerCase()

  return drugs.value.filter((drug) => {
    if (statusFilter.value !== 'all' && drug.status !== statusFilter.value) return false
    if (controlledFilter.value === 'yes' && !drug.is_controlled) return false
    if (controlledFilter.value === 'no' && drug.is_controlled) return false
    if (prescriptionFilter.value === 'yes' && !drug.is_prescription) return false
    if (prescriptionFilter.value === 'no' && drug.is_prescription) return false
    if (dosageValue && drug.dosage_form.toLowerCase() !== dosageValue) return false
    if (!keywordValue) return true

    return [
      drug.drug_id,
      drug.generic_name,
      drug.brand_name,
      drug.dosage_form,
      drug.specification,
      drug.unit,
      drug.indication,
    ]
      .join(' ')
      .toLowerCase()
      .includes(keywordValue)
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

function fillForm(drug: DrugCatalogRecord) {
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
}

function resetEditor() {
  selectedDrugId.value = ''
  form.value = createEmptyForm()
  errorMessage.value = ''
  successMessage.value = ''
  editorVisible.value = true
}

function openDrug(drug: DrugCatalogRecord) {
  fillForm(drug)
  errorMessage.value = ''
  successMessage.value = ''
  editorVisible.value = true
}

async function loadDrugs(selectDrugId = selectedDrugId.value) {
  loading.value = true
  errorMessage.value = ''
  try {
    drugs.value = await getDrugCatalog()
    const next = drugs.value.find((item) => item.drug_id === selectDrugId)
    if (next) fillForm(next)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '药品目录加载失败。'
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
      const updated = await updateDrugCatalogItem(selectedDrugId.value, payload)
      successMessage.value = '药品目录已更新。'
      await loadDrugs(updated.drug_id)
    } else {
      const created = await createDrugCatalogItem(payload)
      successMessage.value = '药品目录已新增。'
      await loadDrugs(created.drug_id)
    }
    editorVisible.value = false
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '药品保存失败。'
  } finally {
    saving.value = false
  }
}

function clearFilters() {
  keyword.value = ''
  statusFilter.value = 'all'
  controlledFilter.value = 'all'
  prescriptionFilter.value = 'all'
  dosageFormFilter.value = ''
}

function statusText(status: DrugCatalogStatus): string {
  return status === 'active' ? '启用' : '停用'
}

function yesNo(value: boolean): string {
  return value ? '是' : '否'
}

function formatTime(value: string): string {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

onMounted(() => {
  void loadDrugs()
})
</script>

<template>
  <section class="workspace-page drug-catalog-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">药品目录 / 基础字典</p>
        <h1>药品目录管理</h1>
        <p>维护慢病场景下的药品字典、剂型规格、处方属性、管制属性和启停状态，为当前用药与权限管理提供基础数据。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="clearFilters">重置筛选</button>
        <button class="primary-button" type="button" @click="resetEditor">新增药品</button>
      </div>
    </header>

    <section class="metric-grid four">
      <article class="metric-card">
        <span>药品总数</span>
        <strong>{{ drugs.length }}</strong>
      </article>
      <article class="metric-card">
        <span>启用药品</span>
        <strong>{{ activeCount }}</strong>
      </article>
      <article class="metric-card">
        <span>处方药</span>
        <strong>{{ prescriptionCount }}</strong>
      </article>
      <article class="metric-card">
        <span>管制药</span>
        <strong>{{ controlledCount }}</strong>
      </article>
    </section>

    <div v-if="errorMessage" class="inline-alert error">{{ errorMessage }}</div>
    <div v-else-if="successMessage" class="inline-alert success">{{ successMessage }}</div>

    <section class="drug-layout">
      <article class="clinical-card catalog-table-card">
        <div class="section-header">
          <div>
            <h2>目录筛选与列表</h2>
            <p>共命中 {{ filteredDrugs.length }} 条药品记录，单击任一行可进入编辑。</p>
          </div>
          <button class="secondary-button" type="button" :disabled="loading" @click="loadDrugs()">刷新列表</button>
        </div>

        <div class="filter-grid">
          <label class="field">
            <span>关键词</span>
            <input v-model="keyword" type="text" placeholder="药品编号 / 通用名 / 适应症" />
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
              <option value="yes">处方药</option>
              <option value="no">非处方药</option>
            </select>
          </label>
          <label class="field">
            <span>管制药</span>
            <select v-model="controlledFilter">
              <option value="all">全部</option>
              <option value="yes">仅管制药</option>
              <option value="no">非管制药</option>
            </select>
          </label>
        </div>

        <div v-if="!filteredDrugs.length && !loading" class="empty-state-card compact">
          <h3>暂无符合条件的药品</h3>
          <p>可以调整筛选条件，或新增一条药品目录记录。</p>
        </div>

        <div v-else class="catalog-table">
          <div class="catalog-head">
            <span>药品</span>
            <span>剂型 / 规格</span>
            <span>适应症</span>
            <span>属性</span>
            <span>状态</span>
          </div>
          <button
            v-for="drug in filteredDrugs"
            :key="drug.drug_id"
            class="catalog-row"
            :class="{ selected: drug.drug_id === selectedDrugId }"
            type="button"
            @click="openDrug(drug)"
          >
            <div class="catalog-cell">
              <strong>{{ drug.generic_name }}</strong>
              <span>{{ drug.brand_name || '无商品名' }} / {{ drug.drug_id }}</span>
            </div>
            <div class="catalog-cell">
              <strong>{{ drug.dosage_form }}</strong>
              <span>{{ drug.specification }} / {{ drug.unit }}</span>
            </div>
            <div class="catalog-cell">
              <strong>{{ drug.indication || '未填写' }}</strong>
              <span>更新于 {{ formatTime(drug.updated_at) }}</span>
            </div>
            <div class="catalog-cell tags">
              <span class="tag">{{ drug.is_prescription ? '处方药' : '非处方药' }}</span>
              <span class="tag warning" v-if="drug.is_controlled">管制药</span>
            </div>
            <div class="catalog-cell">
              <span class="status-pill" :class="drug.status === 'active' ? 'success' : 'muted'">
                {{ statusText(drug.status) }}
              </span>
            </div>
          </button>
        </div>
      </article>

      <aside class="clinical-card catalog-editor-card">
        <div class="section-header">
          <div>
            <h2>{{ isEditing ? '药品详情编辑' : '新增药品目录' }}</h2>
            <p>维护药品目录的最小必要字段，不扩展到库存或收费流程。</p>
          </div>
        </div>

        <div v-if="selectedDrug" class="editor-info-grid">
          <div class="info-item">
            <span>最近更新时间</span>
            <strong>{{ formatTime(selectedDrug.updated_at) }}</strong>
          </div>
          <div class="info-item">
            <span>更新人</span>
            <strong>{{ selectedDrug.updated_by || '--' }}</strong>
          </div>
          <div class="info-item">
            <span>处方药</span>
            <strong>{{ yesNo(selectedDrug.is_prescription) }}</strong>
          </div>
          <div class="info-item">
            <span>管制药</span>
            <strong>{{ yesNo(selectedDrug.is_controlled) }}</strong>
          </div>
        </div>

        <div class="editor-grid">
          <label class="field">
            <span>药品编号</span>
            <input v-model="form.drug_id" :disabled="isEditing" type="text" placeholder="drug-metformin" />
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
          <label class="field full-span">
            <span>适应症</span>
            <input v-model="form.indication" type="text" />
          </label>
          <label class="field">
            <span>目录状态</span>
            <select v-model="form.status">
              <option value="active">启用</option>
              <option value="inactive">停用</option>
            </select>
          </label>
          <label class="field toggle-field">
            <span>处方药</span>
            <input v-model="form.is_prescription" type="checkbox" />
          </label>
          <label class="field toggle-field">
            <span>管制药</span>
            <input v-model="form.is_controlled" type="checkbox" />
          </label>
        </div>

        <div class="form-actions">
          <button class="secondary-button" type="button" @click="resetEditor">清空表单</button>
          <button class="primary-button" type="button" :disabled="saving" @click="saveDrug">
            {{ saving ? '保存中...' : isEditing ? '保存修改' : '创建药品' }}
          </button>
        </div>
      </aside>
    </section>
  </section>
</template>

<style scoped>
.drug-catalog-page,
.drug-layout,
.filter-grid,
.catalog-table,
.editor-grid,
.editor-info-grid {
  display: grid;
  gap: 22px;
}

.drug-layout {
  grid-template-columns: minmax(0, 1.32fr) minmax(360px, 0.92fr);
  align-items: start;
}

.catalog-table-card,
.catalog-editor-card {
  display: grid;
  gap: 18px;
}

.catalog-table-card {
  min-width: 0;
}

.catalog-editor-card {
  position: sticky;
  top: 24px;
}

.header-actions,
.section-header,
.form-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-grid,
.editor-grid,
.editor-info-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field {
  display: grid;
  gap: 8px;
}

.field.full-span {
  grid-column: 1 / -1;
}

.field span {
  color: #3f4848;
  font-size: 13px;
  font-weight: 700;
}

.field input,
.field select {
  width: 100%;
  min-height: 48px;
  border: 1px solid #d5dde0;
  border-radius: 14px;
  background: #fff;
  padding: 0 14px;
  font: inherit;
  color: #181c1e;
}

.toggle-field input {
  width: 20px;
  min-height: 20px;
  padding: 0;
}

.catalog-head,
.catalog-row {
  display: grid;
  grid-template-columns: 1.3fr 1fr 1fr 0.9fr 0.6fr;
  gap: 12px;
  align-items: center;
}

.catalog-head {
  color: #61737b;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.catalog-row {
  border: 1px solid rgba(205, 214, 218, 0.9);
  border-radius: 16px;
  background: #fff;
  padding: 16px;
  text-align: left;
}

.catalog-row.selected {
  border-color: rgba(0, 92, 97, 0.35);
  box-shadow: 0 0 0 2px rgba(0, 92, 97, 0.08);
}

.catalog-cell {
  display: grid;
  gap: 6px;
}

.catalog-cell span {
  color: #61737b;
}

.catalog-cell.tags {
  display: flex;
  flex-wrap: wrap;
}

.tag,
.status-pill {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  padding: 6px 10px;
  background: rgba(235, 238, 239, 0.92);
  color: #31454c;
  font-size: 12px;
  font-weight: 700;
}

.tag.warning {
  background: rgba(255, 236, 226, 0.9);
}

.status-pill.success {
  background: rgba(237, 247, 238, 0.95);
}

.status-pill.muted {
  background: rgba(241, 244, 245, 0.92);
}

.info-item {
  display: grid;
  gap: 6px;
  border-radius: 14px;
  background: rgba(241, 244, 245, 0.92);
  padding: 14px;
}

.info-item span {
  color: #61737b;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.inline-alert {
  border-radius: 14px;
  padding: 14px 16px;
}

.inline-alert.error {
  background: rgba(255, 218, 214, 0.75);
  color: #8c1d18;
}

.inline-alert.success {
  background: rgba(237, 247, 238, 0.9);
  color: #1f6d33;
}

@media (max-width: 1180px) {
  .drug-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .filter-grid,
  .editor-grid,
  .editor-info-grid,
  .catalog-head,
  .catalog-row {
    grid-template-columns: 1fr;
  }
}
</style>
