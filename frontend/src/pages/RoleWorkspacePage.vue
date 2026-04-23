<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Lock, TrendCharts } from '@element-plus/icons-vue'
import { getCoordinationBoard, getRoleWorkspace, getRoleWorkspaces } from '../services/api'
import { buildModelBoardSnapshot } from '../services/modelBoardAdapter'
import { useWorkspaceContext } from '../composables/workspaceContext'
import type { CoordinationBoardResponse, CoordinationItem } from '../services/types'

const workspace = useWorkspaceContext()

const coordinationBoard = ref<CoordinationBoardResponse | null>(null)
const loading = ref(false)

const roleWorkspace = computed(() => {
  const doctor = workspace.currentDoctor
  if (!doctor) return null
  return getRoleWorkspace(doctor.role)
})

const roleWorkspaces = computed(() => getRoleWorkspaces())
const authzSections = computed(() => workspace.authz?.allowedSections ?? [])
const authzApis = computed(() => workspace.authz?.allowedApis ?? [])

const canOpenModelDashboard = computed(() => authzSections.value.includes('model-dashboard'))
const canOpenTrainingCenter = computed(() => authzSections.value.includes('training-center'))
const canOpenModelOperations = computed(() => authzSections.value.includes('model-operations'))
const canOpenInsights = computed(() => authzSections.value.includes('insights'))
const canOpenCoordination = computed(() => authzSections.value.includes('coordination'))

const modelSnapshot = computed(() =>
  buildModelBoardSnapshot({
    modelMetrics: workspace.modelMetrics,
  })
)

const collaborationItems = computed<CoordinationItem[]>(() => coordinationBoard.value?.items.slice(0, 5) ?? [])

const collaborationStats = computed(() => {
  const items = coordinationBoard.value?.items ?? []
  return [
    { label: '协同总数', value: String(items.length), hint: '多角色推进的患者事项' },
    { label: '待处理', value: String(items.filter((item) => item.status === 'open').length), hint: '等待责任人接手' },
    { label: '处理中', value: String(items.filter((item) => item.status === 'in_progress').length), hint: '正在推进的任务' },
    { label: '阻塞项', value: String(items.filter((item) => item.status === 'blocked').length), hint: '需要额外协同' },
  ]
})

const dataInteractionCards = computed(() => [
  {
    title: '医生 -> 档案员',
    detail: '患者身份、附件、时间线和电子档案同步到患者档案页。',
    status: 'archive',
  },
  {
    title: '医生/护士 -> 药师',
    detail: '当前用药、处方审核、药品权限和药房复核进入药事闭环。',
    status: 'medication',
  },
  {
    title: '协同 -> 模型中心',
    detail: '患者级预测、模型看板和训练任务只在授权角色中开放。',
    status: canOpenModelDashboard.value ? 'model-center' : 'locked',
  },
])

function formatTime(value?: string | null) {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 16)
}

function labelForSection(section: string) {
  const labels: Record<string, string> = {
    doctor: '医生工作台',
    archive: '患者档案',
    emr: '电子病历',
    pharmacy: '药房药库',
    coordination: '医护协调',
    tasks: '随访任务',
    contacts: '联系记录',
    flow: '病程流转',
    insights: '模型洞察',
    governance: '治理看板',
    'data-quality': '数据质量',
    'drug-management': '药品目录',
    'drug-permission-management': '药品权限',
    'model-dashboard': '模型看板',
    'training-center': '训练中心',
    'model-operations': '模型调试台',
    'role-workspaces': '权限与角色工作台',
    system: '系统中心',
  }
  return labels[section] ?? section
}

function openSection(section: Parameters<typeof workspace.selectSection>[0]) {
  workspace.selectSection(section)
}

async function refresh() {
  loading.value = true
  try {
    if (!workspace.authz) {
      await workspace.refreshSystemCenter()
    }
    if (canOpenModelDashboard.value && !workspace.modelMetrics) {
      await workspace.refreshModelMetrics()
    }
    if (canOpenCoordination.value) {
      coordinationBoard.value = await getCoordinationBoard()
    } else {
      coordinationBoard.value = null
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void refresh()
})
</script>

<template>
  <section class="workspace-page role-workspace-page">
    <header class="workstation-page-header">
      <div>
        <p class="eyebrow">权限中心</p>
        <h1>权限与角色工作台</h1>
        <p>统一查看角色边界、协作分工、数据交互和模型后台门禁。这里是权限收口页，不替代医生首页或患者详情。</p>
      </div>
      <div class="header-actions">
        <button class="secondary-button" type="button" :disabled="loading" @click="refresh">刷新</button>
        <button class="primary-button" type="button" @click="openSection('coordination')">进入协同</button>
      </div>
    </header>

    <section class="metric-grid four">
      <article class="metric-card">
        <span>当前角色</span>
        <strong>{{ workspace.currentDoctor?.role ?? '--' }}</strong>
        <p>{{ workspace.currentDoctor?.name ?? '--' }}</p>
      </article>
      <article class="metric-card">
        <span>可见模块</span>
        <strong>{{ authzSections.length }}</strong>
        <p>来自后端 `/api/authz/capabilities`</p>
      </article>
      <article class="metric-card">
        <span>可访问 API</span>
        <strong>{{ authzApis.length }}</strong>
        <p>当前角色的后端能力集合</p>
      </article>
      <article class="metric-card">
        <span>协同记录</span>
        <strong>{{ collaborationStats[0]?.value ?? 0 }}</strong>
        <p>多用户推进的患者事项</p>
      </article>
    </section>

    <section class="role-grid">
      <article class="clinical-card role-profile-card">
        <div class="section-header">
          <div>
            <h2>当前角色概览</h2>
            <p>对齐当前账号的可见模块、禁止模块和职责边界。</p>
          </div>
        </div>

        <div v-if="roleWorkspace" class="role-profile">
          <div class="role-profile-head">
            <div>
              <p class="eyebrow">{{ roleWorkspace.title }}</p>
              <strong>{{ workspace.currentDoctor?.name }}</strong>
              <span>{{ workspace.currentDoctor?.department }}</span>
            </div>
            <span class="role-badge">
              <el-icon><Lock /></el-icon>
              {{ roleWorkspace.role }}
            </span>
          </div>

          <p class="role-description">{{ roleWorkspace.description }}</p>

          <div>
            <h3>主模块</h3>
            <div class="chip-row">
              <span v-for="module in roleWorkspace.primaryModules" :key="module.key" class="role-chip">
                {{ module.label }}
              </span>
            </div>
          </div>

          <div>
            <h3>禁止边界</h3>
            <div class="chip-row">
              <span v-for="item in roleWorkspace.forbiddenModules" :key="item" class="role-chip muted">
                {{ item }}
              </span>
            </div>
          </div>

          <div>
            <h3>审计聚焦</h3>
            <div class="chip-row">
              <span v-for="item in roleWorkspace.auditFocus" :key="item" class="role-chip outline">
                {{ item }}
              </span>
            </div>
          </div>
        </div>
      </article>

      <article class="clinical-card role-overview-card">
        <div class="section-header">
          <div>
            <h2>角色总览</h2>
            <p>按职责查看全部工作台，帮助确认谁能做什么、不能做什么。</p>
          </div>
          <el-icon class="section-icon"><TrendCharts /></el-icon>
        </div>

        <div class="role-overview-grid">
          <article v-for="item in roleWorkspaces" :key="item.role" class="role-overview-item">
            <div class="role-overview-head">
              <strong>{{ item.title }}</strong>
              <span>{{ item.role }}</span>
            </div>
            <p>{{ item.description }}</p>
            <div class="chip-row">
              <span v-for="module in item.primaryModules" :key="module.key" class="role-chip outline">
                {{ module.label }}
              </span>
            </div>
          </article>
        </div>
      </article>

      <article class="clinical-card permission-card">
        <div class="section-header">
          <div>
            <h2>权限矩阵</h2>
            <p>前端菜单与后端能力使用同一套模块边界。</p>
          </div>
        </div>

        <div class="chip-row">
          <span v-for="section in authzSections" :key="section" class="role-chip outline">{{ labelForSection(section) }}</span>
        </div>

        <ul class="permission-list">
          <li>
            <strong>模型看板</strong>
            <span :class="canOpenModelDashboard ? 'text-ready' : 'text-muted'">{{ canOpenModelDashboard ? '已授权' : '未授权' }}</span>
          </li>
          <li>
            <strong>训练中心</strong>
            <span :class="canOpenTrainingCenter ? 'text-ready' : 'text-muted'">{{ canOpenTrainingCenter ? '已授权' : '未授权' }}</span>
          </li>
          <li>
            <strong>模型调试台</strong>
            <span :class="canOpenModelOperations ? 'text-ready' : 'text-muted'">{{ canOpenModelOperations ? '已授权' : '未授权' }}</span>
          </li>
          <li>
            <strong>协同工作台</strong>
            <span :class="canOpenCoordination ? 'text-ready' : 'text-muted'">{{ canOpenCoordination ? '已授权' : '未授权' }}</span>
          </li>
          <li>
            <strong>模型洞察</strong>
            <span :class="canOpenInsights ? 'text-ready' : 'text-muted'">{{ canOpenInsights ? '已授权' : '未授权' }}</span>
          </li>
        </ul>
      </article>
    </section>

    <section class="role-grid">
      <article class="clinical-card">
        <div class="section-header">
          <div>
            <h2>多用户协作</h2>
            <p>围绕同一患者，医生、护士、药师和档案员按职责协同推进。</p>
          </div>
        </div>

        <div class="collaboration-grid">
          <article v-for="item in collaborationStats" :key="item.label" class="collaboration-card">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <small>{{ item.hint }}</small>
          </article>
        </div>

        <div class="interaction-flow">
          <article v-for="card in dataInteractionCards" :key="card.title" class="flow-card">
            <div class="flow-head">
              <strong>{{ card.title }}</strong>
              <span>{{ card.status }}</span>
            </div>
            <p>{{ card.detail }}</p>
          </article>
        </div>
      </article>

      <article class="clinical-card">
        <div class="section-header">
          <div>
            <h2>协同记录</h2>
            <p>展示最近的跨角色推进事项，帮助把数据交互和协作闭环串起来。</p>
          </div>
          <button class="secondary-button" type="button" :disabled="!canOpenCoordination" @click="openSection('coordination')">打开协同台</button>
        </div>

        <div v-if="!collaborationItems.length" class="empty-inline">当前没有可展示的协同记录。</div>
        <div v-else class="coordination-preview-list">
          <article v-for="item in collaborationItems" :key="item.coordinationId" class="coordination-preview-card">
            <div class="preview-head">
              <strong>{{ item.patientName }}</strong>
              <span>{{ item.coordinationId }}</span>
            </div>
            <p>{{ item.primaryDisease }} / {{ item.ownerName }} / {{ item.nextAction }}</p>
            <small>{{ formatTime(item.dueDate) }} · {{ item.status }}</small>
          </article>
        </div>
      </article>
    </section>

    <section class="clinical-card">
      <div class="section-header">
        <div>
          <h2>模型后台与训练闭环</h2>
          <p>授权后才开放模型看板、训练中心和调试台，避免把训练和治理动作混进临床主流程。</p>
        </div>
      </div>

      <div class="model-summary-grid">
        <article class="model-summary-card">
          <span>模型版本</span>
          <strong>{{ modelSnapshot.currentModelVersion }}</strong>
          <small>{{ modelSnapshot.currentModelName }}</small>
        </article>
        <article class="model-summary-card">
          <span>最近训练</span>
          <strong>{{ formatTime(modelSnapshot.recentTrainingTime) }}</strong>
          <small>{{ modelSnapshot.recentTrainingTaskStatus }}</small>
        </article>
        <article class="model-summary-card">
          <span>模型健康</span>
          <strong>{{ workspace.health?.model_available ? '可用' : '降级' }}</strong>
          <small>{{ workspace.health?.mode ?? '--' }}</small>
        </article>
        <article class="model-summary-card">
          <span>回退比例</span>
          <strong>{{ modelSnapshot.fallbackRatio === null ? '--' : `${Math.round(modelSnapshot.fallbackRatio * 100)}%` }}</strong>
          <small>推理回退占比</small>
        </article>
      </div>

      <div class="action-row">
        <button class="secondary-button" type="button" :disabled="!canOpenInsights" @click="openSection('insights')">患者模型洞察</button>
        <button class="secondary-button" type="button" :disabled="!canOpenModelDashboard" @click="openSection('model-dashboard')">模型看板</button>
        <button class="secondary-button" type="button" :disabled="!canOpenTrainingCenter" @click="openSection('training-center')">训练中心</button>
        <button class="secondary-button" type="button" :disabled="!canOpenModelOperations" @click="openSection('model-operations')">模型调试台</button>
      </div>
    </section>
  </section>
</template>

<style scoped>
.role-workspace-page {
  display: grid;
  gap: 24px;
}

.role-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.role-profile-card,
.role-overview-card,
.permission-card {
  display: grid;
  gap: 16px;
}

.role-profile {
  display: grid;
  gap: 18px;
}

.role-profile-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
}

.role-profile-head strong {
  display: block;
  color: var(--ws-title);
  font-size: 22px;
}

.role-profile-head span {
  color: var(--ws-text-muted);
}

.section-icon {
  color: var(--ws-accent);
  font-size: 18px;
}

.role-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.08);
  padding: 6px 12px;
  color: var(--ws-title);
  font-weight: 700;
}

.role-description {
  margin: 0;
  color: var(--ws-text-muted);
  line-height: 1.7;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.role-chip {
  border-radius: 999px;
  padding: 7px 12px;
  background: rgba(15, 118, 110, 0.08);
  color: var(--ws-title);
  font-size: 12px;
  font-weight: 700;
}

.role-chip.muted {
  background: rgba(148, 163, 184, 0.16);
  color: rgba(15, 23, 42, 0.72);
}

.role-chip.outline {
  background: transparent;
  border: 1px solid rgba(15, 118, 110, 0.2);
}

.role-overview-grid {
  display: grid;
  gap: 12px;
}

.role-overview-item {
  display: grid;
  gap: 10px;
  border: 1px solid var(--ws-border);
  border-radius: 16px;
  background: var(--ws-surface-soft);
  padding: 14px;
}

.role-overview-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.role-overview-head strong {
  color: var(--ws-title);
  font-size: 15px;
}

.role-overview-head span {
  color: var(--ws-text-muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.role-overview-item p {
  margin: 0;
  color: var(--ws-text-muted);
  line-height: 1.6;
}

.permission-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
}

.permission-list li {
  list-style: none;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--ws-border);
  border-radius: 14px;
  background: var(--ws-surface-soft);
}

.text-ready {
  color: #0f766e;
  font-weight: 700;
}

.text-muted {
  color: var(--ws-text-muted);
}

.collaboration-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.collaboration-card,
.model-summary-card {
  display: grid;
  gap: 8px;
  border-radius: 16px;
  border: 1px solid var(--ws-border);
  background: var(--ws-surface-soft);
  padding: 14px;
}

.collaboration-card span,
.model-summary-card span {
  color: var(--ws-text-muted);
  font-size: 12px;
}

.collaboration-card strong,
.model-summary-card strong {
  color: var(--ws-title);
  font-size: 20px;
}

.collaboration-card small,
.model-summary-card small,
.flow-card p,
.coordination-preview-card p,
.coordination-preview-card small {
  color: var(--ws-text-muted);
  line-height: 1.6;
}

.interaction-flow,
.coordination-preview-list,
.model-summary-grid {
  display: grid;
  gap: 12px;
}

.flow-card,
.coordination-preview-card {
  border: 1px solid var(--ws-border);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.84);
  padding: 14px;
}

.flow-head,
.preview-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.flow-head span,
.preview-head span {
  color: var(--ws-title);
  font-size: 12px;
  font-weight: 700;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.empty-inline {
  margin: 0;
  border: 1px dashed var(--ws-border-strong);
  border-radius: 14px;
  padding: 16px;
  color: var(--ws-text-muted);
  text-align: center;
}

@media (max-width: 1180px) {
  .role-grid,
  .collaboration-grid {
    grid-template-columns: 1fr;
  }

  .role-profile-head {
    display: grid;
  }
}
</style>
