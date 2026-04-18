from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any, Iterable

from fastapi import HTTPException

from ..schemas import DrugPermissionRecord, DrugPermissionRole, DrugPermissionUpsertRequest


_LOCK = Lock()

DEFAULT_RECORDS: list[dict[str, Any]] = [
    {
        "role": "doctor",
        "allow_view": True,
        "allow_prescribe": True,
        "allow_review": False,
        "allow_execute": False,
        "allow_controlled_drug": True,
    },
    {
        "role": "nurse",
        "allow_view": True,
        "allow_prescribe": False,
        "allow_review": False,
        "allow_execute": True,
        "allow_controlled_drug": False,
    },
    {
        "role": "pharmacist",
        "allow_view": True,
        "allow_prescribe": False,
        "allow_review": True,
        "allow_execute": True,
        "allow_controlled_drug": True,
    },
    {
        "role": "archivist",
        "allow_view": True,
        "allow_prescribe": False,
        "allow_review": False,
        "allow_execute": False,
        "allow_controlled_drug": False,
    },
    {
        "role": "admin",
        "allow_view": True,
        "allow_prescribe": True,
        "allow_review": True,
        "allow_execute": True,
        "allow_controlled_drug": True,
    },
]


def _storage_root() -> Path:
    root = Path(
        os.getenv(
            "CTPATH_DRUG_PERMISSION_DIR",
            Path(__file__).resolve().parents[1] / "runtime" / "drug_permissions",
        )
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _records_path() -> Path:
    return _storage_root() / "permissions.json"


def _default_records() -> list[dict[str, Any]]:
    return [dict(item) for item in DEFAULT_RECORDS]


def _load_records() -> list[dict[str, Any]]:
    path = _records_path()
    if not path.exists():
        return _default_records()

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
    except Exception:
        return _default_records()

    return _default_records()


def _save_records(records: list[dict[str, Any]]) -> None:
    path = _records_path()
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["role"] = str(normalized.get("role") or "").strip()
    normalized["allow_view"] = bool(normalized.get("allow_view", False))
    normalized["allow_prescribe"] = bool(normalized.get("allow_prescribe", False))
    normalized["allow_review"] = bool(normalized.get("allow_review", False))
    normalized["allow_execute"] = bool(normalized.get("allow_execute", False))
    normalized["allow_controlled_drug"] = bool(normalized.get("allow_controlled_drug", False))
    return normalized


def _to_public_record(record: dict[str, Any]) -> DrugPermissionRecord:
    return DrugPermissionRecord.model_validate(_normalize_record(record))


def _find_index(records: list[dict[str, Any]], role: str) -> int:
    target = role.strip()
    for index, record in enumerate(records):
        if str(record.get("role") or "").strip() == target:
            return index
    return -1


def _find_record(records: Iterable[dict[str, Any]], role: str) -> dict[str, Any] | None:
    target = role.strip()
    for record in records:
        if str(record.get("role") or "").strip() == target:
            return record
    return None


def list_drug_permissions(*, role: DrugPermissionRole | None = None) -> list[DrugPermissionRecord]:
    records = [_to_public_record(record) for record in _load_records()]
    if role:
        records = [item for item in records if item.role == role]
    return sorted(records, key=lambda item: item.role)


def get_drug_permission_item(role: str) -> DrugPermissionRecord:
    record = _find_record(_load_records(), role)
    if record is None:
        raise HTTPException(status_code=404, detail="Drug permission not found")
    return _to_public_record(record)


def create_drug_permission_item(payload: DrugPermissionUpsertRequest) -> DrugPermissionRecord:
    role = payload.role.strip()
    if not role:
        raise HTTPException(status_code=400, detail="role is required")

    with _LOCK:
        records = [_normalize_record(record) for record in _load_records()]
        if _find_index(records, role) >= 0:
            raise HTTPException(status_code=409, detail="Drug permission already exists")

        record = {
            "role": role,
            "allow_view": payload.allow_view,
            "allow_prescribe": payload.allow_prescribe,
            "allow_review": payload.allow_review,
            "allow_execute": payload.allow_execute,
            "allow_controlled_drug": payload.allow_controlled_drug,
        }
        records.append(record)
        _save_records(records)
        return _to_public_record(record)


def update_drug_permission_item(role: str, payload: DrugPermissionUpsertRequest) -> DrugPermissionRecord:
    target_role = role.strip()
    if payload.role.strip() != target_role:
        raise HTTPException(status_code=400, detail="role does not match path parameter")

    with _LOCK:
        records = [_normalize_record(record) for record in _load_records()]
        index = _find_index(records, target_role)
        if index < 0:
          # Maintain a minimal create-or-update path for seeded roles.
            raise HTTPException(status_code=404, detail="Drug permission not found")

        updated = {
            "role": target_role,
            "allow_view": payload.allow_view,
            "allow_prescribe": payload.allow_prescribe,
            "allow_review": payload.allow_review,
            "allow_execute": payload.allow_execute,
            "allow_controlled_drug": payload.allow_controlled_drug,
        }
        records[index] = updated
        _save_records(records)
        return _to_public_record(updated)
