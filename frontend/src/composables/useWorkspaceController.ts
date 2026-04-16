import { computed, reactive, ref, watch } from 'vue'
import {
  addPatientContactLog,
  addPatientEvent,
  createPatientOutpatientTask,
  generateMedicationPlan,
  getFlowBoard,
  getFollowupWorklist,
  getGovernanceModules,
  getAuthzCapabilities,
  getSystemAudit,
  getMaintenanceOverview,
  getMe,
  getModelMetrics,
  getPatientCase,
  getPatientQuadruples,
  getPatients,
  healthCheck,
  loginDoctor,
  logoutDoctor,
  predictPatient,
  registerDoctor,
  restoreAuthSession,
  savePatient,
  updatePatient,
  updatePatientEncounterStatus,
  updatePatientOutpatientTaskStatus,
} from '../services/api'
import type {
  AuthzCapabilityResponse,
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
  SystemAuditLog,
} from '../services/types'
import { useAuditTrailStore } from '../stores/auditTrailStore'
import { allowedSectionsForRole, sectionLabel } from '../config/workspaceMenu'
import type { AppSection, ArchiveFocusSection, ArchiveMode, DoctorMode } from '../types/workspace'

const RISK_ALL = '全部风险'
const TASK_STATUS_PENDING = 'Pending'
const TASK_STATUS_COMPLETED = 'Completed'
const TASK_STATUS_CLOSED = 'Closed'
const APP_SECTIONS: AppSection[] = [
  'doctor',
  'archive',
  'tasks',
  'governance',
  'insights',
  'contacts',
  'flow',
  'data-quality',
  'system',
]

export function useWorkspaceController() {
  const auditTrail = useAuditTrailStore()
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
    title: 'Attending Physician',
    department: 'Chronic Care Clinic',
  })

  const section = ref<AppSection>('doctor')
  const doctorMode = ref<DoctorMode>('list')
  const archiveMode = ref<ArchiveMode>('list')
  const permissionHint = ref('')

  const allPatients = ref<PatientSummary[]>([])
  const followupItems = ref<FollowupTaskRow[]>([])
  const flowBoardItems = ref<FlowBoardRow[]>([])
  const maintenanceOverview = ref<MaintenanceOverview | null>(null)
  const governanceModules = ref<GovernanceModulesResponse | null>(null)
  const modelMetrics = ref<ModelMetricsResponse | null>(null)
  const me = ref<{ username: string; name: string; title: string; department: string; role: string } | null>(null)
  const authz = ref<AuthzCapabilityResponse | null>(null)
  const systemAudit = ref<SystemAuditLog[]>([])
  const loadingSystemCenter = ref(false)
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
  const loadingOpenArchive = ref(false)
  const loadingOpenFollowup = ref(false)
  const loadingEncounterStatus = ref(false)
  const loadingCreateTask = ref(false)
  const loadingTaskStatus = ref(false)
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
  const workspaceRiskFilter = ref(RISK_ALL)
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
    if (!role) return 'doctor'
    return allowedSectionsForRole(role)[0] ?? 'doctor'
  }

  function parseSection(value: string | null | undefined): AppSection | null {
    if (!value) return null
    return APP_SECTIONS.includes(value as AppSection) ? (value as AppSection) : null
  }

  function canAccessSection(nextSection: AppSection) {
    const role = currentDoctor.value?.role
    if (!role) return false
    return allowedSectionsForRole(role).includes(nextSection)
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
    permissionHint.value = message
  }

  function clearMessages() {
    archiveSuccess.value = ''
    screenError.value = ''
    permissionHint.value = ''
  }

  function logAudit(
    action: 'login' | 'view_patient_detail' | 'trigger_prediction' | 'generate_advice' | 'create_followup_task' | 'modify_archive',
    target: { type: string; id: string; label?: string },
    result: 'success' | 'failed' | 'degraded',
    detail: string,
    actor?: { username?: string; name?: string; role?: 'doctor' | 'nurse' | 'archivist' | 'unknown' }
  ) {
    auditTrail.addAuditLog({
      actor: actor ?? {
        username: currentDoctor.value?.username,
        name: currentDoctor.value?.name,
        role: currentDoctor.value?.role,
      },
      action,
      target,
      result,
      detail,
    })
  }

  function defaultPatientForm(): PatientUpsertPayload {
    return {
      patientId: '',
      name: '',
      age: 0,
      gender: 'Unknown',
      avatarUrl: '',
      phone: '',
      emergencyContactName: '',
      emergencyContactRelation: '',
      emergencyContactPhone: '',
      identityMasked: '',
      insuranceType: 'Urban Employee',
      department: 'Chronic Care Clinic',
      primaryDoctor: currentDoctor.value?.name || 'Doctor',
      caseManager: 'Nurse',
      allergyHistory: '',
      familyHistory: '',
      medicalRecordNumber: '',
      archiveSource: 'outpatient',
      archiveStatus: 'active',
      consentStatus: 'signed',
      primaryDisease: 'Diabetes',
      currentStage: 'Early',
      riskLevel: 'Medium Risk',
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
    return value.toLowerCase().includes('high')
  }

  function isMediumRisk(value: string) {
    return value.toLowerCase().includes('medium')
  }

  function riskRank(value: string) {
    if (isHighRisk(value)) return 0
    if (isMediumRisk(value)) return 1
    return 2
  }

  const riskOptions = computed(() => {
    const dynamicLevels = Array.from(new Set(allPatients.value.map((item) => item.riskLevel)))
    return [RISK_ALL, ...dynamicLevels]
  })

  const filteredWorkspacePatients = computed(() =>
    allPatients.value.filter((item) => {
      const matchesRisk = workspaceRiskFilter.value === RISK_ALL || item.riskLevel === workspaceRiskFilter.value
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

  const appRoleClass = computed(() => `app-role-${currentDoctor.value?.role ?? 'guest'}`)

  const globalLoading = computed(
    () =>
      loadingLogin.value ||
      loadingRegister.value ||
      loadingPatients.value ||
      loadingPatient.value ||
      loadingOpenArchive.value ||
      loadingOpenFollowup.value ||
      loadingEncounterStatus.value ||
      loadingCreateTask.value ||
      loadingTaskStatus.value ||
      loadingBoards.value ||
      loadingGovernance.value ||
      loadingMaintenance.value ||
      loadingModelMetrics.value ||
      loadingSystemCenter.value
  )

  const modelUnavailable = computed(() => Boolean(health.value && health.value.model_available === false))
  const doctorNoPermission = computed(() => Boolean(currentDoctor.value) && !canUseDoctorWorkspace())
  const archiveNoPermission = computed(() => Boolean(currentDoctor.value) && !canManageArchive())
  const followupNoPermission = computed(() => Boolean(currentDoctor.value) && !canUseFollowupWorkspace())
  const currentWorkspace = computed<
    'doctor' | 'archive' | 'governance' | 'model-dashboard' | 'model-insight' | 'followup' | 'system' | 'unknown'
  >(() => {
    if (section.value === 'doctor') return 'doctor'
    if (section.value === 'archive' || section.value === 'data-quality') return 'archive'
    if (section.value === 'governance') return 'governance'
    if (section.value === 'model-dashboard') return 'model-dashboard'
    if (section.value === 'insights') return 'model-insight'
    if (section.value === 'tasks' || section.value === 'contacts' || section.value === 'flow') return 'followup'
    if (section.value === 'system') return 'system'
    return 'unknown'
  })

  async function loadSystemCenter() {
    loadingSystemCenter.value = true
    screenError.value = ''
    try {
      const [meResp, capsResp, auditResp] = await Promise.all([getMe(), getAuthzCapabilities(), getSystemAudit(80)])
      me.value = meResp
      authz.value = capsResp
      systemAudit.value = auditResp.items
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to load system center.'
    } finally {
      loadingSystemCenter.value = false
    }
  }

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

  async function openArchiveInNewTab(patientId: string, focusSection: ArchiveFocusSection = 'overview') {
    if (!canAccessSection('archive')) {
      setPermissionError('Current role has no permission to open patient archive.')
      return
    }
    if (!patientId) {
      screenError.value = 'Please select a patient before opening archive.'
      return
    }

    loadingOpenArchive.value = true
    archiveSuccess.value = ''
    screenError.value = ''
    try {
      const ok = await openPatient(patientId, 'archive', focusSection)
      if (ok) {
        archiveSuccess.value = 'Patient archive opened successfully.'
      }
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to open patient archive.'
    } finally {
      loadingOpenArchive.value = false
    }
  }

  function redirectToHomeSection() {
    const fallback = defaultSectionForRole(currentDoctor.value?.role)
    void navigateToSection(fallback)
  }

  async function openFollowupModule(patientId?: string, targetSection: 'tasks' | 'contacts' | 'flow' = 'tasks') {
    if (!canAccessSection(targetSection)) {
      setPermissionError('Current role has no permission to open follow-up workspace.')
      followupFocusPatientId.value = ''
      redirectToHomeSection()
      return
    }

    // 确保使用正确的 patientId
    const targetPatientId = patientId || selectedPatientId.value || ''
    if (!targetPatientId) {
      screenError.value = 'Please select a patient before opening follow-up workspace.'
      return
    }

    loadingOpenFollowup.value = true
    followupFocusPatientId.value = targetPatientId
    section.value = targetSection
    clearMessages()
    updateWindowQuery(targetSection)

    try {
      await loadOperationalBoards()
      archiveSuccess.value = 'Follow-up workspace opened successfully.'
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to open follow-up workspace.'
    } finally {
      loadingOpenFollowup.value = false
    }
  }

  function openArchiveEventEditor(patientId: string) {
    openArchiveInNewTab(patientId, 'events')
  }

  function openCreateModule() {
    if (!canManageArchive()) {
      setPermissionError('Current role has no permission to create archive.')
      return
    }

    section.value = 'archive'
    archiveMode.value = 'create'
    archiveFocusSection.value = 'overview'
    importResultText.value = ''
    archiveSuccess.value = ''
    screenError.value = ''
    resetPatientEditor()
    archiveSuccess.value = 'Create archive form is ready.'
    updateWindowQuery('archive', 'create')
  }

  function openImportModule() {
    if (!canManageArchive()) {
      setPermissionError('Current role has no permission to import archive.')
      return
    }

    section.value = 'archive'
    archiveMode.value = 'import'
    importResultText.value = ''
    archiveSuccess.value = ''
    screenError.value = ''
    archiveSuccess.value = 'Import module opened.'
    updateWindowQuery('archive', 'import')
  }

  function handleExportPatients() {
    if (!canManageArchive()) {
      setPermissionError('Current role has no permission to export archive.')
      return
    }

    const dataStr = JSON.stringify(allPatients.value, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `patients_${new Date().toISOString().slice(0, 10)}.json`
    link.click()
    URL.revokeObjectURL(url)

    archiveSuccess.value = `Exported ${allPatients.value.length} patients.`
  }

  function markPatientViewed(patientId: string) {
    viewedPatientIds.value = [patientId, ...viewedPatientIds.value.filter((item) => item !== patientId)]
  }

  async function loadPatients() {
    loadingPatients.value = true
    screenError.value = ''
    try {
      allPatients.value = sortPatients(await getPatients())
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to load patients.'
    } finally {
      loadingPatients.value = false
    }
  }

  async function refreshHealthStatus() {
    try {
      health.value = await healthCheck()
    } catch (error) {
      health.value = null
      screenError.value = error instanceof Error ? error.message : 'Failed to load health status.'
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
      screenError.value = error instanceof Error ? error.message : 'Failed to load follow-up board.'
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
      screenError.value = error instanceof Error ? error.message : 'Failed to load governance modules.'
    } finally {
      loadingGovernance.value = false
    }

    loadingMaintenance.value = true
    try {
      maintenanceOverview.value = await getMaintenanceOverview()
    } catch (error) {
      maintenanceOverview.value = null
      screenError.value = error instanceof Error ? error.message : 'Failed to load maintenance overview.'
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
      screenError.value = error instanceof Error ? error.message : 'Failed to load model metrics.'
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

  async function refreshModelMetrics() {
    await refreshHealthStatus()
    // TODO: 添加专门的模型指标加载逻辑
    // 目前使用 health 状态中的模型信息
  }

  async function openPatient(
    patientId: string,
    target: 'doctor' | 'archive' = 'doctor',
    focusSection: ArchiveFocusSection = 'overview'
  ): Promise<boolean> {
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
      logAudit(
        'view_patient_detail',
        { type: 'patient', id: patient.patientId, label: patient.name },
        'success',
        `Opened patient detail in ${resolvedTarget} workspace.`
      )
      return true
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to open patient.'
      logAudit(
        'view_patient_detail',
        { type: 'patient', id: patientId },
        'failed',
        error instanceof Error ? error.message : 'Failed to open patient detail.'
      )
      return false
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
    void navigateToSection('archive')
  }

  function isFollowupSection(value: AppSection) {
    return value === 'tasks' || value === 'contacts' || value === 'flow'
  }

  function isGovernanceSection(value: AppSection) {
    return value === 'governance'
  }

  function isModelDashboardSection(value: AppSection) {
    return value === 'model-dashboard'
  }

  function isModelInsightSection(value: AppSection) {
    return value === 'insights'
  }

  function isArchiveSection(value: AppSection) {
    return value === 'archive' || value === 'data-quality'
  }

  async function navigateToSection(nextSection: AppSection) {
    // 清理上一个模块的状态
    clearModuleState()

    // 重置滚动位置到顶部
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    if (nextSection === 'doctor') {
      section.value = 'doctor'
      doctorMode.value = 'list'
      updateWindowQuery('doctor')
      return
    }

    if (isArchiveSection(nextSection)) {
      section.value = nextSection
      archiveMode.value = 'list'
      archiveFocusSection.value = 'overview'
      updateWindowQuery(nextSection, 'list')
      return
    }

    if (isGovernanceSection(nextSection)) {
      section.value = nextSection
      updateWindowQuery(nextSection)
      if (!maintenanceOverview.value) {
        await refreshGovernanceWorkspace()
      }
      return
    }

    if (isModelDashboardSection(nextSection)) {
      section.value = nextSection
      updateWindowQuery(nextSection)
      if (!modelMetrics.value) {
        await refreshModelMetrics()
      }
      return
    }

    if (isModelInsightSection(nextSection)) {
      section.value = nextSection
      updateWindowQuery(nextSection)
      return
    }

    if (nextSection === 'system') {
      section.value = nextSection
      updateWindowQuery(nextSection)
      await refreshHealthStatus()
      await loadSystemCenter()
      return
    }

    if (isFollowupSection(nextSection)) {
      await openFollowupModule(followupFocusPatientId.value || selectedPatientId.value, nextSection)
      return
    }

    section.value = defaultSectionForRole(currentDoctor.value?.role)
    updateWindowQuery(section.value)
  }

  // 清理模块状态的方法
  function clearModuleState() {
    // 清理选中的患者
    selectedPatientId.value = ''
    selectedPatient.value = null

    // 清理预测结果
    predictionResult.value = null

    // 清理患者详情
    patientQuadruples.value = []

    // 清理档案相关状态
    archiveMode.value = 'list'
    archiveFocusSection.value = 'overview'
    archivePage.value = 1

    // 清理随访相关状态
    followupFocusPatientId.value = ''

    // 清理系统中心状态
    systemAudit.value = []
    authz.value = null
    me.value = null

    // 清理表单数据
    patientForm.value = defaultPatientForm()
    eventForm.value = defaultEventForm()

    // 清理导入导出状态
    importingArchive.value = false
    importResultText.value = ''
  }

  function selectSection(nextSection: AppSection) {
    clearMessages()

    if (!canAccessSection(nextSection)) {
      setPermissionError('Current role has no permission to access this module.')
      redirectToHomeSection()
      return
    }

    void navigateToSection(nextSection)
  }

  async function finishLogin(sessionDoctor: DoctorUser) {
    currentDoctor.value = sessionDoctor
    viewedPatientIds.value = []
    clearMessages()
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

    const requestedSection = parseSection(moduleValue)
    if (requestedSection && canAccessSection(requestedSection)) {
      await navigateToSection(requestedSection)
      return
    }

    if (requestedSection && !canAccessSection(requestedSection)) {
      setPermissionError(
        `No access to ${sectionLabel(requestedSection)}. Redirected to ${sectionLabel(defaultSectionForRole(sessionDoctor.role))}.`
      )
    }

    await navigateToSection(defaultSectionForRole(sessionDoctor.role))
  }

  async function submitLogin() {
    loadingLogin.value = true
    loginError.value = ''

    try {
      const session = await loginDoctor(username.value.trim(), password.value)
      await finishLogin(session.doctor)
      logAudit(
        'login',
        { type: 'session', id: session.doctor.username, label: session.doctor.name },
        'success',
        'User login succeeded.',
        {
          username: session.doctor.username,
          name: session.doctor.name,
          role: session.doctor.role,
        }
      )
    } catch (error) {
      loginError.value = error instanceof Error ? error.message : 'Login failed.'
      logAudit(
        'login',
        { type: 'session', id: username.value.trim() || 'unknown' },
        'failed',
        error instanceof Error ? error.message : 'User login failed.',
        {
          username: username.value.trim() || 'unknown',
          name: username.value.trim() || 'Unknown User',
          role: 'unknown',
        }
      )
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
      registerError.value = error instanceof Error ? error.message : 'Register failed.'
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
        title: 'Attending Physician',
        department: 'Chronic Care Clinic',
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
    permissionHint.value = ''
    archiveSuccess.value = ''
    importResultText.value = ''
    workspaceSearchText.value = ''
    workspaceRiskFilter.value = RISK_ALL
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
      setPermissionError('Current role has no permission to run prediction.')
      return
    }

    loadingPredict.value = true
    archiveSuccess.value = ''
    screenError.value = ''

    try {
      predictionResult.value = await predictPatient({
        patientId: selectedPatient.value.patientId,
        asOfTime: selectedPatient.value.lastVisit,
        topk: 3,
      })
      logAudit(
        'trigger_prediction',
        { type: 'patient', id: selectedPatient.value.patientId, label: selectedPatient.value.name },
        predictionResult.value.mode === 'model' ? 'success' : 'degraded',
        `Prediction completed via ${predictionResult.value.mode}/${predictionResult.value.strategy}.`
      )
      logAudit(
        'generate_advice',
        { type: 'patient', id: selectedPatient.value.patientId, label: selectedPatient.value.name },
        predictionResult.value.advice.length ? (predictionResult.value.mode === 'model' ? 'success' : 'degraded') : 'failed',
        `Advice count: ${predictionResult.value.advice.length}.`
      )
      archiveSuccess.value =
        predictionResult.value.mode === 'model'
          ? 'Prediction updated successfully.'
          : 'Model unavailable, prediction fallback applied.'
      await loadOperationalBoards()
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to run prediction.'
      logAudit(
        'trigger_prediction',
        { type: 'patient', id: selectedPatient.value.patientId, label: selectedPatient.value.name },
        'failed',
        error instanceof Error ? error.message : 'Prediction failed.'
      )
      logAudit(
        'generate_advice',
        { type: 'patient', id: selectedPatient.value.patientId, label: selectedPatient.value.name },
        'failed',
        'Advice generation failed because prediction failed.'
      )
    } finally {
      loadingPredict.value = false
    }
  }

  async function runMedicationPlan(patientId: string, payload: MedicationPlanGeneratePayload) {
    if (!patientId) return
    if (!canUseDoctorWorkspace()) {
      setPermissionError('Current role has no permission to generate medication plan.')
      return
    }

    screenError.value = ''
    archiveSuccess.value = ''

    try {
      medicationPlanResult.value = await generateMedicationPlan(patientId, payload)
      archiveSuccess.value = 'Medication plan generated successfully.'
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to generate medication plan.'
    }
  }

  async function submitArchive() {
    if (!canManageArchive()) {
      setPermissionError('Current role has no permission to submit archive.')
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
      archiveSuccess.value = creating ? 'Archive created successfully.' : 'Archive updated successfully.'
      logAudit(
        'modify_archive',
        { type: 'patient_archive', id: saved.patientId, label: saved.name },
        'success',
        creating ? 'Created patient archive.' : 'Updated patient archive.'
      )
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to submit archive.'
      logAudit(
        'modify_archive',
        { type: 'patient_archive', id: selectedPatientId.value || patientForm.value.patientId || 'unknown' },
        'failed',
        error instanceof Error ? error.message : 'Failed to submit archive.'
      )
    } finally {
      savingPatient.value = false
    }
  }

  async function submitEvent() {
    const patientId = selectedPatientId.value || patientForm.value.patientId
    if (!patientId) {
      screenError.value = 'Please select a patient before saving an event.'
      return
    }

    if (!canRecordClinicalEvent()) {
      setPermissionError('Current role has no permission to submit clinical event.')
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
      archiveSuccess.value = 'Clinical event saved successfully.'
      logAudit(
        'modify_archive',
        { type: 'patient_archive', id: updated.patientId, label: updated.name },
        'success',
        'Updated archive timeline with a clinical event.'
      )
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to submit clinical event.'
      logAudit(
        'modify_archive',
        { type: 'patient_archive', id: patientId },
        'failed',
        error instanceof Error ? error.message : 'Failed to update archive timeline.'
      )
    } finally {
      savingEvent.value = false
    }
  }

  async function applyEncounterStatus(patientId: string, status: 'waiting' | 'in_progress' | 'pending_review' | 'completed') {
    if (!patientId) return
    if (!canUseFollowupWorkspace()) {
      setPermissionError('Current role has no permission to update encounter status.')
      return
    }

    loadingEncounterStatus.value = true
    screenError.value = ''
    archiveSuccess.value = ''

    try {
      const updated = await updatePatientEncounterStatus(patientId, { status })
      if (selectedPatientId.value === patientId) {
        selectedPatient.value = updated
        syncPatientForm(updated)
      }
      await loadPatients()
      await loadOperationalBoards()
      archiveSuccess.value = 'Encounter status updated successfully.'
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to update encounter status.'
    } finally {
      loadingEncounterStatus.value = false
    }
  }

  async function submitContactLog(patientId: string, payload: ContactLogCreatePayload) {
    if (!patientId) {
      screenError.value = 'Please select a patient before submitting contact log.'
      return
    }

    if (!canUseFollowupWorkspace()) {
      setPermissionError('Current role has no permission to submit contact log.')
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
      archiveSuccess.value = 'Contact log saved successfully.'
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to submit contact log.'
    } finally {
      savingContactLog.value = false
    }
  }

  async function registerOutpatientTask(patientId: string, item: OutpatientPlanItem) {
    if (!patientId) return
    if (!canUseDoctorWorkspace()) {
      setPermissionError('Current role has no permission to create outpatient task.')
      return
    }

    loadingCreateTask.value = true
    screenError.value = ''
    archiveSuccess.value = ''

    const dueLabel = item.dueLabel
    const followupDays = dueLabel.includes('1-2') ? 10 : dueLabel.includes('1') ? 7 : 0

    try {
      const updated = await createPatientOutpatientTask(patientId, {
        category: item.category,
        title: item.title,
        owner: item.owner,
        dueDate: new Date(Date.now() + followupDays * 86400000).toISOString().slice(0, 10),
        priority: item.priority,
        note: item.note,
        status: TASK_STATUS_PENDING,
        source: 'workspace',
        actorUsername: currentDoctor.value?.username,
        actorName: currentDoctor.value?.name,
      })
      if (selectedPatientId.value === patientId) {
        selectedPatient.value = updated
        syncPatientForm(updated)
      }
      followupFocusPatientId.value = patientId
      await loadPatients()
      await loadOperationalBoards()
      archiveSuccess.value = 'Outpatient task created successfully.'
      logAudit(
        'create_followup_task',
        { type: 'followup_task', id: patientId, label: item.title },
        'success',
        `Created follow-up task: ${item.title}.`
      )
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to create outpatient task.'
      logAudit(
        'create_followup_task',
        { type: 'followup_task', id: patientId, label: item.title },
        'failed',
        error instanceof Error ? error.message : 'Failed to create follow-up task.'
      )
    } finally {
      loadingCreateTask.value = false
    }
  }

  async function changeOutpatientTaskStatus(patientId: string, taskId: string, status: string) {
    if (!patientId || !taskId) return
    if (!canUseFollowupWorkspace()) {
      setPermissionError('Current role has no permission to update outpatient task status.')
      return
    }

    loadingTaskStatus.value = true
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
      followupFocusPatientId.value = patientId
      await loadPatients()
      await loadOperationalBoards()
      archiveSuccess.value = status === TASK_STATUS_COMPLETED ? 'Task marked as completed.' : 'Task marked as closed.'
    } catch (error) {
      screenError.value = error instanceof Error ? error.message : 'Failed to update outpatient task status.'
    } finally {
      loadingTaskStatus.value = false
    }
  }

  async function submitImport(rows: ImportPreviewPatient[]) {
    if (!canManageArchive()) {
      setPermissionError('Current role has no permission to import archive.')
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
            screenError.value = error instanceof Error ? error.message : 'Failed to import one or more rows.'
          }
        }
      }
    }

    importingArchive.value = false
    await refreshWorkspaceData()
    importResultText.value = `Import complete: success ${successCount}, failed ${failedCount}`

    if (successCount > 0) {
      section.value = 'archive'
      archiveMode.value = 'list'
      archiveSuccess.value = 'Archive import finished.'
      updateWindowQuery('archive', 'list')
    }
  }

  function prevArchivePage() {
    archivePage.value = Math.max(1, archivePage.value - 1)
  }

  function nextArchivePage() {
    archivePage.value = Math.min(archiveTotalPages.value, archivePage.value + 1)
  }

  async function initialize() {
    await refreshHealthStatus()
    const restored = restoreAuthSession()
    if (restored) {
      await finishLogin(restored.doctor)
    }
  }

  watch([workspaceSearchText, workspaceRiskFilter], () => {
    showAllPending.value = false
  })

  watch(archiveTotalPages, (value) => {
    if (archivePage.value > value) {
      archivePage.value = value
    }
  })

  return reactive({
    username,
    password,
    loginError,
    loadingLogin,
    currentDoctor,
    health,
    registerMode,
    registerError,
    loadingRegister,
    registerForm,
    section,
    doctorMode,
    archiveMode,
    allPatients,
    followupItems,
    flowBoardItems,
    maintenanceOverview,
    governanceModules,
    modelMetrics,
    me,
    authz,
    systemAudit,
    loadingSystemCenter,
    followupFocusPatientId,
    archiveFocusSection,
    selectedPatientId,
    selectedPatient,
    patientQuadruples,
    predictionResult,
    medicationPlanResult,
    loadingPatients,
    loadingPatient,
    loadingPredict,
    loadingBoards,
    loadingOpenArchive,
    loadingOpenFollowup,
    loadingEncounterStatus,
    loadingCreateTask,
    loadingTaskStatus,
    loadingGovernance,
    loadingMaintenance,
    loadingModelMetrics,
    savingPatient,
    savingEvent,
    savingContactLog,
    importingArchive,
    screenError,
    permissionHint,
    archiveSuccess,
    importResultText,
    patientForm,
    eventForm,
    showAllPending,
    workspaceSearchText,
    workspaceRiskFilter,
    archivePage,
    relationOptions,
    riskOptions,
    visiblePendingPatients,
    hiddenPendingCount,
    recentViewedPatients,
    archiveTotalPages,
    archivePagedPatients,
    appRoleClass,
    globalLoading,
    modelUnavailable,
    doctorNoPermission,
    archiveNoPermission,
    followupNoPermission,
    currentWorkspace,
    initialize,
    submitLogin,
    submitRegister,
    toggleRegister,
    logout,
    selectSection,
    openPatient,
    openArchiveInNewTab,
    openArchiveEventEditor,
    openFollowupModule,
    backToDoctorList,
    backToArchiveList,
    openCreateModule,
    openImportModule,
    handleExportPatients,
    submitArchive,
    submitEvent,
    submitImport,
    runPrediction,
    runMedicationPlan,
    submitContactLog,
    applyEncounterStatus,
    registerOutpatientTask,
    changeOutpatientTaskStatus,
    prevArchivePage,
    nextArchivePage,
    refreshGovernanceWorkspace,
    refreshModelMetrics,
    loadSystemCenter,
    taskStatusCompleted: TASK_STATUS_COMPLETED,
    taskStatusClosed: TASK_STATUS_CLOSED,
  })
}





