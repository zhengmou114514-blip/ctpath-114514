import type {
  CurrentMedicationInput,
  CurrentMedicationItem,
  MedicationAdequacyAssessment,
  PatientCase,
} from './types'

const MEDICATIONS_STORAGE_KEY = 'ctpath.patient.current_medications'
const AUTH_STORAGE_KEY = 'ctpath.auth.session'

function readAll(): Record<string, CurrentMedicationItem[]> {
  try {
    if (!window?.localStorage) return {}
    return JSON.parse(window.localStorage.getItem(MEDICATIONS_STORAGE_KEY) || '{}') as Record<string, CurrentMedicationItem[]>
  } catch {
    return {}
  }
}

function writeAll(value: Record<string, CurrentMedicationItem[]>) {
  try {
    if (!window?.localStorage) return
    window.localStorage.setItem(MEDICATIONS_STORAGE_KEY, JSON.stringify(value))
  } catch {
    // ignore write errors in local mock mode
  }
}

function getEvaluatorName(): string {
  try {
    const raw = window?.localStorage?.getItem(AUTH_STORAGE_KEY)
    if (!raw) return '当前用户'
    const session = JSON.parse(raw) as { doctor?: { name?: string; username?: string } }
    return session?.doctor?.name || session?.doctor?.username || '当前用户'
  } catch {
    return '当前用户'
  }
}

function toDate(daysFromNow: number) {
  return new Date(Date.now() + daysFromNow * 86400000).toISOString().slice(0, 10)
}

function baselineByDisease(primaryDisease: string): string[] {
  const text = primaryDisease.toLowerCase()
  if (text.includes('diabetes')) return ['metformin', 'sglt2']
  if (text.includes('parkinson')) return ['levodopa']
  if (text.includes('alzheimer')) return ['cholinesterase inhibitor']
  return ['core chronic therapy']
}

function seedMedications(patient: PatientCase): CurrentMedicationItem[] {
  const disease = patient.primaryDisease.toLowerCase()
  if (disease.includes('diabetes')) {
    return [
      {
        medicationId: `med-${patient.patientId}-1`,
        patientId: patient.patientId,
        drugName: '二甲双胍片',
        genericName: 'Metformin',
        dosage: '500 mg',
        frequency: 'bid',
        route: 'po',
        startedAt: toDate(-60),
        expectedEndAt: toDate(30),
        indication: '2型糖尿病基础降糖治疗',
        source: 'mock-local',
      },
    ]
  }

  if (disease.includes('parkinson')) {
    return [
      {
        medicationId: `med-${patient.patientId}-1`,
        patientId: patient.patientId,
        drugName: '左旋多巴/苄丝肼',
        genericName: 'Levodopa/Benserazide',
        dosage: '0.25 g',
        frequency: 'tid',
        route: 'po',
        startedAt: toDate(-90),
        expectedEndAt: toDate(30),
        indication: '帕金森病运动症状控制',
        source: 'mock-local',
      },
    ]
  }

  return []
}

function hasDuplicateMedication(medications: CurrentMedicationItem[]): boolean {
  const seen = new Set<string>()
  for (const item of medications) {
    const key = item.genericName.trim().toLowerCase()
    if (!key) continue
    if (seen.has(key)) return true
    seen.add(key)
  }
  return false
}

function hasConflictPlaceholder(medications: CurrentMedicationItem[]): boolean {
  const names = medications.map((item) => `${item.drugName} ${item.genericName}`.toLowerCase())
  const hasAcei = names.some((x) => x.includes('pril') || x.includes('acei'))
  const hasArb = names.some((x) => x.includes('sartan') || x.includes('arb'))
  return hasAcei && hasArb
}

function includesKeywords(medications: CurrentMedicationItem[], keywords: string[]): boolean {
  const hay = medications.map((item) => `${item.drugName} ${item.genericName} ${item.indication}`.toLowerCase()).join(' | ')
  return keywords.some((word) => hay.includes(word.toLowerCase()))
}

export function getCurrentMedications(patient: PatientCase): CurrentMedicationItem[] {
  const all = readAll()
  const existing = all[patient.patientId]
  if (existing && existing.length) {
    return [...existing].sort((a, b) => b.startedAt.localeCompare(a.startedAt))
  }

  const seeded = seedMedications(patient)
  all[patient.patientId] = seeded
  writeAll(all)
  return [...seeded]
}

export function addCurrentMedication(patientId: string, input: CurrentMedicationInput): CurrentMedicationItem[] {
  const all = readAll()
  const list = all[patientId] ?? []
  const next: CurrentMedicationItem = {
    medicationId: `med-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    patientId,
    ...input,
    source: 'mock-local',
  }

  const updated = [next, ...list]
  all[patientId] = updated
  writeAll(all)
  return [...updated]
}

export function evaluateMedicationAdequacy(
  patient: PatientCase,
  medications: CurrentMedicationItem[],
  modelAdvice: string[]
): MedicationAdequacyAssessment {
  const baseline = baselineByDisease(patient.primaryDisease)
  const coversBaselineTherapy = includesKeywords(medications, baseline)
  const hasDuplicate = hasDuplicateMedication(medications)
  const hasConflict = hasConflictPlaceholder(medications)

  const adviceText = modelAdvice.join(' ').toLowerCase()
  const alignsWithModelAdvice =
    !adviceText ||
    (adviceText.includes('药') || adviceText.includes('medication') ? medications.length > 0 : true)

  const suggestSupplementClasses = coversBaselineTherapy
    ? []
    : baseline.map((item) => `建议补充：${item}`)

  const needsPharmacistReview =
    hasDuplicate || hasConflict || !coversBaselineTherapy || !alignsWithModelAdvice

  const notes: string[] = []
  if (!coversBaselineTherapy) notes.push('基础治疗覆盖不足，请结合指南核对首选药物。')
  if (hasDuplicate) notes.push('检测到疑似重复用药，请复核通用名与适应症。')
  if (hasConflict) notes.push('检测到ACEI/ARB并用提示，仅作冲突占位，请人工判读。')
  if (!alignsWithModelAdvice) notes.push('当前用药与模型建议不一致，建议联合复核。')
  if (needsPharmacistReview) notes.push('建议发起药师复核，确认用药安全性与充分性。')
  if (!notes.length) notes.push('当前评估未发现明显不足，建议继续随访监测。')

  // TODO: replace rule-based mock evaluation with a real medication knowledge-base service.
  return {
    coversBaselineTherapy,
    hasDuplicateMedication: hasDuplicate,
    hasContraindicationConflictPlaceholder: hasConflict,
    alignsWithModelAdvice,
    needsPharmacistReview,
    suggestSupplementClasses,
    notes,
    evaluatedAt: new Date().toISOString(),
    evaluator: getEvaluatorName(),
    source: 'mock-local',
  }
}
