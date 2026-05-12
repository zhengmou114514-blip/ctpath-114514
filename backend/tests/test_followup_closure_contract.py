from __future__ import annotations

from datetime import datetime, timezone
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


def test_doctor_nurse_followup_closure_contract() -> None:
    with TestClient(app) as client:
        doctor_headers = _login_headers(client, "demo_clinic")
        nurse_headers = _login_headers(client, "demo_nurse")

        patients_response = client.get("/api/patients", headers=doctor_headers)
        assert patients_response.status_code == 200, patients_response.text
        patient_id = patients_response.json()[0]["patientId"]

        title = "随访闭环合同测试-{0}".format(uuid4().hex[:8])
        create_response = client.post(
            "/api/worklists/followups",
            headers=doctor_headers,
            json={
                "patientId": patient_id,
                "title": title,
                "owner": "随访护士",
                "dueDate": "2026-05-20",
                "priority": "high",
                "note": "医生从患者详情发起随访任务",
            },
        )
        assert create_response.status_code == 200, create_response.text
        created_task = create_response.json()
        task_id = created_task["taskId"]
        assert created_task["status"] == "pending"
        assert created_task["patientId"] == patient_id

        nurse_worklist_response = client.get("/api/worklists/followups", headers=nurse_headers)
        assert nurse_worklist_response.status_code == 200, nurse_worklist_response.text
        nurse_items = nurse_worklist_response.json()["items"]
        assert any(item["taskId"] == task_id and item["status"] == "pending" for item in nurse_items)

        patch_response = client.patch(
            "/api/worklists/followups/{0}".format(task_id),
            headers=nurse_headers,
            json={
                "status": "not_reached",
                "note": "首次电话未接通",
            },
        )
        assert patch_response.status_code == 200, patch_response.text
        assert patch_response.json()["status"] == "not_reached"

        contact_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        contact_response = client.post(
            "/api/patient/{0}/contact-logs".format(patient_id),
            headers=nurse_headers,
            json={
                "contactTime": contact_time,
                "contactType": "phone",
                "contactTarget": "patient",
                "contactResult": "missed",
                "note": "随访闭环测试：电话未接通，已计划再次联系",
                "nextContactDate": "2026-05-21",
            },
        )
        assert contact_response.status_code == 200, contact_response.text

        detail_response = client.get("/api/patients/{0}".format(patient_id), headers=doctor_headers)
        assert detail_response.status_code == 200, detail_response.text
        patient_detail = detail_response.json()

        latest_followup = patient_detail["latest_followup"]
        assert latest_followup["taskId"] == task_id
        assert latest_followup["status"] == "not_reached"

        recent_contact_logs = patient_detail["recent_contact_logs"]
        assert recent_contact_logs
        assert recent_contact_logs[0]["contactResult"] == "missed"
        assert "随访闭环测试" in recent_contact_logs[0]["note"]

        task_detail = next(item for item in patient_detail["outpatientTasks"] if item["taskId"] == task_id)
        assert task_detail["logs"]
        assert any(log["action"] == "status_updated" for log in task_detail["logs"])

        audit_response = client.get("/api/audit/patient/{0}".format(patient_id), headers=doctor_headers)
        assert audit_response.status_code == 200, audit_response.text
        audit_actions = {item["action"] for item in audit_response.json()}
        assert "followup_task_created" in audit_actions
        assert "followup_task_status_updated" in audit_actions
        assert "contact_log_created" in audit_actions


if __name__ == "__main__":
    test_doctor_nurse_followup_closure_contract()
