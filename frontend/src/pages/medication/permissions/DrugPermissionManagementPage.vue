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
  doctor: '医生',
  nurse: '护士',
  pharmacist: '药师',
  archivist: '档案员',
  admin: '管理员',
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
    errorMessage.value = error instanceof Error ? error.message : '药品权限加载失败。'
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
    errorMessage.value = error instanceof Error ? error.message : '当前角色尚未配置药品权限。'
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
      successMessage.value = '药品权限已更新，后端 RBAC 与审计仍为准。'
    } else {
      await createDrugPermissionItem(payload)
      successMessage.value = '药品权限已创建，后端 RBAC 与审计仍为准。'
    }
    await loadPermissions(payload.role)
    editorVisible.value = false
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '药品权限保存失败。'
  } finally {
    saving.value = false
  }
}

function resetForm() {
  void openRole(selectedRole.value)
}

function yesNo(value: boolean): string {
  return value ? '允许' : '禁止'
}

function roleLabel(role: DrugPermissionRole): string {
  return roleLabels[role] ?? role
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
        <p class="eyebrow">药品治理 / 角色权限</p>
        <h1>药品权限矩阵</h1>
        <p>维护医生、护士、药师、档案员与管理员的药品查看、开立、审核、执行和管制药访问权限。</p>
      </div>
      <div class="header-actions">
        <label class="field compact">
          <span>角色筛选</span>
          <select v-model="roleFilter">
            <option value="all">全部角色</option>
            <option v-for="role in roleOptions" :key="role" :value="role">{{ roleLabel(role) }}</option>
          </select>
        </label>
        <button class="secondary-button" type="button" :disabled="loading" @click="loadPermissions()">刷新权限</button>
      </div>
    </header>

    <section class="metric-grid four">
      <article class="metric-card">
        <span>已配置角色</span>
        <strong>{{ configuredRoles }}</strong>
      </article>
      <article class="metric-card">
        <span>可用管制药</span>
        <strong>{{ controlledRoles }}</strong>
      </article>
      <article class="metric-card">
        <span>具备审核权</span>
        <strong>{{ reviewRoles }}</strong>
      </article>
      <article class="metric-card">
        <span>具备执行权</span>
        <strong>{{ executeRoles }}</strong>
      </article>
    </section>

    <div v-if="errorMessage" class="inline-alert error">{{ errorMessage }}</div>
    <div v-else-if="successMessage" class="inline-alert success">{{ successMessage }}</div>

    <section class="permission-layout">
      <article class="clinical-card permission-table-card">
        <div class="section-header">
          <div>
            <h2>角色权限矩阵</h2>
            <p>当前展示 {{ filteredRecords.length }} 条权限记录，点击任一角色可直接编辑。</p>
          </div>
          <button class="primary-button" type="button" @click="openRole(selectedRole)">编辑当前角色</button>
        </div>

        <div v-if="!filteredRecords.length && !loading" class="empty-state-card compact">
          <h3>暂无权限记录</h3>
          <p>可以先选择一个角色并创建该角色的药品权限矩阵。</p>
        </div>

        <div v-else class="permission-table">
          <div class="permission-head">
            <span>角色</span>
            <span>查看</span>
            <span>开立</span>
            <span>审核</span>
            <span>执行</span>
            <span>管制药</span>
          </div>
          <button
            v-for="row in filteredRecords"
            :key="row.role"
            class="permission-row"
            :class="{ selected: row.role === selectedRole }"
            type="button"
            @click="openRecord(row)"
          >
            <div class="permission-cell role">
              <strong>{{ roleLabel(row.role) }}</strong>
              <span>{{ row.role }}</span>
            </div>
            <span class="permission-badge">{{ yesNo(row.allow_view) }}</span>
            <span class="permission-badge">{{ yesNo(row.allow_prescribe) }}</span>
            <span class="permission-badge">{{ yesNo(row.allow_review) }}</span>
            <span class="permission-badge">{{ yesNo(row.allow_execute) }}</span>
            <span class="permission-badge warning">{{ yesNo(row.allow_controlled_drug) }}</span>
          </button>
        </div>
      </article>

      <aside class="clinical-card permission-editor-card">
        <div class="section-header">
          <div>
            <h2>角色权限编辑</h2>
            <p>普通前端只负责展示与发起修改，最终仍以后端 RBAC 与审计结果为准。</p>
          </div>
        </div>

        <div class="editor-grid">
          <label class="field full-span">
            <span>角色</span>
            <select v-model="form.role">
              <option v-for="role in roleOptions" :key="role" :value="role">{{ roleLabel(role) }}</option>
            </select>
          </label>

          <label class="permission-switch-row">
            <div>
              <strong>查看药品目录</strong>
              <small>允许访问药品目录与患者当前用药信息。</small>
            </div>
            <input v-model="form.allow_view" type="checkbox" />
          </label>

          <label class="permission-switch-row">
            <div>
              <strong>开立用药</strong>
              <small>允许在患者用药闭环中新增或修改处方信息。</small>
            </div>
            <input v-model="form.allow_prescribe" type="checkbox" />
          </label>

          <label class="permission-switch-row">
            <div>
              <strong>审核用药</strong>
              <small>允许药师或审核角色执行处方审核。</small>
            </div>
            <input v-model="form.allow_review" type="checkbox" />
          </label>

          <label class="permission-switch-row">
            <div>
              <strong>执行用药</strong>
              <small>允许护士查看执行结果与随访执行记录。</small>
            </div>
            <input v-model="form.allow_execute" type="checkbox" />
          </label>

          <label class="permission-switch-row controlled">
            <div>
              <strong>管制药权限</strong>
              <small>允许查看和处理管制药范围内的药品及权限动作。</small>
            </div>
            <input v-model="form.allow_controlled_drug" type="checkbox" />
          </label>
        </div>

        <div class="form-actions">
          <button class="secondary-button" type="button" @click="resetForm">重置</button>
          <button class="primary-button" type="button" :disabled="saving" @click="savePermission">
            {{ saving ? '保存中...' : '保存权限' }}
          </button>
        </div>
      </aside>
    </section>
  </section>
</template>

<style scoped>
.drug-permission-page,
.permission-layout,
.editor-grid,
.permission-table {
  display: grid;
  gap: 22px;
}

.permission-layout {
  grid-template-columns: minmax(0, 1.5fr) minmax(340px, 0.95fr);
  align-items: start;
}

.permission-table-card,
.permission-editor-card {
  display: grid;
  gap: 18px;
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

.field {
  display: grid;
  gap: 8px;
}

.field.compact {
  min-width: 180px;
}

.field.full-span {
  grid-column: 1 / -1;
}

.field span {
  color: #3f4848;
  font-size: 13px;
  font-weight: 700;
}

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

.permission-head,
.permission-row {
  display: grid;
  grid-template-columns: 1.3fr repeat(5, minmax(0, 0.8fr));
  gap: 12px;
  align-items: center;
}

.permission-head {
  color: #61737b;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.permission-row {
  border: 1px solid rgba(205, 214, 218, 0.9);
  border-radius: 16px;
  background: #fff;
  padding: 16px;
  text-align: left;
}

.permission-row.selected {
  border-color: rgba(0, 92, 97, 0.35);
  box-shadow: 0 0 0 2px rgba(0, 92, 97, 0.08);
}

.permission-cell.role {
  display: grid;
  gap: 6px;
}

.permission-cell.role span {
  color: #61737b;
}

.permission-badge {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  padding: 6px 10px;
  background: rgba(237, 247, 238, 0.95);
  color: #2b5d36;
  font-size: 12px;
  font-weight: 700;
}

.permission-badge.warning {
  background: rgba(255, 243, 224, 0.92);
  color: #8a4b08;
}

.permission-switch-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid rgba(205, 214, 218, 0.9);
  border-radius: 16px;
  background: #fff;
  padding: 16px;
}

.permission-switch-row div {
  display: grid;
  gap: 4px;
}

.permission-switch-row small {
  color: #61737b;
  line-height: 1.6;
}

.permission-switch-row input {
  width: 20px;
  min-height: 20px;
}

.permission-switch-row.controlled {
  border-color: rgba(255, 171, 64, 0.45);
  background: rgba(255, 248, 235, 0.92);
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
  .permission-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .permission-head,
  .permission-row {
    grid-template-columns: 1fr;
  }
}
</style>
