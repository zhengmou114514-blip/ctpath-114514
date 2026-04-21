<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useWorkspaceContext } from '../composables/workspaceContext'

const workspace = useWorkspaceContext()

const maintenance = computed(() => workspace.maintenanceOverview)
const loading = computed(() => workspace.loadingMaintenance || workspace.loadingGovernance)

const overviewCards = computed(() => {
  const data = maintenance.value
  if (!data) return []
  return [
    { label: '患者总数', value: data.patientCount },
    { label: '病程事件数', value: data.eventCount },
    { label: '高风险患者', value: data.highRiskCount },
    { label: '低支撑档案', value: data.lowSupportCount },
    { label: '逾期随访', value: data.overdueFollowupCount },
    { label: '主索引冲突', value: data.duplicateRiskCount },
  ]
})

const missingFields = computed(() => {
  const data = maintenance.value
  if (!data) return []
  return [
    { label: '缺失病案号', value: data.missingMrnCount },
    { label: '待补知情同意', value: data.pendingConsentCount },
    { label: '低支撑患者', value: data.lowSupportCount },
  ]
})

const anomalyRows = computed(() => {
  const data = maintenance.value
  if (!data) return []
  return (data.recentEvents ?? [])
    .filter((event) => {
      const emptyRelation = !String(event.relation || '').trim()
      const emptyObject = !String(event.objectValue || '').trim()
      const futureTime = new Date(event.eventTime).getTime() > Date.now()
      return emptyRelation || emptyObject || futureTime
    })
    .slice(0, 8)
})

const conflictRows = computed(() => (maintenance.value?.masterIndexAlerts ?? []).slice(0, 8))

const pendingArchiveRows = computed(() => {
  const data = maintenance.value
  if (!data) return []
  return (data.recentPatients ?? [])
    .filter((item) => item.dataSupport === 'low' || item.riskLevel.toLowerCase().includes('high'))
    .slice(0, 8)
})

const governanceActions = computed(() => (maintenance.value?.recentEvents ?? []).slice(0, 8))

function handleRefresh() {
  void workspace.refreshGovernanceWorkspace()
}

onMounted(() => {
  if (!workspace.currentDoctor) return
  if (!workspace.maintenanceOverview) {
    void workspace.refreshGovernanceWorkspace()
  }
})
</script>

<template>
  <section class="governance-page workstation-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">治理中心</p>
        <h1>治理看板</h1>
        <p>面向数据质量、档案治理与异常巡检，不混入当前患者预测结果，也不承担训练中心职责。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="handleRefresh">刷新治理数据</el-button>
    </header>

    <section v-if="loading" class="empty-state-card">正在加载治理看板...</section>
    <section v-else-if="!maintenance" class="empty-state-card">当前没有可用的治理数据。</section>

    <template v-else>
      <section class="metric-grid six">
        <article v-for="card in overviewCards" :key="card.label" class="metric-card">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </section>

      <section class="governance-grid">
        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>数据质量概览</h2>
              <p>集中观察主索引冲突、逾期随访、低支撑档案与高风险患者数量。</p>
            </div>
          </div>
          <div class="quality-grid">
            <article><span>缺失字段总量</span><strong>{{ maintenance.missingMrnCount + maintenance.pendingConsentCount + maintenance.lowSupportCount }}</strong></article>
            <article><span>主索引冲突</span><strong>{{ maintenance.duplicateRiskCount }}</strong></article>
            <article><span>高风险患者</span><strong>{{ maintenance.highRiskCount }}</strong></article>
            <article><span>逾期随访</span><strong>{{ maintenance.overdueFollowupCount }}</strong></article>
          </div>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>缺失字段</h2>
              <p>优先补齐关键字段，减少档案进入低支撑或不可用状态。</p>
            </div>
          </div>
          <ul v-if="missingFields.length" class="simple-list">
            <li v-for="item in missingFields" :key="item.label">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </li>
          </ul>
          <p v-else class="empty-inline">当前没有待补齐字段。</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>异常时间线</h2>
              <p>重点查看关系为空、对象为空或时间异常的病程事件。</p>
            </div>
          </div>
          <ul v-if="anomalyRows.length" class="record-list">
            <li v-for="(item, index) in anomalyRows" :key="`${item.patientId}-${item.eventTime}-${index}`">
              <strong>{{ item.patientName }}</strong>
              <p>{{ item.eventTime }} / {{ item.relationLabel || item.relation || '关系缺失' }} / {{ item.objectValue || '对象缺失' }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">当前没有检测到异常时间线。</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>主索引冲突</h2>
              <p>展示跨来源档案冲突或重复风险，便于后续治理确认。</p>
            </div>
          </div>
          <ul v-if="conflictRows.length" class="record-list">
            <li v-for="item in conflictRows" :key="`${item.patientId}-${item.issueType}`">
              <strong>{{ item.name }}</strong>
              <p>{{ item.issueLabel || item.issueType }} / {{ item.detail }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">当前没有主索引冲突记录。</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>待补全档案</h2>
              <p>聚焦高风险或低支撑患者档案，优先补全关键资料。</p>
            </div>
          </div>
          <ul v-if="pendingArchiveRows.length" class="record-list">
            <li v-for="item in pendingArchiveRows" :key="item.patientId">
              <strong>{{ item.name }}</strong>
              <p>{{ item.primaryDisease }} / {{ item.riskLevel }} / 数据支撑 {{ item.dataSupport }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">当前没有待补全档案。</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>治理动作记录</h2>
              <p>记录近期治理动作线索，为后续审计和核查提供依据。</p>
            </div>
          </div>
          <ul v-if="governanceActions.length" class="record-list">
            <li v-for="(item, index) in governanceActions" :key="`${item.patientId}-${item.eventTime}-${index}`">
              <strong>{{ item.patientName }}</strong>
              <p>{{ item.relationLabel || item.relation }} / {{ item.objectValue || '--' }} / {{ item.source }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">当前没有治理动作记录。</p>
        </article>
      </section>
    </template>
  </section>
</template>

<style scoped>
.governance-page {
  display: grid;
  gap: 24px;
}

.governance-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.quality-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.quality-grid article,
.simple-list li,
.record-list li {
  border: 1px solid var(--ws-border);
  border-radius: 8px;
  background: var(--ws-surface-soft);
  padding: 12px;
}

.quality-grid article {
  display: grid;
  gap: 6px;
}

.quality-grid span,
.simple-list span,
.record-list p {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.quality-grid strong,
.simple-list strong,
.record-list strong {
  color: var(--ws-title);
  font-size: 16px;
}

.simple-list,
.record-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
}

.simple-list li,
.record-list li {
  list-style: none;
}

.simple-list li {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: center;
}

.record-list li {
  display: grid;
  gap: 4px;
}

.record-list p {
  margin: 0;
  line-height: 1.5;
}

.empty-inline {
  margin: 0;
  border: 1px dashed var(--ws-border-strong);
  border-radius: 8px;
  padding: 12px;
  color: var(--ws-text-muted);
  text-align: center;
}

@media (max-width: 1180px) {
  .governance-grid,
  .quality-grid {
    grid-template-columns: 1fr;
  }
}
</style>
