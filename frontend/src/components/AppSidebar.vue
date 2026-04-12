<script setup lang="ts">
import { computed } from 'vue'
import { ROLE_WORKSPACE_MENUS, sectionLabel } from '../config/workspaceMenu'
import type { DoctorUser, HealthResponse } from '../services/types'
import type { AppSection } from '../types/workspace'

const props = defineProps<{
  activeSection: AppSection
  doctor: DoctorUser
  health: HealthResponse | null
  patientCount: number
  followupCount: number
}>()

const emit = defineEmits<{
  (e: 'select', section: AppSection): void
  (e: 'logout'): void
}>()

const menus = computed(() => ROLE_WORKSPACE_MENUS[props.doctor.role])

const roleLabel = computed(() => {
  if (props.doctor.role === 'archivist') return 'Archivist'
  if (props.doctor.role === 'nurse') return 'Nurse'
  return 'Doctor'
})
</script>

<template>
  <aside class="sidebar-shell workstation-sidebar" :class="`sidebar-role-${props.doctor.role}`">
    <div class="brand-panel">
      <div class="brand-mark">HIS</div>
      <div>
        <p class="eyebrow inverse">Outpatient Workstation</p>
        <strong>Chronic Care Clinical Console</strong>
      </div>
    </div>

    <section class="sidebar-card doctor-panel">
      <span class="sidebar-label">{{ props.doctor.department }}</span>
      <strong>{{ props.doctor.name }} / {{ props.doctor.title }}</strong>
      <small>Role: {{ roleLabel }}</small>
      <small>Current Module: {{ sectionLabel(props.activeSection) }}</small>
    </section>

    <section class="sidebar-card sidebar-kpi-card">
      <div class="sidebar-kpi-row">
        <span>Total Patients</span>
        <strong>{{ props.patientCount }}</strong>
      </div>
      <div class="sidebar-kpi-row">
        <span>Follow-up Tasks</span>
        <strong>{{ props.followupCount }}</strong>
      </div>
      <div class="sidebar-kpi-row">
        <span>System Mode</span>
        <strong>{{ props.health?.mode ?? 'unknown' }}</strong>
      </div>
    </section>

    <nav class="sidebar-nav">
      <button
        v-for="item in menus"
        :key="item.section"
        class="nav-item nav-item-detailed"
        :class="{ active: item.section === props.activeSection }"
        @click="emit('select', item.section)"
      >
        <strong>{{ item.label }}</strong>
        <span>{{ item.description }}</span>
      </button>
    </nav>

    <div class="sidebar-actions">
      <button class="sidebar-button ghost" @click="emit('logout')">Sign Out</button>
    </div>
  </aside>
</template>
