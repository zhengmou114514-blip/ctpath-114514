from __future__ import annotations

from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.main import app


def _login_headers(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/login",
        json={"username": username, "password": "demo123456"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer {0}".format(response.json()["token"])}


def test_admin_governance_record_status_change_writes_audit(monkeypatch) -> None:
    with TemporaryDirectory() as governance_dir:
        monkeypatch.setenv("CTPATH_GOVERNANCE_DIR", governance_dir)

        with TestClient(app) as client:
            admin_headers = _login_headers(client, "demo_admin")

            records_response = client.get("/api/governance/records", headers=admin_headers)
            assert records_response.status_code == 200, records_response.text
            records_payload = records_response.json()
            assert records_payload["items"]
            pending_count_before = records_payload["summary"]["pending"]
            target = records_payload["items"][0]

            update_response = client.patch(
                "/api/governance/records/{0}".format(target["recordId"]),
                headers=admin_headers,
                json={
                    "status": "resolved",
                    "handlingNote": "管理员已核对并标记处理完成。",
                },
            )
            assert update_response.status_code == 200, update_response.text
            updated = update_response.json()
            assert updated["status"] == "resolved"
            assert "处理完成" in updated["handlingNote"]

            refreshed_response = client.get("/api/governance/records", headers=admin_headers)
            assert refreshed_response.status_code == 200, refreshed_response.text
            refreshed_payload = refreshed_response.json()
            refreshed_target = next(
                item for item in refreshed_payload["items"] if item["recordId"] == target["recordId"]
            )
            assert refreshed_target["status"] == "resolved"
            assert refreshed_payload["summary"]["pending"] == max(0, pending_count_before - 1)

            audit_response = client.get("/api/audit/system?limit=80", headers=admin_headers)
            assert audit_response.status_code == 200, audit_response.text
            assert any(
                item["action"] == "governance_record_update"
                and target["recordId"] in item["detail"]
                for item in audit_response.json()["items"]
            )


if __name__ == "__main__":
    class _MonkeyPatch:
        def setenv(self, key: str, value: str) -> None:
            import os

            os.environ[key] = value

    test_admin_governance_record_status_change_writes_audit(_MonkeyPatch())
