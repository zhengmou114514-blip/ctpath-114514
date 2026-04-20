<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  createDrugCatalogItem,
  getDrugCatalog,
  updateDrugCatalogItem,
} from '../../services/api'
import type { DrugCatalogRecord, DrugCatalogStatus, DrugCatalogUpsertRequest } from '../../services/types'

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

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
    ].join(' ').toLowerCase().includes(keywordValue)
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

async function loadDrugs(selectDrugId = selectedDrugId.value) {
  loading.value = true
  errorMessage.value = ''
  try {
    drugs.value = await getDrugCatalog()
    const next = drugs.value.find((item) => item.drug_id === selectDrugId) ?? drugs.value[0]
    if (next) openDrug(next)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load drug catalog.'
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
      successMessage.value = 'Drug catalog item updated. Audit log is recorded by backend.'
      await loadDrugs(updated.drug_id)
    } else {
      const created = await createDrugCatalogItem(payload)
      successMessage.value = 'Drug catalog item created. Audit log is recorded by backend.'
      await loadDrugs(created.drug_id)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to save drug catalog item.'
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
  return status === 'active' ? 'Active' : 'Inactive'
}

function yesNo(value: boolean): string {
  return value ? 'Yes' : 'No'
}

function formatTime(value: string): string {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function drugRowClass({ row }: { row: DrugCatalogRecord }) {
  return row.drug_id === selectedDrugId.value ? 'selected-row' : ''
}

onMounted(() => {
  void loadDrugs()
})
</script>

<template>
  <section class="workspace-page drug-catalog-page">
    <el-page-header class="module-page-header" title="Medication module" content="Drug Catalog" />

    <el-card shadow="never" class="module-card">
      <template #header>
        <div class="module-header">
          <div>
            <p class="eyebrow">Medication management</p>
            <h2>Drug Catalog</h2>
            <p>维护慢病诊疗常用药品目录、剂型规格、处方标识、管制标识和启用状态。</p>
          </div>
          <div class="header-actions">
            <el-button @click="resetEditor">New drug</el-button>
            <el-button type="primary" :loading="saving" @click="saveDrug">
              {{ isEditing ? 'Save changes' : 'Create drug' }}
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="12" class="summary-row">
        <el-col :xs="24" :sm="8">
          <el-statistic title="Total drugs" :value="drugs.length" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-statistic title="Active drugs" :value="activeCount" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-statistic title="Controlled drugs" :value="controlledCount" />
        </el-col>
      </el-row>

      <el-alert
        v-if="errorMessage"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
        class="module-alert"
      />
      <el-alert
        v-else-if="successMessage"
        :title="successMessage"
        type="success"
        show-icon
        :closable="false"
        class="module-alert"
      />
    </el-card>

    <section class="module-grid">
      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <div>
              <h3>Catalog List</h3>
              <span>{{ filteredDrugs.length }} visible rows</span>
            </div>
            <el-button :loading="loading" @click="loadDrugs()">Refresh</el-button>
          </div>
        </template>

        <el-form label-position="top" class="filter-form">
          <el-row :gutter="12">
            <el-col :xs="24" :md="8">
              <el-form-item label="Keyword">
                <el-input v-model="keyword" clearable placeholder="Drug ID / generic / indication" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-form-item label="Status">
                <el-select v-model="statusFilter" class="full-width">
                  <el-option label="All" value="all" />
                  <el-option label="Active" value="active" />
                  <el-option label="Inactive" value="inactive" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-form-item label="Dosage form">
                <el-input v-model="dosageFormFilter" clearable placeholder="tablet / capsule / injection" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-form-item label="Prescription">
                <el-select v-model="prescriptionFilter" class="full-width">
                  <el-option label="All" value="all" />
                  <el-option label="Prescription only" value="yes" />
                  <el-option label="Non-prescription" value="no" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-form-item label="Controlled drug">
                <el-select v-model="controlledFilter" class="full-width">
                  <el-option label="All" value="all" />
                  <el-option label="Controlled only" value="yes" />
                  <el-option label="Non-controlled" value="no" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="8" class="filter-actions">
              <el-button @click="clearFilters">Clear filters</el-button>
            </el-col>
          </el-row>
        </el-form>

        <el-table
          v-loading="loading"
          :data="filteredDrugs"
          :row-class-name="drugRowClass"
          border
          stripe
          empty-text="No drug matches current filters."
          @row-click="openDrug"
        >
          <el-table-column prop="drug_id" label="Drug ID" min-width="150" />
          <el-table-column label="Drug" min-width="240">
            <template #default="{ row }">
              <strong>{{ row.generic_name }}</strong>
              <p class="table-subtitle">{{ row.brand_name || 'No brand name' }} / {{ row.indication }}</p>
            </template>
          </el-table-column>
          <el-table-column label="Form" min-width="170">
            <template #default="{ row }">{{ row.dosage_form }} / {{ row.specification }}</template>
          </el-table-column>
          <el-table-column label="Flags" min-width="170">
            <template #default="{ row }">
              <el-tag v-if="row.is_prescription" size="small">Rx</el-tag>
              <el-tag v-if="row.is_controlled" size="small" type="warning" class="tag-gap">Controlled</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Status" width="110">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'danger'" effect="light">
                {{ statusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <div>
              <h3>{{ isEditing ? 'Drug Details' : 'Create Drug' }}</h3>
              <span>Backend keeps validation, audit and controlled-drug permission checks authoritative.</span>
            </div>
            <el-tag :type="form.status === 'active' ? 'success' : 'danger'">{{ statusText(form.status) }}</el-tag>
          </div>
        </template>

        <el-alert
          v-if="form.is_controlled"
          title="This action involves a controlled drug. The backend will reject it unless the current role has controlled-drug permission."
          type="warning"
          show-icon
          :closable="false"
          class="module-alert"
        />

        <el-descriptions v-if="selectedDrug" :column="2" border class="detail-descriptions">
          <el-descriptions-item label="Updated at">{{ formatTime(selectedDrug.updated_at) }}</el-descriptions-item>
          <el-descriptions-item label="Updated by">{{ selectedDrug.updated_by || '--' }}</el-descriptions-item>
          <el-descriptions-item label="Prescription">{{ yesNo(selectedDrug.is_prescription) }}</el-descriptions-item>
          <el-descriptions-item label="Controlled">{{ yesNo(selectedDrug.is_controlled) }}</el-descriptions-item>
        </el-descriptions>

        <el-form label-position="top" class="editor-form">
          <el-row :gutter="12">
            <el-col :xs="24" :md="12">
              <el-form-item label="Drug ID">
                <el-input v-model="form.drug_id" :disabled="isEditing" placeholder="drug-metformin" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Generic name">
                <el-input v-model="form.generic_name" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Brand name">
                <el-input v-model="form.brand_name" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Dosage form">
                <el-input v-model="form.dosage_form" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Specification">
                <el-input v-model="form.specification" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Unit">
                <el-input v-model="form.unit" />
              </el-form-item>
            </el-col>
            <el-col :xs="24">
              <el-form-item label="Indication">
                <el-input v-model="form.indication" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-form-item label="Status">
                <el-select v-model="form.status" class="full-width">
                  <el-option label="Active" value="active" />
                  <el-option label="Inactive" value="inactive" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-form-item label="Prescription drug">
                <el-switch v-model="form.is_prescription" active-text="Yes" inactive-text="No" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-form-item label="Controlled drug">
                <el-switch v-model="form.is_controlled" active-text="Yes" inactive-text="No" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <div class="editor-actions">
          <el-button @click="resetEditor">Reset</el-button>
          <el-button type="primary" :loading="saving" @click="saveDrug">
            {{ isEditing ? 'Save changes' : 'Create drug' }}
          </el-button>
        </div>
      </el-card>
    </section>
  </section>
</template>

<style scoped>
.drug-catalog-page {
  display: grid;
  gap: 24px;
}

.module-page-header {
  padding: 4px 0;
}

.module-card {
  border-radius: 8px;
}

.module-header,
.section-header,
.header-actions,
.editor-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.module-header h2,
.module-header p,
.section-header h3,
.section-header span,
.table-subtitle {
  margin: 0;
}

.eyebrow {
  margin: 0 0 4px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.module-header p,
.section-header span,
.table-subtitle {
  color: #64748b;
  font-size: 12px;
}

.summary-row,
.module-alert,
.filter-form,
.editor-form,
.detail-descriptions {
  margin-top: 14px;
}

.module-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(360px, 0.75fr);
  gap: 24px;
  align-items: start;
}

.full-width {
  width: 100%;
}

.filter-actions {
  display: flex;
  align-items: flex-end;
}

.tag-gap {
  margin-left: 6px;
}

.editor-actions {
  justify-content: flex-end;
  margin-top: 12px;
}

:deep(.selected-row) {
  --el-table-tr-bg-color: #eff6ff;
}

@media (max-width: 1180px) {
  .module-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .module-header,
  .section-header,
  .header-actions {
    display: grid;
  }
}
</style>
