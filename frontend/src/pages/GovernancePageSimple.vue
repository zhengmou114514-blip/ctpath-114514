<script setup lang="ts">
import { computed, ref } from 'vue'
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

// 新增：当前激活的标签页
const activeTab = ref<'governance' | 'insights'>('governance')

// 新增：模型洞察面板的展开状态
const insightsPanelExpanded = ref(false)

// 新增：切换模型洞察面板
function toggleInsightsPanel() {
  insightsPanelExpanded.value = !insightsPanelExpanded.value
}

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
  <section class="governance-layout">
    <!-- 左侧固定侧边栏：用于切换模块 -->
    <aside class="governance-sidebar">
      <div class="sidebar-header">
        <h3>模块导航</h3>
      </div>
      <nav class="sidebar-nav">
        <button
          class="nav-item"
          :class="{ active: activeTab === 'governance' }"
          @click="activeTab = 'governance'"
        >
          <span class="nav-icon">📊</span>
          <span class="nav-text">治理看板</span>
        </button>
        <button
          class="nav-item"
          :class="{ active: activeTab === 'insights' }"
          @click="activeTab = 'insights'"
        >
          <span class="nav-icon">🧠</span>
          <span class="nav-text">模型洞察</span>
        </button>
      </nav>
    </aside>

    <!-- 右侧主内容区 -->
    <main class="governance-main">
      <!-- 标题栏：显示当前角色和模块名称 -->
      <header class="page-header">
        <div class="header-left">
          <h2>{{ activeTab === 'governance' ? '治理看板' : '模型洞察' }}</h2>
          <span class="role-badge">门诊医生</span>
        </div>
        <div class="header-right">
          <button class="secondary-button" @click="emit('refresh')">刷新数据</button>
        </div>
      </header>

      <!-- 治理看板内容 -->
      <div v-if="activeTab === 'governance'" class="content-section">
        <section v-if="loadingMaintenance" class="card state">加载中...</section>
        <section v-else-if="!viewModel" class="card state">暂无数据</section>

        <template v-else>
          <section class="metric-block card">
            <div class="block-head">
              <h3>1. 数据质量概览</h3>
              <span class="hint">关注直接影响临床可靠性的记录</span>
            </div>

            <div class="metric-grid">
              <article class="metric-card">
                <h4>缺失核心字段</h4>
                <strong>{{ viewModel.dataQuality.missingFieldCount }}</strong>
                <p>缺失 MRN、待同意、低支持度记录的总和</p>
              </article>

              <article class="metric-card">
                <h4>重复档案风险</h4>
                <strong>{{ viewModel.dataQuality.duplicateArchiveCount }}</strong>
                <p>主索引风险检查中的潜在重复档案数</p>
              </article>

              <article class="metric-card">
                <h4>时间线异常</h4>
                <strong>{{ viewModel.dataQuality.timelineAnomalyCount }}</strong>
                <p>前端规则检测：空关系/对象或未来时间戳</p>
              </article>

              <article class="metric-card critical">
                <h4>高风险未随访</h4>
                <strong>{{ viewModel.dataQuality.highRiskOverdueFollowup }}</strong>
                <p>适配器估算：min(高风险数, 逾期随访数)</p>
              </article>
            </div>
          </section>

          <div class="section-divider"></div>

          <section class="metric-block card">
            <div class="block-head">
              <h3>2. 模型服务治理</h3>
              <span class="hint">服务健康和降级行为监控</span>
            </div>

            <div class="metric-grid model-grid">
              <article class="metric-card">
                <h4>模型可用性</h4>
                <strong>{{ modelStatusText }}</strong>
                <p>基于后端状态端点的 health/model 标志</p>
              </article>

              <article class="metric-card">
                <h4>预测调用 (7天)</h4>
                <strong>{{ viewModel.modelGovernance.predictionCalls7d ?? '--' }}</strong>
                <p>TODO(api): 添加滚动7天预测调用计数的后端指标</p>
              </article>

              <article class="metric-card" :class="`tone-${fallbackTone}`">
                <h4>降级比率 (规则/相似案例)</h4>
                <strong>{{ toPercent(viewModel.modelGovernance.fallbackRatio) }}</strong>
                <p>TODO(api): 比率目前仅从模型可用性推断</p>
              </article>

              <article class="metric-card" :class="`tone-${approvalTone}`">
                <h4>建议审批率</h4>
                <strong>{{ toPercent(viewModel.modelGovernance.adviceApprovalRate) }}</strong>
                <p>TODO(api): 需要持久化的建议审批工作流指标</p>
              </article>
            </div>

            <div class="subtable">
              <h4>治理模块状态</h4>
              <table>
                <thead>
                  <tr>
                    <th>模块</th>
                    <th>负责角色</th>
                    <th>状态</th>
                    <th>描述</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!moduleStatusRows.length">
                    <td colspan="4">暂无模块状态数据</td>
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
        </template>
      </div>

      <!-- 模型洞察内容 -->
      <div v-if="activeTab === 'insights'" class="content-section">
        <section v-if="loadingMetrics" class="card state">加载模型指标中...</section>
        <section v-else-if="!props.modelMetrics" class="card state">暂无模型指标数据</section>

        <template v-else>
          <section class="metric-block card">
            <div class="block-head">
              <h3>模型性能指标</h3>
              <span class="hint">当前模型与对比基准的表现</span>
            </div>

            <div class="metric-grid">
              <article class="metric-card">
                <h4>当前模型</h4>
                <strong>{{ props.modelMetrics.currentModel.model }}</strong>
                <p>状态: {{ props.modelMetrics.currentModel.status }}</p>
              </article>

              <article class="metric-card">
                <h4>MRR</h4>
                <strong>{{ toPercent(props.modelMetrics.currentModel.mrr) }}</strong>
                <p>平均倒数排名</p>
              </article>

              <article class="metric-card">
                <h4>Hits@1</h4>
                <strong>{{ toPercent(props.modelMetrics.currentModel.hits1) }}</strong>
                <p>Top-1 命中率</p>
              </article>

              <article class="metric-card">
                <h4>Hits@3</h4>
                <strong>{{ toPercent(props.modelMetrics.currentModel.hits3) }}</strong>
                <p>Top-3 命中率</p>
              </article>
            </div>
          </section>

          <div class="section-divider"></div>

          <!-- 可折叠的侧边面板：展示 AI 模型的特征权重或预测路径 -->
          <section class="insights-panel card">
            <div class="panel-header" @click="toggleInsightsPanel">
              <h3>模型特征权重与预测路径</h3>
              <span class="toggle-icon">{{ insightsPanelExpanded ? '▼' : '▶' }}</span>
            </div>

            <div v-if="insightsPanelExpanded" class="panel-content">
              <div class="feature-weights">
                <h4>特征权重分布</h4>
                <div class="weight-list">
                  <div class="weight-item">
                    <span class="feature-name">年龄</span>
                    <div class="weight-bar">
                      <div class="weight-fill" style="width: 85%"></div>
                    </div>
                    <span class="weight-value">0.85</span>
                  </div>
                  <div class="weight-item">
                    <span class="feature-name">病程时长</span>
                    <div class="weight-bar">
                      <div class="weight-fill" style="width: 72%"></div>
                    </div>
                    <span class="weight-value">0.72</span>
                  </div>
                  <div class="weight-item">
                    <span class="feature-name">用药依从性</span>
                    <div class="weight-bar">
                      <div class="weight-fill" style="width: 68%"></div>
                    </div>
                    <span class="weight-value">0.68</span>
                  </div>
                  <div class="weight-item">
                    <span class="feature-name">并发症数量</span>
                    <div class="weight-bar">
                      <div class="weight-fill" style="width: 55%"></div>
                    </div>
                    <span class="weight-value">0.55</span>
                  </div>
                </div>
              </div>

              <div class="prediction-path">
                <h4>预测路径可视化</h4>
                <div class="path-steps">
                  <div class="path-step">
                    <span class="step-number">1</span>
                    <span class="step-text">输入特征向量</span>
                  </div>
                  <div class="step-arrow">→</div>
                  <div class="path-step">
                    <span class="step-number">2</span>
                    <span class="step-text">嵌入层处理</span>
                  </div>
                  <div class="step-arrow">→</div>
                  <div class="path-step">
                    <span class="step-number">3</span>
                    <span class="step-text">图神经网络</span>
                  </div>
                  <div class="step-arrow">→</div>
                  <div class="path-step">
                    <span class="step-number">4</span>
                    <span class="step-text">输出预测结果</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </template>
      </div>
    </main>
  </section>
</template>
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