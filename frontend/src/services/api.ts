import { requestClient } from './request'
import type {
  AdviceGeneratePayload,
  AdviceGenerateResponse,
  AuthSession,
  AuthzCapabilityResponse,
  BusinessClosureSummary,
  BusinessWorkspaceRole,
  ContactLogCreatePayload,
  DoctorWorkbenchStatusPayload,
  DoctorWorkbenchStatusResponse,
  DrugCatalogRecord,
  DrugCatalogStatus,
  DrugCatalogUpsertRequest,
  DrugPermissionRecord,
  DrugPermissionRole,
  DrugPermissionUpsertRequest,
  EncounterStatusPayload,
  FlowBoardResponse,
  GovernanceModulesResponse,
  FollowupWorklistResponse,
  HealthResponse,
  MaintenanceOverview,
  MeResponse,
  MedicationAdequacyAssessment,
  MedicationAssessmentRequest,
  MedicationPlanGeneratePayload,
  MedicationPlanResponse,
  ModelMetricsResponse,
  CoordinationBoardResponse,
  CoordinationCategory,
  CoordinationItem,
  CoordinationItemUpsertRequest,
  CoordinationNoteCreateRequest,
  CoordinationStatus,
  CoordinationStatusUpdateRequest,
  DatabaseBrowserPreviewResponse,
  DatabaseBrowserTablesResponse,
  OutpatientTaskCreatePayload,
  OutpatientTaskStatusUpdatePayload,
  PatientAttachmentRecord,
  PatientAttachmentType,
  PatientCase,
  PatientEventPayload,
  PatientMedicationRecord,
  PatientMedicationUpsertRequest,
  PatientQuadruple,
  PatientSummary,
  PatientUpsertPayload,
  PharmacyDashboardResponse,
  PharmacyInventoryRecord,
  PharmacyInventoryStatus,
  PharmacyInventoryUpsertRequest,
  PharmacyReviewDecisionRequest,
  PharmacyReviewOrder,
  PharmacyStockAdjustRequest,
  PharmacyTransactionRecord,
  PredictResponse,
  RegisterPayload,
  RoleWorkspaceDefinition,
  SystemMapResponse,
  SystemAuditResponse,
  TimelineEvent,
} from './types'

const API_BASE = '/api'
const AUTH_STORAGE_KEY = 'ctpath.auth.session'
const SAVED_ACCOUNTS_KEY = 'ctpath.saved.accounts'
const MAX_SAVED_ACCOUNTS = 10

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T

function isValidStoredDoctor(value: unknown): value is AuthSession['doctor'] {
  if (!value || typeof value !== 'object') return false
  const doctor = value as Partial<AuthSession['doctor']>
  return (
    typeof doctor.username === 'string' &&
    doctor.username.length > 0 &&
    typeof doctor.name === 'string' &&
    doctor.name.length > 0 &&
    (doctor.role === 'doctor' || doctor.role === 'nurse' || doctor.role === 'pharmacist' || doctor.role === 'archivist' || doctor.role === 'admin')
  )
}

function isValidStoredAuthSession(value: unknown): value is AuthSession {
  if (!value || typeof value !== 'object') return false
  const session = value as Partial<AuthSession>
  return typeof session.token === 'string' && session.token.length > 0 && isValidStoredDoctor(session.doctor)
}

function normalizeApiPath(path: string): string {
  if (!path) return '/'

  let normalized = path
  try {
    const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost'
    const parsed = new URL(path, origin)
    normalized = `${parsed.pathname}${parsed.search}${parsed.hash}`
  } catch {
    normalized = path
  }

  if (normalized === API_BASE) return '/'
  if (normalized.startsWith(`${API_BASE}/`)) {
    normalized = normalized.slice(API_BASE.length)
  } else if (normalized === '/api') {
    normalized = '/'
  } else if (normalized.startsWith('/api/')) {
    normalized = normalized.slice('/api'.length)
  }

  if (!normalized.startsWith('/')) {
    normalized = `/${normalized}`
  }

  return normalized
}

type Role = 'doctor' | 'nurse' | 'pharmacist' | 'archivist' | 'admin'
type Paged = { patients: PatientSummary[]; total: number; page: number; page_size: number; total_pages: number }

export interface SavedAccount { username: string; name: string; title: string; department: string; role: Role; lastLoginTime: string; avatarUrl?: string }
export interface PaginatedPatientsResponse extends Paged {}
export interface PaginationParams { page: number; page_size: number; search?: string; risk_level?: string; sort_by?: string; sort_order?: 'asc' | 'desc' }
export interface PaginationResponse<T> { items: T[]; total: number; page: number; page_size: number; total_pages: number }
export interface PatientStats { total: number; by_risk: Record<string, number>; by_age: Record<string, number> }

const ROLE_WORKSPACES: RoleWorkspaceDefinition[] = [
  {
    role: 'doctor',
    title: '医生工作站',
    description: '负责慢病评估、当前患者复核、诊疗建议和患者级模型洞察；训练中心和模型治理不进入临床主流程。',
    primaryModules: [
      {
        key: 'patient-detail',
        label: '患者详情',
        routeHint: '/patient-detail/:patientId',
        responsibility: '查看患者基本信息、病程时间线、风险摘要、电子档案和下一步处理。',
        status: 'ready',
      },
      {
        key: 'patient-archive',
        label: '患者档案',
        routeHint: '/archive',
        responsibility: '查看患者身份、联系方式、附件和建档信息。',
        status: 'ready',
      },
      {
        key: 'model-insight',
        label: '模型洞察',
        routeHint: '/model-insight',
        responsibility: '仅查看当前患者预测结果、证据摘要和建议来源。',
        status: 'limited',
      },
    ],
    forbiddenModules: ['药房库存操作', '住院全流程', '药品权限配置', '训练中心', '模型调试台'],
    auditFocus: ['患者档案查看', '诊疗建议提交', '模型预测运行', '随访结果复核'],
  },
  {
    role: 'nurse',
    title: '护士工作站',
    description: '负责随访执行、联系闭环、病情流转登记和护理协同。',
    primaryModules: [
      {
        key: 'followup-worklist',
        label: '随访任务',
        routeHint: '/nurse-followups',
        responsibility: '处理到期随访和门诊复查任务，不进入模型治理页面。',
        status: 'ready',
      },
      {
        key: 'flow-board',
        label: '病情流转',
        routeHint: '/nurse-followups',
        responsibility: '登记候诊、接诊中和待复核患者流转状态。',
        status: 'ready',
      },
      {
        key: 'collaboration-handoff',
        label: '协同交接',
        routeHint: '/coordination',
        responsibility: '向医生、药师和档案员同步联系记录与下一步说明。',
        status: 'ready',
      },
    ],
    forbiddenModules: ['管制药授权', '药品目录维护', '临床诊疗决策', '模型看板', '训练中心'],
    auditFocus: ['随访联系记录', '随访任务状态', '患者附件查看'],
  },
  {
    role: 'pharmacist',
    title: '药师工作站',
    description: '负责药房库存、处方/用药复核和药事协同支持。',
    primaryModules: [
      {
        key: 'pharmacy-warehouse',
        label: '药房药库',
        routeHint: '/pharmacy',
        responsibility: '查看库存、出入库记录和发药复核队列。',
        status: 'ready',
      },
      {
        key: 'coordination-support',
        label: '医护协同',
        routeHint: '/coordination',
        responsibility: '支持用药复核和跨角色交接备注。',
        status: 'ready',
      },
      {
        key: 'drug-catalog-reference',
        label: '药品目录',
        routeHint: '/drug-management',
        responsibility: '查看药品通用名、剂型规格和状态。',
        status: 'ready',
      },
    ],
    forbiddenModules: ['患者诊断编辑', '训练中心', '模型看板'],
    auditFocus: ['药房库存调整', '药房复核队列', '协同备注新增'],
  },
  {
    role: 'archivist',
    title: '档案员工作站',
    description: '负责患者身份、附件、建档完整性和数据质量。',
    primaryModules: [
      {
        key: 'patient-archive',
        label: '患者档案',
        routeHint: '/archive',
        responsibility: '维护患者身份、联系方式和建档状态。',
        status: 'ready',
      },
      {
        key: 'attachment-review',
        label: '附件审核',
        routeHint: '/archive?module=attachments',
        responsibility: '审核患者照片、证件、转诊单和知情同意书。',
        status: 'ready',
      },
      {
        key: 'data-quality',
        label: '数据质量',
        routeHint: '/governance',
        responsibility: '处理字段缺失、冲突记录和档案补全待办。',
        status: 'ready',
      },
    ],
    forbiddenModules: ['临床诊疗决策', '训练中心', '模型看板'],
    auditFocus: ['患者附件上传', '档案导入', '档案更新', '质量问题处理'],
  },
  {
    role: 'admin',
    title: '管理员工作站',
    description: '负责业务边界配置、审计复核、权限治理和模型中心访问。',
    primaryModules: [
      {
        key: 'role-boundary',
        label: '角色边界矩阵',
        routeHint: '/role-workspaces',
        responsibility: '查看角色访问边界、协同范围和权限授权。',
        status: 'ready',
      },
      {
        key: 'drug-permissions',
        label: '药品权限管理',
        routeHint: '/drug-permission-management',
        responsibility: '配置角色级用药权限和管制药授权审计。',
        status: 'ready',
      },
      {
        key: 'model-center',
        label: '模型中心',
        routeHint: '/model-dashboard',
        responsibility: '监控模型版本、训练状态和部署健康。',
        status: 'ready',
      },
    ],
    forbiddenModules: ['临床诊疗决策', '护理执行', '药房出入库', '住院全流程'],
    auditFocus: ['药品权限新增', '药品权限更新', '药品目录新增', '药品目录更新', '患者附件上传'],
  },
]

function persistAuthSession(session: AuthSession | null) {
  try {
    if (!window?.localStorage) return
    if (session) {
      window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
    } else {
      window.localStorage.removeItem(AUTH_STORAGE_KEY)
    }
  } catch {
    // ignore local storage errors
  }
}

function buildHeaders(contentType = true): HeadersInit {
  const headers: Record<string, string> = {}
  if (contentType) headers['Content-Type'] = 'application/json'
  return headers
}

function mergeRequestHeaders(contentType: boolean, headers?: HeadersInit): Record<string, string> {
  const merged: Record<string, string> = buildHeaders(contentType) as Record<string, string>
  if (!headers) return merged
  if (headers instanceof Headers) {
    headers.forEach((value, key) => {
      merged[key] = value
    })
    return merged
  }
  if (Array.isArray(headers)) {
    for (const [key, value] of headers) {
      merged[String(key)] = String(value)
    }
    return merged
  }
  return { ...merged, ...headers }
}

function parseResponseData<T>(data: unknown): T {
  if (typeof data !== 'string') return data as T
  if (!data) return undefined as T
  return JSON.parse(data) as T
}

function extractErrorDetail(data: unknown, fallback: string): string {
  if (!data) return fallback
  if (typeof data === 'string') {
    try {
      const parsed = JSON.parse(data) as { detail?: unknown }
      return typeof parsed.detail === 'string' ? parsed.detail : fallback
    } catch {
      return data || fallback
    }
  }
  if (typeof data === 'object' && 'detail' in data) {
    const detail = (data as { detail?: unknown }).detail
    return typeof detail === 'string' ? detail : fallback
  }
  return fallback
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const normalizedPath = normalizeApiPath(path)
  const shouldSetContentType =
    options.body !== undefined &&
    !(options.body instanceof FormData) &&
    !(options.body instanceof URLSearchParams)
  try {
    const response = await requestClient.request({
      url: normalizedPath,
      method: options.method ?? 'GET',
      headers: mergeRequestHeaders(shouldSetContentType, options.headers),
      data: options.body,
    })
    if (response.status < 200 || response.status >= 300) {
      if (response.status === 401) {
        persistAuthSession(null)
      }
      const detail = response.status >= 500 ? '业务服务处理失败，请稍后重试或联系管理员。' : extractErrorDetail(response.data, response.statusText || 'Request failed')
      throw new Error(`[${response.status}] ${detail}`)
    }
    return parseResponseData<T>(response.data)
  } catch (e) {
    const m = e instanceof Error ? e.message : ''
    const isNetworkError = !m || /Network Error|Failed to fetch|NetworkError|Load failed|fetch|ECONNREFUSED|ERR_CONNECTION_REFUSED/i.test(m)
    if (isNetworkError) throw new Error('业务服务连接失败，请检查后端服务或重新登录。')
    throw e
  }
}

export function getSavedAccounts(): SavedAccount[] { try { if (!window?.localStorage) return []; return JSON.parse(window.localStorage.getItem(SAVED_ACCOUNTS_KEY) || '[]') as SavedAccount[] } catch { return [] } }
export function saveAccount(account: SavedAccount): void { try { if (!window?.localStorage) return; const xs = getSavedAccounts().filter((x) => x.username !== account.username); xs.unshift(account); window.localStorage.setItem(SAVED_ACCOUNTS_KEY, JSON.stringify(xs.slice(0, MAX_SAVED_ACCOUNTS))) } catch {} }
export function removeSavedAccount(username: string): void { try { if (!window?.localStorage) return; window.localStorage.setItem(SAVED_ACCOUNTS_KEY, JSON.stringify(getSavedAccounts().filter((x) => x.username !== username))) } catch {} }
export function clearSavedAccounts(): void { try { if (!window?.localStorage) return; window.localStorage.removeItem(SAVED_ACCOUNTS_KEY) } catch {} }
export function restoreAuthSession(): AuthSession | null {
  try {
    if (!window?.localStorage) return null
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as unknown
    if (!isValidStoredAuthSession(parsed)) {
      window.localStorage.removeItem(AUTH_STORAGE_KEY)
      return null
    }
    return parsed
  } catch {
    return null
  }
}
export function getRoleWorkspaces(): RoleWorkspaceDefinition[] { return clone(ROLE_WORKSPACES) }
export function getRoleWorkspace(role: BusinessWorkspaceRole): RoleWorkspaceDefinition {
  const fallback = ROLE_WORKSPACES[0]
  if (!fallback) {
    throw new Error('Role workspace definitions are not configured')
  }
  return clone(ROLE_WORKSPACES.find((item) => item.role === role) ?? fallback)
}

export async function loginDoctor(username: string, password: string): Promise<AuthSession> { const s = await request<AuthSession>('/login', { method: 'POST', body: JSON.stringify({ username, password }) }); persistAuthSession(s); saveAccount({ username: s.doctor.username, name: s.doctor.name, title: s.doctor.title, department: s.doctor.department, role: s.doctor.role, lastLoginTime: new Date().toISOString() }); return s }
export async function registerDoctor(payload: RegisterPayload): Promise<AuthSession> { const s = await request<AuthSession>('/register', { method: 'POST', body: JSON.stringify(payload) }); persistAuthSession(s); return s }
export function logoutDoctor() { persistAuthSession(null) }
export async function getPatients(): Promise<PatientSummary[]> { return request('/patients', { method: 'GET' }) }
export async function getPatientsPaginated(params: { page: number; pageSize: number; search?: string; riskLevel?: string; disease?: string }): Promise<PaginatedPatientsResponse> { const q = new URLSearchParams({ page: String(params.page), page_size: String(params.pageSize) }); if (params.search) q.set('search', params.search); if (params.riskLevel) q.set('risk_level', params.riskLevel); if (params.disease) q.set('disease', params.disease); return request(`/patients/paginated?${q.toString()}`, { method: 'GET' }) }
export async function getPatientCase(patientId: string): Promise<PatientCase> { return request(`/patient/${patientId}`, { method: 'GET' }) }
export async function getTimeline(patientId: string): Promise<TimelineEvent[]> { return (await request<{ patientId: string; items: TimelineEvent[] }>(`/timeline/${patientId}`, { method: 'GET' })).items }
export async function getPatientQuadruples(patientId: string): Promise<PatientQuadruple[]> { return (await request<{ patientId: string; items: PatientQuadruple[] }>(`/patient/${patientId}/quadruples`, { method: 'GET' })).items }
export async function getPatientAttachments(patientId: string): Promise<PatientAttachmentRecord[]> { return request(`/patient/${patientId}/attachments`, { method: 'GET' }) }
export async function uploadPatientAttachment(patientId: string, payload: { type: PatientAttachmentType; file: File }): Promise<PatientAttachmentRecord> {
  const formData = new FormData()
  formData.append('type', payload.type)
  formData.append('file', payload.file)
  return request(`/patient/${patientId}/attachments`, { method: 'POST', body: formData })
}
export async function fetchPatientAttachmentBlob(patientId: string, attachmentId: string): Promise<{ blob: Blob; mimeType: string }> {
  const response = await requestClient.request({
    url: `/patient/${patientId}/attachments/${attachmentId}/file`,
    method: 'GET',
    responseType: 'blob',
    validateStatus: () => true,
  })

  if (response.status !== 200) {
    throw new Error(`[${response.status}] Failed to load attachment preview`)
  }

  const mimeType =
    String(response.headers?.['content-type'] ?? response.headers?.['Content-Type'] ?? (response.data as Blob | undefined)?.type ?? 'application/octet-stream') ||
    'application/octet-stream'

  return { blob: response.data as Blob, mimeType }
}
export async function predictPatient(payload: { patientId: string; asOfTime?: string; topk: number }): Promise<PredictResponse> { return request('/predict', { method: 'POST', body: JSON.stringify(payload) }) }
export async function generateAdvice(payload: AdviceGeneratePayload): Promise<AdviceGenerateResponse> { return request('/advice/generate', { method: 'POST', body: JSON.stringify(payload) }) }
export async function generateMedicationPlan(patientId: string, payload: MedicationPlanGeneratePayload): Promise<MedicationPlanResponse> { return request(`/patient/${patientId}/medication-plan/generate`, { method: 'POST', body: JSON.stringify(payload) }) }
export async function getPatientMedications(patientId: string): Promise<PatientMedicationRecord[]> {
  return request(`/patient/${patientId}/medications`, { method: 'GET' })
}
export async function getPatientMedicationAssessment(patientId: string, payload: MedicationAssessmentRequest): Promise<MedicationAdequacyAssessment> {
  return request(`/patient/${patientId}/medication-assessment`, { method: 'POST', body: JSON.stringify(payload) })
}
export async function createPatientMedication(patientId: string, payload: PatientMedicationUpsertRequest): Promise<PatientMedicationRecord> {
  return request(`/patient/${patientId}/medications`, { method: 'POST', body: JSON.stringify(payload) })
}
export async function updatePatientMedication(patientId: string, medicationId: string, payload: PatientMedicationUpsertRequest): Promise<PatientMedicationRecord> {
  return request(`/patient/${patientId}/medications/${medicationId}`, { method: 'PUT', body: JSON.stringify(payload) })
}
export async function getBusinessClosureSummary(patientId: string, modelAdvice: string[] = []): Promise<BusinessClosureSummary> {
  const [attachments, medications, assessment, permissions, drugs] = await Promise.all([
    getPatientAttachments(patientId),
    getPatientMedications(patientId),
    getPatientMedicationAssessment(patientId, { modelAdvice }),
    getDrugPermissions(),
    getDrugCatalog(),
  ])
  const role = restoreAuthSession()?.doctor.role ?? 'doctor'
  const permission = permissions.find((item) => item.role === role) ?? null
  const drugById = new Map(drugs.map((drug) => [drug.drug_id, drug]))
  const controlledMedicationCount = medications.filter((item) => drugById.get(item.drug_id)?.is_controlled).length
  return {
    patientId,
    attachmentCount: attachments.length,
    currentMedicationCount: medications.length,
    activeMedicationCount: medications.filter((item) => item.status === 'active').length,
    controlledMedicationCount,
    needsPharmacistReview: assessment.needsPharmacistReview,
    medicationAssessment: assessment,
    drugPermission: permission,
  }
}
export async function getDrugCatalog(params: { keyword?: string; status?: DrugCatalogStatus; dosageForm?: string; isPrescription?: boolean; isControlled?: boolean } = {}): Promise<DrugCatalogRecord[]> {
  const query = new URLSearchParams()
  if (params.keyword) query.set('keyword', params.keyword)
  if (params.status) query.set('status', params.status)
  if (params.dosageForm) query.set('dosage_form', params.dosageForm)
  if (params.isPrescription !== undefined) query.set('is_prescription', String(params.isPrescription))
  if (params.isControlled !== undefined) query.set('is_controlled', String(params.isControlled))
  const suffix = query.toString() ? `?${query.toString()}` : ''
  return request(`/drugs${suffix}`, { method: 'GET' })
}
export async function getDrugCatalogItem(drugId: string): Promise<DrugCatalogRecord> { return request(`/drugs/${drugId}`, { method: 'GET' }) }
export async function createDrugCatalogItem(payload: DrugCatalogUpsertRequest): Promise<DrugCatalogRecord> { return request('/drugs', { method: 'POST', body: JSON.stringify(payload) }) }
export async function updateDrugCatalogItem(drugId: string, payload: DrugCatalogUpsertRequest): Promise<DrugCatalogRecord> { return request(`/drugs/${drugId}`, { method: 'PUT', body: JSON.stringify(payload) }) }
export async function getDrugPermissions(role?: DrugPermissionRole): Promise<DrugPermissionRecord[]> {
  const suffix = role ? `?role=${encodeURIComponent(role)}` : ''
  return request(`/drug-permissions${suffix}`, { method: 'GET' })
}
export async function getDrugPermissionItem(role: string): Promise<DrugPermissionRecord> {
  return request(`/drug-permissions/${encodeURIComponent(role)}`, { method: 'GET' })
}
export async function createDrugPermissionItem(payload: DrugPermissionUpsertRequest): Promise<DrugPermissionRecord> {
  return request('/drug-permissions', { method: 'POST', body: JSON.stringify(payload) })
}
export async function updateDrugPermissionItem(role: string, payload: DrugPermissionUpsertRequest): Promise<DrugPermissionRecord> {
  return request(`/drug-permissions/${encodeURIComponent(role)}`, { method: 'PUT', body: JSON.stringify(payload) })
}
export async function healthCheck(): Promise<HealthResponse> { return request('/health', { method: 'GET' }) }
export async function getMe(): Promise<MeResponse> { return request('/me', { method: 'GET' }) }
export async function getAuthzCapabilities(): Promise<AuthzCapabilityResponse> { return request('/authz/capabilities', { method: 'GET' }) }
export async function getSystemMap(): Promise<SystemMapResponse> { return request('/systems', { method: 'GET' }) }
export async function getSystemAudit(limit = 50): Promise<SystemAuditResponse> { return request(`/audit/system?limit=${encodeURIComponent(String(limit))}`, { method: 'GET' }) }
export async function getDatabaseBrowserTables(): Promise<DatabaseBrowserTablesResponse> { return request('/database-browser/tables', { method: 'GET' }) }
export async function getDatabaseBrowserTable(tableName: string, limit = 50): Promise<DatabaseBrowserPreviewResponse> {
  return request(`/database-browser/tables/${encodeURIComponent(tableName)}?limit=${encodeURIComponent(String(limit))}`, { method: 'GET' })
}
export async function getModelMetrics(): Promise<ModelMetricsResponse> { return request('/model/metrics', { method: 'GET' }) }
export async function getMaintenanceOverview(): Promise<MaintenanceOverview> { return request('/maintenance/overview', { method: 'GET' }) }
export async function getGovernanceModules(): Promise<GovernanceModulesResponse> { return request('/governance/modules', { method: 'GET' }) }
export async function getFollowupWorklist(): Promise<FollowupWorklistResponse> { return request('/worklists/followups', { method: 'GET' }) }
export async function getFlowBoard(): Promise<FlowBoardResponse> { return request('/worklists/flow-board', { method: 'GET' }) }
export async function updateDoctorWorkbenchPatientStatus(patientId: string, payload: DoctorWorkbenchStatusPayload): Promise<DoctorWorkbenchStatusResponse> {
  return request(`/worklists/patients/${patientId}/status`, { method: 'PATCH', body: JSON.stringify(payload) })
}
export async function getPharmacyDashboard(): Promise<PharmacyDashboardResponse> { return request('/pharmacy/dashboard', { method: 'GET' }) }
export async function getPharmacyInventory(params: { keyword?: string; warehouse?: string; status?: PharmacyInventoryStatus; lowStockOnly?: boolean } = {}): Promise<PharmacyInventoryRecord[]> {
  const query = new URLSearchParams()
  if (params.keyword) query.set('keyword', params.keyword)
  if (params.warehouse) query.set('warehouse', params.warehouse)
  if (params.status) query.set('status', params.status)
  if (params.lowStockOnly) query.set('low_stock_only', 'true')
  const path = query.toString() ? `/pharmacy/inventory?${query.toString()}` : '/pharmacy/inventory'
  return request(path, { method: 'GET' })
}
export async function getPharmacyInventoryItem(itemId: string): Promise<PharmacyInventoryRecord> { return request(`/pharmacy/inventory/${itemId}`, { method: 'GET' }) }
export async function createPharmacyInventoryItem(payload: PharmacyInventoryUpsertRequest): Promise<PharmacyInventoryRecord> { return request('/pharmacy/inventory', { method: 'POST', body: JSON.stringify(payload) }) }
export async function updatePharmacyInventoryItem(itemId: string, payload: PharmacyInventoryUpsertRequest): Promise<PharmacyInventoryRecord> { return request(`/pharmacy/inventory/${itemId}`, { method: 'PUT', body: JSON.stringify(payload) }) }
export async function adjustPharmacyInventoryItem(itemId: string, payload: PharmacyStockAdjustRequest): Promise<PharmacyInventoryRecord> { return request(`/pharmacy/inventory/${itemId}/adjust`, { method: 'PATCH', body: JSON.stringify(payload) }) }
export async function getPharmacyTransactions(limit = 50): Promise<PharmacyTransactionRecord[]> { return request(`/pharmacy/transactions?limit=${encodeURIComponent(String(limit))}`, { method: 'GET' }) }
export async function getPharmacyReviewQueue(status?: string): Promise<PharmacyReviewOrder[]> {
  const query = new URLSearchParams()
  if (status) query.set('status', status)
  const path = query.toString() ? `/pharmacy/review-queue?${query.toString()}` : '/pharmacy/review-queue'
  return request(path, { method: 'GET' })
}
export async function reviewPharmacyOrder(patientId: string, medicationId: string, payload: PharmacyReviewDecisionRequest): Promise<PharmacyReviewOrder> {
  return request(`/pharmacy/review-queue/${patientId}/${medicationId}`, { method: 'PATCH', body: JSON.stringify(payload) })
}
export async function getCoordinationBoard(params: { status?: CoordinationStatus; category?: CoordinationCategory; keyword?: string } = {}): Promise<CoordinationBoardResponse> {
  const query = new URLSearchParams()
  if (params.status) query.set('status', params.status)
  if (params.category) query.set('category', params.category)
  if (params.keyword) query.set('keyword', params.keyword)
  const path = query.toString() ? `/coordination/board?${query.toString()}` : '/coordination/board'
  return request(path, { method: 'GET' })
}
export async function getCoordinationItems(params: { status?: CoordinationStatus; category?: CoordinationCategory; keyword?: string } = {}): Promise<CoordinationItem[]> {
  const query = new URLSearchParams()
  if (params.status) query.set('status', params.status)
  if (params.category) query.set('category', params.category)
  if (params.keyword) query.set('keyword', params.keyword)
  const path = query.toString() ? `/coordination/items?${query.toString()}` : '/coordination/items'
  return request(path, { method: 'GET' })
}
export async function getCoordinationItem(coordinationId: string): Promise<CoordinationItem> { return request(`/coordination/items/${coordinationId}`, { method: 'GET' }) }
export async function createCoordinationItem(payload: CoordinationItemUpsertRequest): Promise<CoordinationItem> { return request('/coordination/items', { method: 'POST', body: JSON.stringify(payload) }) }
export async function updateCoordinationItem(coordinationId: string, payload: CoordinationItemUpsertRequest): Promise<CoordinationItem> { return request(`/coordination/items/${coordinationId}`, { method: 'PUT', body: JSON.stringify(payload) }) }
export async function updateCoordinationItemStatus(coordinationId: string, payload: CoordinationStatusUpdateRequest): Promise<CoordinationItem> { return request(`/coordination/items/${coordinationId}/status`, { method: 'PATCH', body: JSON.stringify(payload) }) }
export async function appendCoordinationNote(coordinationId: string, payload: CoordinationNoteCreateRequest): Promise<CoordinationItem> { return request(`/coordination/items/${coordinationId}/notes`, { method: 'POST', body: JSON.stringify(payload) }) }
export async function savePatient(payload: PatientUpsertPayload): Promise<PatientCase> { return request('/patient', { method: 'POST', body: JSON.stringify(payload) }) }
export async function updatePatient(patientId: string, payload: PatientUpsertPayload): Promise<PatientCase> { return request(`/patient/${patientId}`, { method: 'PUT', body: JSON.stringify(payload) }) }
export async function addPatientEvent(patientId: string, payload: PatientEventPayload): Promise<PatientCase> { return request(`/patient/${patientId}/event`, { method: 'POST', body: JSON.stringify(payload) }) }
export async function addPatientContactLog(patientId: string, payload: ContactLogCreatePayload): Promise<PatientCase> { return request(`/patient/${patientId}/contact-log`, { method: 'POST', body: JSON.stringify(payload) }) }
export async function updatePatientEncounterStatus(patientId: string, payload: EncounterStatusPayload): Promise<PatientCase> { return request(`/patient/${patientId}/encounter-status`, { method: 'PATCH', body: JSON.stringify(payload) }) }
export async function createPatientOutpatientTask(patientId: string, payload: OutpatientTaskCreatePayload): Promise<PatientCase> { return request(`/patient/${patientId}/outpatient-task`, { method: 'POST', body: JSON.stringify(payload) }) }
export async function updatePatientOutpatientTaskStatus(patientId: string, taskId: string, payload: OutpatientTaskStatusUpdatePayload): Promise<PatientCase> { return request(`/patient/${patientId}/outpatient-task/${taskId}`, { method: 'PATCH', body: JSON.stringify(payload) }) }
export async function getPatientsPaginatedV2(params: PaginationParams): Promise<PaginationResponse<PatientSummary>> { const q = new URLSearchParams({ page: String(params.page), page_size: String(params.page_size) }); if (params.search) q.set('search', params.search); if (params.risk_level) q.set('risk_level', params.risk_level); if (params.sort_by) q.set('sort_by', params.sort_by); if (params.sort_order) q.set('sort_order', params.sort_order); return request(`/v2/patients?${q.toString()}`, { method: 'GET' }) }
export async function getPatientStats(): Promise<PatientStats> { return request('/v2/patients/stats/overview', { method: 'GET' }) }
export async function predictMultiStep(payload: { patientId: string; startTime: string; steps: number; stepDays: number; topk: number }) { const b = await predictPatient({ patientId: payload.patientId, asOfTime: payload.startTime, topk: payload.topk }); return { multiStepPredictions: Array.from({ length: payload.steps }, (_, i) => ({ step: i + 1, daysAhead: (i + 1) * payload.stepDays, timestamp: new Date(new Date(payload.startTime).getTime() + (i + 1) * payload.stepDays * 86400000).toISOString(), mode: b.mode, strategy: b.strategy, predictions: b.topk.map((x, j) => ({ ...x, score: Math.max(0.05, Math.min(0.99, x.score - i * 0.03 + j * 0.01)), confidenceInterval: { lower: Math.max(0, x.score - 0.08), upper: Math.min(1, x.score + 0.08), std: 0.05 }, relativeConfidence: Math.max(0.1, 0.9 - i * 0.05) })), evidence: b.evidence })) } }
