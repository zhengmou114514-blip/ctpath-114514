from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Iterable

from fastapi import HTTPException

from ..schemas import DrugCatalogRecord, DrugCatalogStatus, DrugCatalogUpsertRequest


_LOCK = Lock()
DEFAULT_TIMESTAMP = "2026-04-18T00:00:00+00:00"

DEFAULT_DRUGS: list[dict[str, Any]] = [
    {
        "drug_id": "drug-metformin",
        "generic_name": "二甲双胍片",
        "brand_name": "格华止",
        "dosage_form": "片剂",
        "specification": "0.5 g",
        "unit": "盒",
        "is_prescription": True,
        "is_controlled": False,
        "status": "active",
        "indication": "2型糖尿病基础降糖治疗",
        "created_at": DEFAULT_TIMESTAMP,
        "updated_at": DEFAULT_TIMESTAMP,
        "updated_by": "system",
    },
    {
        "drug_id": "drug-amlodipine",
        "generic_name": "苯磺酸氨氯地平片",
        "brand_name": "络活喜",
        "dosage_form": "片剂",
        "specification": "5 mg",
        "unit": "盒",
        "is_prescription": True,
        "is_controlled": False,
        "status": "active",
        "indication": "高血压长期控制",
        "created_at": DEFAULT_TIMESTAMP,
        "updated_at": DEFAULT_TIMESTAMP,
        "updated_by": "system",
    },
    {
        "drug_id": "drug-atorvastatin",
        "generic_name": "阿托伐他汀钙片",
        "brand_name": "立普妥",
        "dosage_form": "片剂",
        "specification": "10 mg",
        "unit": "盒",
        "is_prescription": True,
        "is_controlled": False,
        "status": "active",
        "indication": "高脂血症与动脉粥样硬化危险因素控制",
        "created_at": DEFAULT_TIMESTAMP,
        "updated_at": DEFAULT_TIMESTAMP,
        "updated_by": "system",
    },
    {
        "drug_id": "drug-insulin-glargine",
        "generic_name": "甘精胰岛素注射液",
        "brand_name": "来得时",
        "dosage_form": "注射剂",
        "specification": "3 ml: 300 IU",
        "unit": "支",
        "is_prescription": True,
        "is_controlled": False,
        "status": "active",
        "indication": "需要基础胰岛素控制的糖尿病患者",
        "created_at": DEFAULT_TIMESTAMP,
        "updated_at": DEFAULT_TIMESTAMP,
        "updated_by": "system",
    },
    {
        "drug_id": "drug-clopidogrel",
        "generic_name": "硫酸氢氯吡格雷片",
        "brand_name": "波立维",
        "dosage_form": "片剂",
        "specification": "75 mg",
        "unit": "盒",
        "is_prescription": True,
        "is_controlled": False,
        "status": "active",
        "indication": "冠心病与脑卒中二级预防",
        "created_at": DEFAULT_TIMESTAMP,
        "updated_at": DEFAULT_TIMESTAMP,
        "updated_by": "system",
    },
    {
        "drug_id": "drug-levodopa",
        "generic_name": "左旋多巴苄丝肼片",
        "brand_name": "美多芭",
        "dosage_form": "片剂",
        "specification": "0.25 g",
        "unit": "盒",
        "is_prescription": True,
        "is_controlled": False,
        "status": "active",
        "indication": "帕金森病运动症状控制",
        "created_at": DEFAULT_TIMESTAMP,
        "updated_at": DEFAULT_TIMESTAMP,
        "updated_by": "system",
    },
    {
        "drug_id": "drug-donepezil",
        "generic_name": "盐酸多奈哌齐片",
        "brand_name": "安理申",
        "dosage_form": "片剂",
        "specification": "5 mg",
        "unit": "盒",
        "is_prescription": True,
        "is_controlled": False,
        "status": "inactive",
        "indication": "阿尔茨海默病认知症状改善",
        "created_at": DEFAULT_TIMESTAMP,
        "updated_at": DEFAULT_TIMESTAMP,
        "updated_by": "system",
    },
    {
        "drug_id": "drug-pregabalin",
        "generic_name": "普瑞巴林胶囊",
        "brand_name": "乐瑞卡",
        "dosage_form": "胶囊剂",
        "specification": "75 mg",
        "unit": "盒",
        "is_prescription": True,
        "is_controlled": True,
        "status": "active",
        "indication": "神经病理性疼痛与慢病并发症相关疼痛管理",
        "created_at": DEFAULT_TIMESTAMP,
        "updated_at": DEFAULT_TIMESTAMP,
        "updated_by": "system",
    },
]


def _storage_root() -> Path:
    root = Path(
        os.getenv(
            "CTPATH_DRUG_CATALOG_DIR",
            Path(__file__).resolve().parents[1] / "runtime" / "drug_catalog",
        )
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _records_path() -> Path:
    return _storage_root() / "drugs.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_records() -> list[dict[str, Any]]:
    return [dict(item) for item in DEFAULT_DRUGS]


def _load_records() -> list[dict[str, Any]]:
    path = _records_path()
    if not path.exists():
        return _default_records()

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            records = [item for item in payload if isinstance(item, dict)]
            if records:
                existing_ids = {str(item.get("drug_id") or "").strip() for item in records}
                for seed in _default_records():
                    if seed["drug_id"] not in existing_ids:
                        records.append(seed)
                return records
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
    normalized["drug_id"] = str(normalized.get("drug_id") or "").strip()
    normalized["generic_name"] = str(normalized.get("generic_name") or "").strip()
    normalized["brand_name"] = str(normalized.get("brand_name") or "").strip()
    normalized["dosage_form"] = str(normalized.get("dosage_form") or "").strip()
    normalized["specification"] = str(normalized.get("specification") or "").strip()
    normalized["unit"] = str(normalized.get("unit") or "").strip()
    normalized["is_prescription"] = bool(normalized.get("is_prescription", True))
    normalized["is_controlled"] = bool(normalized.get("is_controlled", False))
    normalized["status"] = str(normalized.get("status") or "active").strip() or "active"
    normalized["indication"] = str(normalized.get("indication") or "").strip()
    normalized["created_at"] = str(normalized.get("created_at") or DEFAULT_TIMESTAMP)
    normalized["updated_at"] = str(normalized.get("updated_at") or normalized["created_at"])
    normalized["updated_by"] = str(normalized.get("updated_by") or "").strip()
    return normalized


def _to_public_record(record: dict[str, Any]) -> DrugCatalogRecord:
    return DrugCatalogRecord.model_validate(_normalize_record(record))


def _find_index(records: list[dict[str, Any]], drug_id: str) -> int:
    target = drug_id.strip()
    for index, record in enumerate(records):
        if str(record.get("drug_id") or "").strip() == target:
            return index
    return -1


def _find_record(records: Iterable[dict[str, Any]], drug_id: str) -> dict[str, Any] | None:
    target = drug_id.strip()
    for record in records:
        if str(record.get("drug_id") or "").strip() == target:
            return record
    return None


def list_drug_catalog(
    *,
    keyword: str | None = None,
    status: DrugCatalogStatus | None = None,
    dosage_form: str | None = None,
    is_prescription: bool | None = None,
    is_controlled: bool | None = None,
) -> list[DrugCatalogRecord]:
    records = [_to_public_record(record) for record in _load_records()]
    keyword_value = (keyword or "").strip().lower()
    dosage_form_value = (dosage_form or "").strip().lower()

    def matches(item: DrugCatalogRecord) -> bool:
        if status and item.status != status:
            return False
        if dosage_form_value and item.dosage_form.lower() != dosage_form_value:
            return False
        if is_prescription is not None and item.is_prescription != is_prescription:
            return False
        if is_controlled is not None and item.is_controlled != is_controlled:
            return False
        if keyword_value:
            haystack = " ".join(
                [
                    item.drug_id,
                    item.generic_name,
                    item.brand_name,
                    item.dosage_form,
                    item.specification,
                    item.unit,
                    item.indication,
                ]
            ).lower()
            return keyword_value in haystack
        return True

    filtered = [item for item in records if matches(item)]
    return sorted(filtered, key=lambda item: (item.status != "active", item.generic_name.lower(), item.drug_id.lower()))


def get_drug_catalog_item(drug_id: str) -> DrugCatalogRecord:
    record = _find_record(_load_records(), drug_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Drug not found")
    return _to_public_record(record)


def create_drug_catalog_item(payload: DrugCatalogUpsertRequest, *, updated_by: str) -> DrugCatalogRecord:
    drug_id = payload.drug_id.strip()
    if not drug_id:
        raise HTTPException(status_code=400, detail="drug_id is required")

    with _LOCK:
        records = [_normalize_record(record) for record in _load_records()]
        if _find_index(records, drug_id) >= 0:
            raise HTTPException(status_code=409, detail="Drug already exists")

        now = _now()
        record = {
            "drug_id": drug_id,
            "generic_name": payload.generic_name.strip(),
            "brand_name": payload.brand_name.strip(),
            "dosage_form": payload.dosage_form.strip(),
            "specification": payload.specification.strip(),
            "unit": payload.unit.strip(),
            "is_prescription": payload.is_prescription,
            "is_controlled": payload.is_controlled,
            "status": payload.status,
            "indication": payload.indication.strip(),
            "created_at": now,
            "updated_at": now,
            "updated_by": updated_by.strip() or "system",
        }
        records.append(record)
        _save_records(records)
        return _to_public_record(record)


def update_drug_catalog_item(
    drug_id: str,
    payload: DrugCatalogUpsertRequest,
    *,
    updated_by: str,
) -> DrugCatalogRecord:
    target_id = drug_id.strip()
    if payload.drug_id.strip() != target_id:
        raise HTTPException(status_code=400, detail="drug_id does not match path parameter")

    with _LOCK:
        records = [_normalize_record(record) for record in _load_records()]
        index = _find_index(records, target_id)
        if index < 0:
            raise HTTPException(status_code=404, detail="Drug not found")

        current = records[index]
        now = _now()
        updated = {
            **current,
            "drug_id": target_id,
            "generic_name": payload.generic_name.strip(),
            "brand_name": payload.brand_name.strip(),
            "dosage_form": payload.dosage_form.strip(),
            "specification": payload.specification.strip(),
            "unit": payload.unit.strip(),
            "is_prescription": payload.is_prescription,
            "is_controlled": payload.is_controlled,
            "status": payload.status,
            "indication": payload.indication.strip(),
            "updated_at": now,
            "updated_by": updated_by.strip() or "system",
        }
        records[index] = updated
        _save_records(records)
        return _to_public_record(updated)
