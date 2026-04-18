import type { MedicationAdequacyAssessment } from './types'

export function buildUnavailableMedicationAssessment(note: string): MedicationAdequacyAssessment {
  return {
    coversBaselineTherapy: false,
    hasDuplicateMedication: false,
    hasContraindicationConflictPlaceholder: false,
    alignsWithModelAdvice: true,
    needsPharmacistReview: true,
    suggestSupplementClasses: [],
    notes: [note],
    evaluatedAt: new Date().toISOString(),
    evaluator: 'frontend-display-fallback',
    source: 'frontend-fallback',
  }
}
