from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Iterable

from fastapi import HTTPException

from ..schemas import PatientMedicationRecord, PatientMedicationUpsertRequest
from ..store import get_patient
from .drug_catalog_service import get_drug_catalog_item, list_drug_catalog

_LOCK = Lock()

_DISEASE_SEEDS: list[tuple[tuple[str, ...], str, str, str, str]] = [
    (("diabetes",), "drug-metformin", "500 mg", "bid", "po"),
    (("hypertension", "blood pressure", "bp"), "drug-amlodipine", "5 mg", "qd", "po"),
    (("lipid", "hyperlip"), "drug-atorvastatin", "10 mg", "qd", "po"),
]


def _storage_root() -> Path:
    root = Path(
        os.getenv(
            "CTPATH_PATIENT_MEDICATION_DIR",
            Path(__file__).resolve().parents[1] / "runtime" / "patient_medications",
        )
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _records_path() -> Path:
    return _storage_root() / "medications.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_date(value: str | None, fallback: date | None = None) -> date:
    if value:
        try:
            return date.fromisoformat(value[:10])
        except Exception:
            pass
    return fallback or date.today()


def _shift_date(value: str | None, days: int) -> str:
    base = _parse_date(value, date.today())
    return (base + timedelta(days=days)).isoformat()


def _snapshot_from_drug(drug_id: str) -> str:
    try:
        drug = get_drug_catalog_item(drug_id)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(status_code=404, detail="Drug not found") from exc

    name_parts = [drug.generic_name.strip()]
    if drug.brand_name.strip():
        name_parts.append(f"({drug.brand_name.strip()})")
    return " ".join(part for part in name_parts if part).strip()


def _choose_seed_drug(patient_disease: str) -> tuple[str, str, str, str] | None:
    text = patient_disease.lower()
    available = {item.drug_id for item in list_drug_catalog()}
    for keywords, drug_id, dosage, frequency, route in _DISEASE_SEEDS:
        if any(keyword in text for keyword in keywords) and drug_id in available:
            return drug_id, dosage, frequency, route
    return None


def _default_seed_records(patient_id: str) -> list[dict[str, Any]]:
    patient = get_patient(patient_id)
    if patient is None:
        return []

    seed = _choose_seed_drug(patient.primaryDisease or "")
    if seed is None:
        return []

    drug_id, dosage, frequency, route = seed
    recorded_date = patient.lastVisit or date.today().isoformat()
    medication_id = f"med-{patient_id.lower()}-{drug_id.replace('drug-', '')}"
    prescriber = str(patient.primaryDoctor or patient.caseManager or "system").strip() or "system"
    now = _now_iso()
    return [
        {
            "medication_id": medication_id,
            "patient_id": patient_id,
            "drug_id": drug_id,
            "drug_name_snapshot": _snapshot_from_drug(drug_id),
            "dosage": dosage,
            "frequency": frequency,
            "route": route,
            "start_date": recorded_date,
            "end_date": _shift_date(recorded_date, 90),
            "status": "active",
            "prescribed_by": prescriber,
            "review_status": "approved",
            "note": "Seeded current medication from the patient's main chronic disease.",
            "created_at": now,
            "updated_at": now,
        }
    ]


def _load_records() -> list[dict[str, Any]]:
    path = _records_path()
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
    path = _records_path()
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["medication_id"] = str(normalized.get("medication_id") or "").strip()
    normalized["patient_id"] = str(normalized.get("patient_id") or "").strip()
    normalized["drug_id"] = str(normalized.get("drug_id") or "").strip()
    normalized["drug_name_snapshot"] = str(normalized.get("drug_name_snapshot") or "").strip()
    normalized["dosage"] = str(normalized.get("dosage") or "").strip()
    normalized["frequency"] = str(normalized.get("frequency") or "").strip()
    normalized["route"] = str(normalized.get("route") or "").strip()
    normalized["start_date"] = str(normalized.get("start_date") or "").strip()
    normalized["end_date"] = str(normalized.get("end_date") or "").strip()
    normalized["status"] = str(normalized.get("status") or "active").strip()
    normalized["prescribed_by"] = str(normalized.get("prescribed_by") or "").strip()
    normalized["review_status"] = str(normalized.get("review_status") or "pending").strip()
    normalized["note"] = str(normalized.get("note") or "").strip()
    normalized["created_at"] = str(normalized.get("created_at") or "").strip()
    normalized["updated_at"] = str(normalized.get("updated_at") or "").strip()
    return normalized


def _to_public_record(record: dict[str, Any]) -> PatientMedicationRecord:
    return PatientMedicationRecord.model_validate(_normalize_record(record))


def _find_index(records: list[dict[str, Any]], patient_id: str, medication_id: str) -> int:
    target_patient = patient_id.strip()
    target_medication = medication_id.strip()
    for index, record in enumerate(records):
        if (
            str(record.get("patient_id") or "").strip() == target_patient
            and str(record.get("medication_id") or "").strip() == target_medication
        ):
            return index
    return -1


def _find_record(records: Iterable[dict[str, Any]], patient_id: str, medication_id: str) -> dict[str, Any] | None:
    target_patient = patient_id.strip()
    target_medication = medication_id.strip()
    for record in records:
        if (
            str(record.get("patient_id") or "").strip() == target_patient
            and str(record.get("medication_id") or "").strip() == target_medication
        ):
            return record
    return None


def _ensure_valid_patient(patient_id: str) -> None:
    if get_patient(patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")


def _seed_if_needed(records: list[dict[str, Any]], patient_id: str) -> list[dict[str, Any]]:
    patient_key = patient_id.strip()
    if any(str(record.get("patient_id") or "").strip() == patient_key for record in records):
        return records

    seeds = _default_seed_records(patient_id)
    if not seeds:
        return records

    next_records = [_normalize_record(record) for record in records] + seeds
    _save_records(next_records)
    return next_records


def list_patient_medications(patient_id: str) -> list[PatientMedicationRecord]:
    if not patient_id:
        return []

    _ensure_valid_patient(patient_id)
    records = _seed_if_needed(_load_records(), patient_id)
    filtered = [
        _to_public_record(record)
        for record in records
        if str(record.get("patient_id") or "").strip() == patient_id.strip()
    ]
    return sorted(filtered, key=lambda item: (item.status != "active", item.start_date, item.medication_id))


def get_patient_medication_item(patient_id: str, medication_id: str) -> PatientMedicationRecord:
    _ensure_valid_patient(patient_id)
    record = _find_record(_seed_if_needed(_load_records(), patient_id), patient_id, medication_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Patient medication not found")
    return _to_public_record(record)


def create_patient_medication(
    patient_id: str,
    payload: PatientMedicationUpsertRequest,
    *,
    prescribed_by: str,
) -> PatientMedicationRecord:
    if payload.patient_id.strip() != patient_id.strip():
        raise HTTPException(status_code=400, detail="patient_id does not match path parameter")

    _ensure_valid_patient(patient_id)
    drug = get_drug_catalog_item(payload.drug_id)

    medication_id = payload.medication_id.strip()
    if not medication_id:
        raise HTTPException(status_code=400, detail="medication_id is required")

    with _LOCK:
        records = _seed_if_needed(_load_records(), patient_id)
        if _find_index(records, patient_id, medication_id) >= 0:
            raise HTTPException(status_code=409, detail="Patient medication already exists")

        now = _now_iso()
        record = {
            "medication_id": medication_id,
            "patient_id": patient_id.strip(),
            "drug_id": payload.drug_id.strip(),
            "drug_name_snapshot": _snapshot_from_drug(drug.drug_id),
            "dosage": payload.dosage.strip(),
            "frequency": payload.frequency.strip(),
            "route": payload.route.strip(),
            "start_date": payload.start_date.strip(),
            "end_date": payload.end_date.strip(),
            "status": payload.status,
            "prescribed_by": prescribed_by.strip() or "current-user",
            "review_status": payload.review_status,
            "note": payload.note.strip(),
            "created_at": now,
            "updated_at": now,
        }
        records.append(record)
        _save_records(records)
        return _to_public_record(record)


def update_patient_medication(
    patient_id: str,
    medication_id: str,
    payload: PatientMedicationUpsertRequest,
    *,
    prescribed_by: str,
) -> PatientMedicationRecord:
    if payload.patient_id.strip() != patient_id.strip():
        raise HTTPException(status_code=400, detail="patient_id does not match path parameter")
    if payload.medication_id.strip() != medication_id.strip():
        raise HTTPException(status_code=400, detail="medication_id does not match path parameter")

    _ensure_valid_patient(patient_id)
    drug = get_drug_catalog_item(payload.drug_id)

    with _LOCK:
        records = _seed_if_needed(_load_records(), patient_id)
        index = _find_index(records, patient_id, medication_id)
        if index < 0:
            raise HTTPException(status_code=404, detail="Patient medication not found")

        current = _normalize_record(records[index])
        updated = {
            "medication_id": medication_id.strip(),
            "patient_id": patient_id.strip(),
            "drug_id": payload.drug_id.strip(),
            "drug_name_snapshot": _snapshot_from_drug(drug.drug_id),
            "dosage": payload.dosage.strip(),
            "frequency": payload.frequency.strip(),
            "route": payload.route.strip(),
            "start_date": payload.start_date.strip(),
            "end_date": payload.end_date.strip(),
            "status": payload.status,
            "prescribed_by": prescribed_by.strip() or current.get("prescribed_by") or "current-user",
            "review_status": payload.review_status,
            "note": payload.note.strip(),
            "created_at": current.get("created_at") or _now_iso(),
            "updated_at": _now_iso(),
        }
        records[index] = updated
        _save_records(records)
        return _to_public_record(updated)
