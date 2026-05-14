from __future__ import annotations

from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _login_headers(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/login",
        json={
            "username": username,
            "password": "demo123456",
        },
    )
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer {0}".format(response.json()["token"])}


def test_doctor_pharmacist_medication_review_closure_contract(monkeypatch) -> None:
    with TemporaryDirectory() as medication_dir:
        monkeypatch.setenv("CTPATH_PATIENT_MEDICATION_DIR", medication_dir)

        with TestClient(app) as client:
            doctor_headers = _login_headers(client, "demo_clinic")
            pharmacist_headers = _login_headers(client, "demo_pharmacist")

            patients_response = client.get("/api/patients", headers=doctor_headers)
            assert patients_response.status_code == 200, patients_response.text
            patient_id = patients_response.json()[0]["patientId"]

            medication_id = "med-review-contract-{0}".format(uuid4().hex[:8])
            create_response = client.post(
                "/api/patient/{0}/medications".format(patient_id),
                headers=doctor_headers,
                json={
                    "medication_id": medication_id,
                    "patient_id": patient_id,
                    "drug_id": "drug-amlodipine",
                    "drug_name_snapshot": "Amlodipine",
                    "dosage": "5 mg",
                    "frequency": "qd",
                    "route": "po",
                    "start_date": "2026-05-12",
                    "end_date": "2026-08-12",
                    "status": "active",
                    "review_status": "pending",
                    "note": "医生提交待药师审核的慢病用药",
                },
            )
            assert create_response.status_code == 201, create_response.text
            assert create_response.json()["review_status"] == "pending"

            queue_response = client.get(
                "/api/pharmacy/review-queue?status=pending",
                headers=pharmacist_headers,
            )
            assert queue_response.status_code == 200, queue_response.text
            assert any(item["medicationId"] == medication_id for item in queue_response.json())

            review_response = client.patch(
                "/api/pharmacy/review-queue/{0}/{1}".format(patient_id, medication_id),
                headers=pharmacist_headers,
                json={
                    "reviewStatus": "approved",
                    "note": "药师审核通过，剂量与频次符合慢病长期用药要求。",
                },
            )
            assert review_response.status_code == 200, review_response.text
            reviewed = review_response.json()
            assert reviewed["reviewStatus"] == "approved"
            review_note = "药师审核通过，剂量与频次符合慢病长期用药要求。"

            doctor_medications_response = client.get(
                "/api/patient/{0}/medications".format(patient_id),
                headers=doctor_headers,
            )
            assert doctor_medications_response.status_code == 200, doctor_medications_response.text
            doctor_record = next(
                item for item in doctor_medications_response.json() if item["medication_id"] == medication_id
            )
            assert doctor_record["review_status"] == "approved"
            assert doctor_record["review_note"] == review_note

            detail_response = client.get("/api/patient/{0}".format(patient_id), headers=doctor_headers)
            assert detail_response.status_code == 200, detail_response.text
            timeline = detail_response.json()["timeline"]
            assert any(
                "medication_review" in "{0} {1}".format(item["title"], item["detail"])
                and "approved" in "{0} {1}".format(item["title"], item["detail"])
                for item in timeline
            )


if __name__ == "__main__":
    class _MonkeyPatch:
        def setenv(self, key: str, value: str) -> None:
            import os

            os.environ[key] = value

    test_doctor_pharmacist_medication_review_closure_contract(_MonkeyPatch())
