<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useWorkspaceContext } from '../composables/workspaceContext'

const workspace = useWorkspaceContext()

const maintenance = computed(() => workspace.maintenanceOverview)

const overviewCards = computed(() => {
  const data = maintenance.value
  if (!data) return []
  return [
    { label: '患者总数', value: data.patientCount },
    { label: '事件总数', value: data.eventCount },
    { label: '高风险患者', value: data.highRiskCount },
    { label: '低支持档案', value: data.lowSupportCount },
    { label: '逾期随访', value: data.overdueFollowupCount },
    { label: '重复风险', value: data.duplicateRiskCount },
  ]
})

const missingFields = computed(() => {
  const data = maintenance.value
  if (!data) return []
  return [
    { label: 'MRN 缺失', value: data.missingMrnCount },
    { label: '知情同意待补', value: data.pendingConsentCount },
    { label: '低支持档案', value: data.lowSupportCount },
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

const conflictRows = computed(() => {
  const data = maintenance.value
  if (!data) return []
  return (data.masterIndexAlerts ?? []).slice(0, 8)
})

const pendingArchiveRows = computed(() => {
  const data = maintenance.value
  if (!data) return []
  return (data.recentPatients ?? [])
    .filter((item) => item.dataSupport === 'low' || item.riskLevel.toLowerCase().includes('high'))
    .slice(0, 8)
})

const governanceActions = computed(() => {
  const data = maintenance.value
  if (!data) return []
  return (data.recentEvents ?? []).slice(0, 8)
})

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
  <section class="workspace-page governance-page">
    <header class="card page-header">
      <div>
        <h2>治理看板</h2>
        <p>只展示数据治理内容，不展示当前患者预测或模型训练面板。</p>
      </div>
      <button class="primary-button" @click="handleRefresh">刷新</button>
    </header>

    <section v-if="workspace.loadingMaintenance || workspace.loadingGovernance" class="card state">
      正在加载治理数据...
    </section>

    <section v-else-if="!maintenance" class="card state">
      暂无治理数据。
    </section>

    <template v-else>
      <section class="summary-grid">
        <article v-for="card in overviewCards" :key="card.label" class="card summary-card">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
        </article>
      </section>

      <section class="detail-grid">
        <article class="card panel">
          <h3>数据质量概览</h3>
          <div class="quality-grid">
            <div class="quality-item">
              <span>缺失字段</span>
              <strong>{{ maintenance.missingMrnCount + maintenance.pendingConsentCount + maintenance.lowSupportCount }}</strong>
            </div>
            <div class="quality-item">
              <span>重复风险</span>
              <strong>{{ maintenance.duplicateRiskCount }}</strong>
            </div>
            <div class="quality-item">
              <span>高风险患者</span>
              <strong>{{ maintenance.highRiskCount }}</strong>
            </div>
            <div class="quality-item">
              <span>逾期随访</span>
              <strong>{{ maintenance.overdueFollowupCount }}</strong>
            </div>
          </div>
        </article>

        <article class="card panel">
          <h3>缺失字段</h3>
          <ul v-if="missingFields.length" class="simple-list">
            <li v-for="item in missingFields" :key="item.label">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </li>
          </ul>
          <p v-else class="empty-inline">暂无缺失字段。</p>
        </article>

        <article class="card panel">
          <h3>异常时间线</h3>
          <ul v-if="anomalyRows.length" class="record-list">
            <li v-for="(item, index) in anomalyRows" :key="`${item.patientId}-${item.eventTime}-${index}`">
              <strong>{{ item.patientName }}</strong>
              <p>{{ item.eventTime }} · {{ item.relationLabel || item.relation }} · {{ item.objectValue || '--' }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">暂无异常时间线。</p>
        </article>

        <article class="card panel">
          <h3>冲突记录</h3>
          <ul v-if="conflictRows.length" class="record-list">
            <li v-for="item in conflictRows" :key="`${item.patientId}-${item.issueType}`">
              <strong>{{ item.name }}</strong>
              <p>{{ item.issueType }} · {{ item.detail }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">暂无冲突记录。</p>
        </article>

        <article class="card panel">
          <h3>待补全档案</h3>
          <ul v-if="pendingArchiveRows.length" class="record-list">
            <li v-for="item in pendingArchiveRows" :key="item.patientId">
              <strong>{{ item.name }}</strong>
              <p>{{ item.primaryDisease }} · {{ item.riskLevel }} · 支持度 {{ item.dataSupport }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">暂无待补全档案。</p>
        </article>

        <article class="card panel">
          <h3>治理动作</h3>
          <ul v-if="governanceActions.length" class="record-list">
            <li v-for="(item, index) in governanceActions" :key="`${item.patientId}-${item.eventTime}-${index}`">
              <strong>{{ item.patientName }}</strong>
              <p>{{ item.relationLabel }} · {{ item.objectValue }} · {{ item.source }}</p>
            </li>
          </ul>
          <p v-else class="empty-inline">暂无治理动作。</p>
        </article>
      </section>
    </template>
  </section>
</template>

<style scoped>
.governance-page {
  padding: 20px;
  display: grid;
  gap: 14px;
  align-content: start;
}

.page-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  color: #17324d;
}

.page-header p {
  margin: 4px 0 0;
  color: #5f758b;
  font-size: 13px;
}

.state {
  padding: 16px;
  color: #5f758b;
  text-align: center;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.summary-card,
.panel {
  padding: 14px;
  display: grid;
  gap: 8px;
}

.summary-card span {
  color: #60778e;
  font-size: 12px;
}

.summary-card strong {
  color: #17324d;
  font-size: 18px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.panel h3 {
  margin: 0;
  color: #17324d;
  font-size: 15px;
}

.quality-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.quality-item {
  border: 1px solid #d7e2ee;
  border-radius: 8px;
  padding: 10px;
  background: #f9fbfd;
  display: grid;
  gap: 6px;
}

.quality-item span {
  color: #60778e;
  font-size: 12px;
}

.quality-item strong {
  color: #17324d;
  font-size: 16px;
}

.simple-list,
.record-list {
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.simple-list li,
.record-list li {
  list-style: none;
  border: 1px solid #d7e2ee;
  border-radius: 8px;
  padding: 10px;
  background: #fbfdff;
  display: grid;
  gap: 4px;
}

.simple-list li {
  grid-template-columns: 1fr auto;
  align-items: center;
}

.simple-list span,
.record-list p {
  color: #60778e;
  font-size: 13px;
  margin: 0;
}

.simple-list strong,
.record-list strong {
  color: #17324d;
}

.empty-inline {
  border: 1px dashed #bfd0e1;
  border-radius: 8px;
  padding: 12px;
  color: #60778e;
  text-align: center;
}

@media (max-width: 1400px) {
  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1200px) {
  .detail-grid,
  .summary-grid,
  .quality-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
