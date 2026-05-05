from __future__ import annotations

import sys
import os
from pathlib import Path

from fastapi.testclient import TestClient

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("CTPATH_ALLOW_DEMO_FALLBACK", "1")

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
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_system_map_contract() -> None:
    with TestClient(app) as client:
        headers = _login_headers(client)
        response = client.get("/api/systems", headers=headers)

        assert response.status_code == 200, response.text
        payload = response.json()
        names = {item["name"] for item in payload["systems"]}

        assert "医护协同系统" in names
        assert "药房药库系统" in names
        assert "电子病历系统" in names
        assert "病案管理系统" in names
        assert "模型管理系统" in names
        assert all("sections" in item and item["sections"] for item in payload["systems"])


if __name__ == "__main__":
    test_system_map_contract()
    print("system-map-ok")
