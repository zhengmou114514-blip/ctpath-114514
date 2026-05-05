from __future__ import annotations

from typing import Dict

from fastapi.testclient import TestClient

from model_api.main import app


def _login_headers(client: TestClient) -> Dict[str, str]:
    response = client.post(
        "/api/login",
        json={
            "username": "model_admin",
            "password": "model123456",
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_model_health_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["status"] in {"healthy", "degraded", "unavailable"}
        assert payload["mode"] == "model"
        assert "X-Trace-Id" in response.headers
        assert "X-Process-Time-Ms" in response.headers


def test_model_auth_and_training_contract() -> None:
    with TestClient(app) as client:
        unauthorized = client.get("/api/model/datasets")
        assert unauthorized.status_code == 401, unauthorized.text
        unauthorized_payload = unauthorized.json()
        assert unauthorized_payload["error_code"] == "HTTP_401"
        assert unauthorized_payload["trace_id"]
        assert unauthorized.headers["X-Trace-Id"] == unauthorized_payload["trace_id"]

        headers = _login_headers(client)

        import_response = client.post(
            "/api/model/datasets/import",
            headers=headers,
            json={
                "datasetName": "答辩演示训练集",
                "fileName": "demo_dataset.csv",
                "content": "patient_id,label\nP001,high\nP002,low\n",
            },
        )
        assert import_response.status_code == 200, import_response.text
        imported = import_response.json()
        assert imported["datasetName"] == "答辩演示训练集"
        assert imported["rowCount"] == 2

        task_response = client.post(
            "/api/model/training-tasks",
            headers=headers,
            json={
                "datasetId": imported["datasetId"],
                "datasetName": imported["datasetName"],
                "modelName": "CTpath Temporal KG",
                "params": {
                    "epochs": 12,
                    "batchSize": 64,
                    "learningRate": 0.001,
                    "embeddingDim": 128,
                    "optimizer": "adamw",
                },
            },
        )
        assert task_response.status_code == 200, task_response.text
        task = task_response.json()
        assert task["datasetId"] == imported["datasetId"]
        assert task["status"] == "queued"
        assert task["logs"]

        versions_response = client.get("/api/model/model-versions", headers=headers)
        assert versions_response.status_code == 200, versions_response.text
        versions = versions_response.json()["items"]
        assert versions

        deploy_response = client.post(
            f"/api/model/model-versions/{versions[0]['versionId']}/deploy",
            headers=headers,
        )
        assert deploy_response.status_code == 200, deploy_response.text
        deployed = deploy_response.json()
        assert deployed["deployed"] is True

        operations_response = client.get("/api/model/operations", headers=headers)
        assert operations_response.status_code == 200, operations_response.text
        operations = operations_response.json()
        assert operations["loginCount"] >= 1
        assert operations["currentUser"]["username"] == "model_admin"
        assert operations["activityLog"]


def main() -> None:
    test_model_health_contract()
    test_model_auth_and_training_contract()
    print("model-contract-ok")


if __name__ == "__main__":
    main()
