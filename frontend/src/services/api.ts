import { requestClient } from './request'
import type {
  AdviceGeneratePayload,
  AdviceGenerateResponse,
  AuthSession,
  AuthzCapabilityResponse,
  ContactLogCreatePayload,
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
  MedicationPlanGeneratePayload,
  MedicationPlanResponse,
  ModelMetricsResponse,
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
  PredictResponse,
  RegisterPayload,
  SystemAuditResponse,
  TimelineEvent,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'
const ENABLE_DEMO_FALLBACK = String(import.meta.env.VITE_ENABLE_DEMO_FALLBACK ?? '').toLowerCase() === 'true'
const AUTH_STORAGE_KEY = 'ctpath.auth.session'
const SAVED_ACCOUNTS_KEY = 'ctpath.saved.accounts'
const MAX_SAVED_ACCOUNTS = 10
let authToken = ''

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

type Role = 'doctor' | 'nurse' | 'archivist'
type Paged = { patients: PatientSummary[]; total: number; page: number; page_size: number; total_pages: number }

export interface SavedAccount { username: string; name: string; title: string; department: string; role: Role; lastLoginTime: string; avatarUrl?: string }
export interface PaginatedPatientsResponse extends Paged {}
export interface PaginationParams { page: number; page_size: number; search?: string; risk_level?: string; sort_by?: string; sort_order?: 'asc' | 'desc' }
export interface PaginationResponse<T> { items: T[]; total: number; page: number; page_size: number; total_pages: number }
export interface PatientStats { total: number; by_risk: Record<string, number>; by_age: Record<string, number> }

const doctors = [
  { username: 'demo_clinic', password: 'demo123456', name: 'Dr. Lin', title: 'Attending Physician', department: 'Chronic Care Clinic', role: 'doctor' as Role },
  { username: 'demo_specialist', password: 'demo123456', name: 'Dr. Zhao', title: 'Specialist', department: 'Neurology', role: 'doctor' as Role },
  { username: 'demo_nurse', password: 'demo123456', name: 'Nurse Chen', title: 'Senior Nurse', department: 'Follow-up Center', role: 'nurse' as Role },
  { username: 'demo_archivist', password: 'demo123456', name: 'Wang Min', title: 'Archivist', department: 'Medical Records', role: 'archivist' as Role },
]

const clone = <T>(v: T): T => JSON.parse(JSON.stringify(v)) as T
const token = (u: string) => `demo-${u}-${Date.now()}`
const sum = (p: PatientCase): PatientSummary => ({ patientId: p.patientId, name: p.name, age: p.age, gender: p.gender, avatarUrl: p.avatarUrl, phone: p.phone, emergencyContactName: p.emergencyContactName, emergencyContactRelation: p.emergencyContactRelation, emergencyContactPhone: p.emergencyContactPhone, identityMasked: p.identityMasked, insuranceType: p.insuranceType, department: p.department, primaryDoctor: p.primaryDoctor, caseManager: p.caseManager, medicalRecordNumber: p.medicalRecordNumber, archiveSource: p.archiveSource, archiveStatus: p.archiveStatus, consentStatus: p.consentStatus, allergyHistory: p.allergyHistory, familyHistory: p.familyHistory, primaryDisease: p.primaryDisease, currentStage: p.currentStage, riskLevel: p.riskLevel, lastVisit: p.lastVisit, summary: p.summary, dataSupport: p.dataSupport })
const findPatient = (id: string) => demoPatients.find((p) => p.patientId === id)
const findDrug = (drugId: string) => demoDrugs.find((drug) => drug.drug_id === drugId)
const findDrugPermission = (role: string) => demoDrugPermissions.find((item) => item.role === role)
const normalizeDrugStatus = (status: string | undefined | null): DrugCatalogStatus => (status === 'inactive' ? 'inactive' : 'active')

function mk(id: string, name: string, age: number, disease: string, stage: string, risk: string, lastVisit: string, summary: string, dataSupport: 'high' | 'medium' | 'low', encounterStatus: 'waiting' | 'in_progress' | 'pending_review' | 'completed' = 'waiting'): PatientCase {
  return { patientId: id, name, age, gender: 'Unknown', avatarUrl: `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(name)}`, phone: '', emergencyContactName: '', emergencyContactRelation: '', emergencyContactPhone: '', identityMasked: '3203********1234', insuranceType: 'Urban Employee', department: 'Chronic Care Clinic', primaryDoctor: 'Dr. Lin', caseManager: 'Nurse Chen', medicalRecordNumber: id, archiveSource: 'outpatient', archiveStatus: 'active', consentStatus: 'signed', allergyHistory: 'None', familyHistory: 'No special family history', primaryDisease: disease, currentStage: stage, riskLevel: risk, lastVisit, summary, encounterStatus, stats: [{ label: 'Stage', value: stage, trend: 'Stable' }, { label: 'Risk', value: risk, trend: 'Needs review' }, { label: 'Support', value: dataSupport, trend: 'Demo data' }], timeline: [{ date: lastVisit, type: 'visit', title: 'Latest visit', detail: summary }, { date: lastVisit, type: 'risk', title: 'Risk review', detail: risk }], predictions: [{ label: `${disease} risk watch`, score: risk.toLowerCase().includes('high') ? 0.78 : risk.toLowerCase().includes('medium') ? 0.57 : 0.31, reason: 'Generated by local demo fallback.' }], pathExplanation: [`patient -> has_disease -> ${disease}`, `${disease} -> stage -> ${stage}`, `${stage} -> risk -> ${risk}`], followUps: [{ title: `Review ${disease} plan`, owner: 'Nurse Chen', dueDate: lastVisit, priority: risk.toLowerCase().includes('high') ? 'high' : 'medium' }], outpatientTasks: [], contactLogs: [], auditLogs: [{ logId: `alog-${id}`, action: 'archive_created', operatorUsername: 'demo_archivist', operatorName: 'Wang Min', detail: 'Created by frontend demo fallback.', createdAt: `${lastVisit}T08:00:00` }], recommendationMode: dataSupport === 'low' ? 'similar-case' : 'model', dataSupport, careAdvice: ['Review the latest structured event set.', 'Prioritize the next follow-up action.', 'Collect more data if support is low.'], similarCases: [{ caseId: `SC-${id}`, disease, matchScore: 0.86, summary: 'Similar cases improved with short follow-up intervals.', suggestion: 'Use a short-cycle follow-up plan for the next visit.' }] }
}

let demoPatients: PatientCase[] = [
  mk('PID1001', 'Liu Mei', 68, 'Diabetes', 'Mid', 'High Risk', '2026-04-03', 'Glucose and blood pressure both need follow-up this week.', 'high'),
  mk('PID1002', 'Zhou Jianhua', 72, "Parkinson's", 'Mid', 'High Risk', '2026-04-01', 'Gait fluctuation requires coordinated outpatient follow-up.', 'medium', 'in_progress'),
  mk('PID1003', 'Li Shufen', 79, "Alzheimer's", 'Late', 'High Risk', '2026-03-28', 'Medication review and sleep monitoring are both pending.', 'high', 'pending_review'),
  mk('PID1004', 'Ma Hui', 61, 'Diabetes', 'Early', 'Medium Risk', '2026-03-25', 'Low structured data support limits confidence in prediction.', 'low'),
]

let demoDrugs: DrugCatalogRecord[] = [
  {
    drug_id: 'drug-metformin',
    generic_name: 'Metformin Hydrochloride',
    brand_name: 'Glucophage',
    dosage_form: 'tablet',
    specification: '0.5 g',
    unit: 'box',
    is_prescription: true,
    is_controlled: false,
    status: 'active',
    indication: 'Type 2 diabetes mellitus',
    created_at: '2026-04-18T00:00:00+00:00',
    updated_at: '2026-04-18T00:00:00+00:00',
    updated_by: 'system',
  },
  {
    drug_id: 'drug-amlodipine',
    generic_name: 'Amlodipine Besylate',
    brand_name: 'Norvasc',
    dosage_form: 'tablet',
    specification: '5 mg',
    unit: 'box',
    is_prescription: true,
    is_controlled: false,
    status: 'active',
    indication: 'Hypertension',
    created_at: '2026-04-18T00:00:00+00:00',
    updated_at: '2026-04-18T00:00:00+00:00',
    updated_by: 'system',
  },
  {
    drug_id: 'drug-atorvastatin',
    generic_name: 'Atorvastatin Calcium',
    brand_name: 'Lipitor',
    dosage_form: 'tablet',
    specification: '10 mg',
    unit: 'box',
    is_prescription: true,
    is_controlled: false,
    status: 'active',
    indication: 'Hyperlipidemia',
    created_at: '2026-04-18T00:00:00+00:00',
    updated_at: '2026-04-18T00:00:00+00:00',
    updated_by: 'system',
  },
]

let demoDrugPermissions: DrugPermissionRecord[] = [
  {
    role: 'doctor',
    allow_view: true,
    allow_prescribe: true,
    allow_review: false,
    allow_execute: false,
    allow_controlled_drug: true,
  },
  {
    role: 'nurse',
    allow_view: true,
    allow_prescribe: false,
    allow_review: false,
    allow_execute: true,
    allow_controlled_drug: false,
  },
  {
    role: 'pharmacist',
    allow_view: true,
    allow_prescribe: false,
    allow_review: true,
    allow_execute: true,
    allow_controlled_drug: true,
  },
  {
    role: 'archivist',
    allow_view: true,
    allow_prescribe: false,
    allow_review: false,
    allow_execute: false,
    allow_controlled_drug: false,
  },
  {
    role: 'admin',
    allow_view: true,
    allow_prescribe: true,
    allow_review: true,
    allow_execute: true,
    allow_controlled_drug: true,
  },
]

let demoPatientMedications: PatientMedicationRecord[] = []

const medicationLabel = (drug: DrugCatalogRecord) =>
  [drug.generic_name, drug.brand_name ? `(${drug.brand_name})` : ''].filter(Boolean).join(' ').trim() || drug.drug_id

function resolveSessionRole(): Role {
  try {
    const raw = window?.localStorage?.getItem(AUTH_STORAGE_KEY)
    if (!raw) return 'doctor'
    const session = JSON.parse(raw) as AuthSession
    const role = session?.doctor?.role
    return role === 'doctor' || role === 'nurse' || role === 'archivist' ? role : 'doctor'
  } catch {
    return 'doctor'
  }
}

function resolveSessionDoctorName(): string {
  try {
    const raw = window?.localStorage?.getItem(AUTH_STORAGE_KEY)
    if (!raw) return 'current-user'
    const session = JSON.parse(raw) as AuthSession
    return session?.doctor?.name || session?.doctor?.username || 'current-user'
  } catch {
    return 'current-user'
  }
}

function medicationSeedSpec(patient: PatientCase): Array<{ drugId: string; dosage: string; frequency: string; route: string }> {
  const disease = patient.primaryDisease.toLowerCase()
  if (disease.includes('diabetes')) return [{ drugId: 'drug-metformin', dosage: '500 mg', frequency: 'bid', route: 'po' }]
  if (disease.includes('hypertension') || disease.includes('blood pressure') || disease.includes('bp')) {
    return [{ drugId: 'drug-amlodipine', dosage: '5 mg', frequency: 'qd', route: 'po' }]
  }
  if (disease.includes('lipid') || disease.includes('hyperlip')) {
    return [{ drugId: 'drug-atorvastatin', dosage: '10 mg', frequency: 'qd', route: 'po' }]
  }
  return []
}

function ensureDemoPatientMedications(patientId: string): PatientMedicationRecord[] {
  const existing = demoPatientMedications.filter((item) => item.patient_id === patientId)
  if (existing.length) return existing

  const patient = findPatient(patientId)
  if (!patient) return []

  const now = new Date().toISOString()
  const seeds = medicationSeedSpec(patient)
  if (!seeds.length) return []

  const records = seeds
    .map<PatientMedicationRecord | null>((seed, index) => {
      const drug = findDrug(seed.drugId)
      if (!drug) return null
      return {
        medication_id: `med-${patientId}-${index + 1}`,
        patient_id: patientId,
        drug_id: drug.drug_id,
        drug_name_snapshot: medicationLabel(drug),
        dosage: seed.dosage,
        frequency: seed.frequency,
        route: seed.route,
        start_date: patient.lastVisit,
        end_date: '2026-12-31',
        status: 'active' as const,
        prescribed_by: patient.primaryDoctor || patient.caseManager || 'current-user',
        review_status: 'approved' as const,
        note: `Seeded current medication for ${patient.primaryDisease}.`,
        created_at: now,
        updated_at: now,
      }
    })
    .filter((item): item is PatientMedicationRecord => item !== null)

  demoPatientMedications = [...demoPatientMedications, ...records]
  return records
}

function resolveMedicationPermission(role: string): DrugPermissionRecord | null {
  const record = findDrugPermission(role)
  if (record) return record
  return findDrugPermission('doctor') ?? null
}

function persistAuthSession(session: AuthSession | null) {
  try { if (!window?.localStorage) return; if (session) window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session)); else window.localStorage.removeItem(AUTH_STORAGE_KEY) } catch {}
}

function buildHeaders(contentType = true): HeadersInit {
  const headers: Record<string, string> = {}
  if (contentType) headers['Content-Type'] = 'application/json'
  if (authToken) headers.Authorization = `Bearer ${authToken}`
  return headers
}

const body = <T>(b?: BodyInit | null) => (b ? JSON.parse(String(b)) as T : {} as T)

async function demoRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const m = (options.method ?? 'GET').toUpperCase()
  const u = new URL(path, 'https://demo.local')
  const s = u.pathname.split('/').filter(Boolean)
  if (u.pathname === '/login' && m === 'POST') {
    const p = body<{ username: string; password: string }>(options.body)
    const d = doctors.find((x) => x.username === p.username && x.password === p.password)
    if (!d) throw new Error('Invalid username or password')
    return { token: token(d.username), doctor: { username: d.username, name: d.name, title: d.title, department: d.department, role: d.role } } as T
  }
  if (u.pathname === '/register' && m === 'POST') {
    const p = body<RegisterPayload>(options.body)
    if (doctors.some((x) => x.username === p.username)) throw new Error('Username already exists')
    doctors.push({ ...p })
    return demoRequest<T>('/login', { method: 'POST', body: JSON.stringify({ username: p.username, password: p.password }) })
  }
  if (u.pathname === '/drugs' && m === 'GET') {
    const keyword = (u.searchParams.get('keyword') ?? '').trim().toLowerCase()
    const statusParam = u.searchParams.get('status')
    const status = statusParam === 'active' || statusParam === 'inactive' ? statusParam : null
    const dosageForm = (u.searchParams.get('dosage_form') ?? '').trim().toLowerCase()
    const isPrescriptionParam = u.searchParams.get('is_prescription')
    const isControlledParam = u.searchParams.get('is_controlled')
    const isPrescription = isPrescriptionParam === null ? null : isPrescriptionParam === 'true'
    const isControlled = isControlledParam === null ? null : isControlledParam === 'true'

    const items = demoDrugs.filter((drug) => {
      if (status && drug.status !== status) return false
      if (dosageForm && drug.dosage_form.toLowerCase() !== dosageForm) return false
      if (isPrescription !== null && drug.is_prescription !== isPrescription) return false
      if (isControlled !== null && drug.is_controlled !== isControlled) return false
      if (keyword) {
        const haystack = [
          drug.drug_id,
          drug.generic_name,
          drug.brand_name,
          drug.dosage_form,
          drug.specification,
          drug.unit,
          drug.indication,
        ].join(' ').toLowerCase()
        return haystack.includes(keyword)
      }
      return true
    })

    return items.sort((left, right) => {
      if (left.status !== right.status) return left.status === 'active' ? -1 : 1
      return `${left.generic_name} ${left.drug_id}`.localeCompare(`${right.generic_name} ${right.drug_id}`)
    }) as T
  }
  if (u.pathname.startsWith('/drugs/') && s[1] && s.length === 2 && m === 'GET') {
    const item = findDrug(s[1])
    if (!item) throw new Error('Drug not found')
    return clone(item) as T
  }
  if (u.pathname === '/drugs' && m === 'POST') {
    const payload = body<DrugCatalogUpsertRequest>(options.body)
    if (!payload.drug_id.trim()) throw new Error('drug_id is required')
    if (findDrug(payload.drug_id.trim())) throw new Error('Drug already exists')
    const now = new Date().toISOString()
    const record: DrugCatalogRecord = {
      drug_id: payload.drug_id.trim(),
      generic_name: payload.generic_name.trim(),
      brand_name: payload.brand_name.trim(),
      dosage_form: payload.dosage_form.trim(),
      specification: payload.specification.trim(),
      unit: payload.unit.trim(),
      is_prescription: payload.is_prescription,
      is_controlled: payload.is_controlled,
      status: normalizeDrugStatus(payload.status),
      indication: payload.indication.trim(),
      created_at: now,
      updated_at: now,
      updated_by: 'frontend-demo',
    }
    demoDrugs = [record, ...demoDrugs]
    return clone(record) as T
  }
  if (u.pathname.startsWith('/drugs/') && s[1] && s.length === 2 && m === 'PUT') {
    const payload = body<DrugCatalogUpsertRequest>(options.body)
    const targetId = s[1]
    if (payload.drug_id.trim() !== targetId) throw new Error('drug_id does not match path parameter')
    const index = demoDrugs.findIndex((drug) => drug.drug_id === targetId)
    if (index < 0) throw new Error('Drug not found')
    const current = demoDrugs[index]
    if (!current) throw new Error('Drug not found')
    const updated: DrugCatalogRecord = {
      ...current,
      drug_id: targetId,
      generic_name: payload.generic_name.trim(),
      brand_name: payload.brand_name.trim(),
      dosage_form: payload.dosage_form.trim(),
      specification: payload.specification.trim(),
      unit: payload.unit.trim(),
      is_prescription: payload.is_prescription,
      is_controlled: payload.is_controlled,
      status: normalizeDrugStatus(payload.status),
      indication: payload.indication.trim(),
      updated_at: new Date().toISOString(),
      updated_by: 'frontend-demo',
    }
    demoDrugs = demoDrugs.map((drug, i) => (i === index ? updated : drug))
    return clone(updated) as T
  }
  if (u.pathname === '/drug-permissions' && m === 'GET') {
    const roleFilter = (u.searchParams.get('role') ?? '').trim()
    const items = roleFilter ? demoDrugPermissions.filter((item) => item.role === roleFilter) : demoDrugPermissions
    return clone(items.slice().sort((left, right) => left.role.localeCompare(right.role))) as T
  }
  if (u.pathname.startsWith('/drug-permissions/') && s[1] && s.length === 2 && m === 'GET') {
    const item = findDrugPermission(s[1])
    if (!item) throw new Error('Drug permission not found')
    return clone(item) as T
  }
  if (u.pathname === '/drug-permissions' && m === 'POST') {
    const payload = body<DrugPermissionUpsertRequest>(options.body)
    const role = payload.role.trim()
    if (!role) throw new Error('role is required')
    if (findDrugPermission(role)) throw new Error('Drug permission already exists')
    const record: DrugPermissionRecord = {
      role: role as DrugPermissionRole,
      allow_view: payload.allow_view,
      allow_prescribe: payload.allow_prescribe,
      allow_review: payload.allow_review,
      allow_execute: payload.allow_execute,
      allow_controlled_drug: payload.allow_controlled_drug,
    }
    demoDrugPermissions = [...demoDrugPermissions, record]
    return clone(record) as T
  }
  if (u.pathname.startsWith('/drug-permissions/') && s[1] && s.length === 2 && m === 'PUT') {
    const payload = body<DrugPermissionUpsertRequest>(options.body)
    const targetRole = s[1]
    if (payload.role.trim() !== targetRole) throw new Error('role does not match path parameter')
    const index = demoDrugPermissions.findIndex((item) => item.role === targetRole)
    if (index < 0) throw new Error('Drug permission not found')
    const updated: DrugPermissionRecord = {
      role: targetRole as DrugPermissionRole,
      allow_view: payload.allow_view,
      allow_prescribe: payload.allow_prescribe,
      allow_review: payload.allow_review,
      allow_execute: payload.allow_execute,
      allow_controlled_drug: payload.allow_controlled_drug,
    }
    demoDrugPermissions = demoDrugPermissions.map((item, itemIndex) => (itemIndex === index ? updated : item))
    return clone(updated) as T
  }
  if (s[0] === 'patient' && s[1] && s[2] === 'medications' && !s[3] && m === 'GET') {
    const role = resolveSessionRole()
    const permission = resolveMedicationPermission(role)
    if (!permission?.allow_view) throw new Error('Role not allowed to view patient medications')
    const patient = findPatient(s[1])
    if (!patient) throw new Error('Patient not found')
    const seeded = ensureDemoPatientMedications(s[1])
    return clone(
      seeded
        .filter((item) => item.patient_id === s[1])
        .sort((left, right) => {
          if (left.status !== right.status) return left.status === 'active' ? -1 : 1
          return `${left.start_date} ${left.medication_id}`.localeCompare(`${right.start_date} ${right.medication_id}`)
        })
    ) as T
  }
  if (s[0] === 'patient' && s[1] && s[2] === 'medications' && !s[3] && m === 'POST') {
    const role = resolveSessionRole()
    const permission = resolveMedicationPermission(role)
    if (!permission || (!permission.allow_prescribe && !permission.allow_review)) {
      throw new Error('Role not allowed to modify patient medications')
    }
    const payload = body<PatientMedicationUpsertRequest>(options.body)
    const patient = findPatient(s[1])
    if (!patient) throw new Error('Patient not found')
    const drug = findDrug(payload.drug_id)
    if (!drug) throw new Error('Drug not found')
    if (drug.is_controlled && !permission.allow_controlled_drug) throw new Error('Controlled drug not allowed for this role')
    if (payload.patient_id.trim() !== s[1]) throw new Error('patient_id does not match path parameter')
    if (demoPatientMedications.some((item) => item.patient_id === s[1] && item.medication_id === payload.medication_id.trim())) {
      throw new Error('Patient medication already exists')
    }
    const now = new Date().toISOString()
    const record: PatientMedicationRecord = {
      medication_id: payload.medication_id.trim(),
      patient_id: s[1],
      drug_id: payload.drug_id.trim(),
      drug_name_snapshot: medicationLabel(drug),
      dosage: payload.dosage.trim(),
      frequency: payload.frequency.trim(),
      route: payload.route.trim(),
      start_date: payload.start_date.trim(),
      end_date: payload.end_date.trim(),
      status: payload.status,
      prescribed_by: resolveSessionDoctorName(),
      review_status: payload.review_status,
      note: payload.note.trim(),
      created_at: now,
      updated_at: now,
    }
    demoPatientMedications = [...demoPatientMedications, record]
    return clone(record) as T
  }
  if (s[0] === 'patient' && s[1] && s[2] === 'medications' && s[3] && m === 'PUT') {
    const role = resolveSessionRole()
    const permission = resolveMedicationPermission(role)
    if (!permission || (!permission.allow_prescribe && !permission.allow_review)) {
      throw new Error('Role not allowed to modify patient medications')
    }
    const payload = body<PatientMedicationUpsertRequest>(options.body)
    const patient = findPatient(s[1])
    if (!patient) throw new Error('Patient not found')
    const drug = findDrug(payload.drug_id)
    if (!drug) throw new Error('Drug not found')
    if (drug.is_controlled && !permission.allow_controlled_drug) throw new Error('Controlled drug not allowed for this role')
    if (payload.patient_id.trim() !== s[1]) throw new Error('patient_id does not match path parameter')
    if (payload.medication_id.trim() !== s[3]) throw new Error('medication_id does not match path parameter')
    const index = demoPatientMedications.findIndex((item) => item.patient_id === s[1] && item.medication_id === s[3])
    if (index < 0) throw new Error('Patient medication not found')
    const current = demoPatientMedications[index]
    if (!current) throw new Error('Patient medication not found')
    const updated: PatientMedicationRecord = {
      medication_id: s[3],
      patient_id: s[1],
      drug_id: payload.drug_id.trim(),
      drug_name_snapshot: medicationLabel(drug),
      dosage: payload.dosage.trim(),
      frequency: payload.frequency.trim(),
      route: payload.route.trim(),
      start_date: payload.start_date.trim(),
      end_date: payload.end_date.trim(),
      status: payload.status,
      prescribed_by: resolveSessionDoctorName(),
      review_status: payload.review_status,
      note: payload.note.trim(),
      created_at: current.created_at,
      updated_at: new Date().toISOString(),
    }
    demoPatientMedications = demoPatientMedications.map((item, itemIndex) => (itemIndex === index ? updated : item))
    return clone(updated) as T
  }
  if (u.pathname === '/health') return { status: 'ok', service: 'ctpath-demo-fallback', mode: 'demo', model_available: false, model_error: 'Backend unavailable, using local demo data.' } as T
  if (u.pathname === '/patients') return demoPatients.slice().sort((a, b) => b.lastVisit.localeCompare(a.lastVisit)).map(sum) as T
  if (u.pathname === '/patients/paginated') {
    const page = Number(u.searchParams.get('page') ?? '1'), size = Number(u.searchParams.get('page_size') ?? '20')
    const search = (u.searchParams.get('search') ?? '').toLowerCase(), risk = (u.searchParams.get('risk_level') ?? '').toLowerCase(), disease = (u.searchParams.get('disease') ?? '').toLowerCase()
    let ps = demoPatients.slice().sort((a, b) => b.lastVisit.localeCompare(a.lastVisit)).map(sum)
    if (search) ps = ps.filter((p) => `${p.patientId} ${p.name} ${p.primaryDisease}`.toLowerCase().includes(search))
    if (risk) ps = ps.filter((p) => p.riskLevel.toLowerCase().includes(risk))
    if (disease) ps = ps.filter((p) => p.primaryDisease.toLowerCase().includes(disease))
    const total = ps.length, total_pages = Math.max(1, Math.ceil(total / size)), start = (page - 1) * size
    return { patients: ps.slice(start, start + size), total, page, page_size: size, total_pages } as T
  }
  if (u.pathname === '/v2/patients') {
    const q = `/patients/paginated?page=${u.searchParams.get('page') ?? 1}&page_size=${u.searchParams.get('page_size') ?? 20}&search=${u.searchParams.get('search') ?? ''}&risk_level=${u.searchParams.get('risk_level') ?? ''}`
    const r = await demoRequest<Paged>(q, { method: 'GET' })
    return { items: r.patients, total: r.total, page: r.page, page_size: r.page_size, total_pages: r.total_pages } as T
  }
  if (u.pathname === '/v2/patients/stats/overview') {
    const ps = demoPatients.map(sum)
    const by_risk = ps.reduce<Record<string, number>>((a, p) => ({ ...a, [p.riskLevel]: (a[p.riskLevel] ?? 0) + 1 }), {})
    const by_age = ps.reduce<Record<string, number>>((a, p) => ({ ...a, [p.age < 50 ? '<50' : p.age < 60 ? '50-59' : p.age < 70 ? '60-69' : p.age < 80 ? '70-79' : '80+']: (a[p.age < 50 ? '<50' : p.age < 60 ? '50-59' : p.age < 70 ? '60-69' : p.age < 80 ? '70-79' : '80+'] ?? 0) + 1 }), {})
    return { total: ps.length, by_risk, by_age } as T
  }
  if (s[0] === 'patient' && s[1] && s.length === 2 && m === 'GET') return clone(findPatient(s[1]) ?? (() => { throw new Error('Patient not found') })()) as T
  if (s[0] === 'timeline' && s[1]) return { patientId: s[1], items: clone((findPatient(s[1])?.timeline ?? [])) } as T
  if (s[0] === 'patient' && s[1] && s[2] === 'quadruples') {
    const p = findPatient(s[1]); if (!p) throw new Error('Patient not found')
    return { patientId: p.patientId, items: [{ subject: p.patientId, relation: 'has_disease', relationLabel: 'Disease', objectValue: p.primaryDisease, timestamp: `${p.lastVisit}T09:00:00`, source: 'demo' }, { subject: p.patientId, relation: 'stage', relationLabel: 'Stage', objectValue: p.currentStage, timestamp: `${p.lastVisit}T09:15:00`, source: 'demo' }] } as T
  }
  if (u.pathname === '/predict' && m === 'POST') {
    const p = findPatient(body<{ patientId: string }>(options.body).patientId); if (!p) throw new Error('Patient not found')
    return { patientId: p.patientId, mode: p.recommendationMode, strategy: p.recommendationMode === 'model' ? 'direct-model' : 'similar-case', generatedAt: new Date().toISOString(), supportSummary: `Demo fallback support level: ${p.dataSupport}.`, evidence: { eventCount: p.timeline.length, timepointCount: p.timeline.length, relationCount: 2, supportLevel: p.dataSupport === 'high' ? 'strong' : p.dataSupport === 'medium' ? 'limited' : 'minimal' }, topk: clone(p.predictions), advice: clone(p.careAdvice), adviceMeta: { provider: 'demo-fallback', model: null, source: 'placeholder', configured: false, connected: false, note: 'Prediction is coming from the frontend fallback.' }, pathExplanation: clone(p.pathExplanation), similarCases: clone(p.similarCases) } as T
  }
  if (u.pathname === '/advice/generate' && m === 'POST') {
    const p = body<AdviceGeneratePayload>(options.body)
    return { advice: [`Review ${p.patient.name || p.patient.patientId} in the next follow-up cycle.`, 'Confirm the latest structured event before final decisions.', 'Use short-interval follow-up if risk remains elevated.'], adviceMeta: { provider: 'demo-fallback', model: null, source: 'placeholder', configured: false, connected: false, note: 'Advice generated locally.' } } as T
  }
  if (s[0] === 'patient' && s[1] && s[2] === 'medication-plan' && s[3] === 'generate' && m === 'POST') {
    const p = findPatient(s[1]); if (!p) throw new Error('Patient not found')
    const payload = body<MedicationPlanGeneratePayload>(options.body)
    const meds = (payload.currentMedications ?? []).filter((item) => String(item).trim())
    const plan = meds.length
      ? meds.slice(0, 4).map((item) => ({
        name: item,
        purpose: 'Continue and re-check efficacy in clinic follow-up.',
        dosage: 'Follow latest prescription',
        frequency: 'Follow latest prescription',
        route: 'Oral',
        duration: 'Reassess in 1-2 weeks',
        cautions: ['Check contraindications and adherence before refill.'],
      }))
      : [{
        name: `${p.primaryDisease} medication review`,
        purpose: 'No current medication provided; start from medication reconciliation.',
        dosage: 'To be confirmed by clinician',
        frequency: 'To be confirmed by clinician',
        route: 'To be confirmed by clinician',
        duration: 'Review at next visit',
        cautions: ['AI fallback output for demo only.'],
      }]
    return {
      patientId: p.patientId,
      generatedAt: new Date().toISOString(),
      medications: plan,
      monitoring: ['Review symptom response and adverse effects within 1-2 weeks.'],
      education: ['Do not self-adjust medication without clinician guidance.'],
      disclaimer: 'Demo fallback output only; not a real prescription.',
      adviceMeta: { provider: 'demo-fallback', model: null, source: 'placeholder', configured: false, connected: false, note: 'Medication plan generated locally.' },
    } as T
  }
  if (u.pathname === '/model/metrics') return { dataset: 'DEMO', currentModel: { model: 'CTpath Demo Rules', status: 'done', mrr: 0.61, hits1: 0.42, hits3: 0.58, hits10: 0.74, note: 'Fallback metrics for presentation.' }, comparisons: [{ model: 'TransE', status: 'done', mrr: 0.49, hits1: 0.31, hits3: 0.47, hits10: 0.69, note: 'Demo baseline.' }] } as T
  if (u.pathname === '/governance/modules') return { mode: 'demo', items: [{ moduleKey: 'cis', title: 'Clinical Intake', domain: 'CIS', ownerRole: 'doctor', status: 'healthy', tone: 'healthy', description: 'Patient triage and review are available in demo mode.', capabilities: ['patient triage', 'prediction entry', 'clinical review'] }, { moduleKey: 'archive', title: 'Archive Management', domain: 'MRMS', ownerRole: 'archivist', status: 'warning', tone: 'warning', description: 'Some records still need more structured data.', capabilities: ['archive update', 'event supplement', 'master index'] }] } as T
  if (u.pathname === '/maintenance/overview') {
    const ps = demoPatients.map(sum)
    return { mode: 'demo', modelAvailable: false, modelError: 'Using frontend fallback data.', patientCount: ps.length, eventCount: demoPatients.reduce((n, p) => n + p.timeline.length, 0), highRiskCount: ps.filter((p) => p.riskLevel.toLowerCase().includes('high')).length, lowSupportCount: ps.filter((p) => p.dataSupport === 'low').length, overdueFollowupCount: demoPatients.reduce((n, p) => n + p.followUps.length, 0), missingMrnCount: 0, pendingConsentCount: 0, duplicateRiskCount: 0, topDiseases: [{ label: 'Diabetes', value: ps.filter((p) => p.primaryDisease === 'Diabetes').length }], sourceStats: [{ label: 'Outpatient', value: ps.length }], relationStats: [{ relation: 'has_disease', label: 'Disease', count: ps.length }, { relation: 'stage', label: 'Stage', count: ps.length }], recentPatients: ps.slice(0, 4).map((p) => ({ patientId: p.patientId, name: p.name, primaryDisease: p.primaryDisease, riskLevel: p.riskLevel, dataSupport: p.dataSupport, lastVisit: p.lastVisit })), masterIndexAlerts: ps.filter((p) => p.dataSupport === 'low').map((p) => ({ patientId: p.patientId, name: p.name, issueType: 'data_support', issueLabel: 'Low support', detail: 'More structured data is needed.', archiveSource: p.archiveSource })), recentEvents: demoPatients.flatMap((p) => p.timeline.map((e) => ({ patientId: p.patientId, patientName: p.name, eventTime: `${e.date}T09:00:00`, relation: e.type, relationLabel: e.title, objectValue: e.detail, source: 'demo' }))).slice(0, 8) } as T
  }
  if (u.pathname === '/worklists/followups') {
    return {
      mode: 'demo',
      items: demoPatients.flatMap((p) => {
        const followupRows = p.followUps.map((t, i) => ({
          taskId: `followup-${p.patientId}-${i + 1}`,
          patientId: p.patientId,
          patientName: p.name,
          primaryDisease: p.primaryDisease,
          riskLevel: p.riskLevel,
          dataSupport: p.dataSupport,
          dueDate: t.dueDate,
          owner: t.owner,
          priority: t.priority,
          taskType: t.title,
          status: 'Pending',
          source: 'followup' as const,
          lastActionBy: p.caseManager,
          lastActionAt: `${p.lastVisit}T09:00:00`,
        }))

        const outpatientRows = p.outpatientTasks.map((task) => ({
          taskId: task.taskId,
          patientId: p.patientId,
          patientName: p.name,
          primaryDisease: p.primaryDisease,
          riskLevel: p.riskLevel,
          dataSupport: p.dataSupport,
          dueDate: task.dueDate,
          owner: task.owner,
          priority: task.priority,
          taskType: task.title,
          status: task.status,
          source: 'outpatient-task' as const,
          lastActionBy: task.updatedBy ?? p.caseManager,
          lastActionAt: task.updatedAt ?? `${p.lastVisit}T09:00:00`,
        }))

        return [...followupRows, ...outpatientRows]
      }),
    } as T
  }
  if (u.pathname === '/worklists/flow-board') return { mode: 'demo', items: demoPatients.map((p) => ({ patientId: p.patientId, patientName: p.name, primaryDisease: p.primaryDisease, currentStage: p.currentStage, riskLevel: p.riskLevel, dataSupport: p.dataSupport, lastVisit: p.lastVisit, flowStatus: p.encounterStatus === 'pending_review' ? 'Pending review' : p.encounterStatus === 'in_progress' ? 'In clinic' : p.dataSupport === 'low' ? 'Need structured data' : 'Waiting', nextAction: p.followUps[0]?.title ?? 'Open patient workspace' })) } as T
  if (u.pathname === '/patient' && m === 'POST') {
    const p = body<PatientUpsertPayload>(options.body)
    const next = mk(p.patientId || `PID${1000 + demoPatients.length + 1}`, p.name, Number(p.age), p.primaryDisease, p.currentStage, p.riskLevel, p.lastVisit, p.summary || `${p.primaryDisease} demo archive.`, p.dataSupport)
    demoPatients = [next, ...demoPatients]
    return clone(next) as T
  }
  if (s[0] === 'patient' && s[1] && m === 'PUT') {
    const p = body<PatientUpsertPayload>(options.body), cur = findPatient(s[1]); if (!cur) throw new Error('Patient not found')
    const next = { ...cur, ...p, age: Number(p.age || cur.age), patientId: s[1] }
    demoPatients = demoPatients.map((x) => x.patientId === s[1] ? next : x)
    return clone(next) as T
  }
  if (s[0] === 'patient' && s[1] && s[2] === 'event' && m === 'POST') {
    const p = body<PatientEventPayload>(options.body), cur = findPatient(s[1]); if (!cur) throw new Error('Patient not found')
    const event: TimelineEvent = { date: p.eventTime.slice(0, 10), type: p.relation === 'med_adherence' ? 'medication' : p.relation === 'stage' || p.relation === 'has_disease' ? 'diagnosis' : 'risk', title: p.relation, detail: p.note || p.objectValue }
    const next = { ...cur, timeline: [event, ...cur.timeline], lastVisit: event.date }
    demoPatients = demoPatients.map((x) => x.patientId === s[1] ? next : x)
    return clone(next) as T
  }
  if (s[0] === 'patient' && s[1] && s[2] === 'contact-log' && m === 'POST') {
    const p = body<ContactLogCreatePayload>(options.body), cur = findPatient(s[1]); if (!cur) throw new Error('Patient not found')
    const next = { ...cur, contactLogs: [{ logId: `clog-${Date.now()}`, contactTime: p.contactTime, contactType: p.contactType, contactTarget: p.contactTarget, contactResult: p.contactResult, operatorUsername: p.actorUsername, operatorName: p.actorName, note: p.note || '', nextContactDate: p.nextContactDate }, ...cur.contactLogs] }
    demoPatients = demoPatients.map((x) => x.patientId === s[1] ? next : x)
    return clone(next) as T
  }
  if (s[0] === 'patient' && s[1] && s[2] === 'encounter-status' && m === 'PATCH') {
    const p = body<EncounterStatusPayload>(options.body), cur = findPatient(s[1]); if (!cur) throw new Error('Patient not found')
    const next = { ...cur, encounterStatus: p.status }
    demoPatients = demoPatients.map((x) => x.patientId === s[1] ? next : x)
    return clone(next) as T
  }
  if (s[0] === 'patient' && s[1] && s[2] === 'outpatient-task' && !s[3] && m === 'POST') {
    const p = body<OutpatientTaskCreatePayload>(options.body), cur = findPatient(s[1]); if (!cur) throw new Error('Patient not found')
    const task = { taskId: `task-${Date.now()}`, category: p.category, title: p.title, owner: p.owner, dueDate: p.dueDate, priority: p.priority, status: p.status ?? '待执行', note: p.note, source: p.source ?? 'workspace', updatedBy: p.actorName, updatedAt: new Date().toISOString(), logs: [] }
    const next = { ...cur, outpatientTasks: [task, ...cur.outpatientTasks] }
    demoPatients = demoPatients.map((x) => x.patientId === s[1] ? next : x)
    return clone(next) as T
  }
  if (s[0] === 'patient' && s[1] && s[2] === 'outpatient-task' && s[3] && m === 'PATCH') {
    const p = body<OutpatientTaskStatusUpdatePayload>(options.body), cur = findPatient(s[1]); if (!cur) throw new Error('Patient not found')
    const next = { ...cur, outpatientTasks: cur.outpatientTasks.map((t) => t.taskId === s[3] ? { ...t, status: p.status, updatedBy: p.actorName, updatedAt: new Date().toISOString() } : t) }
    demoPatients = demoPatients.map((x) => x.patientId === s[1] ? next : x)
    return clone(next) as T
  }
  throw new Error(`Demo fallback does not support ${m} ${path}`)
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const normalizedPath = normalizeApiPath(path)
  const shouldSetContentType =
    options.body !== undefined &&
    !(options.body instanceof FormData) &&
    !(options.body instanceof URLSearchParams)
  try {
    const r = await fetch(`${API_BASE}${normalizedPath}`, { ...options, headers: { ...buildHeaders(shouldSetContentType), ...(options.headers ?? {}) } })
    if (!r.ok) {
      if (ENABLE_DEMO_FALLBACK && r.status >= 500) return demoRequest<T>(normalizedPath, options)
      if (r.status === 401) {
        authToken = ''
        persistAuthSession(null)
      }
      let detail = 'Request failed'
      try { detail = (await r.json()).detail ?? detail } catch { detail = r.statusText || detail }
      throw new Error(`[${r.status}] ${detail}`)
    }
    return r.json() as Promise<T>
  } catch (e) {
    const m = e instanceof Error ? e.message : ''
    const isNetworkError = !m || /Failed to fetch|NetworkError|Load failed|fetch|ECONNREFUSED|ERR_CONNECTION_REFUSED/i.test(m)
    if (ENABLE_DEMO_FALLBACK && isNetworkError) return demoRequest<T>(normalizedPath, options)
    if (isNetworkError) throw new Error(`Cannot connect to backend API (${API_BASE}). Please start backend service.`)
    throw e
  }
}

export function getSavedAccounts(): SavedAccount[] { try { if (!window?.localStorage) return []; return JSON.parse(window.localStorage.getItem(SAVED_ACCOUNTS_KEY) || '[]') as SavedAccount[] } catch { return [] } }
export function saveAccount(account: SavedAccount): void { try { if (!window?.localStorage) return; const xs = getSavedAccounts().filter((x) => x.username !== account.username); xs.unshift(account); window.localStorage.setItem(SAVED_ACCOUNTS_KEY, JSON.stringify(xs.slice(0, MAX_SAVED_ACCOUNTS))) } catch {} }
export function removeSavedAccount(username: string): void { try { if (!window?.localStorage) return; window.localStorage.setItem(SAVED_ACCOUNTS_KEY, JSON.stringify(getSavedAccounts().filter((x) => x.username !== username))) } catch {} }
export function clearSavedAccounts(): void { try { if (!window?.localStorage) return; window.localStorage.removeItem(SAVED_ACCOUNTS_KEY) } catch {} }
export function restoreAuthSession(): AuthSession | null { try { if (!window?.localStorage) return null; const raw = window.localStorage.getItem(AUTH_STORAGE_KEY); if (!raw) return null; const s = JSON.parse(raw) as AuthSession; authToken = s.token; return s } catch { authToken = ''; return null } }

export async function loginDoctor(username: string, password: string): Promise<AuthSession> { const s = await request<AuthSession>('/login', { method: 'POST', body: JSON.stringify({ username, password }) }); authToken = s.token; persistAuthSession(s); saveAccount({ username: s.doctor.username, name: s.doctor.name, title: s.doctor.title, department: s.doctor.department, role: s.doctor.role, lastLoginTime: new Date().toISOString() }); return s }
export async function registerDoctor(payload: RegisterPayload): Promise<AuthSession> { const s = await request<AuthSession>('/register', { method: 'POST', body: JSON.stringify(payload) }); authToken = s.token; persistAuthSession(s); return s }
export function logoutDoctor() { authToken = ''; persistAuthSession(null) }
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
export async function createPatientMedication(patientId: string, payload: PatientMedicationUpsertRequest): Promise<PatientMedicationRecord> {
  return request(`/patient/${patientId}/medications`, { method: 'POST', body: JSON.stringify(payload) })
}
export async function updatePatientMedication(patientId: string, medicationId: string, payload: PatientMedicationUpsertRequest): Promise<PatientMedicationRecord> {
  return request(`/patient/${patientId}/medications/${medicationId}`, { method: 'PUT', body: JSON.stringify(payload) })
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
export async function getSystemAudit(limit = 50): Promise<SystemAuditResponse> { return request(`/audit/system?limit=${encodeURIComponent(String(limit))}`, { method: 'GET' }) }
export async function getModelMetrics(): Promise<ModelMetricsResponse> { return request('/model/metrics', { method: 'GET' }) }
export async function getMaintenanceOverview(): Promise<MaintenanceOverview> { return request('/maintenance/overview', { method: 'GET' }) }
export async function getGovernanceModules(): Promise<GovernanceModulesResponse> { return request('/governance/modules', { method: 'GET' }) }
export async function getFollowupWorklist(): Promise<FollowupWorklistResponse> { return request('/worklists/followups', { method: 'GET' }) }
export async function getFlowBoard(): Promise<FlowBoardResponse> { return request('/worklists/flow-board', { method: 'GET' }) }
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
