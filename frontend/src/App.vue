<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  addPatientEvent,
  getModelMetrics,
  getPatientCase,
  getPatients,
  getTimeline,
  healthCheck,
  loginDoctor,
  logoutDoctor,
  predictPatient,
  savePatient,
  updatePatient,
} from './services/api'
import type {
  DoctorUser,
  HealthResponse,
  ModelMetricsResponse,
  PatientCase,
  PatientEventPayload,
  PatientSummary,
  PatientUpsertPayload,
  PredictResponse,
  TimelineEvent,
  TimelineType,
} from './services/types'

type SectionName = 'workspace' | 'archive' | 'metrics'

const username = ref('doctor01')
const password = ref('ctpath123')
const loginError = ref('')
const loadingLogin = ref(false)
const currentDoctor = ref<DoctorUser | null>(null)
const health = ref<HealthResponse | null>(null)

const section = ref<SectionName>('workspace')
const allPatients = ref<PatientSummary[]>([])
const selectedPatientId = ref('')
const selectedPatient = ref<PatientCase | null>(null)
const timelineItems = ref<TimelineEvent[]>([])
const predictionResult = ref<PredictResponse | null>(null)
const modelMetrics = ref<ModelMetricsResponse | null>(null)

const loadingPatients = ref(false)
const loadingPatient = ref(false)
const loadingTimeline = ref(false)
const loadingPredict = ref(false)
const loadingMetrics = ref(false)
const savingPatient = ref(false)
const savingEvent = ref(false)
const screenError = ref('')
const archiveSuccess = ref('')

const searchText = ref('')
const riskFilter = ref('全部风险')
const riskOptions = ['全部风险', '高风险', '中风险', '低风险']
const relationOptions = [
  'has_disease',
  'stage',
  'med_adherence',
  'medical_history',
  'support_system',
  'sleep_hours_bin',
  'mood_bin',
  'bp_sys_bin',
  'bmi_bin',
  'cholesterol_bin',
]

function defaultPatientForm(): PatientUpsertPayload {
  return {
    patientId: '',
    name: '',
    age: 0,
    gender: '女',
    primaryDisease: '2型糖尿病',
    currentStage: 'Early',
    riskLevel: '中风险',
    lastVisit: new Date().toISOString().slice(0, 10),
    summary: '',
    dataSupport: 'medium',
  }
}

function defaultEventForm(): PatientEventPayload {
  return {
    eventTime: new Date().toISOString().slice(0, 16),
    relation: 'stage',
    objectValue: '',
    note: '',
    source: 'manual',
  }
}

const patientForm = ref<PatientUpsertPayload>(defaultPatientForm())
const eventForm = ref<PatientEventPayload>(defaultEventForm())

const filteredPatients = computed(() => {
  return allPatients.value.filter((item) => {
    const matchesRisk = riskFilter.value === '全部风险' || item.riskLevel === riskFilter.value
    const keyword = searchText.value.trim().toLowerCase()
    const haystack = `${item.patientId} ${item.name} ${item.primaryDisease}`.toLowerCase()
    const matchesSearch = keyword.length === 0 || haystack.includes(keyword)
    return matchesRisk && matchesSearch
  })
})

const patientCountText = computed(() => `${filteredPatients.value.length} / ${allPatients.value.length} 名患者`)
const displayedPrediction = computed(() => predictionResult.value?.topk[0] ?? selectedPatient.value?.predictions[0] ?? null)
const displayedAdvice = computed(() => predictionResult.value?.advice ?? selectedPatient.value?.careAdvice ?? [])
const displayedPath = computed(() => predictionResult.value?.pathExplanation ?? selectedPatient.value?.pathExplanation ?? [])
const displayedSimilarCases = computed(
  () => predictionResult.value?.similarCases ?? selectedPatient.value?.similarCases ?? [],
)

function riskClass(level: string) {
  if (level === '高风险') return 'risk-high'
  if (level === '中风险') return 'risk-medium'
  return 'risk-low'
}

function timelineClass(type: TimelineType) {
  return `event-${type}`
}

function priorityClass(priority: string) {
  return `priority-${priority}`
}

function scoreText(score: number) {
  return `${(score * 100).toFixed(1)}%`
}

function syncPatientForm(patient: PatientCase | null) {
  if (!patient) {
    patientForm.value = defaultPatientForm()
    return
  }
  patientForm.value = {
    patientId: patient.patientId,
    name: patient.name,
    age: patient.age,
    gender: patient.gender,
    primaryDisease: patient.primaryDisease,
    currentStage: patient.currentStage,
    riskLevel: patient.riskLevel,
    lastVisit: patient.lastVisit,
    summary: patient.summary,
    dataSupport: patient.dataSupport,
  }
}

async function loadPatients() {
  loadingPatients.value = true
  screenError.value = ''
  try {
    allPatients.value = await getPatients()
    if (!selectedPatientId.value && allPatients.value[0]) {
      selectedPatientId.value = allPatients.value[0].patientId
      await loadPatient(allPatients.value[0].patientId)
    }
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '加载患者列表失败'
  } finally {
    loadingPatients.value = false
  }
}

async function loadTimeline(patientId: string) {
  loadingTimeline.value = true
  try {
    timelineItems.value = await getTimeline(patientId)
  } catch {
    timelineItems.value = selectedPatient.value?.timeline ?? []
  } finally {
    loadingTimeline.value = false
  }
}

async function loadPatient(patientId: string) {
  if (!patientId) return
  loadingPatient.value = true
  screenError.value = ''
  archiveSuccess.value = ''
  try {
    selectedPatient.value = await getPatientCase(patientId)
    syncPatientForm(selectedPatient.value)
    predictionResult.value = null
    await loadTimeline(patientId)
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '加载患者详情失败'
  } finally {
    loadingPatient.value = false
  }
}

async function loadMetrics() {
  loadingMetrics.value = true
  try {
    modelMetrics.value = await getModelMetrics()
  } catch {
    modelMetrics.value = null
  } finally {
    loadingMetrics.value = false
  }
}

async function submitLogin() {
  loadingLogin.value = true
  loginError.value = ''
  try {
    const session = await loginDoctor(username.value.trim(), password.value)
    currentDoctor.value = session.doctor
    await Promise.all([loadPatients(), loadMetrics()])
  } catch (error) {
    loginError.value = error instanceof Error ? error.message : '登录失败'
  } finally {
    loadingLogin.value = false
  }
}

function logout() {
  logoutDoctor()
  currentDoctor.value = null
  allPatients.value = []
  selectedPatient.value = null
  selectedPatientId.value = ''
  timelineItems.value = []
  predictionResult.value = null
  screenError.value = ''
  archiveSuccess.value = ''
  patientForm.value = defaultPatientForm()
  eventForm.value = defaultEventForm()
}

async function choosePatient(patientId: string) {
  selectedPatientId.value = patientId
  await loadPatient(patientId)
}

function prepareNewArchive() {
  section.value = 'archive'
  selectedPatientId.value = ''
  selectedPatient.value = null
  timelineItems.value = []
  predictionResult.value = null
  archiveSuccess.value = ''
  patientForm.value = defaultPatientForm()
  eventForm.value = defaultEventForm()
}

async function runPrediction() {
  if (!selectedPatient.value) return
  loadingPredict.value = true
  screenError.value = ''
  try {
    predictionResult.value = await predictPatient({
      patientId: selectedPatient.value.patientId,
      asOfTime: selectedPatient.value.lastVisit,
      topk: 3,
    })
    section.value = 'workspace'
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '执行 T+1 预测失败'
  } finally {
    loadingPredict.value = false
  }
}

async function submitArchive() {
  savingPatient.value = true
  archiveSuccess.value = ''
  screenError.value = ''
  try {
    const payload = { ...patientForm.value, age: Number(patientForm.value.age) }
    const saved = selectedPatientId.value
      ? await updatePatient(selectedPatientId.value, payload)
      : await savePatient(payload)

    archiveSuccess.value = selectedPatientId.value ? '患者档案已更新。' : '患者档案已创建。'
    selectedPatientId.value = saved.patientId
    selectedPatient.value = saved
    syncPatientForm(saved)
    timelineItems.value = saved.timeline
    await loadPatients()
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '保存患者档案失败'
  } finally {
    savingPatient.value = false
  }
}

async function submitEvent() {
  const patientId = selectedPatientId.value || patientForm.value.patientId
  if (!patientId) {
    screenError.value = '请先填写并保存患者档案，再补录事件。'
    return
  }
  savingEvent.value = true
  archiveSuccess.value = ''
  screenError.value = ''
  try {
    const updated = await addPatientEvent(patientId, eventForm.value)
    selectedPatientId.value = updated.patientId
    selectedPatient.value = updated
    timelineItems.value = updated.timeline
    archiveSuccess.value = '结构化病历事件已补录。'
    eventForm.value = defaultEventForm()
    await loadPatients()
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '补录病历事件失败'
  } finally {
    savingEvent.value = false
  }
}

watch(selectedPatientId, async (value, oldValue) => {
  if (value && value !== oldValue && currentDoctor.value) {
    await loadPatient(value)
  }
})

onMounted(async () => {
  try {
    health.value = await healthCheck()
  } catch {
    health.value = null
  }
})
</script>

<template>
  <div v-if="!currentDoctor" class="login-shell">
    <section class="login-panel">
      <div class="login-copy">
        <p class="eyebrow">Smart Chronic Care</p>
        <h1>基于时序知识图谱的慢性病辅助诊疗系统</h1>
        <p>
          系统面向医生工作流，完成患者档案管理、病程轨迹展示、T+1 病情推演和辅助诊疗建议。
          后端采用 FastAPI，前端采用 Vue，模型层接入 CTpath / TKGR-GPRSCL。
        </p>

        <ul class="feature-list">
          <li>支持医生身份验证、患者检索和重点风险筛查。</li>
          <li>支持患者历史事件建模为四元组，用于时序知识图谱推理。</li>
          <li>支持样本不足时回退到相似病例辅助建议，保证系统可用性。</li>
        </ul>
      </div>

      <form class="login-form" @submit.prevent="submitLogin">
        <label>
          <span>医生账号</span>
          <input v-model="username" type="text" placeholder="请输入医生账号" />
        </label>

        <label>
          <span>登录密码</span>
          <input v-model="password" type="password" placeholder="请输入登录密码" />
        </label>

        <p class="login-hint">演示账号：doctor01 / ctpath123</p>
        <p class="login-hint">
          服务状态：
          {{ health ? `${health.status} / ${health.mode} / 模型${health.model_available ? '可用' : '不可用'}` : '未连接' }}
        </p>
        <p v-if="loginError" class="login-error">{{ loginError }}</p>

        <button class="primary-button" type="submit" :disabled="loadingLogin">
          {{ loadingLogin ? '登录中...' : '进入医生工作台' }}
        </button>
      </form>
    </section>
  </div>

  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand-block">
        <div class="brand-badge">CT</div>
        <div>
          <p class="eyebrow inverse">Clinical TKG</p>
          <h2>慢病辅助诊疗工作台</h2>
        </div>
      </div>

      <div class="doctor-card">
        <span>{{ currentDoctor.department }}</span>
        <strong>{{ currentDoctor.name }} / {{ currentDoctor.title }}</strong>
        <small>运行模式：{{ health?.mode ?? 'unknown' }}</small>
      </div>

      <nav class="nav-list">
        <button class="nav-item" :class="{ active: section === 'workspace' }" @click="section = 'workspace'">
          病情推演工作台
        </button>
        <button class="nav-item" :class="{ active: section === 'archive' }" @click="section = 'archive'">
          患者档案管理
        </button>
        <button class="nav-item" :class="{ active: section === 'metrics' }" @click="section = 'metrics'">
          模型评估与对比
        </button>
      </nav>

      <button class="ghost-button" @click="prepareNewArchive">新建患者档案</button>

      <div class="sidebar-note">
        <span>任务书对齐说明</span>
        <p>
          当前系统已经覆盖 Web B/S 架构、患者档案管理、病程轨迹展示、T+1 预测、辅助诊疗建议和模型评估展示。
        </p>
      </div>

      <button class="ghost-button" @click="logout">退出登录</button>
    </aside>

    <main class="workspace">
      <header class="workspace-header">
        <div>
          <p class="eyebrow">Doctor Console</p>
          <h1 v-if="section === 'workspace'">病情推演与辅助诊疗建议</h1>
          <h1 v-else-if="section === 'archive'">患者档案管理与事件补录</h1>
          <h1 v-else>模型评估、指标与对比实验</h1>
          <p class="workspace-copy">
            以医生工作台的方式组织患者信息、时序事件、模型预测和相似病例建议，便于答辩演示与复试讲解。
          </p>
        </div>
        <div class="workspace-meta">
          <span>当前患者数</span>
          <strong>{{ allPatients.length }}</strong>
          <small>支持检索、档案维护和病程推演</small>
        </div>
      </header>

      <section v-if="section !== 'metrics'" class="search-bar">
        <div class="search-box">
          <label for="search">搜索患者</label>
          <input id="search" v-model="searchText" type="text" placeholder="请输入患者 ID / 姓名 / 病种" />
        </div>

        <div class="filter-box">
          <label for="risk-filter">风险等级</label>
          <select id="risk-filter" v-model="riskFilter">
            <option v-for="item in riskOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </div>

        <div class="result-box">
          <span>检索结果</span>
          <strong>{{ patientCountText }}</strong>
        </div>
      </section>

      <p v-if="screenError" class="login-error" style="margin-top: 14px">{{ screenError }}</p>
      <p v-if="archiveSuccess" class="success-banner">{{ archiveSuccess }}</p>

      <section v-if="section === 'metrics'" class="surface-card metrics-panel">
        <div class="surface-head">
          <div>
            <p class="eyebrow">Evaluation</p>
            <h3>CHRONIC 数据集模型指标</h3>
          </div>
          <span class="surface-note">{{ loadingMetrics ? '加载中...' : '对齐任务书中的 MRR / Hits@K 指标要求' }}</span>
        </div>

        <div v-if="modelMetrics" class="metrics-grid">
          <article class="metric-card highlight-card">
            <p class="eyebrow">Current Model</p>
            <h4>{{ modelMetrics.currentModel.model }}</h4>
            <div class="metric-values">
              <span>MRR {{ modelMetrics.currentModel.mrr?.toFixed(4) }}</span>
              <span>Hits@1 {{ modelMetrics.currentModel.hits1?.toFixed(4) }}</span>
              <span>Hits@3 {{ modelMetrics.currentModel.hits3?.toFixed(4) }}</span>
              <span>Hits@10 {{ modelMetrics.currentModel.hits10?.toFixed(4) }}</span>
            </div>
            <p>{{ modelMetrics.currentModel.note }}</p>
          </article>

          <article class="metric-card">
            <p class="eyebrow">Comparison Plan</p>
            <h4>任务书要求的对比/消融</h4>
            <div class="metric-table">
              <div class="metric-table-row metric-table-head">
                <span>模型</span>
                <span>状态</span>
                <span>说明</span>
              </div>
              <div v-for="item in modelMetrics.comparisons" :key="item.model" class="metric-table-row">
                <span>{{ item.model }}</span>
                <span>{{ item.status === 'done' ? '已完成' : '待补充' }}</span>
                <span>{{ item.note }}</span>
              </div>
            </div>
          </article>

          <article class="metric-card">
            <p class="eyebrow">Architecture</p>
            <h4>系统链路</h4>
            <ol class="metric-list">
              <li>MySQL 存储医生账号、患者档案和时序病历事件。</li>
              <li>FastAPI 提供登录、档案、时间线、预测和指标接口。</li>
              <li>CTpath 负责 T+1 时序推理，输出病情推演结果。</li>
              <li>样本不足时回退到相似病例辅助建议。</li>
              <li>Vue 前端负责医生工作台和可视化展示。</li>
            </ol>
          </article>
        </div>
      </section>

      <div v-else class="main-grid">
        <section class="patient-list-panel surface-card">
          <div class="surface-head">
            <div>
              <p class="eyebrow">Patient List</p>
              <h3>患者列表</h3>
            </div>
            <span class="surface-note">{{ loadingPatients ? '加载中...' : '按风险等级和病种快速筛查' }}</span>
          </div>

          <div class="patient-list">
            <button
              v-for="patient in filteredPatients"
              :key="patient.patientId"
              class="patient-item"
              :class="{ active: patient.patientId === selectedPatientId }"
              @click="choosePatient(patient.patientId)"
            >
              <div>
                <strong>{{ patient.name }}</strong>
                <span>{{ patient.patientId }} / {{ patient.primaryDisease }}</span>
              </div>
              <span class="risk-pill" :class="riskClass(patient.riskLevel)">{{ patient.riskLevel }}</span>
            </button>
          </div>
        </section>

        <section v-if="section === 'workspace'" class="patient-detail">
          <article v-if="selectedPatient" class="surface-card patient-overview">
            <div class="overview-top">
              <div>
                <p class="eyebrow">Patient Overview</p>
                <h2>{{ selectedPatient.name }}</h2>
                <p class="patient-summary">{{ selectedPatient.summary }}</p>
              </div>
              <div class="patient-risk-box" :class="riskClass(selectedPatient.riskLevel)">
                <span>当前风险</span>
                <strong>{{ selectedPatient.riskLevel }}</strong>
                <small>阶段：{{ selectedPatient.currentStage }}</small>
              </div>
            </div>

            <div class="patient-tags">
              <span>患者 ID：{{ selectedPatient.patientId }}</span>
              <span>{{ selectedPatient.gender }} / {{ selectedPatient.age }} 岁</span>
              <span>病种：{{ selectedPatient.primaryDisease }}</span>
              <span>最近随访：{{ selectedPatient.lastVisit }}</span>
              <span>数据支持：{{ selectedPatient.dataSupport }}</span>
            </div>

            <div class="stats-grid">
              <article v-for="stat in selectedPatient.stats" :key="stat.label" class="stat-card">
                <span>{{ stat.label }}</span>
                <strong>{{ stat.value }}</strong>
                <small>{{ stat.trend }}</small>
              </article>
            </div>
          </article>

          <div v-if="selectedPatient" class="detail-grid">
            <section class="surface-card">
              <div class="surface-head">
                <div>
                  <p class="eyebrow">Trajectory</p>
                  <h3>病程时间线</h3>
                </div>
                <span class="surface-note">{{ loadingTimeline ? '更新中...' : '按时间回看结构化病历事件' }}</span>
              </div>

              <div class="timeline">
                <article v-for="item in (timelineItems.length ? timelineItems : selectedPatient.timeline)" :key="`${item.date}-${item.title}`" class="timeline-item">
                  <div class="timeline-line">
                    <span class="timeline-dot" :class="timelineClass(item.type)" />
                  </div>
                  <div class="timeline-card">
                    <div class="timeline-meta">
                      <span>{{ item.date }}</span>
                      <span class="event-tag" :class="timelineClass(item.type)">{{ item.type }}</span>
                    </div>
                    <h4>{{ item.title }}</h4>
                    <p>{{ item.detail }}</p>
                  </div>
                </article>
              </div>
            </section>

            <section class="surface-card">
              <div class="surface-head">
                <div>
                  <p class="eyebrow">Prediction</p>
                  <h3>T+1 预测与建议</h3>
                </div>
                <button class="primary-button" :disabled="loadingPredict" @click="runPrediction">
                  {{ loadingPredict ? '推演中...' : '执行 T+1 预测' }}
                </button>
              </div>

              <div v-if="displayedPrediction" class="forecast-banner" :class="riskClass(selectedPatient.riskLevel)">
                <div>
                  <span class="forecast-mini">Top-1 Result</span>
                  <h4>{{ displayedPrediction.label }}</h4>
                  <p>{{ displayedPrediction.reason }}</p>
                </div>
                <strong>{{ scoreText(displayedPrediction.score) }}</strong>
              </div>

              <div class="prediction-list">
                <article
                  v-for="item in (predictionResult?.topk ?? selectedPatient.predictions)"
                  :key="item.label"
                  class="prediction-card"
                >
                  <div class="prediction-head">
                    <strong>{{ item.label }}</strong>
                    <span>{{ scoreText(item.score) }}</span>
                  </div>
                  <p>{{ item.reason }}</p>
                </article>
              </div>

              <div class="advice-box">
                <h4>辅助诊疗建议</h4>
                <ul>
                  <li v-for="item in displayedAdvice" :key="item">{{ item }}</li>
                </ul>
              </div>

              <div class="path-box">
                <div class="path-head">
                  <strong>关键路径解释</strong>
                  <small>对应任务书中的图结构路径挖掘能力</small>
                </div>
                <ol>
                  <li v-for="item in displayedPath" :key="item">{{ item }}</li>
                </ol>
              </div>
            </section>

            <section class="surface-card">
              <div class="surface-head">
                <div>
                  <p class="eyebrow">Support</p>
                  <h3>随访任务与相似病例</h3>
                </div>
              </div>

              <div class="task-list">
                <article v-for="task in selectedPatient.followUps" :key="task.title" class="task-card">
                  <div class="task-head">
                    <strong>{{ task.title }}</strong>
                    <span class="priority-pill" :class="priorityClass(task.priority)">
                      {{ task.priority }}
                    </span>
                  </div>
                  <p>{{ task.owner }}</p>
                  <small>截止时间：{{ task.dueDate }}</small>
                </article>
              </div>

              <div class="similar-list">
                <article v-for="item in displayedSimilarCases" :key="item.caseId" class="prediction-card">
                  <div class="prediction-head">
                    <strong>{{ item.caseId }} / {{ item.disease }}</strong>
                    <span>{{ scoreText(item.matchScore) }}</span>
                  </div>
                  <p>{{ item.summary }}</p>
                  <small>{{ item.suggestion }}</small>
                </article>
              </div>
            </section>
          </div>
        </section>

        <section v-else class="patient-detail">
          <article class="surface-card archive-card">
            <div class="surface-head">
              <div>
                <p class="eyebrow">Archive</p>
                <h3>患者档案管理</h3>
              </div>
              <span class="surface-note">覆盖任务书中的“患者档案管理”要求</span>
            </div>

            <div class="form-grid">
              <label>
                <span>患者 ID</span>
                <input v-model="patientForm.patientId" :disabled="!!selectedPatientId" type="text" placeholder="如 PID9010" />
              </label>
              <label>
                <span>患者姓名</span>
                <input v-model="patientForm.name" type="text" placeholder="请输入患者姓名" />
              </label>
              <label>
                <span>年龄</span>
                <input v-model.number="patientForm.age" type="number" min="0" max="120" />
              </label>
              <label>
                <span>性别</span>
                <select v-model="patientForm.gender">
                  <option value="女">女</option>
                  <option value="男">男</option>
                </select>
              </label>
              <label>
                <span>主病种</span>
                <input v-model="patientForm.primaryDisease" type="text" placeholder="如 2型糖尿病" />
              </label>
              <label>
                <span>当前阶段</span>
                <select v-model="patientForm.currentStage">
                  <option value="Early">Early</option>
                  <option value="Mid">Mid</option>
                  <option value="Late">Late</option>
                </select>
              </label>
              <label>
                <span>风险等级</span>
                <select v-model="patientForm.riskLevel">
                  <option value="低风险">低风险</option>
                  <option value="中风险">中风险</option>
                  <option value="高风险">高风险</option>
                </select>
              </label>
              <label>
                <span>最近随访时间</span>
                <input v-model="patientForm.lastVisit" type="date" />
              </label>
              <label>
                <span>数据支持度</span>
                <select v-model="patientForm.dataSupport">
                  <option value="high">high</option>
                  <option value="medium">medium</option>
                  <option value="low">low</option>
                </select>
              </label>
              <label class="form-span-full">
                <span>病情摘要</span>
                <textarea v-model="patientForm.summary" rows="4" placeholder="请输入患者病情摘要" />
              </label>
            </div>

            <div class="form-actions">
              <button class="primary-button" :disabled="savingPatient" @click="submitArchive">
                {{ savingPatient ? '保存中...' : selectedPatientId ? '更新患者档案' : '创建患者档案' }}
              </button>
              <button class="secondary-button" @click="prepareNewArchive">清空表单</button>
            </div>
          </article>

          <article class="surface-card archive-card">
            <div class="surface-head">
              <div>
                <p class="eyebrow">Event</p>
                <h3>结构化病历事件补录</h3>
              </div>
              <span class="surface-note">用于构建 (s, r, o, t) 四元组事件流</span>
            </div>

            <div class="form-grid">
              <label>
                <span>事件时间</span>
                <input v-model="eventForm.eventTime" type="datetime-local" />
              </label>
              <label>
                <span>关系类型</span>
                <select v-model="eventForm.relation">
                  <option v-for="item in relationOptions" :key="item" :value="item">{{ item }}</option>
                </select>
              </label>
              <label>
                <span>对象值</span>
                <input v-model="eventForm.objectValue" type="text" placeholder="如 Late / Low / Q2" />
              </label>
              <label class="form-span-full">
                <span>事件备注</span>
                <textarea v-model="eventForm.note" rows="3" placeholder="请输入临床说明或补充备注" />
              </label>
            </div>

            <div class="form-actions">
              <button class="primary-button" :disabled="savingEvent" @click="submitEvent">
                {{ savingEvent ? '提交中...' : '补录结构化事件' }}
              </button>
            </div>
          </article>

          <article v-if="selectedPatient" class="surface-card archive-card">
            <div class="surface-head">
              <div>
                <p class="eyebrow">Preview</p>
                <h3>当前患者时间线预览</h3>
              </div>
            </div>

            <div class="timeline">
              <article v-for="item in (timelineItems.length ? timelineItems : selectedPatient.timeline)" :key="`${item.date}-${item.title}`" class="timeline-item">
                <div class="timeline-line">
                  <span class="timeline-dot" :class="timelineClass(item.type)" />
                </div>
                <div class="timeline-card">
                  <div class="timeline-meta">
                    <span>{{ item.date }}</span>
                    <span class="event-tag" :class="timelineClass(item.type)">{{ item.type }}</span>
                  </div>
                  <h4>{{ item.title }}</h4>
                  <p>{{ item.detail }}</p>
                </div>
              </article>
            </div>
          </article>
        </section>
      </div>
    </main>
  </div>
</template>
