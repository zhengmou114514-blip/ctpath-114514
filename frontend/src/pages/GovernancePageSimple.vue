<script setup lang="ts">
import { ref, computed } from 'vue'
import type { 
  DoctorUser, 
  HealthResponse, 
  MaintenanceOverview,
  ModelMetricsResponse 
} from '../services/types'

const props = defineProps<{
  doctorRole: DoctorUser['role']
  health: HealthResponse | null
  maintenance: MaintenanceOverview | null
  modelMetrics: ModelMetricsResponse | null
  loadingMaintenance: boolean
  loadingMetrics: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

// 当前激活的标签页
const activeTab = ref('system')

// 系统状态
const systemStatus = computed(() => {
  if (!props.health) return '未知'
  return props.health.status === 'ok' ? '正常' : '异常'
})

// 数据库状态
const dbStatus = computed(() => {
  if (!props.health?.db) return '未知'
  return props.health.db === 'connected' ? '已连接' : '未连接'
})

// 模型状态
const modelStatus = computed(() => {
  if (!props.modelMetrics) return '未加载'
  return '已加载'
})

// 患者统计
const patientStats = computed(() => {
  if (!props.maintenance) return null
  return {
    total: props.maintenance.patientCount || 0,
    highRisk: props.maintenance.highRiskCount || 0,
    lowSupport: props.maintenance.lowSupportCount || 0
  }
})
</script>

<template>
  <div class="governance-page-simple">
    <!-- 标签页切换 -->
    <div class="tabs">
      <button :class="{ active: activeTab === 'system' }" @click="activeTab = 'system'">
        系统状态
      </button>
      <button :class="{ active: activeTab === 'data' }" @click="activeTab = 'data'">
        数据概览
      </button>
      <button v-if="doctorRole === 'doctor'" :class="{ active: activeTab === 'model' }" @click="activeTab = 'model'">
        模型信息
      </button>
    </div>
    
    <!-- 系统状态 -->
    <div v-if="activeTab === 'system'" class="tab-content">
      <div class="status-grid">
        <div class="status-card">
          <div class="label">系统状态</div>
          <div class="value" :class="systemStatus === '正常' ? 'success' : 'error'">
            {{ systemStatus }}
          </div>
        </div>
        
        <div class="status-card">
          <div class="label">数据库</div>
          <div class="value" :class="dbStatus === '已连接' ? 'success' : 'error'">
            {{ dbStatus }}
          </div>
        </div>
        
        <div class="status-card">
          <div class="label">预测模型</div>
          <div class="value" :class="modelStatus === '已加载' ? 'success' : 'warning'">
            {{ modelStatus }}
          </div>
        </div>
        
        <div class="status-card">
          <div class="label">版本</div>
          <div class="value">{{ health?.version || '-' }}</div>
        </div>
      </div>
      
      <div class="action-bar">
        <button @click="emit('refresh')">刷新状态</button>
      </div>
    </div>
    
    <!-- 数据概览 -->
    <div v-else-if="activeTab === 'data'" class="tab-content">
      <div v-if="patientStats" class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ patientStats.total }}</div>
          <div class="stat-label">患者总数</div>
        </div>
        
        <div class="stat-card highlight">
          <div class="stat-value">{{ patientStats.highRisk }}</div>
          <div class="stat-label">高风险患者</div>
        </div>
        
        <div class="stat-card warning">
          <div class="stat-value">{{ patientStats.lowSupport }}</div>
          <div class="stat-label">低支持度患者</div>
        </div>
      </div>
      
      <div v-else class="empty">暂无数据</div>
    </div>
    
    <!-- 模型信息 -->
    <div v-else-if="activeTab === 'model'" class="tab-content">
      <div v-if="modelMetrics" class="model-info">
        <div class="info-section">
          <h3>模型性能</h3>
          <div class="info-row">
            <span class="label">准确率</span>
            <span class="value">{{ (modelMetrics.accuracy * 100).toFixed(1) }}%</span>
          </div>
          <div class="info-row">
            <span class="label">召回率</span>
            <span class="value">{{ (modelMetrics.recall * 100).toFixed(1) }}%</span>
          </div>
          <div class="info-row">
            <span class="label">F1分数</span>
            <span class="value">{{ (modelMetrics.f1Score * 100).toFixed(1) }}%</span>
          </div>
        </div>
        
        <div class="info-section">
          <h3>训练信息</h3>
          <div class="info-row">
            <span class="label">训练样本</span>
            <span class="value">{{ modelMetrics.trainingSamples }}</span>
          </div>
          <div class="info-row">
            <span class="label">最后训练</span>
            <span class="value">{{ modelMetrics.lastTrained || '-' }}</span>
          </div>
        </div>
      </div>
      
      <div v-else class="empty">模型信息未加载</div>
    </div>
  </div>
</template>

<style scoped>
.governance-page-simple {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  background: white;
  padding: 8px;
  border-radius: 4px;
}

.tabs button {
  flex: 1;
  padding: 10px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-radius: 4px;
  transition: all 0.3s;
}

.tabs button:hover {
  background: #f5f5f5;
}

.tabs button.active {
  background: #1890ff;
  color: white;
}

.tab-content {
  background: white;
  border-radius: 4px;
  padding: 20px;
}

/* 系统状态 */
.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.status-card {
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
  text-align: center;
}

.status-card .label {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}

.status-card .value {
  font-size: 18px;
  font-weight: 600;
}

.status-card .value.success {
  color: #52c41a;
}

.status-card .value.error {
  color: #f5222d;
}

.status-card .value.warning {
  color: #fa8c16;
}

.action-bar {
  text-align: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.action-bar button {
  padding: 8px 24px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

/* 数据概览 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  padding: 24px;
  background: #fafafa;
  border-radius: 4px;
  text-align: center;
}

.stat-card .stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #333;
  margin-bottom: 8px;
}

.stat-card .stat-label {
  font-size: 14px;
  color: #999;
}

.stat-card.highlight {
  background: #fff1f0;
}

.stat-card.highlight .stat-value {
  color: #f5222d;
}

.stat-card.warning {
  background: #fff7e6;
}

.stat-card.warning .stat-value {
  color: #fa8c16;
}

/* 模型信息 */
.model-info {
  max-width: 600px;
}

.info-section {
  margin-bottom: 24px;
}

.info-section h3 {
  margin: 0 0 12px 0;
  font-size: 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #fafafa;
}

.info-row .label {
  color: #666;
}

.info-row .value {
  font-weight: 500;
}

.empty {
  padding: 40px;
  text-align: center;
  color: #999;
}

/* 响应式 */
@media (max-width: 768px) {
  .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
