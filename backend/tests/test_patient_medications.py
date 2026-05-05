from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    temp_dir = Path(__file__).resolve().parent / "app" / "runtime" / "patient_medication_test_case"
    temp_dir.mkdir(parents=True, exist_ok=True)
    os.environ["CTPATH_PATIENT_MEDICATION_DIR"] = str(temp_dir)

    from app.store import list_patients
    from app.schemas import PatientMedicationUpsertRequest
    from app.services.patient_medication_service import (
        create_patient_medication,
        get_patient_medication_item,
        list_patient_medications,
        update_patient_medication,
    )

    patients = list_patients()
    assert patients, "at least one patient should exist for medication tests"
    patient_id = str(patients[0]["patientId"])

    seeded = list_patient_medications(patient_id)
    assert all(record.patient_id == patient_id for record in seeded)

    created = create_patient_medication(
        patient_id,
        PatientMedicationUpsertRequest(
            medication_id=f"med-{patient_id.lower()}-test-001",
            patient_id=patient_id,
            drug_id="drug-amlodipine",
            drug_name_snapshot="Amlodipine Besylate (Norvasc)",
            dosage="5 mg",
            frequency="qd",
            route="po",
            start_date="2026-04-18",
            end_date="2026-05-18",
            status="active",
            review_status="pending",
            note="Test medication",
        ),
        prescribed_by="Dr. Lin",
    )
    assert created.medication_id == f"med-{patient_id.lower()}-test-001"

    updated = update_patient_medication(
        patient_id,
        f"med-{patient_id.lower()}-test-001",
        PatientMedicationUpsertRequest(
            medication_id=f"med-{patient_id.lower()}-test-001",
            patient_id=patient_id,
            drug_id="drug-amlodipine",
            drug_name_snapshot="Amlodipine Besylate (Norvasc)",
            dosage="10 mg",
            frequency="qd",
            route="po",
            start_date="2026-04-18",
            end_date="2026-06-18",
            status="paused",
            review_status="approved",
            note="Updated test medication",
        ),
        prescribed_by="Dr. Lin",
    )
    assert updated.dosage == "10 mg"
    assert updated.review_status == "approved"

    item = get_patient_medication_item(patient_id, f"med-{patient_id.lower()}-test-001")
    assert item.status == "paused"
    assert item.review_status == "approved"

    filtered = list_patient_medications(patient_id)
    assert any(record.medication_id == f"med-{patient_id.lower()}-test-001" for record in filtered)

    print("patient-medication-ok")


if __name__ == "__main__":
    main()
