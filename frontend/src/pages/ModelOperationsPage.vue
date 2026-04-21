<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceContext } from '../composables/workspaceContext'
import { getSystemAudit } from '../services/api'
import { buildModelBoardSnapshot } from '../services/modelBoardAdapter'
import { listModelDatasets, listTrainingTasks } from '../services/modelTrainingAdapter'
import type { SystemAuditLog } from '../services/types'

const workspace = useWorkspaceContext()
const router = useRouter()

const loading = ref(false)
const auditError = ref('')
const auditRows = ref<SystemAuditLog[]>([])
const datasetsCount = ref(0)
const trainingTasksCount = ref(0)

const board = computed(() =>
  buildModelBoardSnapshot({
    modelMetrics: workspace.modelMetrics,
    maintenance: workspace.maintenanceOverview,
    patientCount: workspace.allPatients.length,
  })
)

const loginRows = computed(() =>
  auditRows.value.filter((row) => {
    const haystack = `${row.action} ${row.path} ${row.detail}`.toLowerCase()
    return haystack.includes('login') || haystack.includes('signin') || haystack.includes('/api/login')
  })
)

const latestLogin = computed(() => loginRows.value[0] ?? null)
const currentUser = computed(() => workspace.currentDoctor)

const modelHealthLabel = computed(() => {
  if (!workspace.health) return '状态待加载'
  if (workspace.health.model_available) return '模型可用'
  if (workspace.health.model_error) return `降级运行：${workspace.health.model_error}`
  return '模型不可用'
})

function formatDateTime(value?: string | null) {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

async function refreshOperations() {
  loading.value = true
  auditError.value = ''
  try {
    await workspace.refreshGovernanceWorkspace()
    const auditResp = await getSystemAudit(120)
    auditRows.value = auditResp.items
    datasetsCount.value = listModelDatasets().length
    trainingTasksCount.value = listTrainingTasks().length
  } catch (error) {
    auditError.value = error instanceof Error ? error.message : '模型运营台加载失败。'
  } finally {
    loading.value = false
  }
}

function openTrainingCenter() {
  workspace.selectSection('training-center')
  void router.push({ name: 'training-center' })
}

function openModelDashboard() {
  workspace.selectSection('model-dashboard')
  void router.push({ name: 'model-dashboard' })
}

onMounted(() => {
  void refreshOperations()
})
</script>

<template>
  <section class="workspace-page model-operations-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">模型运营台</p>
        <h1>模型运营台</h1>
        <p>单独承接模型相关运营信息，不再混入医生首页。这里集中查看登录次数、当前用户、模型状态和近期训练概览。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" @click="openModelDashboard">返回模型看板</button>
        <button class="primary-button" type="button" @click="openTrainingCenter">进入训练中心</button>
      </div>
    </header>

    <p v-if="auditError" class="error-banner">{{ auditError }}</p>

    <section class="operations-metrics">
      <article class="clinical-card metric-panel">
        <span>登录次数</span>
        <strong>{{ loginRows.length }}</strong>
        <small>基于最近 120 条系统审计记录统计</small>
      </article>
      <article class="clinical-card metric-panel">
        <span>当前用户</span>
        <strong>{{ currentUser?.name || '--' }}</strong>
        <small>{{ currentUser?.department || '--' }} / {{ currentUser?.role || '--' }}</small>
      </article>
      <article class="clinical-card metric-panel">
        <span>模型状态</span>
        <strong>{{ board.currentModelVersion }}</strong>
        <small>{{ modelHealthLabel }}</small>
      </article>
      <article class="clinical-card metric-panel">
        <span>训练资源</span>
        <strong>{{ trainingTasksCount }}</strong>
        <small>{{ datasetsCount }} 个数据集</small>
      </article>
    </section>

    <section class="operations-grid">
      <article class="clinical-card info-panel">
        <div class="section-header">
          <div>
            <h2>用户信息</h2>
            <p>展示当前登录账号和最近一次登录记录。</p>
          </div>
        </div>

        <dl class="detail-list">
          <div>
            <dt>账号</dt>
            <dd>{{ currentUser?.username || '--' }}</dd>
          </div>
          <div>
            <dt>姓名</dt>
            <dd>{{ currentUser?.name || '--' }}</dd>
          </div>
          <div>
            <dt>职称</dt>
            <dd>{{ currentUser?.title || '--' }}</dd>
          </div>
          <div>
            <dt>科室</dt>
            <dd>{{ currentUser?.department || '--' }}</dd>
          </div>
          <div>
            <dt>角色</dt>
            <dd>{{ currentUser?.role || '--' }}</dd>
          </div>
          <div>
            <dt>最近登录</dt>
            <dd>{{ formatDateTime(latestLogin?.createdAt) }}</dd>
          </div>
        </dl>
      </article>

      <article class="clinical-card info-panel">
        <div class="section-header">
          <div>
            <h2>模型信息</h2>
            <p>展示当前模型版本、训练时间和线上推理概览。</p>
          </div>
        </div>

        <dl class="detail-list">
          <div>
            <dt>模型名称</dt>
            <dd>{{ board.currentModelName }}</dd>
          </div>
          <div>
            <dt>模型版本</dt>
            <dd>{{ board.currentModelVersion }}</dd>
          </div>
          <div>
            <dt>最近训练时间</dt>
            <dd>{{ formatDateTime(board.recentTrainingTime) }}</dd>
          </div>
          <div>
            <dt>MRR</dt>
            <dd>{{ board.mrr ? `${(board.mrr * 100).toFixed(1)}%` : '--' }}</dd>
          </div>
          <div>
            <dt>Hits@10</dt>
            <dd>{{ board.hits10 ? `${(board.hits10 * 100).toFixed(1)}%` : '--' }}</dd>
          </div>
          <div>
            <dt>近 7 天调用量</dt>
            <dd>{{ board.recentInferenceCalls ?? '--' }}</dd>
          </div>
        </dl>
      </article>
    </section>

    <section class="operations-grid">
      <article class="clinical-card info-panel">
        <div class="section-header">
          <div>
            <h2>登录审计摘要</h2>
            <p>用于验收登录链路和账号使用情况。</p>
          </div>
          <button class="secondary-button" type="button" :disabled="loading" @click="refreshOperations">刷新</button>
        </div>

        <div v-if="!loginRows.length" class="empty-state-card compact-empty">
          最近没有读到登录相关审计记录。
        </div>
        <div v-else class="audit-list">
          <article v-for="row in loginRows.slice(0, 8)" :key="row.logId" class="audit-item">
            <strong>{{ row.username || '--' }}</strong>
            <p>{{ row.method }} {{ row.path }}</p>
            <small>{{ formatDateTime(row.createdAt) }} / {{ row.result }}</small>
          </article>
        </div>
      </article>

      <article class="clinical-card info-panel">
        <div class="section-header">
          <div>
            <h2>模型运营说明</h2>
            <p>这里承接模型运营信息，不替代患者级模型洞察，也不替代训练中心。</p>
          </div>
        </div>
        <ul class="bullet-list">
          <li>患者级预测结果仍在“患者详情 / 模型洞察”查看。</li>
          <li>训练数据导入和训练任务发起仍在“训练中心”完成。</li>
          <li>本页只做运营态信息汇总，便于答辩展示和链路验收。</li>
          <li>“另一个端口”本轮按独立入口页实现，避免拆分第二套登录会话。</li>
        </ul>
      </article>
    </section>
  </section>
</template>

<style scoped>
.model-operations-page {
  display: grid;
  gap: 24px;
}

.operations-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.metric-panel {
  display: grid;
  gap: 10px;
}

.metric-panel span,
.metric-panel small {
  color: rgba(63, 72, 73, 0.74);
}

.metric-panel strong {
  font-size: clamp(26px, 4vw, 38px);
}

.operations-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.info-panel {
  display: grid;
  gap: 18px;
}

.detail-list {
  display: grid;
  gap: 12px;
  margin: 0;
}

.detail-list div {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(190, 200, 201, 0.45);
}

.detail-list dt {
  color: rgba(63, 72, 73, 0.72);
  font-family: var(--ws-font-headline);
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.detail-list dd {
  margin: 0;
  color: var(--ws-on-surface);
  font-weight: 600;
}

.audit-list {
  display: grid;
  gap: 12px;
}

.audit-item {
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(241, 244, 245, 0.92);
}

.audit-item p,
.audit-item small {
  margin: 6px 0 0;
  color: rgba(63, 72, 73, 0.8);
}

.compact-empty {
  min-height: 180px;
}

@media (max-width: 1180px) {
  .operations-metrics,
  .operations-grid {
    grid-template-columns: 1fr;
  }
}
</style>
