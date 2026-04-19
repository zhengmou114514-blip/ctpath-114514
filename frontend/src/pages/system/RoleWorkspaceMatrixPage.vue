<script setup lang="ts">
import { computed, ref } from 'vue'
import { getRoleWorkspaces } from '../../services/api'
import type { BusinessWorkspaceRole, RoleWorkspaceDefinition } from '../../services/types'

const workspaces = ref<RoleWorkspaceDefinition[]>(getRoleWorkspaces())
const selectedRole = ref<BusinessWorkspaceRole>('doctor')

const selectedWorkspace = computed(
  () => workspaces.value.find((item) => item.role === selectedRole.value) ?? workspaces.value[0]
)

function statusText(status: string): string {
  return status === 'ready' ? 'Ready' : status === 'limited' ? 'Limited' : 'Blocked'
}
</script>

<template>
  <section class="workspace-page role-workspace-page">
    <header class="card page-header">
      <div>
        <p class="eyebrow">Role boundary</p>
        <h2>Doctor / Nurse / Pharmacist / Admin Workstations</h2>
        <p>
          First-round role landing map for chronic-care business modules. It narrows responsibilities without adding
          inventory, billing, inpatient, full prescription flow, model debug console or training center work.
        </p>
      </div>
    </header>

    <section class="role-tabs">
      <button
        v-for="workspace in workspaces"
        :key="workspace.role"
        type="button"
        :class="{ active: workspace.role === selectedRole }"
        @click="selectedRole = workspace.role"
      >
        {{ workspace.title }}
      </button>
    </section>

    <section v-if="selectedWorkspace" class="role-layout">
      <article class="card role-card">
        <p class="eyebrow">Selected role</p>
        <h3>{{ selectedWorkspace.title }}</h3>
        <p>{{ selectedWorkspace.description }}</p>

        <div class="boundary-block">
          <h4>Forbidden in this role</h4>
          <ul>
            <li v-for="item in selectedWorkspace.forbiddenModules" :key="item">{{ item }}</li>
          </ul>
        </div>

        <div class="boundary-block">
          <h4>Audit focus</h4>
          <ul>
            <li v-for="item in selectedWorkspace.auditFocus" :key="item">{{ item }}</li>
          </ul>
        </div>
      </article>

      <article class="card module-card">
        <div class="card-head">
          <h3>Allowed business modules</h3>
          <span>{{ selectedWorkspace.primaryModules.length }} modules</span>
        </div>

        <div class="module-list">
          <article v-for="module in selectedWorkspace.primaryModules" :key="module.key" class="module-row">
            <div>
              <strong>{{ module.label }}</strong>
              <p>{{ module.responsibility }}</p>
              <small>{{ module.routeHint }}</small>
            </div>
            <span class="status-pill" :class="module.status">{{ statusText(module.status) }}</span>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.role-workspace-page {
  display: grid;
  gap: 16px;
}

.eyebrow {
  margin: 0 0 4px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.role-tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.role-tabs button {
  border: 1px solid rgba(148, 163, 184, 0.34);
  border-radius: 999px;
  background: #fff;
  color: #334155;
  cursor: pointer;
  font-weight: 700;
  padding: 9px 14px;
}

.role-tabs button.active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
}

.role-layout {
  display: grid;
  grid-template-columns: minmax(300px, 0.8fr) minmax(0, 1.2fr);
  gap: 16px;
  align-items: start;
}

.role-card h3,
.role-card p,
.card-head h3,
.module-row p {
  margin: 0;
}

.role-card,
.module-card {
  display: grid;
  gap: 14px;
}

.boundary-block {
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 12px;
  background: #f8fafc;
  padding: 12px;
}

.boundary-block h4,
.boundary-block ul {
  margin: 0;
}

.boundary-block ul {
  padding-left: 18px;
  color: #334155;
}

.card-head,
.module-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-head span,
.module-row p,
.module-row small {
  color: #64748b;
  font-size: 12px;
}

.module-list {
  display: grid;
  gap: 10px;
}

.module-row {
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 12px;
  padding: 12px;
}

.module-row strong {
  color: #0f172a;
}

.module-row small {
  display: inline-flex;
  margin-top: 6px;
}

.status-pill {
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
}

.status-pill.ready {
  background: #dcfce7;
  color: #166534;
}

.status-pill.limited {
  background: #fff7ed;
  color: #9a3412;
}

.status-pill.blocked {
  background: #fee2e2;
  color: #991b1b;
}

@media (max-width: 960px) {
  .role-layout {
    grid-template-columns: 1fr;
  }
}
</style>
