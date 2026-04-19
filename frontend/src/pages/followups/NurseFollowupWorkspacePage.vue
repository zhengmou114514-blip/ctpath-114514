<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getFlowBoard, getFollowupWorklist } from '../../services/api'
import type { FlowBoardRow, FollowupTaskRow } from '../../services/types'

const loading = ref(false)
const errorMessage = ref('')
const followups = ref<FollowupTaskRow[]>([])
const flowRows = ref<FlowBoardRow[]>([])

const highPriorityCount = computed(() => followups.value.filter((item) => item.priority === 'high').length)
const pendingReviewCount = computed(() => flowRows.value.filter((item) => item.flowStatus.toLowerCase().includes('review')).length)

async function reload() {
  loading.value = true
  errorMessage.value = ''
  try {
    const [worklist, flowBoard] = await Promise.all([
      getFollowupWorklist(),
      getFlowBoard(),
    ])
    followups.value = worklist.items
    flowRows.value = flowBoard.items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load nurse follow-up workspace.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void reload()
})
</script>

<template>
  <section class="workspace-page nurse-followup-page">
    <header class="card page-header">
      <div>
        <p class="eyebrow">Nurse workstation</p>
        <h2>Follow-up / Care Flow</h2>
        <p>
          Nurse scope is limited to follow-up execution, contact closure and care-flow coordination.
          It does not expose drug catalog administration, controlled-drug grants or model governance.
        </p>
      </div>
      <button class="secondary-button" type="button" :disabled="loading" @click="reload">
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <section class="summary-grid">
      <article class="card metric-card">
        <span>Follow-up tasks</span>
        <strong>{{ followups.length }}</strong>
      </article>
      <article class="card metric-card">
        <span>High priority</span>
        <strong>{{ highPriorityCount }}</strong>
      </article>
      <article class="card metric-card">
        <span>Care flow rows</span>
        <strong>{{ flowRows.length }}</strong>
      </article>
      <article class="card metric-card">
        <span>Pending review</span>
        <strong>{{ pendingReviewCount }}</strong>
      </article>
    </section>

    <p v-if="errorMessage" class="card error-card">{{ errorMessage }}</p>

    <section class="nurse-grid">
      <article class="card table-card">
        <div class="card-head">
          <h3>Follow-up Worklist</h3>
          <span>{{ followups.length }} rows</span>
        </div>
        <p v-if="loading" class="empty-state">Loading follow-up tasks...</p>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Patient</th>
                <th>Disease / Risk</th>
                <th>Due</th>
                <th>Owner</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in followups" :key="`${item.patientId}-${item.taskId || item.taskType}`">
                <td>
                  <strong>{{ item.patientName }}</strong>
                  <p>{{ item.patientId }}</p>
                </td>
                <td>{{ item.primaryDisease }} / {{ item.riskLevel }}</td>
                <td>{{ item.dueDate }}</td>
                <td>{{ item.owner }}</td>
                <td>{{ item.status }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="card table-card">
        <div class="card-head">
          <h3>Care Flow Board</h3>
          <span>{{ flowRows.length }} rows</span>
        </div>
        <p v-if="loading" class="empty-state">Loading care flow...</p>
        <div v-else class="flow-list">
          <article v-for="item in flowRows" :key="item.patientId" class="flow-row">
            <div>
              <strong>{{ item.patientName }}</strong>
              <p>{{ item.primaryDisease }} / {{ item.currentStage }} / {{ item.riskLevel }}</p>
            </div>
            <div>
              <span class="flow-status">{{ item.flowStatus }}</span>
              <p>{{ item.nextAction }}</p>
            </div>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.nurse-followup-page {
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

.summary-grid,
.nurse-grid {
  display: grid;
  gap: 16px;
}

.summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.nurse-grid {
  grid-template-columns: minmax(0, 1.2fr) minmax(340px, 0.8fr);
  align-items: start;
}

.metric-card {
  display: grid;
  gap: 4px;
}

.metric-card span,
.card-head span,
td p,
.flow-row p {
  color: #64748b;
  font-size: 12px;
}

.metric-card strong {
  color: #0f172a;
  font-size: 24px;
}

.error-card {
  color: #991b1b;
  text-align: center;
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.card-head h3,
td p,
.flow-row p {
  margin: 0;
}

.table-wrap {
  margin-top: 12px;
  overflow: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
  padding: 10px;
  text-align: left;
  vertical-align: top;
}

.empty-state {
  margin: 12px 0 0;
  border: 1px dashed rgba(148, 163, 184, 0.42);
  border-radius: 10px;
  color: #64748b;
  padding: 16px;
  text-align: center;
}

.flow-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.flow-row {
  display: grid;
  gap: 8px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 12px;
  padding: 12px;
}

.flow-status {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
}

@media (max-width: 1120px) {
  .summary-grid,
  .nurse-grid {
    grid-template-columns: 1fr;
  }
}
</style>
