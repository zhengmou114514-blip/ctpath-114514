from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

import app.dataset_loader as dataset_loader
from app.main import app


def _login_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/login",
        json={
            "username": "demo_clinic",
            "password": "demo123456",
        },
    )
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _storage_dir() -> Path:
    repo_tmp_root = Path(__file__).resolve().parent / "_tmp"
    repo_tmp_root.mkdir(parents=True, exist_ok=True)
    storage_dir = repo_tmp_root / f"attachments-{uuid4().hex}"
    storage_dir.mkdir(parents=True, exist_ok=False)
    return storage_dir


def test_patient_attachments_upload_list_and_preview() -> None:
    dataset_loader.init_dataset = lambda: {}
    os.environ["CTPATH_ATTACHMENT_STORAGE_DIR"] = str(_storage_dir())

    with TestClient(app) as client:
        headers = _login_headers(client)

        upload = client.post(
            "/api/patient/PID0025/attachments",
            headers=headers,
            data={"type": "patient_photo"},
            files={"file": ("photo.png", b"\x89PNG\r\n\x1a\nmock-png-data", "image/png")},
        )

        assert upload.status_code == 200, upload.text
        record = upload.json()
        assert record["patientId"] == "PID0025"
        assert record["type"] == "patient_photo"
        assert record["typeLabel"]
        assert record["uploadedBy"]
        assert record["previewUrl"].endswith(f"/api/patient/PID0025/attachments/{record['attachmentId']}/file")

        listing = client.get("/api/patient/PID0025/attachments", headers=headers)
        assert listing.status_code == 200, listing.text
        assert len(listing.json()) == 1
        assert listing.json()[0]["attachmentId"] == record["attachmentId"]

        preview = client.get(record["previewUrl"], headers=headers)
        assert preview.status_code == 200, preview.text
        assert preview.headers["content-type"].startswith("image/png")


def test_patient_attachment_rejects_unsupported_file_type() -> None:
    dataset_loader.init_dataset = lambda: {}
    os.environ["CTPATH_ATTACHMENT_STORAGE_DIR"] = str(_storage_dir())

    with TestClient(app) as client:
        headers = _login_headers(client)

        response = client.post(
            "/api/patient/PID0025/attachments",
            headers=headers,
            data={"type": "id_card"},
            files={"file": ("note.txt", b"plain-text", "text/plain")},
        )

        assert response.status_code == 415, response.text


def main() -> None:
    test_patient_attachments_upload_list_and_preview()
    test_patient_attachment_rejects_unsupported_file_type()
    print("attachment-flow-ok")


if __name__ == "__main__":
    main()
