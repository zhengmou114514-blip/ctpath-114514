<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  createDrugPermissionItem,
  getDrugPermissionItem,
  getDrugPermissions,
  updateDrugPermissionItem,
} from '../../../services/api'
import type { DrugPermissionRecord, DrugPermissionRole, DrugPermissionUpsertRequest } from '../../../services/types'

const roleOptions: DrugPermissionRole[] = ['doctor', 'nurse', 'pharmacist', 'archivist', 'admin']

const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const roleFilter = ref<'all' | DrugPermissionRole>('all')
const selectedRole = ref<DrugPermissionRole>('doctor')
const records = ref<DrugPermissionRecord[]>([])

const form = reactive<DrugPermissionUpsertRequest>({
  role: 'doctor',
  allow_view: true,
  allow_prescribe: true,
  allow_review: false,
  allow_execute: false,
  allow_controlled_drug: true,
})

const filteredRecords = computed(() => {
  if (roleFilter.value === 'all') return records.value
  return records.value.filter((item) => item.role === roleFilter.value)
})

const controlledRoles = computed(() => records.value.filter((item) => item.allow_controlled_drug).length)

function applyRecord(record: DrugPermissionRecord) {
  selectedRole.value = record.role
  form.role = record.role
  form.allow_view = record.allow_view
  form.allow_prescribe = record.allow_prescribe
  form.allow_review = record.allow_review
  form.allow_execute = record.allow_execute
  form.allow_controlled_drug = record.allow_controlled_drug
}

async function loadPermissions(selectRole: DrugPermissionRole = selectedRole.value) {
  loading.value = true
  errorMessage.value = ''
  try {
    records.value = await getDrugPermissions()
    const next = records.value.find((item) => item.role === selectRole) ?? records.value[0]
    if (next) applyRecord(next)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load drug permissions.'
  } finally {
    loading.value = false
  }
}

async function openRole(role: DrugPermissionRole) {
  selectedRole.value = role
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const record = await getDrugPermissionItem(role)
    applyRecord(record)
  } catch (error) {
    form.role = role
    form.allow_view = false
    form.allow_prescribe = false
    form.allow_review = false
    form.allow_execute = false
    form.allow_controlled_drug = false
    errorMessage.value = error instanceof Error ? error.message : 'Role permission is not configured yet.'
  }
}

async function savePermission() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const payload = { ...form }
    const exists = records.value.some((item) => item.role === payload.role)
    if (exists) {
      await updateDrugPermissionItem(payload.role, payload)
      successMessage.value = 'Permission updated. Audit log recorded by backend.'
    } else {
      await createDrugPermissionItem(payload)
      successMessage.value = 'Permission created. Audit log recorded by backend.'
    }
    await loadPermissions(payload.role)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to save drug permission.'
  } finally {
    saving.value = false
  }
}

function resetForm() {
  void openRole(selectedRole.value)
}

function yesNo(value: boolean): string {
  return value ? 'Yes' : 'No'
}

watch(roleFilter, () => {
  if (roleFilter.value !== 'all') {
    void openRole(roleFilter.value)
  }
})

onMounted(() => {
  void loadPermissions()
})
</script>

<template>
  <section class="workspace-page drug-permission-page">
    <header class="card page-header">
      <div>
        <p class="eyebrow">Medication governance</p>
        <h2>Drug Permission Management</h2>
        <p>Configure role-level medication permissions separately from the drug catalog and patient details.</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="resetForm">Reset role</button>
        <button class="primary-button" type="button" :disabled="saving" @click="savePermission">
          {{ saving ? 'Saving...' : 'Save permission' }}
        </button>
      </div>
    </header>

    <section class="summary-strip">
      <article class="card metric-card">
        <span>Configured roles</span>
        <strong>{{ records.length }}</strong>
      </article>
      <article class="card metric-card">
        <span>Controlled-drug roles</span>
        <strong>{{ controlledRoles }}</strong>
      </article>
      <article class="card metric-card">
        <span>Current role</span>
        <strong>{{ form.role }}</strong>
      </article>
    </section>

    <section v-if="errorMessage" class="card message-card error">{{ errorMessage }}</section>
    <section v-else-if="successMessage" class="card message-card success">{{ successMessage }}</section>

    <section class="permission-layout">
      <article class="card panel list-panel">
        <div class="panel-head">
          <div>
            <h3>Permission List</h3>
            <p>Review by role before editing.</p>
          </div>
          <label class="field compact-field">
            <span>Role filter</span>
            <select v-model="roleFilter">
              <option value="all">All roles</option>
              <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
            </select>
          </label>
        </div>

        <div v-if="loading" class="empty-state compact">Loading permission matrix...</div>
        <div v-else-if="!filteredRecords.length" class="empty-state compact">No role permission record found.</div>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Role</th>
                <th>View</th>
                <th>Prescribe</th>
                <th>Review</th>
                <th>Execute</th>
                <th>Controlled</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in filteredRecords"
                :key="item.role"
                :class="{ active: item.role === selectedRole }"
                @click="openRole(item.role)"
              >
                <td><strong>{{ item.role }}</strong></td>
                <td>{{ yesNo(item.allow_view) }}</td>
                <td>{{ yesNo(item.allow_prescribe) }}</td>
                <td>{{ yesNo(item.allow_review) }}</td>
                <td>{{ yesNo(item.allow_execute) }}</td>
                <td>
                  <span class="controlled-pill" :class="{ enabled: item.allow_controlled_drug }">
                    {{ yesNo(item.allow_controlled_drug) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="card panel editor-panel">
        <div class="panel-head">
          <div>
            <h3>Role Permission Editor</h3>
            <p>Changes are audited through the backend operation audit entry.</p>
          </div>
        </div>

        <div v-if="form.allow_controlled_drug" class="controlled-notice">
          Granting controlled-drug permission is itself a controlled action. The backend will reject it if your role is not allowed.
        </div>

        <div class="edit-grid">
          <label class="field">
            <span>Role</span>
            <select v-model="form.role">
              <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
            </select>
          </label>

          <label class="check-field">
            <input v-model="form.allow_view" type="checkbox" />
            <span>Allow view drug catalog and patient medications</span>
          </label>

          <label class="check-field">
            <input v-model="form.allow_prescribe" type="checkbox" />
            <span>Allow prescribing or editing current medication</span>
          </label>

          <label class="check-field">
            <input v-model="form.allow_review" type="checkbox" />
            <span>Allow pharmacist-style medication review</span>
          </label>

          <label class="check-field">
            <input v-model="form.allow_execute" type="checkbox" />
            <span>Allow medication execution view/action</span>
          </label>

          <label class="check-field warning">
            <input v-model="form.allow_controlled_drug" type="checkbox" />
            <span>Allow controlled-drug operations</span>
          </label>
        </div>

        <div class="detail-actions">
          <button class="secondary-button" type="button" @click="resetForm">Reset</button>
          <button class="primary-button" type="button" :disabled="saving" @click="savePermission">
            {{ saving ? 'Saving...' : 'Save permission' }}
          </button>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.summary-strip,
.permission-layout {
  display: grid;
  gap: 16px;
}

.summary-strip {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.permission-layout {
  grid-template-columns: minmax(0, 1.15fr) minmax(360px, 0.85fr);
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
.field span {
  color: #64748b;
  font-size: 12px;
}

.metric-card strong {
  color: #0f172a;
  font-size: 22px;
  text-transform: capitalize;
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

.compact-field {
  min-width: 180px;
}

.field,
.edit-grid {
  display: grid;
  gap: 10px;
}

.field {
  gap: 6px;
}

.field select {
  width: 100%;
}

.table-wrap {
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
}

tbody tr {
  cursor: pointer;
}

tbody tr.active {
  background: rgba(37, 99, 235, 0.08);
}

.controlled-pill {
  display: inline-flex;
  border-radius: 999px;
  padding: 4px 8px;
  background: #f1f5f9;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.controlled-pill.enabled,
.controlled-notice,
.check-field.warning {
  background: #fff7ed;
  color: #9a3412;
}

.controlled-notice {
  border: 1px solid #fed7aa;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 14px;
  font-size: 13px;
}

.check-field {
  display: flex;
  gap: 10px;
  align-items: center;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 10px;
  padding: 10px 12px;
  color: #334155;
}

.check-field input {
  width: 16px;
  height: 16px;
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

@media (max-width: 1120px) {
  .summary-strip,
  .permission-layout {
    grid-template-columns: 1fr;
  }
}
</style>
