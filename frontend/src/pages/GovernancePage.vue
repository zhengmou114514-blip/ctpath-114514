<script setup lang="ts">
import GovernancePageSimple from './GovernancePageSimple.vue'
import type {
  DoctorUser,
  GovernanceModulesResponse,
  HealthResponse,
  MaintenanceOverview,
  ModelMetricsResponse,
} from '../services/types'

const props = defineProps<{
  doctorRole: DoctorUser['role']
  health: HealthResponse | null
  maintenance: MaintenanceOverview | null
  governanceModules: GovernanceModulesResponse | null
  modelMetrics: ModelMetricsResponse | null
  loadingGovernance: boolean
  loadingMaintenance: boolean
  loadingMetrics: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()
</script>

<template>
  <GovernancePageSimple
    :doctor-role="props.doctorRole"
    :health="props.health"
    :maintenance="props.maintenance"
    :model-metrics="props.modelMetrics"
    :loading-maintenance="props.loadingMaintenance || props.loadingGovernance"
    :loading-metrics="props.loadingMetrics"
    @refresh="emit('refresh')"
  />
</template>

