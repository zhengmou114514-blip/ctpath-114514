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
      successMessage.value = 'Drug catalog item updated. Audit log recorded by backend.'
      await loadDrugs(updated.drug_id)
    } else {
      const created = await createDrugCatalogItem(payload)
      successMessage.value = 'Drug catalog item created. Audit log recorded by backend.'
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

onMounted(() => {
  void loadDrugs()
})
</script>

<template>
  <section class="workspace-page drug-catalog-page">
    <header class="card page-header">
      <div>
        <p class="eyebrow">Medication management</p>
        <h2>Drug Catalog</h2>
        <p>Maintain the minimum chronic-care drug directory: generic name, brand, dosage form, specification, status and controlled-drug flag.</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="resetEditor">New drug</button>
        <button class="primary-button" type="button" :disabled="saving" @click="saveDrug">
          {{ saving ? 'Saving...' : isEditing ? 'Save changes' : 'Create drug' }}
        </button>
      </div>
    </header>

    <section class="summary-strip">
      <article class="card metric-card">
        <span>Total drugs</span>
        <strong>{{ drugs.length }}</strong>
      </article>
      <article class="card metric-card">
        <span>Controlled drugs</span>
        <strong>{{ controlledCount }}</strong>
      </article>
      <article class="card metric-card">
        <span>Visible rows</span>
        <strong>{{ filteredDrugs.length }}</strong>
      </article>
    </section>

    <section v-if="errorMessage" class="card message-card error">{{ errorMessage }}</section>
    <section v-else-if="successMessage" class="card message-card success">{{ successMessage }}</section>

    <section class="drug-layout">
      <article class="card panel list-panel">
        <div class="panel-head">
          <div>
            <h3>Catalog List</h3>
            <p>Use filters before editing a drug item.</p>
          </div>
          <button class="secondary-button" type="button" :disabled="loading" @click="loadDrugs()">
            {{ loading ? 'Refreshing...' : 'Refresh' }}
          </button>
        </div>

        <div class="filter-grid">
          <label class="field">
            <span>Keyword</span>
            <input v-model="keyword" type="text" placeholder="drug id / generic / indication" />
          </label>
          <label class="field">
            <span>Status</span>
            <select v-model="statusFilter">
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </label>
          <label class="field">
            <span>Dosage form</span>
            <input v-model="dosageFormFilter" type="text" placeholder="tablet / capsule / injection" />
          </label>
          <label class="field">
            <span>Prescription</span>
            <select v-model="prescriptionFilter">
              <option value="all">All</option>
              <option value="yes">Prescription only</option>
              <option value="no">Non-prescription</option>
            </select>
          </label>
          <label class="field">
            <span>Controlled drug</span>
            <select v-model="controlledFilter">
              <option value="all">All</option>
              <option value="yes">Controlled only</option>
              <option value="no">Non-controlled</option>
            </select>
          </label>
          <div class="filter-actions">
            <button class="secondary-button" type="button" @click="clearFilters">Clear filters</button>
          </div>
        </div>

        <div v-if="loading" class="empty-state compact">Loading drug catalog...</div>
        <div v-else-if="!filteredDrugs.length" class="empty-state compact">No drug matches current filters.</div>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Drug ID</th>
                <th>Drug</th>
                <th>Form</th>
                <th>Flags</th>
                <th>Status</th>
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
                  <p>{{ drug.brand_name || 'No brand name' }} / {{ drug.indication }}</p>
                </td>
                <td>{{ drug.dosage_form }} / {{ drug.specification }}</td>
                <td>
                  <span v-if="drug.is_prescription" class="tag">Rx</span>
                  <span v-if="drug.is_controlled" class="tag warning">Controlled</span>
                </td>
                <td><span class="status-badge" :class="drug.status">{{ statusText(drug.status) }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="card panel editor-panel">
        <div class="panel-head">
          <div>
            <h3>{{ isEditing ? 'Drug Details' : 'Create Drug' }}</h3>
            <p>Controlled-drug changes are checked by backend permission rules.</p>
          </div>
          <span class="status-badge" :class="selectedDrug?.status ?? form.status">{{ selectedDrug ? statusText(selectedDrug.status) : statusText(form.status) }}</span>
        </div>

        <div v-if="form.is_controlled" class="controlled-notice">
          This action involves a controlled drug. The backend will reject it unless the current role has controlled-drug permission.
        </div>

        <div class="detail-summary" v-if="selectedDrug">
          <p><span>Updated at</span><strong>{{ formatTime(selectedDrug.updated_at) }}</strong></p>
          <p><span>Updated by</span><strong>{{ selectedDrug.updated_by || '--' }}</strong></p>
          <p><span>Prescription</span><strong>{{ yesNo(selectedDrug.is_prescription) }}</strong></p>
          <p><span>Controlled</span><strong>{{ yesNo(selectedDrug.is_controlled) }}</strong></p>
        </div>

        <div class="edit-grid">
          <label class="field">
            <span>Drug ID</span>
            <input v-model="form.drug_id" :disabled="isEditing" type="text" placeholder="drug-metformin" />
          </label>
          <label class="field">
            <span>Generic name</span>
            <input v-model="form.generic_name" type="text" />
          </label>
          <label class="field">
            <span>Brand name</span>
            <input v-model="form.brand_name" type="text" />
          </label>
          <label class="field">
            <span>Dosage form</span>
            <input v-model="form.dosage_form" type="text" />
          </label>
          <label class="field">
            <span>Specification</span>
            <input v-model="form.specification" type="text" />
          </label>
          <label class="field">
            <span>Unit</span>
            <input v-model="form.unit" type="text" />
          </label>
          <label class="field wide">
            <span>Indication</span>
            <input v-model="form.indication" type="text" />
          </label>
          <label class="field">
            <span>Status</span>
            <select v-model="form.status">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </label>
          <label class="field">
            <span>Prescription drug</span>
            <select v-model="form.is_prescription">
              <option :value="true">Yes</option>
              <option :value="false">No</option>
            </select>
          </label>
          <label class="field">
            <span>Controlled drug</span>
            <select v-model="form.is_controlled">
              <option :value="true">Yes</option>
              <option :value="false">No</option>
            </select>
          </label>
        </div>

        <div class="detail-actions">
          <button class="secondary-button" type="button" @click="resetEditor">Reset</button>
          <button class="primary-button" type="button" :disabled="saving" @click="saveDrug">
            {{ saving ? 'Saving...' : isEditing ? 'Save changes' : 'Create drug' }}
          </button>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.summary-strip,
.drug-layout {
  display: grid;
  gap: 16px;
}

.summary-strip {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.drug-layout {
  grid-template-columns: minmax(0, 1.25fr) minmax(360px, 0.75fr);
  align-items: start;
}

.eyebrow {
  margin: 0 0 4px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.metric-card {
  display: grid;
  gap: 4px;
}

.metric-card span,
.panel-head p,
.field span,
.detail-summary span {
  color: #64748b;
  font-size: 12px;
}

.metric-card strong {
  color: #0f172a;
  font-size: 24px;
}

.message-card {
  border-left: 4px solid #2563eb;
}

.message-card.error {
  border-left-color: #dc2626;
  color: #991b1b;
}

.message-card.success {
  border-left-color: #16a34a;
  color: #166534;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.panel-head h3 {
  margin: 0;
}

.filter-grid,
.edit-grid,
.detail-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.field {
  display: grid;
  gap: 6px;
}

.field.wide,
.filter-actions,
.detail-actions {
  grid-column: 1 / -1;
}

.filter-actions,
.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.field input,
.field select {
  width: 100%;
}

.table-wrap {
  margin-top: 16px;
  overflow: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  text-align: left;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  padding: 11px 10px;
  vertical-align: top;
}

tbody tr {
  cursor: pointer;
}

tbody tr.active {
  background: rgba(37, 99, 235, 0.08);
}

td p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 12px;
}

.tag,
.status-badge {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 700;
}

.tag {
  margin-right: 4px;
  background: #e0f2fe;
  color: #075985;
}

.tag.warning,
.controlled-notice {
  background: #fff7ed;
  color: #9a3412;
}

.status-badge.active {
  background: rgba(34, 197, 94, 0.14);
  color: #15803d;
}

.status-badge.inactive {
  background: rgba(248, 113, 113, 0.14);
  color: #b91c1c;
}

.controlled-notice {
  border: 1px solid #fed7aa;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 14px;
  font-size: 13px;
}

.detail-summary {
  margin-bottom: 16px;
}

.detail-summary p {
  margin: 0;
  display: grid;
  gap: 4px;
}

@media (max-width: 1120px) {
  .summary-strip,
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
