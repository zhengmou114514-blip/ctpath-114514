<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { AuthzCapabilityResponse, DoctorUser, HealthResponse, SystemAuditLog } from '../services/types'
import { getAuthzCapabilities, getSystemAudit } from '../services/api'

const props = defineProps<{
  doctor: DoctorUser
  health: HealthResponse | null
}>()

const loading = ref(false)
const error = ref('')
const caps = ref<AuthzCapabilityResponse | null>(null)
const auditRows = ref<SystemAuditLog[]>([])

const modeLabel = computed(() => props.health?.mode ?? '--')
const modelLabel = computed(() => (props.health?.model_available ? '可用' : '不可用'))

function formatTime(value: string) {
  return (value || '').replace('T', ' ').slice(0, 19) || '--'
}

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const [capsResp, auditResp] = await Promise.all([getAuthzCapabilities(), getSystemAudit(80)])
    caps.value = capsResp
    auditRows.value = auditResp.items
  } catch (e) {
    error.value = e instanceof Error ? e.message : '系统中心加载失败。'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void refresh()
})
</script>

<template>
  <section class="system-center page-shell">
    <header class="card page-header">
      <div>
        <h2>系统中心</h2>
        <p>查看当前账号、权限能力和最近系统审计记录。这里不承接模型训练和患者级诊疗内容。</p>
      </div>
      <button class="primary-button" :disabled="loading" @click="refresh">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </header>

    <p v-if="error" class="error-banner">{{ error }}</p>

    <section class="card grid kpi-grid">
      <article class="kpi">
        <span>运行模式</span>
        <strong>{{ modeLabel }}</strong>
        <small>health: {{ props.health?.status ?? '--' }}</small>
      </article>
      <article class="kpi">
        <span>模型状态</span>
        <strong>{{ modelLabel }}</strong>
        <small>{{ props.health?.model_error ?? '当前无异常' }}</small>
      </article>
      <article class="kpi">
        <span>当前账号</span>
        <strong>{{ props.doctor.name }}</strong>
        <small>{{ props.doctor.department }} / {{ props.doctor.role }}</small>
      </article>
    </section>

    <section class="card grid two-col">
      <article class="panel">
        <h3>可访问模块</h3>
        <p class="hint">根据当前角色返回允许访问的模块和 API 能力。</p>
        <div v-if="!caps" class="empty-mini">正在载入权限信息...</div>
        <template v-else>
          <div class="chips">
            <span v-for="s in caps.allowedSections" :key="s" class="chip">{{ s }}</span>
          </div>
          <details class="api-list">
            <summary>允许访问的 API（{{ caps.allowedApis.length }}）</summary>
            <ul>
              <li v-for="api in caps.allowedApis" :key="api" class="mono">{{ api }}</li>
            </ul>
          </details>
        </template>
      </article>

      <article class="panel">
        <h3>最近审计记录</h3>
        <p class="hint">用于查看访问结果、接口路径和最近账号动作。</p>
        <div v-if="!auditRows.length" class="empty-mini">暂无审计记录。</div>
        <div v-else class="audit-table">
          <header>
            <span>时间</span>
            <span>结果</span>
            <span>角色</span>
            <span>账号</span>
            <span>请求</span>
          </header>
          <article v-for="row in auditRows.slice(0, 30)" :key="row.logId">
            <span>{{ formatTime(row.createdAt) }}</span>
            <span class="badge" :class="row.result === 'denied' ? 'bad' : 'ok'">{{ row.result }}</span>
            <span>{{ row.role ?? '--' }}</span>
            <span>{{ row.username ?? '--' }}</span>
            <span class="mono">{{ row.method }} {{ row.path }}</span>
          </article>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.system-center {
  padding: 20px;
  display: grid;
  gap: 12px;
}

.page-header {
  padding: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.page-header h2 {
  margin: 0;
}

.page-header p {
  margin: 6px 0 0;
  color: var(--ws-text-muted, #617385);
  font-size: 0.92rem;
}

.kpi-grid {
  padding: 12px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.kpi {
  display: grid;
  gap: 6px;
}

.kpi span {
  color: var(--ws-text-muted, #617385);
  font-size: 0.82rem;
}

.kpi strong {
  font-size: 1.2rem;
  color: var(--ws-title, #10263c);
}

.kpi small {
  color: var(--ws-text-muted, #617385);
}

.two-col {
  padding: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.panel h3 {
  margin: 0;
  font-size: 1rem;
}

.hint {
  margin: 6px 0 10px;
  color: var(--ws-text-muted, #617385);
  font-size: 0.86rem;
}

.empty-mini {
  margin: 0;
  border: 1px dashed var(--ws-border-strong, #b8c7d8);
  border-radius: 10px;
  padding: 10px;
  color: var(--ws-text-muted, #617385);
  text-align: center;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  border: 1px solid var(--ws-border, #cfd9e5);
  background: #f7fafd;
  color: var(--ws-title, #10263c);
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
}

.api-list {
  margin-top: 10px;
}

.api-list summary {
  cursor: pointer;
  color: #2f5f8f;
  font-weight: 700;
}

.api-list ul {
  margin: 8px 0 0;
  padding-left: 18px;
  display: grid;
  gap: 6px;
}

.audit-table {
  border: 1px solid var(--ws-border, #cfd9e5);
  border-radius: 10px;
  overflow: hidden;
}

.audit-table header,
.audit-table article {
  display: grid;
  gap: 8px;
  padding: 8px 10px;
  grid-template-columns: 1.3fr .7fr .7fr .9fr 2fr;
  font-size: 0.84rem;
}

.audit-table header {
  background: #f1f6fb;
  color: #2f4f70;
  font-weight: 700;
  border-bottom: 1px solid var(--ws-border, #cfd9e5);
}

.audit-table article {
  border-top: 1px solid #e7edf4;
}

.badge {
  width: fit-content;
  border-radius: 999px;
  padding: 2px 8px;
  border: 1px solid transparent;
  font-weight: 700;
  font-size: 0.78rem;
}

.badge.ok {
  background: #e9f8f1;
  border-color: #bde7d1;
  color: #1d7b5c;
}

.badge.bad {
  background: #fdeced;
  border-color: #efc2c5;
  color: #a4383f;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

@media (max-width: 1100px) {
  .kpi-grid,
  .two-col {
    grid-template-columns: 1fr;
  }

  .audit-table header,
  .audit-table article {
    grid-template-columns: 1fr;
  }
}
</style>
