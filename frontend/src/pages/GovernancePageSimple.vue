<script setup lang="ts">
import { computed } from 'vue'
import type {
  DoctorUser,
  GovernanceArchiveRow,
  GovernanceCenterViewModel,
  GovernanceModulesResponse,
  GovernanceOperationRecord,
  GovernanceStatusTone,
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
  loadingMaintenance: boolean
  loadingMetrics: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

function toPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) return '--'
  return `${(value * 100).toFixed(1)}%`
}

function toneByRatio(value: number | null): GovernanceStatusTone {
  if (value === null) return 'neutral'
  if (value >= 0.8) return 'danger'
  if (value >= 0.4) return 'warning'
  return 'ok'
}

function safeLower(value: string): string {
  return String(value || '').toLowerCase()
}

const viewModel = computed<GovernanceCenterViewModel | null>(() => {
  if (!props.maintenance) return null

  const maintenance = props.maintenance
  const recentEvents = maintenance.recentEvents ?? []
  const recentPatients = maintenance.recentPatients ?? []

  const missingFieldCount =
    (maintenance.missingMrnCount ?? 0) +
    (maintenance.pendingConsentCount ?? 0) +
    (maintenance.lowSupportCount ?? 0)

  const duplicateArchiveCount = maintenance.duplicateRiskCount ?? 0

  const timelineAnomalyCount = recentEvents.filter((event) => {
    const emptyRelation = !String(event.relation || '').trim()
    const emptyObject = !String(event.objectValue || '').trim()
    const futureTime = new Date(event.eventTime).getTime() > Date.now()
    return emptyRelation || emptyObject || futureTime
  }).length

  const highRiskOverdueFollowup = Math.min(
    maintenance.highRiskCount ?? 0,
    maintenance.overdueFollowupCount ?? 0
  )

  const modelAvailable = Boolean(props.health?.model_available) || Boolean(maintenance.modelAvailable)

  // TODO(api): backend does not provide real 7-day prediction call count yet.
  const predictionCalls7d: number | null = null

  // TODO(api): backend does not provide direct fallback ratio yet.
  const fallbackRatio: number | null = modelAvailable ? null : 1

  // TODO(api): backend does not provide advice review approval rate yet.
  const adviceApprovalRate: number | null = null

  const pendingCompletionRows: GovernanceArchiveRow[] = (maintenance.masterIndexAlerts ?? []).map((item) => ({
    patientId: item.patientId,
    patientName: item.name,
    issueType: item.issueLabel,
    detail: item.detail,
    source: item.archiveSource,
    priority: safeLower(item.issueLabel).includes('duplicate') ? 'high' : 'medium',
  }))

  const pendingReviewRows: GovernanceArchiveRow[] = recentPatients
    .filter((item) => {
      const riskHigh = safeLower(item.riskLevel).includes('high')
      const supportLow = item.dataSupport === 'low'
      return riskHigh || supportLow
    })
    .map((item) => ({
      patientId: item.patientId,
      patientName: item.name,
      issueType: 'Pending clinical review',
      detail: `${item.riskLevel}; data support: ${item.dataSupport}`,
      source: 'maintenance-overview',
      priority: safeLower(item.riskLevel).includes('high') ? 'high' : 'medium',
    }))

  const governanceActions: GovernanceOperationRecord[] = recentEvents.slice(0, 8).map((event, index) => ({
    id: `gov-${index + 1}`,
    actionType: 'governance_action',
    patientId: event.patientId,
    patientName: event.patientName,
    summary: `${event.relationLabel}: ${event.objectValue}`,
    operator: event.source || 'system',
    createdAt: event.eventTime,
  }))

  const correctionRecords: GovernanceOperationRecord[] = recentEvents
    .filter((event) => ['stage', 'diagnosis', 'medication'].includes(safeLower(event.relation)))
    .slice(0, 8)
    .map((event, index) => ({
      id: `fix-${index + 1}`,
      actionType: 'correction_record',
      patientId: event.patientId,
      patientName: event.patientName,
      summary: `Corrected ${event.relationLabel}: ${event.objectValue}`,
      operator: event.source || 'system',
      createdAt: event.eventTime,
    }))

  const riskEscalations: GovernanceOperationRecord[] = recentEvents
    .filter((event) => {
      const relation = safeLower(event.relation)
      const detail = safeLower(event.objectValue)
      return relation.includes('risk') || detail.includes('high')
    })
    .slice(0, 8)
    .map((event, index) => ({
      id: `risk-${index + 1}`,
      actionType: 'risk_escalation',
      patientId: event.patientId,
      patientName: event.patientName,
      summary: `Risk event: ${event.objectValue}`,
      operator: event.source || 'system',
      createdAt: event.eventTime,
    }))

  return {
    dataQuality: {
      missingFieldCount,
      duplicateArchiveCount,
      timelineAnomalyCount,
      highRiskOverdueFollowup,
    },
    modelGovernance: {
      modelAvailable,
      predictionCalls7d,
      fallbackRatio,
      adviceApprovalRate,
    },
    archiveGovernance: {
      pendingCompletionRows,
      pendingReviewRows,
    },
    operationTraces: {
      governanceActions,
      correctionRecords,
      riskEscalations,
    },
  }
})

const modelStatusText = computed(() => {
  if (!viewModel.value) return 'Unknown'
  return viewModel.value.modelGovernance.modelAvailable ? 'Available' : 'Unavailable / Fallback'
})

const fallbackTone = computed(() => toneByRatio(viewModel.value?.modelGovernance.fallbackRatio ?? null))

const approvalTone = computed(() => {
  const rate = viewModel.value?.modelGovernance.adviceApprovalRate ?? null
  if (rate === null) return 'neutral'
  if (rate >= 0.85) return 'ok'
  if (rate >= 0.65) return 'warning'
  return 'danger'
})

const moduleStatusRows = computed(() => (props.governanceModules?.items ?? []).map((item) => ({
  moduleKey: item.moduleKey,
  title: item.title,
  ownerRole: item.ownerRole,
  status: item.status,
  tone: item.tone,
  description: item.description,
})))
</script>

<template>
  <section class="governance-center">
    <header class="page-head card">
      <div>
        <h2>Data Quality and Clinical Decision Governance Center</h2>
        <p>
          Unified view for data quality, model-service governance, archive governance, and auditable operational traces.
          Metrics marked as TODO are frontend adapter placeholders pending dedicated backend fields.
        </p>
      </div>
      <button class="secondary-button" @click="emit('refresh')">Refresh Governance Data</button>
    </header>

    <section v-if="loadingMaintenance" class="card state">Loading governance data...</section>
    <section v-else-if="!viewModel" class="card state">No governance data available.</section>

    <template v-else>
      <section class="metric-block card">
        <div class="block-head">
          <h3>1. Data Quality Overview</h3>
          <span class="hint">Focus on records that directly affect clinical reliability.</span>
        </div>

        <div class="metric-grid">
          <article class="metric-card">
            <h4>Missing Core Fields</h4>
            <strong>{{ viewModel.dataQuality.missingFieldCount }}</strong>
            <p>Sum of missing MRN, pending consent, and low-support records.</p>
          </article>

          <article class="metric-card">
            <h4>Duplicate Archive Risk</h4>
            <strong>{{ viewModel.dataQuality.duplicateArchiveCount }}</strong>
            <p>Potential duplicate archive count from master index risk checks.</p>
          </article>

          <article class="metric-card">
            <h4>Timeline Anomalies</h4>
            <strong>{{ viewModel.dataQuality.timelineAnomalyCount }}</strong>
            <p>Detected by frontend rules: empty relation/object or future timestamp.</p>
          </article>

          <article class="metric-card critical">
            <h4>High-Risk Not Followed Up</h4>
            <strong>{{ viewModel.dataQuality.highRiskOverdueFollowup }}</strong>
            <p>Adapter estimate: min(high-risk count, overdue follow-up count). TODO(api)</p>
          </article>
        </div>
      </section>

      <section class="metric-block card">
        <div class="block-head">
          <h3>2. Model Service Governance</h3>
          <span class="hint">Service health and fallback behavior monitoring.</span>
        </div>

        <div class="metric-grid model-grid">
          <article class="metric-card">
            <h4>Model Availability</h4>
            <strong>{{ modelStatusText }}</strong>
            <p>Based on health/model flags from backend status endpoints.</p>
          </article>

          <article class="metric-card">
            <h4>Prediction Calls (7d)</h4>
            <strong>{{ viewModel.modelGovernance.predictionCalls7d ?? '--' }}</strong>
            <p>TODO(api): add backend metric for rolling 7-day predict invocation count.</p>
          </article>

          <article class="metric-card" :class="`tone-${fallbackTone}`">
            <h4>Fallback Ratio (Rules/Similar-case)</h4>
            <strong>{{ toPercent(viewModel.modelGovernance.fallbackRatio) }}</strong>
            <p>TODO(api): ratio currently inferred from model availability only.</p>
          </article>

          <article class="metric-card" :class="`tone-${approvalTone}`">
            <h4>Advice Approval Rate</h4>
            <strong>{{ toPercent(viewModel.modelGovernance.adviceApprovalRate) }}</strong>
            <p>TODO(api): requires persisted advice review workflow metrics.</p>
          </article>
        </div>

        <div class="subtable">
          <h4>Governance Modules Status</h4>
          <table>
            <thead>
              <tr>
                <th>Module</th>
                <th>Owner Role</th>
                <th>Status</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!moduleStatusRows.length">
                <td colspan="4">No module status data.</td>
              </tr>
              <tr v-for="row in moduleStatusRows" :key="row.moduleKey">
                <td>{{ row.title }}</td>
                <td>{{ row.ownerRole }}</td>
                <td><span class="status-pill" :class="`tone-${row.tone}`">{{ row.status }}</span></td>
                <td>{{ row.description }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="metric-block card">
        <div class="block-head">
          <h3>3. Archive Governance</h3>
          <span class="hint">Queue-based archive remediation and review.</span>
        </div>

        <div class="table-grid">
          <article class="subtable">
            <h4>Pending Completion Archives</h4>
            <table>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Issue</th>
                  <th>Detail</th>
                  <th>Source</th>
                  <th>Priority</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!viewModel.archiveGovernance.pendingCompletionRows.length">
                  <td colspan="5">No pending completion archives.</td>
                </tr>
                <tr v-for="row in viewModel.archiveGovernance.pendingCompletionRows" :key="`completion-${row.patientId}-${row.issueType}`">
                  <td>{{ row.patientId }} / {{ row.patientName }}</td>
                  <td>{{ row.issueType }}</td>
                  <td>{{ row.detail }}</td>
                  <td>{{ row.source }}</td>
                  <td><span class="status-pill" :class="`priority-${row.priority}`">{{ row.priority }}</span></td>
                </tr>
              </tbody>
            </table>
          </article>

          <article class="subtable">
            <h4>Pending Review Archives</h4>
            <table>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Issue</th>
                  <th>Detail</th>
                  <th>Source</th>
                  <th>Priority</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!viewModel.archiveGovernance.pendingReviewRows.length">
                  <td colspan="5">No pending review archives.</td>
                </tr>
                <tr v-for="row in viewModel.archiveGovernance.pendingReviewRows" :key="`review-${row.patientId}-${row.issueType}`">
                  <td>{{ row.patientId }} / {{ row.patientName }}</td>
                  <td>{{ row.issueType }}</td>
                  <td>{{ row.detail }}</td>
                  <td>{{ row.source }}</td>
                  <td><span class="status-pill" :class="`priority-${row.priority}`">{{ row.priority }}</span></td>
                </tr>
              </tbody>
            </table>
          </article>
        </div>
      </section>

      <section class="metric-block card">
        <div class="block-head">
          <h3>4. Operation Traces</h3>
          <span class="hint">Recent auditable governance actions and risk changes.</span>
        </div>

        <div class="table-grid">
          <article class="subtable">
            <h4>Recent Governance Actions</h4>
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Patient</th>
                  <th>Action</th>
                  <th>Operator</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!viewModel.operationTraces.governanceActions.length">
                  <td colspan="4">No governance actions.</td>
                </tr>
                <tr v-for="row in viewModel.operationTraces.governanceActions" :key="row.id">
                  <td>{{ row.createdAt.replace('T', ' ').slice(0, 16) }}</td>
                  <td>{{ row.patientId }} / {{ row.patientName }}</td>
                  <td>{{ row.summary }}</td>
                  <td>{{ row.operator }}</td>
                </tr>
              </tbody>
            </table>
          </article>

          <article class="subtable">
            <h4>Recent Correction Records</h4>
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Patient</th>
                  <th>Correction</th>
                  <th>Operator</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!viewModel.operationTraces.correctionRecords.length">
                  <td colspan="4">No correction records.</td>
                </tr>
                <tr v-for="row in viewModel.operationTraces.correctionRecords" :key="row.id">
                  <td>{{ row.createdAt.replace('T', ' ').slice(0, 16) }}</td>
                  <td>{{ row.patientId }} / {{ row.patientName }}</td>
                  <td>{{ row.summary }}</td>
                  <td>{{ row.operator }}</td>
                </tr>
              </tbody>
            </table>
          </article>

          <article class="subtable full-width">
            <h4>Recent Risk Escalations</h4>
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Patient</th>
                  <th>Escalation</th>
                  <th>Operator</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!viewModel.operationTraces.riskEscalations.length">
                  <td colspan="4">No risk escalation records.</td>
                </tr>
                <tr v-for="row in viewModel.operationTraces.riskEscalations" :key="row.id">
                  <td>{{ row.createdAt.replace('T', ' ').slice(0, 16) }}</td>
                  <td>{{ row.patientId }} / {{ row.patientName }}</td>
                  <td>{{ row.summary }}</td>
                  <td>{{ row.operator }}</td>
                </tr>
              </tbody>
            </table>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.governance-center {
  display: grid;
  gap: 12px;
  color: #17324b;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
}

.page-head h2 {
  margin: 0;
  font-size: 1.05rem;
  color: #10263c;
}

.page-head p {
  margin: 6px 0 0;
  color: #5d7387;
  font-size: 0.84rem;
  max-width: 900px;
}

.card {
  border: 1px solid #cfd9e5;
  border-radius: 10px;
  background: #ffffff;
}

.state {
  padding: 16px;
  color: #5d7387;
}

.metric-block {
  padding: 12px;
  display: grid;
  gap: 10px;
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
}

.block-head h3 {
  margin: 0;
  color: #10263c;
  font-size: 0.98rem;
}

.hint {
  color: #637b8f;
  font-size: 0.78rem;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.metric-card {
  border: 1px solid #d4dee9;
  border-radius: 8px;
  background: #f9fcff;
  padding: 10px;
  display: grid;
  gap: 6px;
}

.metric-card h4 {
  margin: 0;
  font-size: 0.84rem;
  color: #1a3750;
}

.metric-card strong {
  font-size: 1.3rem;
  color: #10263c;
}

.metric-card p {
  margin: 0;
  color: #637b8f;
  font-size: 0.78rem;
  line-height: 1.4;
}

.metric-card.critical {
  border-color: #efc2c5;
  background: #fff5f6;
}

.tone-neutral {
  border-color: #d4dee9;
  background: #f9fcff;
}

.tone-ok {
  border-color: #c4e5d7;
  background: #eef9f3;
}

.tone-warning {
  border-color: #efdbb2;
  background: #fff8eb;
}

.tone-danger {
  border-color: #efc2c5;
  background: #fff2f4;
}

.table-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.subtable {
  border: 1px solid #d4dee9;
  border-radius: 8px;
  background: #fbfdff;
  padding: 10px;
  display: grid;
  gap: 8px;
}

.subtable.full-width {
  grid-column: 1 / -1;
}

.subtable h4 {
  margin: 0;
  font-size: 0.88rem;
  color: #10263c;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

th,
td {
  border-bottom: 1px solid #e4ebf3;
  text-align: left;
  padding: 8px 6px;
  vertical-align: top;
}

th {
  color: #516b82;
  font-weight: 600;
  background: #f4f8fc;
}

td {
  color: #1f3850;
}

.status-pill {
  display: inline-flex;
  border-radius: 999px;
  border: 1px solid transparent;
  padding: 2px 8px;
  font-size: 0.72rem;
  font-weight: 700;
}

.status-pill.tone-healthy,
.status-pill.tone-ok {
  background: #eaf8f1;
  border-color: #bfe5d2;
  color: #1d7b5c;
}

.status-pill.tone-warning {
  background: #fff4e5;
  border-color: #efd7ad;
  color: #9b6518;
}

.status-pill.tone-normal,
.status-pill.tone-neutral {
  background: #eef3f9;
  border-color: #cfdae7;
  color: #3f6283;
}

.status-pill.priority-high {
  background: #fdeced;
  border-color: #efc2c5;
  color: #a4383f;
}

.status-pill.priority-medium {
  background: #fff4e2;
  border-color: #efdbb2;
  color: #9b6518;
}

.status-pill.priority-low {
  background: #e9f8f1;
  border-color: #bde7d1;
  color: #1d7b5c;
}

@media (max-width: 1400px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .table-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 920px) {
  .page-head {
    flex-direction: column;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>