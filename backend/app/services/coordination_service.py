from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Iterable

from fastapi import HTTPException

from ..schemas import (
    CoordinationBoardResponse,
    CoordinationCategory,
    CoordinationItem,
    CoordinationItemUpsertRequest,
    CoordinationNote,
    CoordinationNoteCreateRequest,
    CoordinationParticipant,
    CoordinationStatus,
    CoordinationStatusUpdateRequest,
    CoordinationSummaryItem,
)
from ..store import get_patient, list_patients

_LOCK = Lock()
DEFAULT_TIMESTAMP = "2026-04-18T00:00:00+00:00"


def _storage_root() -> Path:
    root = Path(
        os.getenv(
            "CTPATH_COORDINATION_DIR",
            Path(__file__).resolve().parents[1] / "runtime" / "coordination",
        )
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _records_path() -> Path:
    return _storage_root() / "coordination.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _shift_date(value: str | None, days: int) -> str:
    try:
        base = datetime.fromisoformat((value or "")[:10]).date()
    except Exception:
        base = datetime.now(timezone.utc).date()
    return (base + timedelta(days=days)).isoformat()


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


def _normalize_participant(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["role"] = str(normalized.get("role") or "doctor").strip() or "doctor"
    normalized["name"] = str(normalized.get("name") or "").strip()
    normalized["relation"] = str(normalized.get("relation") or "").strip()
    normalized["phone"] = str(normalized.get("phone") or "").strip()
    return normalized


def _normalize_note(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["noteId"] = str(normalized.get("noteId") or "").strip()
    normalized["createdAt"] = str(normalized.get("createdAt") or DEFAULT_TIMESTAMP)
    normalized["createdBy"] = str(normalized.get("createdBy") or "").strip()
    normalized["createdByRole"] = str(normalized.get("createdByRole") or "doctor").strip() or "doctor"
    normalized["action"] = str(normalized.get("action") or "note").strip() or "note"
    normalized["note"] = str(normalized.get("note") or "").strip()
    return normalized


def _normalize_item(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    normalized["coordinationId"] = str(normalized.get("coordinationId") or "").strip()
    normalized["patientId"] = str(normalized.get("patientId") or "").strip()
    normalized["patientName"] = str(normalized.get("patientName") or "").strip()
    normalized["primaryDisease"] = str(normalized.get("primaryDisease") or "").strip()
    normalized["currentStage"] = str(normalized.get("currentStage") or "").strip()
    normalized["riskLevel"] = str(normalized.get("riskLevel") or "").strip()
    normalized["category"] = str(normalized.get("category") or "followup").strip() or "followup"
    normalized["status"] = str(normalized.get("status") or "open").strip() or "open"
    normalized["ownerRole"] = str(normalized.get("ownerRole") or "doctor").strip() or "doctor"
    normalized["ownerName"] = str(normalized.get("ownerName") or "").strip()
    normalized["nextAction"] = str(normalized.get("nextAction") or "").strip()
    normalized["dueDate"] = str(normalized.get("dueDate") or DEFAULT_TIMESTAMP)
    normalized["lastUpdatedAt"] = str(normalized.get("lastUpdatedAt") or DEFAULT_TIMESTAMP)
    normalized["summary"] = str(normalized.get("summary") or "").strip()
    normalized["participants"] = [_normalize_participant(item) for item in normalized.get("participants", []) if isinstance(item, dict)]
    normalized["notes"] = [_normalize_note(item) for item in normalized.get("notes", []) if isinstance(item, dict)]
    return normalized


def _item_model(record: dict[str, Any]) -> CoordinationItem:
    return CoordinationItem.model_validate(_normalize_item(record))


def _participant_block(patient) -> list[CoordinationParticipant]:
    participants = [
        CoordinationParticipant(
            role="doctor",
            name=str(getattr(patient, "primaryDoctor", "") or "责任医生").strip() or "责任医生",
            relation="责任医生",
            phone=str(getattr(patient, "phone", "") or "").strip(),
        ),
        CoordinationParticipant(
            role="nurse",
            name=str(getattr(patient, "caseManager", "") or "个案管理师").strip() or "个案管理师",
            relation="个案管理师",
            phone=str(getattr(patient, "emergencyContactPhone", "") or "").strip(),
        ),
        CoordinationParticipant(
            role="pharmacist",
            name="药师复核",
            relation="药师复核",
            phone="",
        ),
    ]
    if getattr(patient, "archiveStatus", ""):
        participants.append(
            CoordinationParticipant(
                role="archivist",
                name="档案员",
                relation="档案维护",
                phone="",
            )
        )
    return participants


def _category_for_patient(patient) -> CoordinationCategory:
    disease = str(getattr(patient, "primaryDisease", "") or "").lower()
    stage = str(getattr(patient, "currentStage", "") or "").lower()
    risk = str(getattr(patient, "riskLevel", "") or "").lower()
    if "diabetes" in disease or "hypertension" in disease or "bp" in disease:
        return "medication_review"
    if "late" in stage or "high" in risk:
        return "case_review"
    if getattr(patient, "outpatientTasks", []):
        return "handoff"
    return "followup"


def _status_for_patient(patient) -> CoordinationStatus:
    risk = str(getattr(patient, "riskLevel", "") or "").lower()
    support = str(getattr(patient, "dataSupport", "") or "").lower()
    if "high" in risk and support == "low":
        return "blocked"
    if "high" in risk:
        return "in_progress"
    return "open"


def _owner_role_for_category(category: CoordinationCategory) -> str:
    if category == "medication_review":
        return "pharmacist"
    if category == "handoff":
        return "nurse"
    if category == "referral":
        return "doctor"
    if category == "family_contact":
        return "nurse"
    if category == "case_review":
        return "doctor"
    return "nurse"


def _owner_name_for_category(patient, category: CoordinationCategory) -> str:
    if category == "medication_review":
        return str(getattr(patient, "caseManager", "") or "药师复核").strip() or "药师复核"
    return str(getattr(patient, "primaryDoctor", "") or getattr(patient, "caseManager", "") or "责任人").strip() or "责任人"


def _summary_text(patient) -> str:
    return "{0} / {1} / 患者电话 {2} / 紧急联系人 {3}".format(
        getattr(patient, "name", ""),
        getattr(patient, "primaryDisease", ""),
        str(getattr(patient, "phone", "") or "待补齐").strip() or "待补齐",
        str(getattr(patient, "emergencyContactName", "") or "待补齐").strip() or "待补齐",
    )


def _next_action(patient, category: CoordinationCategory) -> str:
    if category == "medication_review":
        return "复核当前用药并同步药房意见"
    if category == "handoff":
        return "完成交接并更新随访状态"
    if category == "referral":
        return "确认转诊信息和下一次复诊安排"
    if category == "family_contact":
        return "核对家属联系方式并回访"
    if category == "case_review":
        return "补齐病历信息并完成个案复核"
    return "联系患者并更新协同备注"


def _default_items() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for patient in list_patients():
        patient_id = str(patient.get("patientId") or "").strip()
        if not patient_id:
            continue
        case = get_patient(patient_id)
        if case is None:
            continue
        category = _category_for_patient(case)
        status = _status_for_patient(case)
        owner_role = _owner_role_for_category(category)
        owner_name = _owner_name_for_category(case, category)
        due_date = case.followUps[0].dueDate if getattr(case, "followUps", []) else _shift_date(getattr(case, "lastVisit", None), 7)
        records.append(
            {
                "coordinationId": f"coord-{patient_id}",
                "patientId": patient_id,
                "patientName": case.name,
                "primaryDisease": case.primaryDisease,
                "currentStage": case.currentStage,
                "riskLevel": case.riskLevel,
                "category": category,
                "status": status,
                "ownerRole": owner_role,
                "ownerName": owner_name,
                "nextAction": _next_action(case, category),
                "dueDate": due_date,
                "lastUpdatedAt": f"{getattr(case, 'lastVisit', DEFAULT_TIMESTAMP)}T09:30:00+00:00",
                "summary": _summary_text(case),
                "participants": [participant.model_dump() for participant in _participant_block(case)],
                "notes": [
                    {
                        "noteId": f"note-{patient_id}-seed",
                        "createdAt": f"{getattr(case, 'lastVisit', DEFAULT_TIMESTAMP)}T09:00:00+00:00",
                        "createdBy": owner_name,
                        "createdByRole": owner_role,
                        "action": "seed",
                        "note": "已根据档案总览、联系方式和当前用药生成协同初始记录。",
                    }
                ],
            }
        )
    return records


def _load_records() -> list[dict[str, Any]]:
    path = _records_path()
    records = _load_json(path, _default_items())
    if not path.exists():
        _save_json(path, records)
    return [_normalize_item(record) for record in records] or _default_items()


def _save_records(records: list[dict[str, Any]]) -> None:
    _save_json(_records_path(), records)


def _find_index(records: list[dict[str, Any]], coordination_id: str) -> int:
    target = coordination_id.strip()
    for index, record in enumerate(records):
        if str(record.get("coordinationId") or "").strip() == target:
            return index
    return -1


def _find_record(records: Iterable[dict[str, Any]], coordination_id: str) -> dict[str, Any] | None:
    target = coordination_id.strip()
    for record in records:
        if str(record.get("coordinationId") or "").strip() == target:
            return record
    return None


def list_coordination_items(
    *,
    status: CoordinationStatus | None = None,
    category: CoordinationCategory | None = None,
    keyword: str | None = None,
) -> list[CoordinationItem]:
    keyword_value = (keyword or "").strip().lower()
    records = [_item_model(record) for record in _load_records()]

    def matches(item: CoordinationItem) -> bool:
        if status and item.status != status:
            return False
        if category and item.category != category:
            return False
        if keyword_value:
            haystack = " ".join(
                [
                    item.coordinationId,
                    item.patientId,
                    item.patientName,
                    item.primaryDisease,
                    item.currentStage,
                    item.ownerName,
                    item.summary,
                    item.nextAction,
                ]
            ).lower()
            return keyword_value in haystack
        return True

    filtered = [item for item in records if matches(item)]
    return sorted(filtered, key=lambda item: (item.status in {"done", "closed"}, item.lastUpdatedAt, item.patientId))


def get_coordination_item(coordination_id: str) -> CoordinationItem:
    record = _find_record(_load_records(), coordination_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Coordination item not found")
    return _item_model(record)


def upsert_coordination_item(
    payload: CoordinationItemUpsertRequest,
    *,
    operator_username: str,
    operator_name: str,
    operator_role: str,
) -> CoordinationItem:
    item_id = payload.coordinationId.strip()
    if not item_id:
        raise HTTPException(status_code=400, detail="coordinationId is required")

    with _LOCK:
        records = _load_records()
        index = _find_index(records, item_id)
        notes: list[dict[str, Any]] = []
        if index >= 0:
            notes = [item for item in records[index].get("notes", []) if isinstance(item, dict)]
        now = _now()
        record = {
            "coordinationId": item_id,
            "patientId": payload.patientId.strip(),
            "patientName": payload.patientName.strip(),
            "primaryDisease": payload.primaryDisease.strip(),
            "currentStage": payload.currentStage.strip(),
            "riskLevel": payload.riskLevel.strip(),
            "category": payload.category,
            "status": payload.status,
            "ownerRole": payload.ownerRole,
            "ownerName": payload.ownerName.strip(),
            "nextAction": payload.nextAction.strip(),
            "dueDate": payload.dueDate.strip(),
            "lastUpdatedAt": now,
            "summary": payload.summary.strip(),
            "participants": [participant.model_dump() for participant in payload.participants],
            "notes": notes,
        }
        records = [rec for rec in records if str(rec.get("coordinationId") or "").strip() != item_id]
        records.insert(0, record)
        _save_records(records)
        return _item_model(record)


def update_coordination_status(coordination_id: str, payload: CoordinationStatusUpdateRequest) -> CoordinationItem:
    with _LOCK:
        records = _load_records()
        index = _find_index(records, coordination_id)
        if index < 0:
            raise HTTPException(status_code=404, detail="Coordination item not found")
        current = dict(records[index])
        current["status"] = payload.status
        current["lastUpdatedAt"] = _now()
        if payload.note.strip():
            current_notes = [item for item in current.get("notes", []) if isinstance(item, dict)]
            current_notes.append(
                {
                    "noteId": f"note-{coordination_id}-{len(current_notes) + 1}",
                    "createdAt": _now(),
                    "createdBy": payload.operatorName or payload.operatorUsername or "system",
                    "createdByRole": payload.operatorRole,
                    "action": "status",
                    "note": payload.note.strip(),
                }
            )
            current["notes"] = current_notes
        records[index] = current
        _save_records(records)
        return _item_model(current)


def append_coordination_note(coordination_id: str, payload: CoordinationNoteCreateRequest) -> CoordinationItem:
    with _LOCK:
        records = _load_records()
        index = _find_index(records, coordination_id)
        if index < 0:
            raise HTTPException(status_code=404, detail="Coordination item not found")
        current = dict(records[index])
        notes = [item for item in current.get("notes", []) if isinstance(item, dict)]
        notes.append(
            {
                "noteId": f"note-{coordination_id}-{len(notes) + 1}",
                "createdAt": _now(),
                "createdBy": payload.operatorName or payload.operatorUsername or "system",
                "createdByRole": payload.operatorRole,
                "action": payload.action or "note",
                "note": payload.note.strip(),
            }
        )
        current["notes"] = notes
        current["lastUpdatedAt"] = _now()
        records[index] = current
        _save_records(records)
        return _item_model(current)


def get_coordination_board(
    *,
    status: CoordinationStatus | None = None,
    category: CoordinationCategory | None = None,
    keyword: str | None = None,
) -> CoordinationBoardResponse:
    items = list_coordination_items(status=status, category=category, keyword=keyword)
    summary = [
        CoordinationSummaryItem(label="协同总数", value=str(len(items)), trend="稳定"),
        CoordinationSummaryItem(label="待处理", value=str(len([item for item in items if item.status == "open"])), trend="待跟进"),
        CoordinationSummaryItem(label="处理中", value=str(len([item for item in items if item.status == "in_progress"])), trend="推进中"),
        CoordinationSummaryItem(label="阻塞", value=str(len([item for item in items if item.status == "blocked"])), trend="重点关注"),
    ]
    return CoordinationBoardResponse(summary=summary, items=items)
