from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _login_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/login",
        json={
            "username": "demo_clinic",
            "password": "demo123456",
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_predict_api_contract() -> None:
    with TestClient(app) as client:
        headers = _login_headers(client)

        response = client.post(
            "/api/predict",
            headers=headers,
            json={
                "patientId": "PID0191",
                "topk": 3,
            },
        )

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["patientId"] == "PID0191"
        assert payload["mode"] in {"model", "similar-case"}
        assert payload["strategy"] in {"direct-model", "proxy-model", "rules", "similar-case"}
        assert isinstance(payload["topk"], list) and payload["topk"]
        assert {"label", "score", "reason"} <= set(payload["topk"][0].keys())
        assert isinstance(payload["advice"], list)
        assert isinstance(payload["pathExplanation"], list)
        assert {"eventCount", "timepointCount", "relationCount", "supportLevel"} <= set(payload["evidence"].keys())


def test_middleware_trace_and_auth_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/patients")

        assert response.status_code == 401, response.text
        payload = response.json()
        assert payload["error_code"] == "UNAUTHORIZED"
        assert payload["trace_id"]
        assert response.headers["X-Trace-Id"] == payload["trace_id"]


def test_business_health_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

        assert response.status_code == 200, response.text
        assert "X-Trace-Id" in response.headers
        assert "X-Process-Time-Ms" in response.headers


def test_model_metrics_requires_admin() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/login",
            json={
                "username": "demo_clinic",
                "password": "demo123456",
            },
        )
        assert response.status_code == 200, response.text
        token = response.json()["token"]

        metrics_response = client.get(
            "/api/model/metrics",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert metrics_response.status_code == 403, metrics_response.text
        payload = metrics_response.json()
        assert payload["error_code"] == "FORBIDDEN"
        assert payload["trace_id"]
        assert metrics_response.headers["X-Trace-Id"] == payload["trace_id"]


def main() -> None:
    test_predict_api_contract()
    test_middleware_trace_and_auth_contract()
    test_business_health_contract()
    test_model_metrics_requires_admin()
    print("closure-contract-ok")


if __name__ == "__main__":
    main()
