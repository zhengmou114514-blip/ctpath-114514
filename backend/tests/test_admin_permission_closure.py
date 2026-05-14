from __future__ import annotations

from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _login_headers(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/login",
        json={"username": username, "password": "demo123456"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer {0}".format(response.json()["token"])}


def test_admin_drug_permission_change_controls_pharmacist_review(monkeypatch) -> None:
    with TemporaryDirectory() as medication_dir, TemporaryDirectory() as permission_dir:
        monkeypatch.setenv("CTPATH_PATIENT_MEDICATION_DIR", medication_dir)
        monkeypatch.setenv("CTPATH_DRUG_PERMISSION_DIR", permission_dir)

        with TestClient(app) as client:
            admin_headers = _login_headers(client, "demo_admin")
            doctor_headers = _login_headers(client, "demo_clinic")
            pharmacist_headers = _login_headers(client, "demo_pharmacist")

            patients_response = client.get("/api/patients", headers=doctor_headers)
            assert patients_response.status_code == 200, patients_response.text
            patient_id = patients_response.json()[0]["patientId"]

            medication_id = "admin-permission-{0}".format(uuid4().hex[:8])
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
                    "start_date": "2026-05-14",
                    "end_date": "2026-08-14",
                    "status": "active",
                    "review_status": "pending",
                    "note": "权限闭环测试待审核用药",
                },
            )
            assert create_response.status_code == 201, create_response.text

            current_permission = client.get("/api/drug-permissions/pharmacist", headers=admin_headers).json()
            disabled_permission = {**current_permission, "allow_review": False}
            disable_response = client.put(
                "/api/drug-permissions/pharmacist",
                headers=admin_headers,
                json=disabled_permission,
            )
            assert disable_response.status_code == 200, disable_response.text
            assert disable_response.json()["allow_review"] is False

            denied_review = client.patch(
                "/api/pharmacy/review-queue/{0}/{1}".format(patient_id, medication_id),
                headers=pharmacist_headers,
                json={"reviewStatus": "approved", "note": "此时药师复核权限已关闭"},
            )
            assert denied_review.status_code == 403, denied_review.text

            enabled_permission = {**current_permission, "allow_review": True}
            enable_response = client.put(
                "/api/drug-permissions/pharmacist",
                headers=admin_headers,
                json=enabled_permission,
            )
            assert enable_response.status_code == 200, enable_response.text
            assert enable_response.json()["allow_review"] is True

            approved_review = client.patch(
                "/api/pharmacy/review-queue/{0}/{1}".format(patient_id, medication_id),
                headers=pharmacist_headers,
                json={"reviewStatus": "approved", "note": "管理员恢复权限后药师审核通过"},
            )
            assert approved_review.status_code == 200, approved_review.text
            assert approved_review.json()["reviewStatus"] == "approved"

            audit_response = client.get("/api/audit/system?limit=80", headers=admin_headers)
            assert audit_response.status_code == 200, audit_response.text
            audit_items = audit_response.json()["items"]
            assert any(
                item["action"] == "drug_permission_update" and "pharmacist" in item["detail"]
                for item in audit_items
            )


if __name__ == "__main__":
    class _MonkeyPatch:
        def setenv(self, key: str, value: str) -> None:
            import os

            os.environ[key] = value

    test_admin_drug_permission_change_controls_pharmacist_review(_MonkeyPatch())
