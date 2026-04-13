<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  modelMetrics: any
  patientCount: number
  followupCount: number
  systemMode: string
}>()

const emit = defineEmits<{
  refresh: []
  exportReport: []
}>()

// 高风险患者预警列表（示例数据）
const highRiskPatients = ref([
  {
    id: 'P001',
    name: '张三',
    ctResult: '肺结节',
    riskLevel: '高',
    warningTime: '2024-01-15 10:30',
    lastFollowup: '2024-01-10'
  },
  {
    id: 'P002',
    name: '李四',
    ctResult: '肺结节增大',
    riskLevel: '高',
    warningTime: '2024-01-15 09:15',
    lastFollowup: '2024-01-08'
  },
  {
    id: 'P003',
    name: '王五',
    ctResult: '新发结节',
    riskLevel: '中',
    warningTime: '2024-01-14 16:45',
    lastFollowup: '2024-01-12'
  },
  {
    id: 'P004',
    name: '赵六',
    ctResult: '结节稳定',
    riskLevel: '低',
    warningTime: '2024-01-14 14:20',
    lastFollowup: '2024-01-13'
  }
])

function getRiskColor(level: string): string {
  switch (level) {
    case '高': return 'high'
    case '中': return 'medium'
    case '低': return 'low'
    default: return 'neutral'
  }
}

function viewTrack(patientId: string) {
  console.log('查看轨迹:', patientId)
}

function createFollowup(patientId: string) {
  console.log('下发随访:', patientId)
}

const showDemoAlert = computed(() => props.systemMode === 'demo')
</script>

<template>
  <section class="insights-page">
    <!-- Demo 环境提示 -->
    <div v-if="showDemoAlert" class="demo-alert">
      <span class="alert-icon">⚠️</span>
      <span class="alert-text">当前处于演示环境，数据为模拟数据，仅供功能展示使用</span>
    </div>

    <header class="page-header card">
      <div class="header-left">
        <h2>模型洞察</h2>
        <span class="module-badge">AI 模型性能监控与风险预警</span>
      </div>
      <div class="header-actions">
        <button class="secondary-button" @click="emit('refresh')">刷新数据</button>
        <button class="primary-button" @click="emit('exportReport')">导出报表</button>
      </div>
    </header>

    <!-- 统计卡片区域 -->
    <section class="stats-cards">
      <div class="stat-card">
        <span class="stat-label">患者总数</span>
        <strong class="stat-value">{{ props.patientCount }}</strong>
      </div>
      
      <div class="stat-card">
        <span class="stat-label">随访任务</span>
        <strong class="stat-value">{{ props.followupCount }}</strong>
      </div>
      
      <div class="stat-card">
        <span class="stat-label">模型状态</span>
        <span class="stat-status" :class="props.modelMetrics.currentModel.available ? 'success' : 'error'">
          {{ props.modelMetrics.currentModel.available ? '正常' : '异常' }}
        </span>
      </div>
    </section>

    <!-- 模型性能指标 -->
    <section class="metric-block card">
      <div class="block-head">
        <h3>模型性能指标</h3>
        <span class="hint">当前模型：{{ props.modelMetrics.currentModel.name }}</span>
      </div>

      <div class="metric-grid">
        <article class="metric-card">
          <h4>AUC</h4>
          <strong>{{ (props.modelMetrics.currentModel.auc * 100).toFixed(1) }}%</strong>
          <p>曲线下面积</p>
        </article>

        <article class="metric-card">
          <h4>MRR</h4>
          <strong>{{ (props.modelMetrics.currentModel.mrr * 100).toFixed(1) }}%</strong>
          <p>平均倒数排名</p>
        </article>

        <article class="metric-card">
          <h4>Hits@1</h4>
          <strong>{{ (props.modelMetrics.currentModel.hits1 * 100).toFixed(1) }}%</strong>
          <p>Top-1 命中率</p>
        </article>

        <article class="metric-card">
          <h4>Hits@3</h4>
          <strong>{{ (props.modelMetrics.currentModel.hits3 * 100).toFixed(1) }}%</strong>
          <p>Top-3 命中率</p>
        </article>
      </div>
    </section>

    <!-- 高风险患者预警列表 -->
    <section class="warning-block card">
      <div class="block-head">
        <h3>高风险患者预警列表</h3>
        <span class="hint">需要重点关注和随访的患者</span>
      </div>

      <div class="warning-table-container">
        <table class="warning-table">
          <thead>
            <tr>
              <th>患者姓名</th>
              <th>CT识别结果</th>
              <th>风险等级</th>
              <th>预警时间</th>
              <th>最近随访</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="patient in highRiskPatients" :key="patient.id">
              <td class="patient-name">
                <strong>{{ patient.name }}</strong>
              </td>
              <td class="ct-result">{{ patient.ctResult }}</td>
              <td class="risk-level">
                <span class="risk-badge" :class="getRiskColor(patient.riskLevel)">
                  {{ patient.riskLevel }}
                </span>
              </td>
              <td class="warning-time">{{ patient.warningTime }}</td>
              <td class="last-followup">{{ patient.lastFollowup }}</td>
              <td class="actions">
                <button class="action-btn secondary" @click="viewTrack(patient.id)">
                  查看轨迹
                </button>
                <button class="action-btn primary" @click="createFollowup(patient.id)">
                  下发随访
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </section>
</template>

<style scoped>
.insights-page {
  padding: 24px;
  display: grid;
  gap: 24px;
  align-content: start;
}

/* Demo 环境提示 */
.demo-alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: #fff1f0;
  border: 1px solid #ffa39e;
  border-radius: 8px;
  color: #cf1322;
  font-size: 14px;
  font-weight: 500;
}

.alert-icon {
  font-size: 18px;
}

/* 页面标题 */
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

.header-actions {
  display: flex;
  gap: 12px;
}

/* 统计卡片区域 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-label {
  font-size: 14px;
  color: #595959;
  font-weight: 500;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #1890ff;
  line-height: 1;
}

.stat-status {
  display: inline-flex;
  align-items: center;
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
}

.stat-status.success {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.stat-status.error {
  background: #fff1f0;
  color: #ff4d4f;
  border: 1px solid #ffa39e;
}

/* 模型性能指标 */
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

/* 高风险患者预警列表 */
.warning-block {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.warning-table-container {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.warning-table {
  width: 100%;
  border-collapse: collapse;
}

.warning-table thead {
  background: #fafafa;
  border-bottom: 2px solid #e2e8f0;
}

.warning-table th {
  padding: 14px 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #595959;
}

.warning-table tbody tr {
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s ease;
}

.warning-table tbody tr:hover {
  background: #fafafa;
}

.warning-table tbody tr:last-child {
  border-bottom: none;
}

.warning-table td {
  padding: 14px 16px;
  font-size: 14px;
  color: #2d3748;
}

.patient-name strong {
  font-weight: 600;
  color: #1a202c;
}

.ct-result {
  color: #718096;
}

.risk-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
}

.risk-badge.high {
  background: #ff4d4f;
  color: #fff;
}

.risk-badge.medium {
  background: #faad14;
  color: #fff;
}

.risk-badge.low {
  background: #52c41a;
  color: #fff;
}

.warning-time,
.last-followup {
  color: #a0aec0;
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid;
}

.action-btn.primary {
  background: #1890ff;
  color: #fff;
  border-color: #1890ff;
}

.action-btn.primary:hover {
  background: #40a9ff;
  border-color: #40a9ff;
}

.action-btn.secondary {
  background: #fff;
  color: #1890ff;
  border-color: #1890ff;
}

.action-btn.secondary:hover {
  background: #e6f7ff;
}

@media (max-width: 1400px) {
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .stats-cards {
    grid-template-columns: 1fr;
  }
}
</style>
