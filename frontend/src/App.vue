<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import AppSidebar, { type AppSection } from './components/AppSidebar.vue'
import LoginScreen from './components/LoginScreen.vue'
import RoleWorkspaceBanner from './components/RoleWorkspaceBanner.vue'
import WorkspaceTopbar from './components/WorkspaceTopbar.vue'
import ArchivePage from './pages/ArchivePage.vue'
import DoctorWorkspacePage from './pages/DoctorWorkspacePage.vue'
import FollowupPage from './pages/FollowupPage.vue'
import GovernancePage from './pages/GovernancePageSimple.vue'
import {
  addPatientContactLog,
  addPatientEvent,
  createPatientOutpatientTask,
  generateMedicationPlan,
  getFlowBoard,
  getFollowupWorklist,
  getGovernanceModules,
  getMaintenanceOverview,
  getModelMetrics,
  getPatients,
  getPatientCase,
  getPatientQuadruples,
  healthCheck,
  loginDoctor,
  logoutDoctor,
  predictPatient,
  registerDoctor,
  restoreAuthSession,
  savePatient,
  updatePatientEncounterStatus,
  updatePatientOutpatientTaskStatus,
  updatePatient,
} from './services/api'
import type {
  ContactLogCreatePayload,
  DoctorUser,
  FlowBoardRow,
  FollowupTaskRow,
  GovernanceModulesResponse,
  HealthResponse,
  ImportPreviewPatient,
  MaintenanceOverview,
  MedicationPlanGeneratePayload,
  MedicationPlanResponse,
  ModelMetricsResponse,
  OutpatientPlanItem,
  PatientCase,
  PatientEventPayload,
  PatientQuadruple,
  PatientSummary,
  PatientUpsertPayload,
  PredictResponse,
  RegisterPayload,
} from './services/types'

type DoctorMode = 'list' | 'detail'
type ArchiveMode = 'list' | 'detail' | 'create' | 'import'
type ArchiveFocusSection = 'overview' | 'events'

const username = ref('demo_clinic')
const password = ref('demo123456')
const loginError = ref('')
const loadingLogin = ref(false)
const currentDoctor = ref<DoctorUser | null>(null)
const health = ref<HealthResponse | null>(null)

const registerMode = ref(false)
const registerError = ref('')
const loadingRegister = ref(false)
const registerForm = ref<RegisterPayload>({
  username: '',
  password: '',
  name: '',
  role: 'doctor',
  title: '涓绘不鍖诲笀',
  department: '鎱㈢梾绠＄悊闂ㄨ瘖',
})

const section = ref<AppSection>('doctor')
const doctorMode = ref<DoctorMode>('list')
const archiveMode = ref<ArchiveMode>('list')

const allPatients = ref<PatientSummary[]>([])
const followupItems = ref<FollowupTaskRow[]>([])
const flowBoardItems = ref<FlowBoardRow[]>([])
const maintenanceOverview = ref<MaintenanceOverview | null>(null)
const governanceModules = ref<GovernanceModulesResponse | null>(null)
const modelMetrics = ref<ModelMetricsResponse | null>(null)
const followupFocusPatientId = ref('')
const archiveFocusSection = ref<ArchiveFocusSection>('overview')
const viewedPatientIds = ref<string[]>([])
const showAllPending = ref(false)
const selectedPatientId = ref('')
const selectedPatient = ref<PatientCase | null>(null)
const patientQuadruples = ref<PatientQuadruple[]>([])
const predictionResult = ref<PredictResponse | null>(null)
const medicationPlanResult = ref<MedicationPlanResponse | null>(null)

const loadingPatients = ref(false)
const loadingPatient = ref(false)
const loadingPredict = ref(false)
const loadingBoards = ref(false)
const loadingGovernance = ref(false)
const loadingMaintenance = ref(false)
const loadingModelMetrics = ref(false)
const savingPatient = ref(false)
const savingEvent = ref(false)
const savingContactLog = ref(false)
const importingArchive = ref(false)
const screenError = ref('')
const archiveSuccess = ref('')
const importResultText = ref('')

const workspaceSearchText = ref('')
const workspaceRiskFilter = ref('全部风险')
const archivePage = ref(1)
const archivePageSize = 6

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

function defaultSectionForRole(role: DoctorUser['role'] | undefined): AppSection {
  if (role === 'archivist') return 'archive'
  if (role === 'nurse') return 'tasks'
  return 'doctor'
}

function canAccessSection(nextSection: AppSection) {
  const role = currentDoctor.value?.role
  if (!role) return false
  if (role === 'archivist') return nextSection === 'archive' || nextSection === 'governance'
  if (role === 'nurse') return nextSection !== 'doctor'
  return true
}

function canManageArchive() {
  const role = currentDoctor.value?.role
  return role === 'doctor' || role === 'archivist'
}

function canRecordClinicalEvent() {
  return currentDoctor.value?.role === 'doctor'
}

function canUseFollowupWorkspace() {
  const role = currentDoctor.value?.role
  return role === 'doctor' || role === 'nurse'
}

function canUseDoctorWorkspace() {
  return currentDoctor.value?.role === 'doctor'
}

function canUseGovernanceWorkspace() {
  const role = currentDoctor.value?.role
  return role === 'doctor' || role === 'archivist'
}

function setPermissionError(message: string) {
  archiveSuccess.value = ''
  screenError.value = message
}

const appRoleClass = computed(() => `app-role-${currentDoctor.value?.role ?? 'guest'}`)

function defaultPatientForm(): PatientUpsertPayload {
  return {
    patientId: '',
    name: '',
    age: 0,
    gender: '女',
    avatarUrl: '',
    phone: '',
    emergencyContactName: '',
    emergencyContactRelation: '',
    emergencyContactPhone: '',
    identityMasked: '',
    insuranceType: '城镇职工',
    department: '慢病管理门诊',
    primaryDoctor: currentDoctor.value?.name || '周医生',
    caseManager: '张护士',
    allergyHistory: '无',
    familyHistory: '无特殊家族史',
    medicalRecordNumber: '',
    archiveSource: 'outpatient',
    archiveStatus: 'active',
    consentStatus: 'signed',
    primaryDisease: 'Diabetes',
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

function isHighRisk(value: string) {
  const raw = value.toLowerCase()
  return value.includes('高') || raw.includes('high')
}

function isMediumRisk(value: string) {
  const raw = value.toLowerCase()
  return value.includes('中') || raw.includes('medium')
}

function riskRank(value: string) {
  if (isHighRisk(value)) return 0
  if (isMediumRisk(value)) return 1
  return 2
}

const riskOptions = computed(() => {
  const dynamicLevels = Array.from(new Set(allPatients.value.map((item) => item.riskLevel)))
  return ['全部风险', ...dynamicLevels]
})

const filteredWorkspacePatients = computed(() =>
  allPatients.value.filter((item) => {
    const matchesRisk = workspaceRiskFilter.value === '全部风险' || item.riskLevel === workspaceRiskFilter.value
    const keyword = workspaceSearchText.value.trim().toLowerCase()
    const haystack = `${item.patientId} ${item.name} ${item.primaryDisease}`.toLowerCase()
    return matchesRisk && (!keyword || haystack.includes(keyword))
  })
)

const pendingWorkspacePatients = computed(() =>
  filteredWorkspacePatients.value.filter((patient) => !viewedPatientIds.value.includes(patient.patientId))
)

const visiblePendingPatients = computed(() =>
  showAllPending.value ? pendingWorkspacePatients.value : pendingWorkspacePatients.value.slice(0, 2)
)

const hiddenPendingCount = computed(() =>
  Math.max(0, pendingWorkspacePatients.value.length - visiblePendingPatients.value.length)
)

const recentViewedPatients = computed(() =>
  viewedPatientIds.value
    .map((patientId) => allPatients.value.find((patient) => patient.patientId === patientId))
    .filter((patient): patient is PatientSummary => Boolean(patient))
    .slice(0, 4)
)

const archiveTotalPages = computed(() => Math.max(1, Math.ceil(allPatients.value.length / archivePageSize)))
const archivePagedPatients = computed(() => {
  const start = (archivePage.value - 1) * archivePageSize
  return allPatients.value.slice(start, start + archivePageSize)
})

function sortPatients(items: PatientSummary[]) {
  return [...items].sort((left, right) => {
    const riskCompare = riskRank(left.riskLevel) - riskRank(right.riskLevel)
    if (riskCompare !== 0) return riskCompare
    return right.lastVisit.localeCompare(left.lastVisit)
  })
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
    avatarUrl: patient.avatarUrl,
    phone: patient.phone,
    emergencyContactName: patient.emergencyContactName,
    emergencyContactRelation: patient.emergencyContactRelation,
    emergencyContactPhone: patient.emergencyContactPhone,
    identityMasked: patient.identityMasked,
    insuranceType: patient.insuranceType,
    department: patient.department,
    primaryDoctor: patient.primaryDoctor,
    caseManager: patient.caseManager,
    medicalRecordNumber: patient.medicalRecordNumber,
    archiveSource: patient.archiveSource,
    archiveStatus: patient.archiveStatus,
    consentStatus: patient.consentStatus,
    allergyHistory: patient.allergyHistory,
    familyHistory: patient.familyHistory,
    primaryDisease: patient.primaryDisease,
    currentStage: patient.currentStage,
    riskLevel: patient.riskLevel,
    lastVisit: patient.lastVisit,
    summary: patient.summary,
    dataSupport: patient.dataSupport,
  }
}

function resetPatientEditor() {
  selectedPatientId.value = ''
  selectedPatient.value = null
  patientQuadruples.value = []
  predictionResult.value = null
  medicationPlanResult.value = null
  patientForm.value = defaultPatientForm()
  eventForm.value = defaultEventForm()
}

function updateWindowQuery(
  nextSection: AppSection,
  nextArchiveMode: ArchiveMode = archiveMode.value,
  patientId = '',
  focusSection: ArchiveFocusSection = archiveFocusSection.value
) {
  if (typeof window === 'undefined') return
  const url = new URL(window.location.href)
  url.searchParams.delete('view')
  url.searchParams.delete('patientId')
  url.searchParams.delete('focus')
  url.searchParams.delete('resume')
  url.searchParams.delete('module')

  if (nextSection === 'archive' && nextArchiveMode === 'detail' && patientId) {
    url.searchParams.set('view', 'archive-detail')
    url.searchParams.set('patientId', patientId)
    if (focusSection === 'events') {
      url.searchParams.set('focus', 'events')
    }
  } else {
    url.searchParams.set('module', nextSection)
  }

  window.history.replaceState({}, '', url.toString())
}

function openArchiveInNewTab(patientId: string, focusSection: ArchiveFocusSection = 'overview') {
  if (!canAccessSection('archive')) {
    setPermissionError('当前账号无权进入档案模块。')
    return
  }
  if (typeof window === 'undefined') return
  const url = new URL(window.location.href)
  url.searchParams.set('view', 'archive-detail')
  url.searchParams.set('patientId', patientId)
  url.searchParams.set('resume', '1')
  if (focusSection === 'events') {
    url.searchParams.set('focus', 'events')
  } else {
    url.searchParams.delete('focus')
  }
  url.searchParams.delete('module')
  window.open(url.toString(), '_blank', 'noopener')
}

function redirectToHomeSection() {
  const fallback = defaultSectionForRole(currentDoctor.value?.role)
  if (fallback === 'archive') {
    section.value = 'archive'
    archiveMode.value = 'list'
    archiveFocusSection.value = 'overview'
    updateWindowQuery('archive', 'list')
    return
  }

  if (fallback === 'tasks') {
    followupFocusPatientId.value = ''
    section.value = 'tasks'
    updateWindowQuery('tasks')
    if (!flowBoardItems.value.length && !followupItems.value.length) {
      void loadOperationalBoards()
    }
    return
  }

  section.value = 'doctor'
  doctorMode.value = 'list'
  updateWindowQuery('doctor')
}

async function openFollowupModule(patientId?: string) {
  if (!canAccessSection('tasks')) {
    setPermissionError('当前账号无权进入随访工作台。')
    followupFocusPatientId.value = ''
    redirectToHomeSection()
    return
  }

  followupFocusPatientId.value = patientId ?? ''
  section.value = 'tasks'
  archiveSuccess.value = ''
  screenError.value = ''
  updateWindowQuery('tasks')

  if (patientId && !flowBoardItems.value.length && !followupItems.value.length) {
    await loadOperationalBoards()
  }
}

function openArchiveEventEditor(patientId: string) {
  openArchiveInNewTab(patientId, 'events')
}

function openCreateModule() {
  if (!canManageArchive()) {
    setPermissionError('当前账号无权新建或修改患者档案。')
    return
  }

  section.value = 'archive'
  archiveMode.value = 'create'
  archiveFocusSection.value = 'overview'
  importResultText.value = ''
  archiveSuccess.value = ''
  screenError.value = ''
  resetPatientEditor()
  updateWindowQuery('archive', 'create')
}

function openImportModule() {
  if (!canManageArchive()) {
    setPermissionError('当前账号无权导入患者档案。')
    return
  }

  section.value = 'archive'
  archiveMode.value = 'import'
  importResultText.value = ''
  archiveSuccess.value = ''
  screenError.value = ''
  updateWindowQuery('archive', 'import')
}

function handleExportPatients() {
  if (!canManageArchive()) {
    setPermissionError('当前账号无权导出患者档案。')
    return
  }

  // 导出患者数据为JSON
  const dataStr = JSON.stringify(allPatients.value, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `patients_${new Date().toISOString().slice(0, 10)}.json`
  link.click()
  URL.revokeObjectURL(url)

  archiveSuccess.value = `已导出 ${allPatients.value.length} 个患者档案`
}

function markPatientViewed(patientId: string) {
  viewedPatientIds.value = [patientId, ...viewedPatientIds.value.filter((item) => item !== patientId)]
}

async function loadPatients() {
  loadingPatients.value = true
  screenError.value = ''
  try {
    // 当前工作台在前端本地分页，直接拉取完整患者列表更稳定，
    // 避免与后端分页上限不一致导致档案页显示 0 条。
    allPatients.value = sortPatients(await getPatients())
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '加载患者列表失败'
  } finally {
    loadingPatients.value = false
  }
}

async function refreshHealthStatus() {
  try {
    health.value = await healthCheck()
  } catch (error) {
    health.value = null
    screenError.value = error instanceof Error ? error.message : '无法连接后端服务，请检查后端是否启动。'
  }
}

async function loadOperationalBoards() {
  if (!canUseFollowupWorkspace()) {
    loadingBoards.value = false
    followupItems.value = []
    flowBoardItems.value = []
    followupFocusPatientId.value = ''
    return
  }

  loadingBoards.value = true
  try {
    const [followups, flowBoard] = await Promise.all([getFollowupWorklist(), getFlowBoard()])
    followupItems.value = followups.items
    flowBoardItems.value = flowBoard.items
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '加载任务中心数据失败'
  } finally {
    loadingBoards.value = false
  }
}

async function loadGovernanceBoards() {
  if (!canUseGovernanceWorkspace()) {
    governanceModules.value = null
    maintenanceOverview.value = null
    modelMetrics.value = null
    loadingGovernance.value = false
    loadingMaintenance.value = false
    loadingModelMetrics.value = false
    return
  }

  loadingGovernance.value = true
  try {
    governanceModules.value = await getGovernanceModules()
  } catch (error) {
    governanceModules.value = null
    screenError.value = error instanceof Error ? error.message : '加载模块治理信息失败'
  } finally {
    loadingGovernance.value = false
  }

  loadingMaintenance.value = true
  try {
    maintenanceOverview.value = await getMaintenanceOverview()
  } catch (error) {
    maintenanceOverview.value = null
    screenError.value = error instanceof Error ? error.message : '加载治理概览失败'
  } finally {
    loadingMaintenance.value = false
  }

  if (!canUseDoctorWorkspace()) {
    modelMetrics.value = null
    loadingModelMetrics.value = false
    return
  }

  loadingModelMetrics.value = true
  try {
    modelMetrics.value = await getModelMetrics()
  } catch (error) {
    modelMetrics.value = null
    screenError.value = error instanceof Error ? error.message : '加载模型指标失败'
  } finally {
    loadingModelMetrics.value = false
  }
}

async function refreshWorkspaceData() {
  await refreshHealthStatus()
  await loadPatients()
  await loadOperationalBoards()
  await loadGovernanceBoards()
}

async function refreshGovernanceWorkspace() {
  await refreshHealthStatus()
  await loadGovernanceBoards()
}

async function openPatient(patientId: string, target: 'doctor' | 'archive' = 'doctor', focusSection: ArchiveFocusSection = 'overview') {
  const resolvedTarget = target === 'doctor' && !canUseDoctorWorkspace() ? 'archive' : target
  loadingPatient.value = true
  screenError.value = ''
  archiveSuccess.value = ''

  try {
    const patient = await getPatientCase(patientId)
    selectedPatientId.value = patientId
    selectedPatient.value = patient
    syncPatientForm(patient)

    if (resolvedTarget === 'doctor') {
      patientQuadruples.value = await getPatientQuadruples(patientId)
      predictionResult.value = null
      medicationPlanResult.value = null
      markPatientViewed(patientId)
      section.value = 'doctor'
      doctorMode.value = 'detail'
      updateWindowQuery('doctor')
    } else {
      section.value = 'archive'
      archiveMode.value = 'detail'
      archiveFocusSection.value = focusSection
      updateWindowQuery('archive', 'detail', patientId, focusSection)
    }
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '加载患者详情失败'
  } finally {
    loadingPatient.value = false
  }
}

function backToDoctorList() {
  if (!canAccessSection('doctor')) {
    redirectToHomeSection()
    return
  }

  section.value = 'doctor'
  doctorMode.value = 'list'
  updateWindowQuery('doctor')
}

function backToArchiveList() {
  section.value = 'archive'
  archiveMode.value = 'list'
  archiveFocusSection.value = 'overview'
  updateWindowQuery('archive', 'list')
}

function selectSection(nextSection: AppSection) {
  archiveSuccess.value = ''
  screenError.value = ''

  if (!canAccessSection(nextSection)) {
    setPermissionError('当前账号无权进入该模块。')
    redirectToHomeSection()
    return
  }

  if (nextSection === 'doctor') {
    section.value = 'doctor'
    doctorMode.value = 'list'
    updateWindowQuery('doctor')
    return
  }

  if (nextSection === 'archive') {
    section.value = 'archive'
    archiveMode.value = 'list'
    archiveFocusSection.value = 'overview'
    updateWindowQuery('archive', 'list')
    return
  }

  if (nextSection === 'governance') {
    section.value = 'governance'
    updateWindowQuery('governance')
    if (!maintenanceOverview.value) {
      void refreshGovernanceWorkspace()
    }
    return
  }

  void openFollowupModule()
}

async function finishLogin(sessionDoctor: DoctorUser) {
  currentDoctor.value = sessionDoctor
  viewedPatientIds.value = []
  await refreshWorkspaceData()

  const url = typeof window !== 'undefined' ? new URL(window.location.href) : null
  const hasArchiveDetail = url?.searchParams.get('view') === 'archive-detail'
  const patientId = url?.searchParams.get('patientId')
  const focus = url?.searchParams.get('focus') === 'events' ? 'events' : 'overview'
  const moduleValue = url?.searchParams.get('module')

  if (hasArchiveDetail && patientId && canAccessSection('archive')) {
    await openPatient(patientId, 'archive', focus)
    return
  }

  if (moduleValue === 'archive' && canAccessSection('archive')) {
    section.value = 'archive'
    archiveMode.value = 'list'
    updateWindowQuery('archive', 'list')
    return
  }

  if (moduleValue === 'tasks' && canAccessSection('tasks')) {
    await openFollowupModule()
    return
  }

  if (moduleValue === 'governance' && canAccessSection('governance')) {
    section.value = 'governance'
    updateWindowQuery('governance')
    return
  }

  if (moduleValue === 'doctor' && canAccessSection('doctor')) {
    section.value = 'doctor'
    doctorMode.value = 'list'
    updateWindowQuery('doctor')
    return
  }

  section.value = defaultSectionForRole(sessionDoctor.role)
  doctorMode.value = 'list'
  archiveMode.value = 'list'
  updateWindowQuery(section.value)
}

async function submitLogin() {
  loadingLogin.value = true
  loginError.value = ''

  try {
    const session = await loginDoctor(username.value.trim(), password.value)
    await finishLogin(session.doctor)
  } catch (error) {
    loginError.value = error instanceof Error ? error.message : '鐧诲綍澶辫触'
  } finally {
    loadingLogin.value = false
  }
}

async function submitRegister() {
  loadingRegister.value = true
  registerError.value = ''

  try {
    const session = await registerDoctor(registerForm.value)
    registerMode.value = false
    await finishLogin(session.doctor)
  } catch (error) {
    registerError.value = error instanceof Error ? error.message : '娉ㄥ唽澶辫触'
  } finally {
    loadingRegister.value = false
  }
}

function toggleRegister(value: boolean) {
  registerMode.value = value
  loginError.value = ''
  registerError.value = ''
  if (!value) {
    registerForm.value = {
      username: '',
      password: '',
      name: '',
      role: 'doctor',
      title: '主治医师',
      department: '慢病管理门诊',
    }
  }
}

function logout() {
  logoutDoctor()
  currentDoctor.value = null
  allPatients.value = []
  followupItems.value = []
  flowBoardItems.value = []
  governanceModules.value = null
  maintenanceOverview.value = null
  modelMetrics.value = null
  followupFocusPatientId.value = ''
  archiveFocusSection.value = 'overview'
  viewedPatientIds.value = []
  screenError.value = ''
  archiveSuccess.value = ''
  importResultText.value = ''
  workspaceSearchText.value = ''
  workspaceRiskFilter.value = '全部风险'
  archivePage.value = 1
  section.value = 'doctor'
  doctorMode.value = 'list'
  archiveMode.value = 'list'
  resetPatientEditor()
  updateWindowQuery('doctor')
}

async function runPrediction() {
  if (!selectedPatient.value) return
  if (!canUseDoctorWorkspace()) {
    setPermissionError('当前账号无权运行临床预测。')
    return
  }

  loadingPredict.value = true
  screenError.value = ''

  try {
    predictionResult.value = await predictPatient({
      patientId: selectedPatient.value.patientId,
      asOfTime: selectedPatient.value.lastVisit,
      topk: 3,
    })
    await loadOperationalBoards()
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '杩愯棰勬祴澶辫触'
  } finally {
    loadingPredict.value = false
  }
}

async function runMedicationPlan(patientId: string, payload: MedicationPlanGeneratePayload) {
  if (!patientId) return
  if (!canUseDoctorWorkspace()) {
    setPermissionError('当前账号无权生成用药建议。')
    return
  }

  screenError.value = ''
  archiveSuccess.value = ''

  try {
    medicationPlanResult.value = await generateMedicationPlan(patientId, payload)
    archiveSuccess.value = '用药建议已生成，请结合门诊处方复核后执行。'
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '生成用药建议失败'
  }
}

async function submitArchive() {
  if (!canManageArchive()) {
    setPermissionError('当前账号无权保存患者档案。')
    return
  }

  savingPatient.value = true
  archiveSuccess.value = ''
  screenError.value = ''
  const creating = !selectedPatientId.value

  try {
    const payload = {
      ...patientForm.value,
      age: Number(patientForm.value.age),
      actorUsername: currentDoctor.value?.username,
      actorName: currentDoctor.value?.name,
    }
    const saved = selectedPatientId.value
      ? await updatePatient(selectedPatientId.value, payload)
      : await savePatient(payload)

    selectedPatientId.value = saved.patientId
    selectedPatient.value = saved
    syncPatientForm(saved)
    await refreshWorkspaceData()

    section.value = 'archive'
    archiveMode.value = 'detail'
    archiveFocusSection.value = 'overview'
    updateWindowQuery('archive', 'detail', saved.patientId, 'overview')
    archiveSuccess.value = creating ? '患者档案已创建，可继续补录结构化事件。' : '患者档案已更新。'
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '保存患者档案失败'
  } finally {
    savingPatient.value = false
  }
}

async function submitEvent() {
  const patientId = selectedPatientId.value || patientForm.value.patientId
  if (!patientId) {
    screenError.value = '请先创建患者基础档案，再补录结构化事件。'
    return
  }

  if (!canRecordClinicalEvent()) {
    setPermissionError('当前账号无权补录结构化临床事件。')
    return
  }

  savingEvent.value = true
  archiveSuccess.value = ''
  screenError.value = ''

  try {
    const updated = await addPatientEvent(patientId, {
      ...eventForm.value,
      actorUsername: currentDoctor.value?.username,
      actorName: currentDoctor.value?.name,
    })
    selectedPatientId.value = updated.patientId
    selectedPatient.value = updated
    syncPatientForm(updated)
    eventForm.value = defaultEventForm()
    await refreshWorkspaceData()
    archiveSuccess.value = '结构化事件已写入患者档案。'
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '新增结构化事件失败'
  } finally {
    savingEvent.value = false
  }
}

async function applyEncounterStatus(patientId: string, status: 'waiting' | 'in_progress' | 'pending_review' | 'completed') {
  if (!patientId) return
  if (!canUseFollowupWorkspace()) {
    setPermissionError('当前账号无权更新接诊状态。')
    return
  }

  screenError.value = ''

  try {
    const updated = await updatePatientEncounterStatus(patientId, { status })
    if (selectedPatientId.value === patientId) {
      selectedPatient.value = updated
      syncPatientForm(updated)
    }
    await loadOperationalBoards()
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '更新接诊状态失败'
  }
}

async function submitContactLog(patientId: string, payload: ContactLogCreatePayload) {
  if (!patientId) {
    screenError.value = '请先选择患者，再记录电话随访结果。'
    return
  }

  if (!canUseFollowupWorkspace()) {
    setPermissionError('当前账号无权登记联系记录。')
    return
  }

  savingContactLog.value = true
  archiveSuccess.value = ''
  screenError.value = ''

  try {
    const updated = await addPatientContactLog(patientId, {
      ...payload,
      actorUsername: currentDoctor.value?.username,
      actorName: currentDoctor.value?.name,
    })
    selectedPatientId.value = updated.patientId
    selectedPatient.value = updated
    syncPatientForm(updated)
    await refreshWorkspaceData()
    archiveSuccess.value = '联系记录已写入患者档案。'
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '保存联系记录失败'
  } finally {
    savingContactLog.value = false
  }
}

async function registerOutpatientTask(patientId: string, item: OutpatientPlanItem) {
  if (!patientId) return
  if (!canUseDoctorWorkspace()) {
    setPermissionError('当前账号无权登记门诊任务。')
    return
  }

  screenError.value = ''
  archiveSuccess.value = ''

  const dueLabel = item.dueLabel
  const followupDays = dueLabel.includes('1-2') ? 10 : dueLabel.includes('1') ? 7 : 0

  try {
    const updated = await createPatientOutpatientTask(patientId, {
      category: item.category,
      title: item.title,
      owner: item.owner,
      dueDate: new Date(Date.now() + followupDays * 86400000)
        .toISOString()
        .slice(0, 10),
      priority: item.priority,
      note: item.note,
      status: '待执行',
      source: 'workspace',
      actorUsername: currentDoctor.value?.username,
      actorName: currentDoctor.value?.name,
    })
    if (selectedPatientId.value === patientId) {
      selectedPatient.value = updated
      syncPatientForm(updated)
    }
    await loadOperationalBoards()
    archiveSuccess.value = '闂ㄨ瘖浠诲姟宸茬櫥璁板埌鍚庣宸ヤ綔闃熷垪'
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '登记门诊任务失败'
  }
}

async function changeOutpatientTaskStatus(
  patientId: string,
  taskId: string,
  status: '已完成' | '已关闭'
) {
  if (!patientId || !taskId) return
  if (!canUseFollowupWorkspace()) {
    setPermissionError('当前账号无权更新门诊任务状态。')
    return
  }

  screenError.value = ''
  archiveSuccess.value = ''

  try {
    const updated = await updatePatientOutpatientTaskStatus(patientId, taskId, {
      status,
      actorUsername: currentDoctor.value?.username,
      actorName: currentDoctor.value?.name,
    })
    if (selectedPatientId.value === patientId) {
      selectedPatient.value = updated
      syncPatientForm(updated)
    }
    await loadOperationalBoards()
    archiveSuccess.value = status === '已完成' ? '门诊任务已标记为完成' : '门诊任务已关闭'
  } catch (error) {
    screenError.value = error instanceof Error ? error.message : '更新门诊任务状态失败'
  }
}

async function submitImport(rows: ImportPreviewPatient[]) {
  if (!canManageArchive()) {
    setPermissionError('当前账号无权批量导入患者档案。')
    return
  }

  importingArchive.value = true
  screenError.value = ''
  archiveSuccess.value = ''
  importResultText.value = ''
  let successCount = 0
  let failedCount = 0

  for (const row of rows) {
    const payload: PatientUpsertPayload = {
      patientId: row.patientId,
      name: row.name,
      age: Number(row.age) || 0,
      gender: row.gender,
      avatarUrl: row.avatarUrl,
      phone: row.phone,
      emergencyContactName: row.emergencyContactName,
      emergencyContactRelation: row.emergencyContactRelation,
      emergencyContactPhone: row.emergencyContactPhone,
      identityMasked: row.identityMasked,
      insuranceType: row.insuranceType,
      department: row.department,
      primaryDoctor: row.primaryDoctor,
      caseManager: row.caseManager,
      medicalRecordNumber: row.medicalRecordNumber,
      archiveSource: row.archiveSource,
      archiveStatus: row.archiveStatus,
      consentStatus: row.consentStatus,
      allergyHistory: row.allergyHistory,
      familyHistory: row.familyHistory,
      primaryDisease: row.primaryDisease,
      currentStage: row.currentStage,
      riskLevel: row.riskLevel,
      lastVisit: row.lastVisit,
      summary: row.summary,
      dataSupport: row.dataSupport,
      actorUsername: currentDoctor.value?.username,
      actorName: currentDoctor.value?.name,
    }

    try {
      await savePatient(payload)
      successCount += 1
    } catch (error) {
      try {
        await updatePatient(payload.patientId, payload)
        successCount += 1
      } catch {
        failedCount += 1
        if (!screenError.value) {
          screenError.value = error instanceof Error ? error.message : '閮ㄥ垎妗ｆ瀵煎叆澶辫触'
        }
      }
    }
  }

  importingArchive.value = false
  await refreshWorkspaceData()
  importResultText.value = `导入完成：成功 ${successCount} 条，失败 ${failedCount} 条。`
  if (successCount > 0) {
    section.value = 'archive'
    archiveMode.value = 'list'
    archiveSuccess.value = '外院档案已导入，可继续打开详情补录结构化事件。'
    updateWindowQuery('archive', 'list')
  }
}

function prevArchivePage() {
  archivePage.value = Math.max(1, archivePage.value - 1)
}

function nextArchivePage() {
  archivePage.value = Math.min(archiveTotalPages.value, archivePage.value + 1)
}

watch([workspaceSearchText, workspaceRiskFilter], () => {
  showAllPending.value = false
})

watch(archiveTotalPages, (value) => {
  if (archivePage.value > value) {
    archivePage.value = value
  }
})

onMounted(async () => {
  await refreshHealthStatus()

  if (typeof window === 'undefined') return
  const url = new URL(window.location.href)
  if (url.searchParams.get('resume') !== '1') return

  const restored = restoreAuthSession()
  if (restored) {
    await finishLogin(restored.doctor)
  }
})
</script>

<template>
  <LoginScreen
    v-if="!currentDoctor"
    :username="username"
    :password="password"
    :login-error="loginError"
    :loading-login="loadingLogin"
    :health="health"
    :register-mode="registerMode"
    :register-form="registerForm"
    :register-error="registerError"
    :loading-register="loadingRegister"
    @update:username="username = $event"
    @update:password="password = $event"
    @submit-login="submitLogin"
    @toggle-register="toggleRegister"
    @submit-register="submitRegister"
  />

  <div v-else class="app-shell" :class="appRoleClass">
    <AppSidebar
      :active-section="section"
      :doctor="currentDoctor"
      :health="health"
      :patient-count="allPatients.length"
      :followup-count="followupItems.length"
      @select="selectSection"
      @logout="logout"
    />

    <main class="main-shell">
      <p v-if="screenError" class="error-banner">{{ screenError }}</p>
      <p v-if="archiveSuccess" class="success-banner">{{ archiveSuccess }}</p>

      <WorkspaceTopbar
        :doctor="currentDoctor"
        :section="section"
        :health="health"
      />

      <RoleWorkspaceBanner
        :doctor="currentDoctor"
        :section="section"
        :patient-count="allPatients.length"
        :followup-count="followupItems.length"
      />

      <!-- 医生工作台（使用带分页的组件） -->
      <DoctorWorkspacePage
        v-if="section === 'doctor' && currentDoctor.role === 'doctor'"
        :mode="doctorMode"
        :all-patients="allPatients"
        :patients="visiblePendingPatients"
        :recent-viewed="recentViewedPatients"
        :flow-board-items="flowBoardItems"
        :selected-patient="selectedPatient"
        :patient-quadruples="patientQuadruples"
        :prediction-result="predictionResult"
        :medication-plan-result="medicationPlanResult"
        :encounter-status="selectedPatient?.encounterStatus ?? 'waiting'"
        :saving-contact-log="savingContactLog"
        :loading-patients="loadingPatients"
        :loading-patient="loadingPatient"
        :loading-predict="loadingPredict"
        :search-text="workspaceSearchText"
        :risk-filter="workspaceRiskFilter"
        :risk-options="riskOptions"
        :hidden-count="hiddenPendingCount"
        :show-all-pending="showAllPending"
        @update:search-text="workspaceSearchText = $event"
        @update:risk-filter="workspaceRiskFilter = $event"
        @toggle-show-all="showAllPending = !showAllPending"
        @open="openPatient($event, 'doctor')"
        @open-archive="openArchiveInNewTab"
        @open-archive-events="openArchiveEventEditor"
        @open-followup="openFollowupModule"
        @update-encounter-status="applyEncounterStatus"
        @create-outpatient-task="registerOutpatientTask"
        @submit-contact-log="submitContactLog"
        @generate-medication-plan="runMedicationPlan"
        @predict="runPrediction"
        @back="backToDoctorList"
      />

      <ArchivePage
        v-else-if="section === 'archive'"
        :mode="archiveMode"
        :all-patients="allPatients"
        :patients="archivePagedPatients"
        :loading-patients="loadingPatients"
        :current-page="archivePage"
        :total-pages="archiveTotalPages"
        :patient-count="allPatients.length"
        :patient-form="patientForm"
        :selected-patient-id="selectedPatientId"
        :event-form="eventForm"
        :relation-options="relationOptions"
        :saving-patient="savingPatient"
        :saving-event="savingEvent"
        :timeline-items="selectedPatient?.timeline ?? []"
        :selected-patient="selectedPatient"
        :focus-section="archiveFocusSection"
        :importing-archive="importingArchive"
        :import-result-text="importResultText"
        :doctor-role="currentDoctor.role"
        @open="openPatient($event, 'archive')"
        @create="openCreateModule"
        @import="openImportModule"
        @export="handleExportPatients"
        @prev-page="prevArchivePage"
        @next-page="nextArchivePage"
        @submit-archive="submitArchive"
        @submit-event="submitEvent"
        @submit-import="submitImport"
        @prepare-new="openCreateModule"
        @back="backToArchiveList"
      />

      <GovernancePage
        v-else-if="section === 'governance'"
        :doctor-role="currentDoctor.role"
        :health="health"
        :maintenance="maintenanceOverview"
        :governance-modules="governanceModules"
        :model-metrics="modelMetrics"
        :loading-governance="loadingGovernance"
        :loading-maintenance="loadingMaintenance"
        :loading-metrics="loadingModelMetrics"
        @refresh="refreshGovernanceWorkspace"
        @open-patient="openPatient($event, 'archive')"
      />

      <FollowupPage
        v-else
        :loading="loadingBoards"
        :followup-items="followupItems"
        :flow-board-items="flowBoardItems"
        :selected-patient-id="followupFocusPatientId"
        :saving-contact-log="savingContactLog"
        :doctor-role="currentDoctor.role"
        @open-patient="openPatient($event, 'doctor')"
        @open-archive="openArchiveInNewTab"
        @complete-task="changeOutpatientTaskStatus($event.patientId, $event.taskId, '已完成')"
        @close-task="changeOutpatientTaskStatus($event.patientId, $event.taskId, '已关闭')"
        @submit-contact-log="submitContactLog"
      />
    </main>
  </div>
</template>

