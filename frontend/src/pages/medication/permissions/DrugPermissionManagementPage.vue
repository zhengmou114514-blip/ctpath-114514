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
const reviewRoles = computed(() => records.value.filter((item) => item.allow_review).length)
const executeRoles = computed(() => records.value.filter((item) => item.allow_execute).length)

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
      successMessage.value = 'Permission updated. Audit log is recorded by backend.'
    } else {
      await createDrugPermissionItem(payload)
      successMessage.value = 'Permission created. Audit log is recorded by backend.'
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

function permissionTagType(value: boolean) {
  return value ? 'success' : 'info'
}

function rowClass({ row }: { row: DrugPermissionRecord }) {
  return row.role === selectedRole.value ? 'selected-row' : ''
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
    <el-page-header class="module-page-header" title="Medication module" content="Drug Permission Management" />

    <el-card shadow="never" class="module-card">
      <template #header>
        <div class="module-header">
          <div>
            <p class="eyebrow">Medication governance</p>
            <h2>Drug Permission Management</h2>
            <p>Configure role-level medication permissions separately from patient detail and drug catalog maintenance.</p>
          </div>
          <div class="header-actions">
            <el-button @click="resetForm">Reset role</el-button>
            <el-button type="primary" :loading="saving" @click="savePermission">Save permission</el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="12" class="summary-row">
        <el-col :xs="24" :sm="6">
          <el-statistic title="Configured roles" :value="records.length" />
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-statistic title="Controlled-drug roles" :value="controlledRoles" />
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-statistic title="Review roles" :value="reviewRoles" />
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-statistic title="Execute roles" :value="executeRoles" />
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

    <section class="permission-grid">
      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <div>
              <h3>Permission Matrix</h3>
              <span>{{ filteredRecords.length }} visible role records</span>
            </div>
            <el-select v-model="roleFilter" class="role-filter">
              <el-option label="All roles" value="all" />
              <el-option v-for="role in roleOptions" :key="role" :label="role" :value="role" />
            </el-select>
          </div>
        </template>

        <el-table
          v-loading="loading"
          :data="filteredRecords"
          :row-class-name="rowClass"
          border
          stripe
          empty-text="No role permission record found."
          @row-click="(row: DrugPermissionRecord) => openRole(row.role)"
        >
          <el-table-column prop="role" label="Role" min-width="120" />
          <el-table-column label="View" width="105">
            <template #default="{ row }">
              <el-tag :type="permissionTagType(row.allow_view)" effect="light">{{ yesNo(row.allow_view) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Prescribe" width="120">
            <template #default="{ row }">
              <el-tag :type="permissionTagType(row.allow_prescribe)" effect="light">{{ yesNo(row.allow_prescribe) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Review" width="110">
            <template #default="{ row }">
              <el-tag :type="permissionTagType(row.allow_review)" effect="light">{{ yesNo(row.allow_review) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Execute" width="110">
            <template #default="{ row }">
              <el-tag :type="permissionTagType(row.allow_execute)" effect="light">{{ yesNo(row.allow_execute) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="Controlled drug" min-width="140">
            <template #default="{ row }">
              <el-tag :type="row.allow_controlled_drug ? 'warning' : 'info'" effect="light">
                {{ yesNo(row.allow_controlled_drug) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <div>
              <h3>Role Permission Editor</h3>
              <span>All changes are saved through backend audit and permission guards.</span>
            </div>
            <el-tag>{{ form.role }}</el-tag>
          </div>
        </template>

        <el-alert
          v-if="form.allow_controlled_drug"
          title="Granting controlled-drug permission is a controlled action. Backend permission checks remain authoritative."
          type="warning"
          show-icon
          :closable="false"
          class="module-alert"
        />

        <el-form label-position="top" class="editor-form">
          <el-form-item label="Role">
            <el-select v-model="form.role" class="full-width">
              <el-option v-for="role in roleOptions" :key="role" :label="role" :value="role" />
            </el-select>
          </el-form-item>

          <el-divider content-position="left">Permission switches</el-divider>

          <div class="switch-list">
            <label class="switch-row">
              <span>
                <strong>View</strong>
                <small>View drug catalog and patient medication information.</small>
              </span>
              <el-switch v-model="form.allow_view" />
            </label>
            <label class="switch-row">
              <span>
                <strong>Prescribe</strong>
                <small>Create or edit current medication records.</small>
              </span>
              <el-switch v-model="form.allow_prescribe" />
            </label>
            <label class="switch-row">
              <span>
                <strong>Review</strong>
                <small>Perform pharmacist-style medication review.</small>
              </span>
              <el-switch v-model="form.allow_review" />
            </label>
            <label class="switch-row">
              <span>
                <strong>Execute</strong>
                <small>View or execute nursing medication-related work.</small>
              </span>
              <el-switch v-model="form.allow_execute" />
            </label>
            <label class="switch-row controlled">
              <span>
                <strong>Controlled drug</strong>
                <small>Allow controlled-drug catalog or permission actions.</small>
              </span>
              <el-switch v-model="form.allow_controlled_drug" />
            </label>
          </div>
        </el-form>

        <div class="editor-actions">
          <el-button @click="resetForm">Reset</el-button>
          <el-button type="primary" :loading="saving" @click="savePermission">Save permission</el-button>
        </div>
      </el-card>
    </section>
  </section>
</template>

<style scoped>
.drug-permission-page {
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
.editor-actions,
.switch-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.module-header h2,
.module-header p,
.section-header h3,
.section-header span {
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
.switch-row small {
  color: #64748b;
  font-size: 12px;
}

.summary-row,
.module-alert,
.editor-form {
  margin-top: 14px;
}

.permission-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(360px, 0.85fr);
  gap: 24px;
  align-items: start;
}

.role-filter {
  width: 180px;
}

.full-width {
  width: 100%;
}

.switch-list {
  display: grid;
  gap: 10px;
}

.switch-row {
  align-items: center;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
}

.switch-row span {
  display: grid;
  gap: 3px;
}

.switch-row.controlled {
  border-color: #fed7aa;
  background: #fff7ed;
}

.editor-actions {
  justify-content: flex-end;
  margin-top: 14px;
}

:deep(.selected-row) {
  --el-table-tr-bg-color: #eff6ff;
}

@media (max-width: 1180px) {
  .permission-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .module-header,
  .section-header,
  .header-actions,
  .switch-row {
    display: grid;
  }

  .role-filter {
    width: 100%;
  }
}
</style>
