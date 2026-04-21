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
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load medication catalog.'
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
      successMessage.value = 'Medication updated.'
      await loadDrugs(updated.drug_id)
    } else {
      const created = await createDrugCatalogItem(payload)
      successMessage.value = 'Medication created.'
      await loadDrugs(created.drug_id)
    }
    editorVisible.value = false
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to save medication.'
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
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">Medication management</p>
        <h1>Medication Catalog</h1>
        <p>Maintain the chronic-care medication dictionary, prescription flags, controlled-drug flags, and catalog status.</p>
      </div>
      <div class="header-actions">
        <el-button @click="clearFilters">Reset filters</el-button>
        <el-button type="primary" @click="resetEditor">New medication</el-button>
      </div>
    </header>

    <section class="metric-grid three">
      <article class="metric-card">
        <span>Total medications</span>
        <strong>{{ drugs.length }}</strong>
      </article>
      <article class="metric-card">
        <span>Active</span>
        <strong>{{ activeCount }}</strong>
      </article>
      <article class="metric-card">
        <span>Controlled</span>
        <strong>{{ controlledCount }}</strong>
      </article>
    </section>

    <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />
    <el-alert v-else-if="successMessage" :title="successMessage" type="success" show-icon :closable="false" />

    <el-card shadow="never" class="module-card">
      <template #header>
        <div class="section-header">
          <div>
            <h3>Catalog Table</h3>
            <span>{{ filteredDrugs.length }} matching records</span>
          </div>
          <el-button :loading="loading" @click="loadDrugs()">Refresh</el-button>
        </div>
      </template>

      <el-form label-position="top" class="filter-form">
        <el-row :gutter="12">
          <el-col :xs="24" :md="8">
            <el-form-item label="Keyword">
              <el-input v-model="keyword" clearable placeholder="Drug ID / generic name / indication" />
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
            <el-form-item label="Controlled">
              <el-select v-model="controlledFilter" class="full-width">
                <el-option label="All" value="all" />
                <el-option label="Controlled only" value="yes" />
                <el-option label="Non-controlled" value="no" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8" class="filter-actions">
            <el-button @click="clearFilters">Clear</el-button>
          </el-col>
        </el-row>
      </el-form>

      <el-table
        v-loading="loading"
        :data="filteredDrugs"
        :row-class-name="drugRowClass"
        border
        stripe
        empty-text="No medication records."
        @row-click="openDrug"
      >
        <el-table-column prop="drug_id" label="Drug ID" min-width="150" />
        <el-table-column label="Medication" min-width="240">
          <template #default="{ row }">
            <strong>{{ row.generic_name }}</strong>
            <p class="table-subtitle">{{ row.brand_name || 'No brand' }} / {{ row.indication }}</p>
          </template>
        </el-table-column>
        <el-table-column label="Form / Spec" min-width="170">
          <template #default="{ row }">{{ row.dosage_form }} / {{ row.specification }}</template>
        </el-table-column>
        <el-table-column label="Flags" min-width="180">
          <template #default="{ row }">
            <el-tag v-if="row.is_prescription" size="small">Prescription</el-tag>
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

    <el-drawer v-model="editorVisible" :title="isEditing ? 'Medication Detail / Edit' : 'New Medication'" size="520px">
      <div class="drawer-body">
        <el-alert
          v-if="form.is_controlled"
          title="Controlled medication requires matching role permissions before use in clinical workflows."
          type="warning"
          show-icon
          :closable="false"
        />

        <el-descriptions v-if="selectedDrug" :column="2" border>
          <el-descriptions-item label="Updated at">{{ formatTime(selectedDrug.updated_at) }}</el-descriptions-item>
          <el-descriptions-item label="Updated by">{{ selectedDrug.updated_by || '--' }}</el-descriptions-item>
          <el-descriptions-item label="Prescription">{{ yesNo(selectedDrug.is_prescription) }}</el-descriptions-item>
          <el-descriptions-item label="Controlled">{{ yesNo(selectedDrug.is_controlled) }}</el-descriptions-item>
        </el-descriptions>

        <el-form label-position="top" class="editor-form">
          <el-row :gutter="12">
            <el-col :xs="24" :md="12">
              <el-form-item label="Drug ID"><el-input v-model="form.drug_id" :disabled="isEditing" placeholder="drug-metformin" /></el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Generic name"><el-input v-model="form.generic_name" /></el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Brand name"><el-input v-model="form.brand_name" /></el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Dosage form"><el-input v-model="form.dosage_form" /></el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Specification"><el-input v-model="form.specification" /></el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="Unit"><el-input v-model="form.unit" /></el-form-item>
            </el-col>
            <el-col :xs="24">
              <el-form-item label="Indication"><el-input v-model="form.indication" /></el-form-item>
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
              <el-form-item label="Prescription"><el-switch v-model="form.is_prescription" active-text="Yes" inactive-text="No" /></el-form-item>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-form-item label="Controlled"><el-switch v-model="form.is_controlled" active-text="Yes" inactive-text="No" /></el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <div class="editor-actions">
          <el-button @click="editorVisible = false">Cancel</el-button>
          <el-button type="primary" :loading="saving" @click="saveDrug">
            {{ isEditing ? 'Save changes' : 'Create medication' }}
          </el-button>
        </div>
      </div>
    </el-drawer>
  </section>
</template>

<style scoped>
.drug-catalog-page,
.drawer-body {
  display: grid;
  gap: 24px;
}

.module-card {
  border-radius: 8px;
}

.section-header,
.header-actions,
.editor-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-header h3,
.section-header span,
.table-subtitle {
  margin: 0;
}

.section-header span,
.table-subtitle {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.filter-form,
.editor-form {
  margin-top: 14px;
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
}

:deep(.selected-row) {
  --el-table-tr-bg-color: #eff6ff;
}

@media (max-width: 720px) {
  .section-header,
  .header-actions {
    display: grid;
  }
}
</style>
