<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  viewModel: any
  loadingMaintenance: boolean
}>()

const emit = defineEmits<{
  refresh: []
}>()

function toPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '--'
  return `${(value * 100).toFixed(1)}%`
}

const modelStatusText = computed(() => {
  if (!props.viewModel) return '--'
  const { modelAvailable, rulesFallbackActive, similarCaseFallbackActive } = props.viewModel.modelGovernance
  if (modelAvailable) return '正常'
  if (rulesFallbackActive || similarCaseFallbackActive) return '降级'
  return '异常'
})

const fallbackTone = computed(() => {
  if (!props.viewModel) return 'neutral'
  const ratio = props.viewModel.modelGovernance.fallbackRatio
  if (ratio === null || ratio === undefined) return 'neutral'
  if (ratio > 0.3) return 'critical'
  if (ratio > 0.1) return 'warning'
  return 'success'
})

const approvalTone = computed(() => {
  if (!props.viewModel) return 'neutral'
  const rate = props.viewModel.modelGovernance.adviceApprovalRate
  if (rate === null || rate === undefined) return 'neutral'
  if (rate < 0.6) return 'critical'
  if (rate < 0.8) return 'warning'
  return 'success'
})

const moduleStatusRows = computed(() => {
  if (!props.viewModel) return []
  return [
    {
      moduleKey: 'data-quality',
      title: '数据质量治理',
      ownerRole: '系统管理员',
      status: props.viewModel.dataQuality.missingFieldCount > 0 ? '需关注' : '正常',
      tone: props.viewModel.dataQuality.missingFieldCount > 0 ? 'warning' : 'success',
      description: '监控核心字段缺失、重复档案、时间线异常'
    },
    {
      moduleKey: 'model-service',
      title: '模型服务治理',
      ownerRole: '技术团队',
      status: props.viewModel.modelGovernance.modelAvailable ? '正常' : '降级',
      tone: props.viewModel.modelGovernance.modelAvailable ? 'success' : 'warning',
      description: '模型可用性、降级策略、预测调用监控'
    },
    {
      moduleKey: 'archive',
      title: '档案治理',
      ownerRole: '档案管理员',
      status: (props.viewModel.archiveGovernance.pendingCompletionRows.length + props.viewModel.archiveGovernance.pendingReviewRows.length) > 0 ? '需处理' : '正常',
      tone: (props.viewModel.archiveGovernance.pendingCompletionRows.length + props.viewModel.archiveGovernance.pendingReviewRows.length) > 0 ? 'warning' : 'success',
      description: '待完成档案、待审核档案队列管理'
    }
  ]
})
</script>

<template>
  <section class="governance-page">
    <header class="page-header card">
      <div class="header-left">
        <h2>治理看板</h2>
        <span class="module-badge">数据质量与临床决策治理中心</span>
      </div>
      <button class="primary-button" @click="emit('refresh')">刷新数据</button>
    </header>

    <section v-if="loadingMaintenance" class="card state">加载中...</section>
    <section v-else-if="!viewModel" class="card state">暂无数据</section>

    <template v-else>
      <!-- 1. 数据质量概览 -->
      <section class="metric-block card">
        <div class="block-head">
          <h3>1. 数据质量概览</h3>
          <span class="hint">关注直接影响临床可靠性的记录</span>
        </div>

        <div class="metric-grid">
          <article class="metric-card">
            <h4>核心字段缺失</h4>
            <strong>{{ viewModel.dataQuality.missingFieldCount }}</strong>
            <p>MRN缺失、待知情同意、低支持记录总和</p>
          </article>

          <article class="metric-card">
            <h4>重复档案风险</h4>
            <strong>{{ viewModel.dataQuality.duplicateArchiveCount }}</strong>
            <p>主索引风险检查发现的潜在重复档案</p>
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

      <!-- 2. 模型服务治理 -->
      <section class="metric-block card">
        <div class="block-head">
          <h3>2. 模型服务治理</h3>
          <span class="hint">服务健康与降级行为监控</span>
        </div>

        <div class="metric-grid model-grid">
          <article class="metric-card">
            <h4>模型可用性</h4>
            <strong>{{ modelStatusText }}</strong>
            <p>基于后端状态端点的健康/模型标志</p>
          </article>

          <article class="metric-card">
            <h4>预测调用 (7天)</h4>
            <strong>{{ viewModel.modelGovernance.predictionCalls7d ?? '--' }}</strong>
            <p>滚动7天预测调用计数</p>
          </article>

          <article class="metric-card" :class="`tone-${fallbackTone}`">
            <h4>降级比例</h4>
            <strong>{{ toPercent(viewModel.modelGovernance.fallbackRatio) }}</strong>
            <p>规则/相似病例降级占比</p>
          </article>

          <article class="metric-card" :class="`tone-${approvalTone}`">
            <h4>建议采纳率</h4>
            <strong>{{ toPercent(viewModel.modelGovernance.adviceApprovalRate) }}</strong>
            <p>需要持久化的建议审核工作流指标</p>
          </article>
        </div>

        <div class="subtable">
          <h4>治理模块状态</h4>
          <table>
            <thead>
              <tr>
                <th>模块</th>
                <th>负责人</th>
                <th>状态</th>
                <th>描述</th>
              </tr>
            </thead>
            <tbody>
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

      <!-- 3. 档案治理 -->
      <section class="metric-block card">
        <div class="block-head">
          <h3>3. 档案治理</h3>
          <span class="hint">基于队列的档案修复与审核</span>
        </div>

        <div class="table-grid">
          <article class="subtable">
            <h4>待完成档案</h4>
            <table>
              <thead>
                <tr>
                  <th>患者</th>
                  <th>问题</th>
                  <th>详情</th>
                  <th>来源</th>
                  <th>优先级</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!viewModel.archiveGovernance.pendingCompletionRows.length">
                  <td colspan="5">无待完成档案</td>
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
            <h4>待审核档案</h4>
            <table>
              <thead>
                <tr>
                  <th>患者</th>
                  <th>问题</th>
                  <th>详情</th>
                  <th>来源</th>
                  <th>优先级</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!viewModel.archiveGovernance.pendingReviewRows.length">
                  <td colspan="5">无待审核档案</td>
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

      <!-- 4. 操作痕迹 -->
      <section class="metric-block card">
        <div class="block-head">
          <h3>4. 操作痕迹</h3>
          <span class="hint">最近的治理操作、修正记录和风险升级</span>
        </div>

        <div class="table-grid">
          <article class="subtable">
            <h4>治理操作</h4>
            <table>
              <thead>
                <tr>
                  <th>患者</th>
                  <th>摘要</th>
                  <th>操作人</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!viewModel.operationTraces.governanceActions.length">
                  <td colspan="4">无最近治理操作</td>
                </tr>
                <tr v-for="row in viewModel.operationTraces.governanceActions" :key="row.id">
                  <td>{{ row.patientId }} / {{ row.patientName }}</td>
                  <td>{{ row.summary }}</td>
                  <td>{{ row.operator }}</td>
                  <td>{{ row.createdAt }}</td>
                </tr>
              </tbody>
            </table>
          </article>

          <article class="subtable">
            <h4>修正记录</h4>
            <table>
              <thead>
                <tr>
                  <th>患者</th>
                  <th>摘要</th>
                  <th>操作人</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!viewModel.operationTraces.correctionRecords.length">
                  <td colspan="4">无最近修正记录</td>
                </tr>
                <tr v-for="row in viewModel.operationTraces.correctionRecords" :key="row.id">
                  <td>{{ row.patientId }} / {{ row.patientName }}</td>
                  <td>{{ row.summary }}</td>
                  <td>{{ row.operator }}</td>
                  <td>{{ row.createdAt }}</td>
                </tr>
              </tbody>
            </table>
          </article>

          <article class="subtable">
            <h4>风险升级</h4>
            <table>
              <thead>
                <tr>
                  <th>患者</th>
                  <th>摘要</th>
                  <th>操作人</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!viewModel.operationTraces.riskEscalations.length">
                  <td colspan="4">无最近风险升级</td>
                </tr>
                <tr v-for="row in viewModel.operationTraces.riskEscalations" :key="row.id">
                  <td>{{ row.patientId }} / {{ row.patientName }}</td>
                  <td>{{ row.summary }}</td>
                  <td>{{ row.operator }}</td>
                  <td>{{ row.createdAt }}</td>
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
.governance-page {
  padding: 24px;
  display: grid;
  gap: 24px;
  align-content: start;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 20px 24px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2d3748;
}

.module-badge {
  padding: 4px 12px;
  border-radius: 4px;
  background: #e6f7ff;
  color: #1890ff;
  font-size: 13px;
  font-weight: 500;
}

.metric-block {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f3f5;
}

.block-head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2d3748;
}

.hint {
  font-size: 13px;
  color: #718096;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  padding: 16px;
  border-radius: 8px;
  background: #f8f9fa;
  border: 1px solid #e2e8f0;
  display: grid;
  gap: 8px;
}

.metric-card h4 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #4a5568;
}

.metric-card strong {
  font-size: 28px;
  font-weight: 700;
  color: #2d3748;
}

.metric-card p {
  margin: 0;
  font-size: 12px;
  color: #a0aec0;
}

.metric-card.critical {
  background: #fed7d7;
  border-color: #fc8181;
}

.metric-card.critical strong {
  color: #c53030;
}

.metric-card.tone-success {
  background: #c6f6d5;
  border-color: #9ae6b4;
}

.metric-card.tone-warning {
  background: #feebc8;
  border-color: #fbd38d;
}

.metric-card.tone-critical {
  background: #fed7d7;
  border-color: #fc8181;
}

.model-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.subtable {
  margin-top: 24px;
}

.subtable h4 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #2d3748;
}

.subtable table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
}

.subtable th {
  padding: 10px 12px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #4a5568;
  background: #f8f9fa;
  border-bottom: 1px solid #e2e8f0;
}

.subtable td {
  padding: 10px 12px;
  font-size: 13px;
  color: #2d3748;
  border-bottom: 1px solid #f1f3f5;
}

.subtable tbody tr:last-child td {
  border-bottom: none;
}

.table-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.status-pill {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid;
}

.status-pill.tone-success {
  background: #c6f6d5;
  border-color: #9ae6b4;
  color: #276749;
}

.status-pill.tone-warning {
  background: #feebc8;
  border-color: #fbd38d;
  color: #c05621;
}

.status-pill.tone-critical {
  background: #fed7d7;
  border-color: #fc8181;
  color: #c53030;
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

.state {
  padding: 40px;
  text-align: center;
  color: #718096;
  font-size: 14px;
}

@media (max-width: 1400px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .table-grid {
    grid-template-columns: 1fr;
  }
}
</style>
