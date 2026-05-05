from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from ..schemas import (
    DrugCatalogRecord,
    MedicationAdequacyAssessment,
    PatientCase,
    PatientMedicationRecord,
)


def _normalize(value: str) -> str:
    return value.strip().lower()


def _baseline_by_disease(primary_disease: str) -> List[str]:
    text = _normalize(primary_disease)
    if "diabetes" in text:
        return ["metformin"]
    if "hypertension" in text or "blood pressure" in text or "bp" in text:
        return ["amlodipine", "lisinopril", "losartan"]
    if "lipid" in text or "hyperlip" in text:
        return ["atorvastatin", "rosuvastatin"]
    if "parkinson" in text:
        return ["levodopa"]
    return ["core chronic therapy"]


def _active_medications(medications: List[PatientMedicationRecord]) -> List[PatientMedicationRecord]:
    return [item for item in medications if item.status != "stopped"]


def _medication_text(
    medication: PatientMedicationRecord,
    drug_catalog: List[DrugCatalogRecord],
) -> str:
    drug = next((item for item in drug_catalog if item.drug_id == medication.drug_id), None)
    parts = [
        medication.drug_name_snapshot,
        medication.drug_id,
        medication.dosage,
        medication.frequency,
        medication.route,
        medication.note,
        drug.generic_name if drug else "",
        drug.brand_name if drug else "",
        drug.indication if drug else "",
    ]
    return " ".join(part for part in parts if part).lower()


def has_duplicate_medication(medications: List[PatientMedicationRecord]) -> bool:
    seen = set()
    for item in _active_medications(medications):
        key = _normalize("{0} {1}".format(item.drug_id, item.drug_name_snapshot))
        if not key:
            continue
        if key in seen:
            return True
        seen.add(key)
    return False


def has_controlled_drug_conflict(
    medications: List[PatientMedicationRecord],
    drug_catalog: List[DrugCatalogRecord],
) -> bool:
    controlled_ids = {item.drug_id for item in drug_catalog if item.is_controlled}
    return any(item.drug_id in controlled_ids for item in _active_medications(medications))


def covers_baseline_therapy(
    patient: PatientCase,
    medications: List[PatientMedicationRecord],
    drug_catalog: List[DrugCatalogRecord],
) -> bool:
    keywords = _baseline_by_disease(patient.primaryDisease)
    haystack = " | ".join(_medication_text(item, drug_catalog) for item in _active_medications(medications))
    return any(keyword in haystack for keyword in keywords)


def aligns_with_model_advice(
    medications: List[PatientMedicationRecord],
    model_advice: List[str],
) -> bool:
    advice_text = _normalize(" ".join(model_advice))
    if not advice_text:
        return True
    mentions_medication = any(
        keyword in advice_text
        for keyword in ("medication", "drug", "medicine", "用药", "药物", "药品", "药")
    )
    if mentions_medication:
        return bool(_active_medications(medications))
    return True


def assess_patient_medication_adequacy(
    *,
    patient: PatientCase,
    medications: List[PatientMedicationRecord],
    model_advice: List[str],
    drug_catalog: List[DrugCatalogRecord],
) -> MedicationAdequacyAssessment:
    baseline_keywords = _baseline_by_disease(patient.primaryDisease)
    covers_baseline = covers_baseline_therapy(patient, medications, drug_catalog)
    duplicate = has_duplicate_medication(medications)
    controlled_conflict = has_controlled_drug_conflict(medications, drug_catalog)
    advice_aligned = aligns_with_model_advice(medications, model_advice)

    notes: List[str] = []
    if not covers_baseline:
        notes.append("Baseline therapy coverage is incomplete for the current primary disease.")
    if duplicate:
        notes.append("Duplicate active medication is detected and should be reviewed.")
    if controlled_conflict:
        notes.append("Controlled medication is present and requires pharmacist review.")
    if not advice_aligned:
        notes.append("Model advice mentions medication, but no active medication record is available.")
    if not notes:
        notes.append("Medication rules did not detect duplicate, coverage, review, or advice-alignment risks.")

    return MedicationAdequacyAssessment(
        coversBaselineTherapy=covers_baseline,
        hasDuplicateMedication=duplicate,
        hasContraindicationConflictPlaceholder=controlled_conflict,
        alignsWithModelAdvice=advice_aligned,
        needsPharmacistReview=duplicate or controlled_conflict or not covers_baseline or not advice_aligned,
        suggestSupplementClasses=[] if covers_baseline else ["Consider {0}".format(item) for item in baseline_keywords],
        notes=notes,
        evaluatedAt=datetime.now(timezone.utc).isoformat(),
        evaluator="backend-medication-rule-service",
        source="backend-rule-engine",
    )
