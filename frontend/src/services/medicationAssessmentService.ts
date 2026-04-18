import type { DrugCatalogRecord, MedicationAdequacyAssessment, PatientCase, PatientMedicationRecord } from './types'

function normalize(text: string): string {
  return text.trim().toLowerCase()
}

function baselineByDisease(primaryDisease: string): string[] {
  const text = normalize(primaryDisease)
  if (text.includes('diabetes')) return ['metformin']
  if (text.includes('hypertension') || text.includes('blood pressure') || text.includes('bp')) {
    return ['amlodipine', 'lisinopril', 'losartan']
  }
  if (text.includes('lipid') || text.includes('hyperlip')) return ['atorvastatin', 'rosuvastatin']
  if (text.includes('parkinson')) return ['levodopa']
  return ['core chronic therapy']
}

function medicationText(medication: PatientMedicationRecord, drugCatalog?: DrugCatalogRecord[]): string {
  const drug = drugCatalog?.find((item) => item.drug_id === medication.drug_id)
  return [
    medication.drug_name_snapshot,
    medication.drug_id,
    medication.dosage,
    medication.frequency,
    medication.route,
    medication.note,
    drug?.generic_name,
    drug?.brand_name,
    drug?.indication,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

export function hasDuplicateMedication(medications: PatientMedicationRecord[]): boolean {
  const active = medications.filter((item) => item.status !== 'stopped')
  const seen = new Set<string>()
  for (const item of active) {
    const key = normalize(`${item.drug_id} ${item.drug_name_snapshot}`)
    if (!key) continue
    if (seen.has(key)) return true
    seen.add(key)
  }
  return false
}

export function hasControlledDrugConflict(
  medications: PatientMedicationRecord[],
  drugCatalog: DrugCatalogRecord[] = []
): boolean {
  const controlledIds = new Set(drugCatalog.filter((item) => item.is_controlled).map((item) => item.drug_id))
  return medications.some((item) => item.status !== 'stopped' && controlledIds.has(item.drug_id))
}

export function coversBaselineTherapy(
  patient: PatientCase,
  medications: PatientMedicationRecord[],
  drugCatalog: DrugCatalogRecord[] = []
): boolean {
  const keywords = baselineByDisease(patient.primaryDisease)
  const haystack = medications.map((item) => medicationText(item, drugCatalog)).join(' | ')
  return keywords.some((keyword) => haystack.includes(keyword))
}

export function alignsWithModelAdvice(
  medications: PatientMedicationRecord[],
  modelAdvice: string[]
): boolean {
  const adviceText = normalize(modelAdvice.join(' '))
  if (!adviceText) return true
  if (
    adviceText.includes('medication') ||
    adviceText.includes('drug') ||
    adviceText.includes('用药') ||
    adviceText.includes('药')
  ) {
    return medications.length > 0
  }
  return true
}

export function evaluateMedicationAdequacy(
  patient: PatientCase,
  medications: PatientMedicationRecord[],
  modelAdvice: string[],
  drugCatalog: DrugCatalogRecord[] = []
): MedicationAdequacyAssessment {
  const baseline = baselineByDisease(patient.primaryDisease)
  const coversBaseline = coversBaselineTherapy(patient, medications, drugCatalog)
  const duplicate = hasDuplicateMedication(medications)
  const conflict = hasControlledDrugConflict(medications, drugCatalog)
  const adviceAligned = alignsWithModelAdvice(medications, modelAdvice)

  const notes: string[] = []
  if (!coversBaseline) {
    notes.push('基础治疗覆盖不足，请结合病种与目录核对首选用药。')
  }
  if (duplicate) {
    notes.push('检测到重复用药提示，请核对通用名和现用状态。')
  }
  if (conflict) {
    notes.push('检测到管制药占位冲突或高风险药物提示，请人工复核。')
  }
  if (!adviceAligned) {
    notes.push('当前用药与模型建议不一致，建议联合复核。')
  }
  if (!notes.length) {
    notes.push('当前评估未发现明显用药不足，建议继续随访监测。')
  }

  return {
    coversBaselineTherapy: coversBaseline,
    hasDuplicateMedication: duplicate,
    hasContraindicationConflictPlaceholder: conflict,
    alignsWithModelAdvice: adviceAligned,
    needsPharmacistReview: duplicate || conflict || !coversBaseline || !adviceAligned,
    suggestSupplementClasses: coversBaseline ? [] : baseline.map((item) => `建议补充：${item}`),
    notes,
    evaluatedAt: new Date().toISOString(),
    evaluator: 'frontend-rule-engine',
    source: 'mock-local',
  }
}
