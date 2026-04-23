from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Iterable

from fastapi import HTTPException

from ..schemas import (
    PharmacyDashboardResponse,
    PharmacyInventoryRecord,
    PharmacyInventoryStatus,
    PharmacyInventoryUpsertRequest,
    PharmacyReviewOrder,
    PharmacyStockAdjustRequest,
    PharmacySummaryItem,
    PharmacyTransactionRecord,
    PatientMedicationRecord,
    PatientMedicationReviewStatus,
    PatientMedicationStatus,
    PatientMedicationUpsertRequest,
)
from .drug_catalog_service import list_drug_catalog
from .patient_medication_service import get_patient_medication_item, list_patient_medications, update_patient_medication
from ..store import get_patient, list_patients


_LOCK = Lock()
DEFAULT_TIMESTAMP = "2026-04-18T00:00:00+00:00"


def _storage_root() -> Path:
    root = Path(
        os.getenv(
            "CTPATH_PHARMACY_DIR",
            Path(__file__).resolve().parents[1] / "runtime" / "pharmacy",
        )
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _inventory_path() -> Path:
    return _storage_root() / "inventory.json"


def _transactions_path() -> Path:
    return _storage_root() / "transactions.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path, default: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not path.exists():
        return [dict(item) for item in default]
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
    except Exception:
        return [dict(item) for item in default]
    return [dict(item) for item in default]


def _save_json(path: Path, records: list[dict[str, Any]]) -> None:
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def _default_inventory_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, drug in enumerate(list_drug_catalog(status="active")):
        base_stock = max(24, 120 - index * 14)
        controlled_bonus = 18 if drug.is_controlled else 0
        records.append(
            {
                "itemId": f"stock-{drug.drug_id}",
                "drugId": drug.drug_id,
                "drugName": " ".join(
                    part for part in [drug.generic_name.strip(), f"({drug.brand_name.strip()})" if drug.brand_name.strip() else ""] if part
                ),
                "warehouse": "主药房",
                "batchNo": f"BATCH-{index + 1:03d}",
                "lotNo": f"LOT-{202604 + index}",
                "unit": drug.unit,
                "currentStock": base_stock + controlled_bonus,
                "reservedStock": 4 if drug.is_controlled else 2,
                "minStock": 28 if drug.is_controlled else 18,
                "expiryDate": "2027-12-31" if index % 2 == 0 else "2027-06-30",
                "status": "active",
                "supplier": "慢病药品配送中心",
                "lastInboundAt": DEFAULT_TIMESTAMP,
                "lastOutboundAt": DEFAULT_TIMESTAMP,
                "updatedBy": "system",
                "updatedAt": DEFAULT_TIMESTAMP,
            }
        )
    return records


def _normalize_inventory_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["itemId"] = str(normalized.get("itemId") or "").strip()
    normalized["drugId"] = str(normalized.get("drugId") or "").strip()
    normalized["drugName"] = str(normalized.get("drugName") or "").strip()
    normalized["warehouse"] = str(normalized.get("warehouse") or "").strip()
    normalized["batchNo"] = str(normalized.get("batchNo") or "").strip()
    normalized["lotNo"] = str(normalized.get("lotNo") or "").strip()
    normalized["unit"] = str(normalized.get("unit") or "").strip()
    normalized["currentStock"] = max(0, int(normalized.get("currentStock") or 0))
    normalized["reservedStock"] = max(0, int(normalized.get("reservedStock") or 0))
    normalized["minStock"] = max(0, int(normalized.get("minStock") or 0))
    normalized["expiryDate"] = str(normalized.get("expiryDate") or "").strip()
    normalized["status"] = str(normalized.get("status") or "active").strip() or "active"
    normalized["supplier"] = str(normalized.get("supplier") or "").strip()
    normalized["lastInboundAt"] = str(normalized.get("lastInboundAt") or DEFAULT_TIMESTAMP)
    normalized["lastOutboundAt"] = str(normalized.get("lastOutboundAt") or DEFAULT_TIMESTAMP)
    normalized["updatedBy"] = str(normalized.get("updatedBy") or "").strip()
    normalized["updatedAt"] = str(normalized.get("updatedAt") or normalized["lastInboundAt"])
    return normalized


def _normalize_transaction_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["transactionId"] = str(normalized.get("transactionId") or "").strip()
    normalized["itemId"] = str(normalized.get("itemId") or "").strip()
    normalized["drugId"] = str(normalized.get("drugId") or "").strip()
    normalized["change"] = int(normalized.get("change") or 0)
    normalized["direction"] = str(normalized.get("direction") or "adjust").strip()
    normalized["note"] = str(normalized.get("note") or "").strip()
    normalized["operatorUsername"] = str(normalized.get("operatorUsername") or "").strip() or None
    normalized["operatorName"] = str(normalized.get("operatorName") or "").strip() or None
    normalized["createdAt"] = str(normalized.get("createdAt") or DEFAULT_TIMESTAMP)
    return normalized


def _inventory_model(record: dict[str, Any]) -> PharmacyInventoryRecord:
    return PharmacyInventoryRecord.model_validate(_normalize_inventory_record(record))


def _transaction_model(record: dict[str, Any]) -> PharmacyTransactionRecord:
    return PharmacyTransactionRecord.model_validate(_normalize_transaction_record(record))


def _load_inventory_records() -> list[dict[str, Any]]:
    records = _load_json(_inventory_path(), _default_inventory_records())
    return [_normalize_inventory_record(record) for record in records] or _default_inventory_records()


def _load_transactions() -> list[dict[str, Any]]:
    records = _load_json(_transactions_path(), [])
    return [_normalize_transaction_record(record) for record in records]


def _save_inventory_records(records: list[dict[str, Any]]) -> None:
    _save_json(_inventory_path(), records)


def _save_transactions(records: list[dict[str, Any]]) -> None:
    _save_json(_transactions_path(), records)


def _find_inventory_index(records: list[dict[str, Any]], item_id: str) -> int:
    target = item_id.strip()
    for index, record in enumerate(records):
        if str(record.get("itemId") or "").strip() == target:
            return index
    return -1


def _find_inventory_record(records: Iterable[dict[str, Any]], item_id: str) -> dict[str, Any] | None:
    target = item_id.strip()
    for record in records:
        if str(record.get("itemId") or "").strip() == target:
            return record
    return None


def _make_transaction(
    *,
    item_id: str,
    drug_id: str,
    change: int,
    direction: str,
    note: str,
    operator_username: str | None,
    operator_name: str | None,
) -> dict[str, Any]:
    return {
        "transactionId": f"tx-{datetime.now(timezone.utc).timestamp():.0f}-{item_id}",
        "itemId": item_id,
        "drugId": drug_id,
        "change": change,
        "direction": direction,
        "note": note,
        "operatorUsername": operator_username,
        "operatorName": operator_name,
        "createdAt": _now(),
    }


def _sync_status(stock: int, min_stock: int, expiry_date: str) -> PharmacyInventoryStatus:
    if stock <= 0:
        return "out_of_stock"
    try:
        expiry = datetime.fromisoformat(expiry_date[:10])
        if expiry.date() < datetime.now(timezone.utc).date():
            return "expired"
    except Exception:
        pass
    if stock <= min_stock:
        return "low"
    return "active"


def list_pharmacy_inventory(
    *,
    keyword: str | None = None,
    warehouse: str | None = None,
    status: PharmacyInventoryStatus | None = None,
    low_stock_only: bool = False,
) -> list[PharmacyInventoryRecord]:
    keyword_value = (keyword or "").strip().lower()
    warehouse_value = (warehouse or "").strip().lower()
    records = [_inventory_model(record) for record in _load_inventory_records()]

    def matches(item: PharmacyInventoryRecord) -> bool:
        if status and item.status != status:
            return False
        if low_stock_only and item.currentStock > item.minStock:
            return False
        if warehouse_value and item.warehouse.lower() != warehouse_value:
            return False
        if keyword_value:
            haystack = " ".join(
                [
                    item.itemId,
                    item.drugId,
                    item.drugName,
                    item.warehouse,
                    item.batchNo,
                    item.lotNo,
                    item.supplier,
                ]
            ).lower()
            return keyword_value in haystack
        return True

    filtered = [item for item in records if matches(item)]
    return sorted(filtered, key=lambda item: (item.status not in {"low", "out_of_stock", "expired"}, item.warehouse.lower(), item.drugName.lower()))


def get_pharmacy_inventory_item(item_id: str) -> PharmacyInventoryRecord:
    record = _find_inventory_record(_load_inventory_records(), item_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Pharmacy inventory item not found")
    return _inventory_model(record)


def upsert_pharmacy_inventory_item(
    payload: PharmacyInventoryUpsertRequest,
    *,
    updated_by: str,
) -> PharmacyInventoryRecord:
    item_id = payload.itemId.strip()
    if not item_id:
        raise HTTPException(status_code=400, detail="itemId is required")

    with _LOCK:
        records = _load_inventory_records()
        now = _now()
        record = {
            "itemId": item_id,
            "drugId": payload.drugId.strip(),
            "drugName": payload.drugName.strip(),
            "warehouse": payload.warehouse.strip(),
            "batchNo": payload.batchNo.strip(),
            "lotNo": payload.lotNo.strip(),
            "unit": payload.unit.strip(),
            "currentStock": int(payload.currentStock),
            "reservedStock": int(payload.reservedStock),
            "minStock": int(payload.minStock),
            "expiryDate": payload.expiryDate.strip(),
            "status": _sync_status(int(payload.currentStock), int(payload.minStock), payload.expiryDate),
            "supplier": payload.supplier.strip(),
            "lastInboundAt": now,
            "lastOutboundAt": now,
            "updatedBy": updated_by.strip() or "system",
            "updatedAt": now,
        }
        index = _find_inventory_index(records, item_id)
        if index >= 0:
            record["lastInboundAt"] = records[index].get("lastInboundAt") or now
            record["lastOutboundAt"] = records[index].get("lastOutboundAt") or now
            records[index] = record
        else:
            records.append(record)
        _save_inventory_records(records)
        return _inventory_model(record)


def adjust_pharmacy_inventory_item(
    item_id: str,
    payload: PharmacyStockAdjustRequest,
    *,
    updated_by: str,
) -> PharmacyInventoryRecord:
    with _LOCK:
        records = _load_inventory_records()
        index = _find_inventory_index(records, item_id)
        if index < 0:
            raise HTTPException(status_code=404, detail="Pharmacy inventory item not found")

        current = dict(records[index])
        stock = int(current.get("currentStock") or 0)
        reserved = int(current.get("reservedStock") or 0)
        direction = payload.direction
        quantity = int(payload.quantity)

        if direction in {"outbound", "discard"} and stock < quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock for adjustment")

        delta = quantity if direction in {"inbound", "transfer"} else -quantity
        next_stock = max(0, stock + delta)
        updated_at = _now()
        current["currentStock"] = next_stock
        current["status"] = _sync_status(next_stock, int(current.get("minStock") or 0), str(current.get("expiryDate") or ""))
        current["updatedBy"] = updated_by.strip() or "system"
        current["updatedAt"] = updated_at
        if direction == "inbound":
            current["lastInboundAt"] = updated_at
        else:
            current["lastOutboundAt"] = updated_at
        records[index] = _normalize_inventory_record(current)
        _save_inventory_records(records)

        transactions = _load_transactions()
        transactions.append(
            _make_transaction(
                item_id=current["itemId"],
                drug_id=current["drugId"],
                change=delta,
                direction=direction,
                note=payload.note,
                operator_username=payload.operatorUsername or updated_by,
                operator_name=payload.operatorName or updated_by,
            )
        )
        _save_transactions(transactions)
        return _inventory_model(current)


def list_pharmacy_transactions(limit: int = 50) -> list[PharmacyTransactionRecord]:
    records = [_transaction_model(record) for record in _load_transactions()]
    return sorted(records, key=lambda item: item.createdAt, reverse=True)[: max(0, limit)]


def _patient_medication_to_review_order(record: PatientMedicationRecord, patient_name: str) -> PharmacyReviewOrder:
    return PharmacyReviewOrder(
        patientId=record.patient_id,
        patientName=patient_name,
        medicationId=record.medication_id,
        drugId=record.drug_id,
        drugNameSnapshot=record.drug_name_snapshot,
        dosage=record.dosage,
        frequency=record.frequency,
        route=record.route,
        reviewStatus=record.review_status,
        status=record.status,
        prescribedBy=record.prescribed_by,
        note=record.note or "",
        createdAt=record.created_at,
        updatedAt=record.updated_at,
    )


def list_pharmacy_review_queue(*, status: str | None = None) -> list[PharmacyReviewOrder]:
    queue: list[PharmacyReviewOrder] = []
    for patient in list_patients():
        patient_id = str(patient.get("patientId") or "").strip()
        if not patient_id:
            continue
        patient_case = get_patient(patient_id)
        if patient_case is None:
            continue
        for medication in list_patient_medications(patient_id):
            if status and medication.review_status != status:
                continue
            queue.append(_patient_medication_to_review_order(medication, patient_case.name))
    return sorted(queue, key=lambda item: (item.reviewStatus != "pending", item.updatedAt, item.patientId, item.medicationId))


def review_pharmacy_order(
    patient_id: str,
    medication_id: str,
    *,
    review_status: PatientMedicationReviewStatus,
    note: str = "",
    operator_username: str | None = None,
    operator_name: str | None = None,
) -> PharmacyReviewOrder:
    current = get_patient_medication_item(patient_id, medication_id)
    next_payload = PatientMedicationUpsertRequest(
        medication_id=current.medication_id,
        patient_id=current.patient_id,
        drug_id=current.drug_id,
        drug_name_snapshot=current.drug_name_snapshot,
        dosage=current.dosage,
        frequency=current.frequency,
        route=current.route,
        start_date=current.start_date,
        end_date=current.end_date,
        status=current.status,
        review_status=review_status,
        note=note or current.note,
    )
    updated = update_patient_medication(
        patient_id,
        medication_id,
        next_payload,
        prescribed_by=operator_name or operator_username or current.prescribed_by,
    )
    patient = get_patient(patient_id)
    return _patient_medication_to_review_order(updated, patient.name if patient else patient_id)


def get_pharmacy_dashboard() -> PharmacyDashboardResponse:
    inventory = list_pharmacy_inventory()
    queue = list_pharmacy_review_queue()
    transactions = list_pharmacy_transactions(30)
    summary = [
        PharmacySummaryItem(label="库存条目", value=str(len(inventory)), trend="稳定"),
        PharmacySummaryItem(label="低库存", value=str(len([item for item in inventory if item.status == 'low'])), trend="关注"),
        PharmacySummaryItem(label="待复核处方", value=str(len([item for item in queue if item.reviewStatus == 'pending'])), trend="待处理"),
        PharmacySummaryItem(label="管制药库存", value=str(len([item for item in inventory if 'controlled' in item.drugId or 'morphine' in item.drugName.lower()])), trend="受控"),
    ]
    return PharmacyDashboardResponse(summary=summary, inventory=inventory, reviewQueue=queue, transactions=transactions)
