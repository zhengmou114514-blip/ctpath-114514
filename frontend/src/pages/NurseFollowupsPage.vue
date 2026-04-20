<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  getFlowBoard,
  getFollowupWorklist,
  getPatientCase,
} from '../services/api'
import type { ContactLog, FlowBoardRow, FollowupTaskRow } from '../services/types'

type ContactLogRow = ContactLog & {
  patientId: string
  patientName: string
}

const loading = ref(false)
const errorMessage = ref('')
const followups = ref<FollowupTaskRow[]>([])
const flowRows = ref<FlowBoardRow[]>([])
const contactLogs = ref<ContactLogRow[]>([])

const today = new Date().toISOString().slice(0, 10)

const todayFollowups = computed(() =>
  followups.value.filter((item) => item.dueDate <= today && item.status !== 'completed' && item.status !== 'closed')
)

const missedContacts = computed(() => contactLogs.value.filter((item) => item.contactResult === 'missed'))
const doctorReviewRows = computed(() => flowRows.value.filter((item) => item.flowStatus.toLowerCase().includes('review')))

async function loadContactLogs(items: FollowupTaskRow[]) {
  const uniquePatientIds = [...new Set(items.map((item) => item.patientId))].slice(0, 12)
  const patients = await Promise.all(
    uniquePatientIds.map(async (patientId) => {
      try {
        return await getPatientCase(patientId)
      } catch {
        return null
      }
    })
  )

  contactLogs.value = patients
    .filter((patient): patient is NonNullable<typeof patient> => patient !== null)
    .flatMap((patient) =>
      patient.contactLogs.map((log) => ({
        ...log,
        patientId: patient.patientId,
        patientName: patient.name,
      }))
    )
    .sort((left, right) => right.contactTime.localeCompare(left.contactTime))
}

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
    await loadContactLogs(worklist.items)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load nurse follow-up workspace.'
  } finally {
    loading.value = false
  }
}

function priorityTagType(priority: FollowupTaskRow['priority']) {
  if (priority === 'high') return 'danger'
  if (priority === 'medium') return 'warning'
  return 'success'
}

function contactTagType(result: ContactLog['contactResult']) {
  if (result === 'missed') return 'danger'
  if (result === 'urgent') return 'warning'
  if (result === 'scheduled') return 'primary'
  return 'success'
}

onMounted(() => {
  void reload()
})
</script>

<template>
  <section class="nurse-followups-page workstation-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">Nurse follow-ups</p>
        <h1>护士随访工作台</h1>
        <p>只挂载待随访任务、未接通联系、医生复核队列和联系记录。</p>
      </div>
      <el-button :loading="loading" @click="reload">刷新</el-button>
    </header>

    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
      :closable="false"
    />

    <section class="metric-grid four">
      <article class="metric-card">
        <span>今日随访</span>
        <strong>{{ todayFollowups.length }}</strong>
      </article>
      <article class="metric-card">
        <span>未接通</span>
        <strong>{{ missedContacts.length }}</strong>
      </article>
      <article class="metric-card">
        <span>医生复核</span>
        <strong>{{ doctorReviewRows.length }}</strong>
      </article>
      <article class="metric-card">
        <span>联系记录</span>
        <strong>{{ contactLogs.length }}</strong>
      </article>
    </section>

    <section class="nurse-grid">
      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <div>
              <h2>今日待随访</h2>
              <p>{{ today }}</p>
            </div>
          </div>
        </template>
        <el-table v-loading="loading" :data="todayFollowups" border stripe empty-text="今日暂无待随访任务。">
          <el-table-column label="患者" min-width="170">
            <template #default="{ row }">
              <strong>{{ row.patientName }}</strong>
              <p class="table-subtitle">{{ row.patientId }}</p>
            </template>
          </el-table-column>
          <el-table-column label="疾病 / 风险" min-width="190">
            <template #default="{ row }">{{ row.primaryDisease }} / {{ row.riskLevel }}</template>
          </el-table-column>
          <el-table-column prop="dueDate" label="截止" width="115" />
          <el-table-column label="优先级" width="120">
            <template #default="{ row }">
              <el-tag :type="priorityTagType(row.priority)" effect="light">{{ row.priority }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="130" />
        </el-table>
      </el-card>

      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <div>
              <h2>未接通联系</h2>
              <p>{{ missedContacts.length }} 条记录</p>
            </div>
          </div>
        </template>
        <el-table v-loading="loading" :data="missedContacts" border stripe empty-text="暂无未接通联系记录。">
          <el-table-column label="患者" min-width="160">
            <template #default="{ row }">
              <strong>{{ row.patientName }}</strong>
              <p class="table-subtitle">{{ row.patientId }}</p>
            </template>
          </el-table-column>
          <el-table-column prop="contactTime" label="时间" min-width="150" />
          <el-table-column prop="contactTarget" label="对象" width="130" />
          <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip />
        </el-table>
      </el-card>

      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <div>
              <h2>医生复核队列</h2>
              <p>{{ doctorReviewRows.length }} 条</p>
            </div>
          </div>
        </template>
        <el-table v-loading="loading" :data="doctorReviewRows" border stripe empty-text="暂无等待医生复核的患者。">
          <el-table-column label="患者" min-width="160">
            <template #default="{ row }">
              <strong>{{ row.patientName }}</strong>
              <p class="table-subtitle">{{ row.patientId }}</p>
            </template>
          </el-table-column>
          <el-table-column label="疾病 / 阶段" min-width="190">
            <template #default="{ row }">{{ row.primaryDisease }} / {{ row.currentStage }}</template>
          </el-table-column>
          <el-table-column prop="flowStatus" label="流转状态" min-width="140" />
          <el-table-column prop="nextAction" label="下一步" min-width="220" show-overflow-tooltip />
        </el-table>
      </el-card>

      <el-card shadow="never" class="module-card">
        <template #header>
          <div class="section-header">
            <div>
              <h2>联系记录</h2>
              <p>{{ contactLogs.length }} 条记录</p>
            </div>
          </div>
        </template>
        <el-table v-loading="loading" :data="contactLogs" border stripe empty-text="暂无联系记录。">
          <el-table-column label="患者" min-width="160">
            <template #default="{ row }">
              <strong>{{ row.patientName }}</strong>
              <p class="table-subtitle">{{ row.patientId }}</p>
            </template>
          </el-table-column>
          <el-table-column prop="contactTime" label="时间" min-width="150" />
          <el-table-column prop="contactType" label="方式" width="110" />
          <el-table-column label="结果" width="125">
            <template #default="{ row }">
              <el-tag :type="contactTagType(row.contactResult)" effect="light">{{ row.contactResult }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="operatorName" label="操作人" min-width="130" />
          <el-table-column prop="note" label="备注" min-width="220" show-overflow-tooltip />
        </el-table>
      </el-card>
    </section>
  </section>
</template>

<style scoped>
.nurse-followups-page {
  display: grid;
  gap: 24px;
}

.nurse-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.table-subtitle {
  margin: 2px 0 0;
  color: var(--ws-text-muted);
  font-size: 12px;
}

@media (max-width: 1180px) {
  .nurse-grid {
    grid-template-columns: 1fr;
  }
}
</style>
