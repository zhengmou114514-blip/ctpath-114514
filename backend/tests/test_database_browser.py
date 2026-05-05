from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("CTPATH_ALLOW_DEMO_FALLBACK", "1")
os.environ.pop("CTPATH_DB_URL", None)

from app.main import app


def _login_headers(client: TestClient, username: str) -> dict[str, str]:
    response = client.post("/api/login", json={"username": username, "password": "demo123456"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_database_browser_is_admin_only() -> None:
    with TestClient(app) as client:
        doctor_headers = _login_headers(client, "demo_clinic")
        response = client.get("/api/database-browser/tables", headers=doctor_headers)

        assert response.status_code == 403


def test_database_browser_reports_demo_mode_without_mysql_url() -> None:
    with TestClient(app) as client:
        admin_headers = _login_headers(client, "demo_admin")
        response = client.get("/api/database-browser/tables", headers=admin_headers)

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["connected"] is False
        assert payload["mode"] == "demo"
        assert any(item["tableName"] == "patients" for item in payload["tables"])


if __name__ == "__main__":
    test_database_browser_is_admin_only()
    test_database_browser_reports_demo_mode_without_mysql_url()
    print("database-browser-ok")
