<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import type {
  ContactLogCreatePayload,
  EncounterStatus,
  MedicationPlanGeneratePayload,
  MedicationPlanResponse,
  OutpatientPlanItem,
  PatientCase,
  PatientQuadruple,
  PredictResponse,
  SimilarCase,
} from '../services/types'
import PatientHeader from './PatientHeader.vue'
import QuadruplePanel from './QuadruplePanel.vue'
import StatsGrid from './StatsGrid.vue'

const props = defineProps<{
  patient: PatientCase | null
  quadruples: PatientQuadruple[]
  predictionResult: PredictResponse | null
  medicationPlanResult: MedicationPlanResponse | null
  loadingPredict: boolean
  savingContactLog: boolean
  encounterStatus: EncounterStatus
}>()

const emit = defineEmits<{
  (e: 'predict'): void
  (e: 'back'): void
  (e: 'open-archive', patientId: string): void
  (e: 'open-archive-events', patientId: string): void
  (e: 'open-followup', patientId: string): void
  (e: 'update-encounter-status', status: EncounterStatus): void
  (e: 'create-outpatient-task', item: OutpatientPlanItem): void
  (e: 'submit-contact-log', payload: ContactLogCreatePayload): void
  (e: 'generate-medication-plan', payload: MedicationPlanGeneratePayload): void
}>()

const currentPrediction = computed(() => props.predictionResult?.topk[0] ?? props.patient?.predictions[0] ?? null)
const predictionItems = computed(() => props.predictionResult?.topk ?? props.patient?.predictions ?? [])
const adviceItems = computed(() => props.predictionResult?.advice ?? props.patient?.careAdvice ?? [])
const adviceMeta = computed(() => props.predictionResult?.adviceMeta ?? props.medicationPlanResult?.adviceMeta ?? null)
const pathItems = computed(() => props.predictionResult?.pathExplanation ?? props.patient?.pathExplanation ?? [])
const evidence = computed(() => props.predictionResult?.evidence ?? null)
const similarCases = computed<SimilarCase[]>(() => props.predictionResult?.similarCases ?? props.patient?.similarCases ?? [])
const followupTasks = computed(() => props.patient?.followUps ?? [])
const contactLogs = computed(() => props.patient?.contactLogs ?? [])

const encounterOptions: Array<{ value: EncounterStatus; label: string; note: string }> = [
  { value: 'waiting', label: '候诊', note: '等待接诊与任务确认' },
  { value: 'in_progress', label: '接诊中', note: '门诊评估与计划执行中' },
  { value: 'pending_review', label: '待复核', note: '待医生复核预测与处置' },
  { value: 'completed', label: '已完成', note: '本次接诊流程已完成' },
]

const evidenceAnchor = ref<HTMLElement | null>(null)
const evidenceFocusState = ref<{ active: boolean; hint: string }>({ active: false, hint: '' })
let evidenceFocusTimer: ReturnType<typeof setTimeout> | null = null

const contactType = ref<ContactLogCreatePayload['contactType']>('phone')
const contactTarget = ref<ContactLogCreatePayload['contactTarget']>('patient')
const contactResult = ref<ContactLogCreatePayload['contactResult']>('reached')
const contactTime = ref(new Date().toISOString().slice(0, 16))
const nextContactDate = ref('')
const contactNote = ref('')

const medicationInput = ref('')
const goalInput = ref('')
const medicationNotes = ref('')

const encounterStatusLabel = computed(
  () => encounterOptions.find((item) => item.value === props.encounterStatus)?.label ?? '候诊'
)

const encounterStatusNote = computed(
  () => encounterOptions.find((item) => item.value === props.encounterStatus)?.note ?? '等待接诊与任务确认'
)

const encounterStatusTone = computed(() => {
  if (props.encounterStatus === 'in_progress') return 'status-active'
  if (props.encounterStatus === 'pending_review') return 'status-review'
  if (props.encounterStatus === 'completed') return 'status-complete'
  return 'status-waiting'
})

const activePathItems = computed(() => {
  if (!evidenceFocusState.value.active) return pathItems.value
  const hint = evidenceFocusState.value.hint.trim().toLowerCase()
  if (!hint) return pathItems.value
  const filtered = pathItems.value.filter((item) => item.toLowerCase().includes(hint))
  return filtered.length ? filtered : pathItems.value
})

const highlightedQuadrupleKeys = computed(() => {
  if (!evidenceFocusState.value.active || !props.quadruples.length) return []
  const normalizedPaths = activePathItems.value.map((item) => item.toLowerCase())
  const hint = evidenceFocusState.value.hint.trim().toLowerCase()
  const matches = props.quadruples.filter((item) => {
    const datePart = (item.timestamp.split('T')[0] ?? '').toLowerCase()
    const relation = item.relation.toLowerCase()
    const relationLabel = item.relationLabel.toLowerCase()
    const objectValue = item.objectValue.toLowerCase()
    const subject = item.subject.toLowerCase()
    return normalizedPaths.some(
      (step) =>
        step.includes(datePart) ||
        step.includes(relation) ||
        step.includes(relationLabel) ||
        step.includes(objectValue) ||
        step.includes(subject) ||
        (hint ? step.includes(hint) : false)
    )
  })
  const selected = matches.length ? matches : props.quadruples.slice(0, Math.min(3, props.quadruples.length))
  return selected.map((item) => `${item.subject}-${item.relation}-${item.timestamp}`)
})

const registeredPlanKeys = computed(() => {
  const tasks = props.patient?.outpatientTasks ?? []
  return new Set(tasks.map((item) => `${item.category}:${item.title}`))
})

const planItems = computed(() => {
  const disease = props.patient?.primaryDisease ?? ''
  const riskLevel = props.patient?.riskLevel ?? ''
  const supportLevel = props.predictionResult?.evidence.supportLevel ?? 'minimal'
  const predictionLabel = currentPrediction.value?.label ?? '待预测'
  const exams: OutpatientPlanItem[] = []
  const rechecks: OutpatientPlanItem[] = []

  if (disease.toLowerCase().includes('diabetes')) {
    exams.push({
      id: 'exam-hba1c',
      category: 'exam',
      title: '补充 HbA1c 与空腹血糖',
      owner: '门诊医生',
      dueLabel: '1 周内',
      priority: isHighRiskLevel(riskLevel) ? 'high' : 'medium',
      note: '用于校准近期风险变化并支持用药调整。',
    })
  } else {
    exams.push({
      id: 'exam-general',
      category: 'exam',
      title: '补齐本次关键检查',
      owner: '门诊医生',
      dueLabel: '本次接诊',
      priority: isHighRiskLevel(riskLevel) ? 'high' : 'medium',
      note: '补齐关键临床指标后再确认风险趋势。',
    })
  }

  if (supportLevel !== 'strong') {
    exams.push({
      id: 'exam-structure',
      category: 'exam',
      title: '补录结构化事件',
      owner: '医生/档案员',
      dueLabel: '尽快',
      priority: 'high',
      note: '提升数据支持度，改善模型解释与复核质量。',
    })
  }

  rechecks.push({
    id: 'recheck-model',
    category: 'recheck',
    title: '复核模型预测',
    owner: '责任医生',
    dueLabel: props.encounterStatus === 'completed' ? '下次复诊' : '本次接诊',
    priority: isHighRiskLevel(riskLevel) ? 'high' : 'medium',
    note: `当前 Top-1：${predictionLabel}，请结合病程与检查结果复核。`,
  })

  if (followupTasks.value[0]) {
    rechecks.push({
      id: 'recheck-followup',
      category: 'recheck',
      title: '确认随访执行',
      owner: followupTasks.value[0].owner,
      dueLabel: followupTasks.value[0].dueDate,
      priority: followupTasks.value[0].priority,
      note: `已登记随访：${followupTasks.value[0].title}`,
    })
  }

  return { exams: exams.slice(0, 3), rechecks: rechecks.slice(0, 3) }
})

function scoreText(score: number) {
  return `${(score * 100).toFixed(1)}%`
}

function strategyLabel(value: string | undefined) {
  if (value === 'direct-model') return '直接模型'
  if (value === 'proxy-model') return '代理模型'
  if (value === 'rules') return '规则引擎'
  if (value === 'similar-case') return '相似病例'
  return '待预测'
}

function supportLevelLabel(value: string) {
  if (value === 'strong') return '强'
  if (value === 'limited') return '中'
  if (value === 'minimal') return '弱'
  return value
}

function adviceSourceLabel() {
  if (!adviceMeta.value) return '建议来源待生成'
  if (adviceMeta.value.source === 'deepseek' && adviceMeta.value.connected) return `${adviceMeta.value.provider} / 在线建议`
  return `${adviceMeta.value.provider} / 本地回退`
}

function parseTextList(raw: string) {
  return raw
    .split(/[\n,，;；、]/g)
    .map((item) => item.trim())
    .filter((item, index, arr) => item && arr.indexOf(item) === index)
}

function submitMedicationPlan() {
  emit('generate-medication-plan', {
    currentMedications: parseTextList(medicationInput.value),
    careGoals: parseTextList(goalInput.value),
    clinicalNotes: medicationNotes.value.trim(),
  })
}

function isHighRiskLevel(value: string) {
  const raw = value.toLowerCase()
  return value.includes('高') || raw.includes('high')
}

function priorityLabel(value: OutpatientPlanItem['priority']) {
  if (value === 'high') return '高优先'
  if (value === 'medium') return '中优先'
  return '低优先'
}

function priorityTone(value: OutpatientPlanItem['priority']) {
  if (value === 'high') return 'risk-high'
  if (value === 'medium') return 'risk-medium'
  return 'risk-low'
}

function taskRegistered(item: OutpatientPlanItem) {
  return registeredPlanKeys.value.has(`${item.category}:${item.title}`)
}

function createOutpatientTask(item: OutpatientPlanItem) {
  emit('create-outpatient-task', item)
}

function clearEvidenceFocusTimer() {
  if (evidenceFocusTimer) {
    clearTimeout(evidenceFocusTimer)
    evidenceFocusTimer = null
  }
}

function resetEvidenceFocus() {
  clearEvidenceFocusTimer()
  evidenceFocusState.value = { active: false, hint: '' }
}

function goToEvidence(hint = '') {
  clearEvidenceFocusTimer()
  evidenceFocusState.value = { active: true, hint: hint.trim().toLowerCase() }
  evidenceAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  evidenceFocusTimer = setTimeout(() => {
    resetEvidenceFocus()
  }, 6000)
}

function openArchiveEvents() {
  if (props.patient) emit('open-archive-events', props.patient.patientId)
}

function openFollowup() {
  if (props.patient) emit('open-followup', props.patient.patientId)
}

function changeEncounterStatus(status: EncounterStatus) {
  emit('update-encounter-status', status)
}

function submitContactLog() {
  emit('submit-contact-log', {
    contactTime: contactTime.value,
    contactType: contactType.value,
    contactTarget: contactTarget.value,
    contactResult: contactResult.value,
    note: contactNote.value.trim(),
    nextContactDate: nextContactDate.value || undefined,
  })
  contactResult.value = 'reached'
  contactNote.value = ''
  nextContactDate.value = ''
}

onBeforeUnmount(() => {
  clearEvidenceFocusTimer()
})
</script>

<template>
  <section v-if="props.patient" class="doctor-detail-layout">
    <aside class="card doctor-detail-sidebar">
      <div class="doctor-detail-sidebar-head">
        <button class="secondary-button" @click="emit('back')">返回患者列表</button>
        <button class="primary-button" :disabled="props.loadingPredict" @click="emit('predict')">
          {{ props.loadingPredict ? '预测中...' : '生成 N+1 预测' }}
        </button>
      </div>

      <PatientHeader :patient="props.patient" />
      <StatsGrid :stats="props.patient.stats" />

      <section class="mini-panel encounter-status-panel">
        <div class="mini-head">
          <h4>接诊状态</h4>
          <span>{{ encounterStatusLabel }} / {{ encounterStatusNote }}</span>
        </div>
        <div class="status-switch-grid">
          <button
            v-for="item in encounterOptions"
            :key="item.value"
            class="status-switch-button"
            :class="{ active: props.encounterStatus === item.value, [encounterStatusTone]: props.encounterStatus === item.value }"
            @click="changeEncounterStatus(item.value)"
          >
            <strong>{{ item.label }}</strong>
            <span>{{ item.note }}</span>
          </button>
        </div>
      </section>

      <div class="detail-quick-actions">
        <button class="secondary-button" @click="openArchiveEvents">打开档案事件</button>
        <button class="secondary-button" @click="openFollowup">进入随访任务</button>
      </div>
    </aside>

    <section class="doctor-detail-main">
      <article class="decision-card card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">风险预测</p>
            <h3>模型输出与证据摘要</h3>
          </div>
          <span class="panel-meta">{{ strategyLabel(props.predictionResult?.strategy) }}</span>
        </div>

        <div v-if="props.predictionResult" class="strategy-strip">
          <div>
            <span class="data-label">证据摘要</span>
            <strong>{{ props.predictionResult.supportSummary }}</strong>
          </div>
        </div>

        <div v-if="evidence" class="evidence-grid">
          <div class="evidence-item"><span>事件数</span><strong>{{ evidence.eventCount }}</strong></div>
          <div class="evidence-item"><span>时间点</span><strong>{{ evidence.timepointCount }}</strong></div>
          <div class="evidence-item"><span>关系数</span><strong>{{ evidence.relationCount }}</strong></div>
          <div class="evidence-item"><span>支持度</span><strong>{{ supportLevelLabel(evidence.supportLevel) }}</strong></div>
        </div>

        <div v-if="currentPrediction" class="hero-prediction">
          <div>
            <span class="data-label">Top-1 预测</span>
            <h4>{{ currentPrediction.label }}</h4>
            <p>{{ currentPrediction.reason }}</p>
          </div>
          <strong>{{ scoreText(currentPrediction.score) }}</strong>
        </div>

        <div class="prediction-stack">
          <article v-for="item in predictionItems" :key="item.label" class="prediction-row">
            <div>
              <strong>{{ item.label }}</strong>
              <p>{{ item.reason }}</p>
            </div>
            <span>{{ scoreText(item.score) }}</span>
          </article>
        </div>
      </article>

      <article ref="evidenceAnchor" class="card evidence-card" :class="{ 'is-focus-target': evidenceFocusState.active }">
        <div class="panel-head">
          <div>
            <p class="eyebrow">预测依据</p>
            <h3>四元组与路径解释</h3>
          </div>
          <div class="evidence-head-actions">
            <span class="panel-meta">{{ evidenceFocusState.active ? '高亮已开启，6 秒后自动恢复' : '可跳转定位证据关键词' }}</span>
            <button v-if="evidenceFocusState.active" class="text-button" @click="resetEvidenceFocus">取消高亮</button>
          </div>
        </div>

        <QuadruplePanel
          :quadruples="props.quadruples"
          :highlighted-keys="highlightedQuadrupleKeys"
          :focused="evidenceFocusState.active"
        />

        <section class="mini-panel" :class="{ 'is-focus-target': evidenceFocusState.active }">
          <div class="mini-head">
            <h4>路径解释</h4>
            <span>展示模型推断链路，便于门诊复核</span>
          </div>
          <ol class="plain-list ordered">
            <li
              v-for="item in pathItems"
              :key="item"
              :class="{
                'path-step-active': evidenceFocusState.active && activePathItems.includes(item),
                'path-step-muted': evidenceFocusState.active && !activePathItems.includes(item),
              }"
            >
              {{ item }}
            </li>
          </ol>
        </section>
      </article>
    </section>

    <aside class="doctor-detail-sidepanel">
      <article class="card llm-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">用药管理</p>
            <h3>DeepSeek 智能用药建议</h3>
          </div>
          <span class="panel-meta">{{ props.medicationPlanResult?.adviceMeta.provider ?? '待生成' }}</span>
        </div>

        <section class="mini-panel">
          <div class="mini-head">
            <h4>输入上下文</h4>
            <span>支持手动补充当前用药、治疗目标和备注</span>
          </div>
          <div class="form-grid">
            <label class="field full-span">
              <span>当前用药（逗号/换行分隔）</span>
              <textarea v-model="medicationInput" rows="2" placeholder="如：二甲双胍, 阿托伐他汀" />
            </label>
            <label class="field full-span">
              <span>治疗目标（可选）</span>
              <textarea v-model="goalInput" rows="2" placeholder="如：控制空腹血糖、降低跌倒风险" />
            </label>
            <label class="field full-span">
              <span>临床备注（可选）</span>
              <textarea v-model="medicationNotes" rows="2" placeholder="如：近期依从性下降，需家属协助" />
            </label>
          </div>
          <div class="form-actions">
            <button class="primary-button" @click="submitMedicationPlan">生成用药建议</button>
            <button class="text-button" @click="goToEvidence('medication')">定位用药相关证据</button>
          </div>
        </section>

        <section v-if="props.medicationPlanResult" class="mini-panel">
          <div class="mini-head">
            <h4>方案输出</h4>
            <span>{{ new Date(props.medicationPlanResult.generatedAt).toLocaleString() }}</span>
          </div>

          <div class="plan-list">
            <article v-for="item in props.medicationPlanResult.medications" :key="item.name" class="plan-item-card">
              <div class="plan-item-head">
                <strong>{{ item.name }}</strong>
              </div>
              <p>{{ item.purpose }}</p>
              <div class="plan-meta">
                <span>剂量：{{ item.dosage }}</span>
                <span>频次：{{ item.frequency }}</span>
              </div>
              <div class="plan-meta">
                <span>途径：{{ item.route || '未说明' }}</span>
                <span>疗程：{{ item.duration || '未说明' }}</span>
              </div>
              <ul v-if="item.cautions.length" class="plain-list">
                <li v-for="warning in item.cautions" :key="warning">{{ warning }}</li>
              </ul>
            </article>
          </div>

          <div v-if="props.medicationPlanResult.monitoring.length" class="mini-panel">
            <div class="mini-head"><h4>监测建议</h4></div>
            <ul class="plain-list">
              <li v-for="row in props.medicationPlanResult.monitoring" :key="row">{{ row }}</li>
            </ul>
          </div>

          <div v-if="props.medicationPlanResult.education.length" class="mini-panel">
            <div class="mini-head"><h4>患者宣教</h4></div>
            <ul class="plain-list">
              <li v-for="row in props.medicationPlanResult.education" :key="row">{{ row }}</li>
            </ul>
          </div>

          <p class="empty-note">{{ props.medicationPlanResult.disclaimer }}</p>
        </section>
      </article>

      <article class="card plan-board">
        <div class="panel-head">
          <div>
            <p class="eyebrow">门诊执行</p>
            <h3>检查与复核任务建议</h3>
          </div>
        </div>

        <div class="plan-grid">
          <section class="mini-panel">
            <div class="mini-head"><h4>建议检查</h4></div>
            <div class="plan-list">
              <article v-for="item in planItems.exams" :key="item.id" class="plan-item-card">
                <div class="plan-item-head">
                  <strong>{{ item.title }}</strong>
                  <span class="risk-pill" :class="priorityTone(item.priority)">{{ priorityLabel(item.priority) }}</span>
                </div>
                <div class="plan-meta">
                  <span>负责人：{{ item.owner }}</span>
                  <span>时限：{{ item.dueLabel }}</span>
                </div>
                <p>{{ item.note }}</p>
                <div class="inline-actions">
                  <button class="text-button" :disabled="taskRegistered(item)" @click="createOutpatientTask(item)">
                    {{ taskRegistered(item) ? '已登记门诊任务' : '登记门诊任务' }}
                  </button>
                  <button class="text-button" @click="goToEvidence(item.note)">定位证据</button>
                </div>
              </article>
            </div>
          </section>

          <section class="mini-panel">
            <div class="mini-head"><h4>建议复核</h4></div>
            <div class="plan-list">
              <article v-for="item in planItems.rechecks" :key="item.id" class="plan-item-card">
                <div class="plan-item-head">
                  <strong>{{ item.title }}</strong>
                  <span class="risk-pill" :class="priorityTone(item.priority)">{{ priorityLabel(item.priority) }}</span>
                </div>
                <div class="plan-meta">
                  <span>负责人：{{ item.owner }}</span>
                  <span>时限：{{ item.dueLabel }}</span>
                </div>
                <p>{{ item.note }}</p>
                <div class="inline-actions">
                  <button class="text-button" :disabled="taskRegistered(item)" @click="createOutpatientTask(item)">
                    {{ taskRegistered(item) ? '已登记门诊任务' : '登记门诊任务' }}
                  </button>
                  <button class="text-button" @click="openFollowup">进入随访任务</button>
                </div>
              </article>
            </div>
          </section>
        </div>
      </article>

      <article class="card advice-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">临床建议</p>
            <h3>随访建议与风险提示</h3>
          </div>
          <span class="panel-meta">{{ adviceSourceLabel() }}</span>
        </div>
        <ul v-if="adviceItems.length" class="plain-list">
          <li v-for="item in adviceItems" :key="item" class="action-list-item">
            <span>{{ item }}</span>
            <div class="inline-actions">
              <button class="text-button" @click="openFollowup">随访任务</button>
              <button class="text-button" @click="goToEvidence(item)">证据定位</button>
            </div>
          </li>
        </ul>
        <p v-else class="empty-note">当前暂无建议，请先生成预测或用药方案。</p>
      </article>

      <article class="card contact-log-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">联系记录</p>
            <h3>电话随访与反馈</h3>
          </div>
        </div>

        <section class="mini-panel">
          <div class="form-grid">
            <label class="field">
              <span>联系时间</span>
              <input v-model="contactTime" type="datetime-local" />
            </label>
            <label class="field">
              <span>联系类型</span>
              <select v-model="contactType">
                <option value="phone">电话随访</option>
                <option value="family">家属联系</option>
                <option value="wechat">微信联系</option>
                <option value="outpatient">门诊沟通</option>
              </select>
            </label>
            <label class="field">
              <span>联系对象</span>
              <select v-model="contactTarget">
                <option value="patient">患者本人</option>
                <option value="emergency_contact">紧急联系人</option>
              </select>
            </label>
            <label class="field">
              <span>联系结果</span>
              <select v-model="contactResult">
                <option value="reached">已联系</option>
                <option value="missed">未接通</option>
                <option value="scheduled">已预约</option>
                <option value="urgent">需加急处理</option>
              </select>
            </label>
            <label class="field">
              <span>下次联系日期</span>
              <input v-model="nextContactDate" type="date" />
            </label>
            <label class="field full-span">
              <span>备注</span>
              <textarea v-model="contactNote" rows="3" placeholder="记录患者反馈、风险变化与后续安排" />
            </label>
          </div>
          <div class="form-actions">
            <button class="primary-button" :disabled="props.savingContactLog" @click="submitContactLog">
              {{ props.savingContactLog ? '保存中...' : '保存联系记录' }}
            </button>
            <button class="secondary-button" @click="openFollowup">进入随访任务</button>
          </div>
        </section>

        <section class="mini-panel">
          <div class="mini-head">
            <h4>最近记录</h4>
            <span>{{ contactLogs.length }} 条</span>
          </div>
          <div v-if="contactLogs.length" class="preview-list">
            <article v-for="item in contactLogs" :key="item.logId" class="preview-row">
              <strong>{{ item.contactType }} / {{ item.contactResult }}</strong>
              <span>{{ item.contactTime.replace('T', ' ') }}</span>
              <p>{{ item.note || '无备注' }}</p>
            </article>
          </div>
          <article v-else class="empty-card compact">
            <p>当前暂无联系记录，可先补一条电话随访结果。</p>
          </article>
        </section>
      </article>

      <article class="card similar-case-card">
        <div class="panel-head">
          <div>
            <p class="eyebrow">相似病例</p>
            <h3>用于辅助判断处置策略</h3>
          </div>
        </div>

        <div v-if="similarCases.length" class="case-grid">
          <article v-for="item in similarCases" :key="item.caseId" class="case-card">
            <div class="case-head">
              <strong>{{ item.caseId }}</strong>
              <span>{{ scoreText(item.matchScore) }}</span>
            </div>
            <small>{{ item.disease }}</small>
            <p>{{ item.summary }}</p>
            <p>{{ item.suggestion }}</p>
          </article>
        </div>

        <article v-else class="empty-card compact">
          <p>当前暂无相似病例数据。</p>
        </article>
      </article>
    </aside>
  </section>
</template>
