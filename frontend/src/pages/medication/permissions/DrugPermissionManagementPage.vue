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
const roleLabels: Record<DrugPermissionRole, string> = {
  doctor: 'Doctor',
  nurse: 'Nurse',
  pharmacist: 'Pharmacist',
  archivist: 'Archivist',
  admin: 'Admin',
}

const loading = ref(false)
const saving = ref(false)
const editorVisible = ref(false)
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

const configuredRoles = computed(() => records.value.length)
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

function applyEmptyRole(role: DrugPermissionRole) {
  selectedRole.value = role
  form.role = role
  form.allow_view = false
  form.allow_prescribe = false
  form.allow_review = false
  form.allow_execute = false
  form.allow_controlled_drug = false
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

async function openRole(role: DrugPermissionRole, showEditor = true) {
  selectedRole.value = role
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const record = await getDrugPermissionItem(role)
    applyRecord(record)
  } catch (error) {
    applyEmptyRole(role)
    errorMessage.value = error instanceof Error ? error.message : 'Role permission is not configured yet.'
  } finally {
    editorVisible.value = showEditor
  }
}

function openRecord(row: DrugPermissionRecord) {
  void openRole(row.role)
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
      successMessage.value = 'Permission updated. Backend audit remains authoritative.'
    } else {
      await createDrugPermissionItem(payload)
      successMessage.value = 'Permission created. Backend audit remains authoritative.'
    }
    await loadPermissions(payload.role)
    editorVisible.value = false
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

function roleLabel(role: DrugPermissionRole): string {
  return roleLabels[role] ?? role
}

function rowClass({ row }: { row: DrugPermissionRecord }) {
  return row.role === selectedRole.value ? 'selected-row' : ''
}

watch(roleFilter, () => {
  if (roleFilter.value !== 'all') {
    void openRole(roleFilter.value, false)
  }
})

onMounted(() => {
  void loadPermissions()
})
</script>

<template>
  <section class="workspace-page drug-permission-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">Medication governance</p>
        <h1>Drug Permission Matrix</h1>
        <p>Configure role-level medication visibility, prescribing, review, execution, and controlled-drug access.</p>
      </div>
      <div class="header-actions">
        <el-select v-model="roleFilter" class="role-filter">
          <el-option label="All roles" value="all" />
          <el-option v-for="role in roleOptions" :key="role" :label="roleLabel(role)" :value="role" />
        </el-select>
        <el-button :loading="loading" @click="loadPermissions()">Refresh</el-button>
      </div>
    </header>

    <section class="metric-grid four">
      <article class="metric-card">
        <span>Configured roles</span>
        <strong>{{ configuredRoles }}</strong>
      </article>
      <article class="metric-card">
        <span>Controlled access</span>
        <strong>{{ controlledRoles }}</strong>
      </article>
      <article class="metric-card">
        <span>Review roles</span>
        <strong>{{ reviewRoles }}</strong>
      </article>
      <article class="metric-card">
        <span>Execute roles</span>
        <strong>{{ executeRoles }}</strong>
      </article>
    </section>

    <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />
    <el-alert v-else-if="successMessage" :title="successMessage" type="success" show-icon :closable="false" />

    <el-card shadow="never" class="module-card">
      <template #header>
        <div class="section-header">
          <div>
            <h3>Role Permission Matrix</h3>
            <span>{{ filteredRecords.length }} visible role records. Click a role to edit.</span>
          </div>
          <el-button type="primary" plain @click="openRole(selectedRole)">Edit selected role</el-button>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="filteredRecords"
        :row-class-name="rowClass"
        border
        stripe
        empty-text="No role permission record found."
        @row-click="openRecord"
      >
        <el-table-column label="Role" min-width="130">
          <template #default="{ row }">
            <strong>{{ roleLabel(row.role) }}</strong>
            <p class="table-subtitle">{{ row.role }}</p>
          </template>
        </el-table-column>
        <el-table-column label="View catalog" width="120">
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
        <el-table-column label="Controlled drug" min-width="150">
          <template #default="{ row }">
            <el-tag :type="row.allow_controlled_drug ? 'warning' : 'info'" effect="light">
              {{ yesNo(row.allow_controlled_drug) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="editorVisible" title="Edit Role Permission" width="560px">
      <div class="dialog-body">
        <el-alert
          v-if="form.allow_controlled_drug"
          title="Controlled-drug permission is sensitive. Backend RBAC and audit remain the source of truth."
          type="warning"
          show-icon
          :closable="false"
        />

        <el-form label-position="top" class="editor-form">
          <el-form-item label="Role">
            <el-select v-model="form.role" class="full-width">
              <el-option v-for="role in roleOptions" :key="role" :label="roleLabel(role)" :value="role" />
            </el-select>
          </el-form-item>

          <div class="switch-list">
            <label class="switch-row">
              <span>
                <strong>View catalog and medication</strong>
                <small>Allows reading drug catalog and patient medication information.</small>
              </span>
              <el-switch v-model="form.allow_view" />
            </label>
            <label class="switch-row">
              <span>
                <strong>Prescribe</strong>
                <small>Allows creating or editing patient medication records.</small>
              </span>
              <el-switch v-model="form.allow_prescribe" />
            </label>
            <label class="switch-row">
              <span>
                <strong>Review</strong>
                <small>Allows pharmacist-style medication review.</small>
              </span>
              <el-switch v-model="form.allow_review" />
            </label>
            <label class="switch-row">
              <span>
                <strong>Execute</strong>
                <small>Allows nursing execution or medication follow-up work.</small>
              </span>
              <el-switch v-model="form.allow_execute" />
            </label>
            <label class="switch-row controlled">
              <span>
                <strong>Controlled drug access</strong>
                <small>Allows access to controlled-drug catalog and permission actions.</small>
              </span>
              <el-switch v-model="form.allow_controlled_drug" />
            </label>
          </div>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="editorVisible = false">Cancel</el-button>
        <el-button @click="resetForm">Reset</el-button>
        <el-button type="primary" :loading="saving" @click="savePermission">Save permission</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.drug-permission-page,
.dialog-body {
  display: grid;
  gap: 24px;
}

.module-card {
  border-radius: 8px;
}

.section-header,
.header-actions,
.switch-row {
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
.table-subtitle,
.switch-row small {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.role-filter {
  width: 180px;
}

.full-width {
  width: 100%;
}

.editor-form {
  margin-top: 2px;
}

.switch-list {
  display: grid;
  gap: 10px;
}

.switch-row {
  align-items: center;
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  padding: 12px;
}

.switch-row span {
  display: grid;
  gap: 3px;
}

.switch-row.controlled {
  border-color: #f59e0b;
  background: #fffbeb;
}

:deep(.selected-row) {
  --el-table-tr-bg-color: #eff6ff;
}

@media (max-width: 720px) {
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
