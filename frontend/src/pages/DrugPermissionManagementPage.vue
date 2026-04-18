<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  createDrugPermissionItem,
  getDrugPermissionItem,
  getDrugPermissions,
  updateDrugPermissionItem,
} from '../services/api'
import type { DrugPermissionRecord, DrugPermissionRole, DrugPermissionUpsertRequest } from '../services/types'

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

const roleOptions: DrugPermissionRole[] = ['doctor', 'nurse', 'pharmacist', 'archivist', 'admin']

const filteredRecords = computed(() => {
  if (roleFilter.value === 'all') return records.value
  return records.value.filter((item) => item.role === roleFilter.value)
})

function applyRecord(record: DrugPermissionRecord) {
  selectedRole.value = record.role
  form.role = record.role
  form.allow_view = record.allow_view
  form.allow_prescribe = record.allow_prescribe
  form.allow_review = record.allow_review
  form.allow_execute = record.allow_execute
  form.allow_controlled_drug = record.allow_controlled_drug
}

async function loadPermissions(selectRole?: DrugPermissionRole) {
  loading.value = true
  errorMessage.value = ''
  try {
    records.value = await getDrugPermissions()
    const nextRole = selectRole ?? selectedRole.value
    const current = records.value.find((item) => item.role === nextRole) ?? records.value[0]
    if (current) {
      applyRecord(current)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载药品权限失败。'
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
    errorMessage.value = error instanceof Error ? error.message : '加载角色权限失败。'
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
      successMessage.value = '药品权限已更新。'
    } else {
      await createDrugPermissionItem(payload)
      successMessage.value = '药品权限已新增。'
    }
    await loadPermissions(payload.role)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存药品权限失败。'
  } finally {
    saving.value = false
  }
}

function resetForm() {
  void openRole(selectedRole.value)
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
        <h2>药品权限管理</h2>
        <p>只维护角色级药品权限，不承接库存、处方流、训练中心或模型调试台。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="resetForm">恢复当前角色</button>
        <button class="primary-button" type="button" :disabled="saving" @click="savePermission">
          {{ saving ? '保存中...' : '保存权限' }}
        </button>
      </div>
    </header>

    <section v-if="errorMessage" class="card empty-state">
      {{ errorMessage }}
    </section>

    <section v-else-if="successMessage" class="card empty-state success">
      {{ successMessage }}
    </section>

    <section class="drug-permission-layout">
      <article class="card panel list-panel">
        <div class="panel-head">
          <div>
            <h3>权限列表</h3>
            <p>{{ filteredRecords.length }} 个角色配置</p>
          </div>
          <label class="field compact-field">
            <span>按角色查看</span>
            <select v-model="roleFilter">
              <option value="all">全部角色</option>
              <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
            </select>
          </label>
        </div>

        <div v-if="loading" class="card empty-state compact">正在加载药品权限...</div>
        <div v-else-if="!filteredRecords.length" class="card empty-state compact">暂无药品权限记录。</div>
        <div v-else class="permission-table">
          <table>
            <thead>
              <tr>
                <th>角色</th>
                <th>查看</th>
                <th>开立</th>
                <th>审核</th>
                <th>执行</th>
                <th>管制药</th>
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
                <td>{{ item.allow_view ? '是' : '否' }}</td>
                <td>{{ item.allow_prescribe ? '是' : '否' }}</td>
                <td>{{ item.allow_review ? '是' : '否' }}</td>
                <td>{{ item.allow_execute ? '是' : '否' }}</td>
                <td>{{ item.allow_controlled_drug ? '是' : '否' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="card panel editor-panel">
        <div class="panel-head">
          <div>
            <h3>权限编辑</h3>
            <p>当前正在编辑 {{ form.role }}。</p>
          </div>
        </div>

        <div class="edit-grid">
          <label class="field">
            <span>角色</span>
            <select v-model="form.role">
              <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
            </select>
          </label>

          <label class="field">
            <span>是否可查看</span>
            <select v-model="form.allow_view">
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select>
          </label>

          <label class="field">
            <span>是否可开立</span>
            <select v-model="form.allow_prescribe">
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select>
          </label>

          <label class="field">
            <span>是否可审核</span>
            <select v-model="form.allow_review">
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select>
          </label>

          <label class="field">
            <span>是否可执行</span>
            <select v-model="form.allow_execute">
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select>
          </label>

          <label class="field">
            <span>是否可管制药</span>
            <select v-model="form.allow_controlled_drug">
              <option :value="true">是</option>
              <option :value="false">否</option>
            </select>
          </label>
        </div>

        <div class="detail-actions">
          <button class="secondary-button" type="button" @click="resetForm">重置</button>
          <button class="primary-button" type="button" :disabled="saving" @click="savePermission">
            {{ saving ? '保存中...' : '保存当前角色' }}
          </button>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.drug-permission-layout {
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

.compact-field {
  min-width: 180px;
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

.permission-table {
  overflow: auto;
}

.permission-table table {
  width: 100%;
  border-collapse: collapse;
}

.permission-table th,
.permission-table td {
  text-align: left;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  padding: 12px 10px;
}

.permission-table tbody tr {
  cursor: pointer;
}

.permission-table tbody tr.active {
  background: rgba(56, 189, 248, 0.08);
}

.edit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

@media (max-width: 1100px) {
  .drug-permission-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .edit-grid {
    grid-template-columns: 1fr;
  }
}
</style>
