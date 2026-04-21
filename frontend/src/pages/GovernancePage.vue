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
    { label: '患者档案', value: data.patientCount },
    { label: '病程事件', value: data.eventCount },
    { label: '高风险患者', value: data.highRiskCount },
    { label: '低支持档案', value: data.lowSupportCount },
    { label: '逾期随访', value: data.overdueFollowupCount },
    { label: '冲突风险', value: data.duplicateRiskCount },
  ]
})

const missingFields = computed(() => {
  const data = maintenance.value
  if (!data) return []
  return [
    { label: '缺失病案号', value: data.missingMrnCount },
    { label: '待知情同意', value: data.pendingConsentCount },
    { label: '数据支持不足', value: data.lowSupportCount },
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
        <p class="eyebrow">Governance center</p>
        <h1>治理中心</h1>
        <p>只展示数据质量、冲突记录、待补全档案和治理动作，不承载患者预测或模型训练。</p>
      </div>
      <el-button type="primary" :loading="loading" @click="handleRefresh">刷新</el-button>
    </header>

    <section v-if="loading" class="empty-state-card">正在加载治理数据...</section>
    <section v-else-if="!maintenance" class="empty-state-card">暂无治理数据。</section>

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
              <p>缺失字段、冲突风险和逾期随访。</p>
            </div>
          </div>
          <div class="quality-grid">
            <article><span>缺失/待同意</span><strong>{{ maintenance.missingMrnCount + maintenance.pendingConsentCount + maintenance.lowSupportCount }}</strong></article>
            <article><span>冲突风险</span><strong>{{ maintenance.duplicateRiskCount }}</strong></article>
            <article><span>高风险患者</span><strong>{{ maintenance.highRiskCount }}</strong></article>
            <article><span>逾期随访</span><strong>{{ maintenance.overdueFollowupCount }}</strong></article>
          </div>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>缺失字段</h2>
              <p>档案员和治理人员需要优先补齐的字段。</p>
            </div>
          </div>
          <ul v-if="missingFields.length" class="simple-list">
            <li v-for="item in missingFields" :key="item.label">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </li>
          </ul>
          <p v-else class="empty-inline">暂无缺失字段。</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>异常时间线</h2>
              <p>关系缺失、对象缺失或未来时间等异常事件。</p>
            </div>
          </div>
          <ul v-if="anomalyRows.length" class="record-list">
            <li v-for="(item, index) in anomalyRows" :key="`${item.patientId}-${item.eventTime}-${index}`">
              <strong>{{ item.patientName }}</strong>
              <p>{{ item.eventTime }} / {{ item.relationLabel || item.relation || '关系缺失' }} / {{ item.objectValue || '对象值缺失' }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">暂无异常时间线。</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>冲突记录</h2>
              <p>主索引和档案一致性风险。</p>
            </div>
          </div>
          <ul v-if="conflictRows.length" class="record-list">
            <li v-for="item in conflictRows" :key="`${item.patientId}-${item.issueType}`">
              <strong>{{ item.name }}</strong>
              <p>{{ item.issueLabel || item.issueType }} / {{ item.detail }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">暂无冲突记录。</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>待补全档案</h2>
              <p>优先处理高风险或低数据支持患者。</p>
            </div>
          </div>
          <ul v-if="pendingArchiveRows.length" class="record-list">
            <li v-for="item in pendingArchiveRows" :key="item.patientId">
              <strong>{{ item.name }}</strong>
              <p>{{ item.primaryDisease }} / {{ item.riskLevel }} / 数据支持 {{ item.dataSupport }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">暂无待补全档案。</p>
        </article>

        <article class="clinical-card">
          <div class="section-header">
            <div>
              <h2>治理动作记录</h2>
              <p>最近治理相关事件和来源。</p>
            </div>
          </div>
          <ul v-if="governanceActions.length" class="record-list">
            <li v-for="(item, index) in governanceActions" :key="`${item.patientId}-${item.eventTime}-${index}`">
              <strong>{{ item.patientName }}</strong>
              <p>{{ item.relationLabel || item.relation }} / {{ item.objectValue || '--' }} / {{ item.source }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">暂无治理动作记录。</p>
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
