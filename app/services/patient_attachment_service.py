from __future__ import annotations

import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from ..schemas import PatientAttachmentRecord, PatientAttachmentType


ATTACHMENT_TYPE_LABELS: dict[PatientAttachmentType, str] = {
    "patient_photo": "患者照片",
    "id_card": "身份证照片",
    "insurance_card": "医保卡照片",
    "referral_note": "转诊单",
    "exam_report": "检查报告",
    "informed_consent": "知情同意书",
}

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
}

_LOCK = Lock()


def _storage_root() -> Path:
    root = Path(
        os.getenv(
            "CTPATH_ATTACHMENT_STORAGE_DIR",
            Path(__file__).resolve().parents[1] / "runtime" / "patient_attachments",
        )
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _metadata_path() -> Path:
    return _storage_root() / "metadata.json"


def _patient_dir(patient_id: str) -> Path:
    path = _storage_root() / patient_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_records() -> list[dict[str, Any]]:
    path = _metadata_path()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
    except Exception:
        return []
    return []


def _save_records(records: list[dict[str, Any]]) -> None:
    path = _metadata_path()
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def _is_supported_attachment(file_name: str, mime_type: str) -> bool:
    suffix = Path(file_name).suffix.lower()
    normalized_mime = (mime_type or "").strip().lower()
    if suffix in ALLOWED_EXTENSIONS:
        return True
    if normalized_mime in ALLOWED_MIME_TYPES:
        return True
    guessed = mimetypes.guess_extension(normalized_mime or "")
    return bool(guessed and guessed.lower() in ALLOWED_EXTENSIONS)


def _build_preview_url(patient_id: str, attachment_id: str) -> str:
    return f"/api/patient/{patient_id}/attachments/{attachment_id}/file"


def _to_public_record(record: dict[str, Any]) -> PatientAttachmentRecord:
    payload = dict(record)
    payload["previewUrl"] = _build_preview_url(str(payload["patientId"]), str(payload["attachmentId"]))
    payload.pop("storageFileName", None)
    return PatientAttachmentRecord.model_validate(payload)


def _find_record(patient_id: str, attachment_id: str) -> dict[str, Any] | None:
    for record in _load_records():
        if record.get("patientId") == patient_id and record.get("attachmentId") == attachment_id:
            return record
    return None


def _attachment_path(record: dict[str, Any]) -> Path:
    return _patient_dir(str(record["patientId"])) / str(record["storageFileName"])


def list_patient_attachments(patient_id: str) -> list[PatientAttachmentRecord]:
    if not patient_id:
        return []
    records = [
        _to_public_record(record)
        for record in _load_records()
        if record.get("patientId") == patient_id
    ]
    return sorted(records, key=lambda item: item.uploadedAt, reverse=True)


def get_patient_attachment_file(patient_id: str, attachment_id: str) -> tuple[Path, dict[str, Any]]:
    record = _find_record(patient_id, attachment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    path = _attachment_path(record)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Attachment file missing")

    return path, record


def create_patient_attachment(
    *,
    patient_id: str,
    attachment_type: PatientAttachmentType,
    file_name: str,
    mime_type: str,
    file_bytes: bytes,
    uploaded_by: str,
) -> PatientAttachmentRecord:
    if not patient_id:
        raise HTTPException(status_code=400, detail="Patient ID is required")
    if not file_name:
        raise HTTPException(status_code=400, detail="File name is required")
    if not _is_supported_attachment(file_name, mime_type):
        raise HTTPException(status_code=415, detail="Unsupported file type")

    suffix = Path(file_name).suffix.lower()
    if not suffix:
        guessed = mimetypes.guess_extension((mime_type or "").strip().lower())
        suffix = guessed if guessed else ".bin"

    attachment_id = f"att-{uuid4().hex}"
    stored_file_name = f"{attachment_id}{suffix}"
    storage_path = _patient_dir(patient_id) / stored_file_name
    storage_path.write_bytes(file_bytes)

    now = datetime.now(timezone.utc).isoformat()
    record: dict[str, Any] = {
        "attachmentId": attachment_id,
        "patientId": patient_id,
        "type": attachment_type,
        "typeLabel": ATTACHMENT_TYPE_LABELS[attachment_type],
        "fileName": file_name,
        "mimeType": mime_type or "application/octet-stream",
        "fileSize": len(file_bytes),
        "uploadedAt": now,
        "uploadedBy": uploaded_by.strip() or "当前用户",
        "source": "local-file",
        "storageFileName": stored_file_name,
    }

    with _LOCK:
        records = _load_records()
        records = [item for item in records if item.get("attachmentId") != attachment_id]
        records.append(record)
        _save_records(records)

    return _to_public_record(record)
