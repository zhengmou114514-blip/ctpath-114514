from __future__ import annotations


def main() -> None:
    from app.schemas import DrugCatalogRecord, PatientCase, PatientMedicationRecord
    from app.services.medication_assessment_service import assess_patient_medication_adequacy

    patient = PatientCase(
        patientId="PID-T1",
        name="Demo Patient",
        age=66,
        gender="Unknown",
        primaryDisease="Diabetes",
        currentStage="Mid",
        riskLevel="High Risk",
        lastVisit="2026-04-19",
        summary="Medication assessment test patient.",
        dataSupport="high",
        stats=[],
        timeline=[],
        predictions=[],
        pathExplanation=[],
        followUps=[],
        recommendationMode="model",
        careAdvice=[],
        similarCases=[],
    )
    drug = DrugCatalogRecord(
        drug_id="drug-metformin",
        generic_name="Metformin Hydrochloride",
        dosage_form="tablet",
        specification="0.5 g",
        unit="box",
        is_prescription=True,
        is_controlled=False,
        status="active",
        indication="Type 2 diabetes mellitus",
        created_at="2026-04-19T00:00:00+00:00",
        updated_at="2026-04-19T00:00:00+00:00",
    )
    medication = PatientMedicationRecord(
        medication_id="med-1",
        patient_id="PID-T1",
        drug_id="drug-metformin",
        drug_name_snapshot="Metformin Hydrochloride",
        dosage="500 mg",
        frequency="bid",
        route="po",
        start_date="2026-04-19",
        end_date="2026-12-31",
        status="active",
        prescribed_by="demo_doctor",
        review_status="approved",
        created_at="2026-04-19T00:00:00+00:00",
        updated_at="2026-04-19T00:00:00+00:00",
    )

    assessment = assess_patient_medication_adequacy(
        patient=patient,
        medications=[medication, medication.copy(update={"medication_id": "med-2"})],
        model_advice=["Continue medication review."],
        drug_catalog=[drug],
    )

    assert assessment.source == "backend-rule-engine"
    assert assessment.coversBaselineTherapy is True
    assert assessment.hasDuplicateMedication is True
    assert assessment.needsPharmacistReview is True

    print("medication-assessment-ok")


if __name__ == "__main__":
    main()
