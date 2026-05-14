from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, List

from ..model_service import MODEL_SERVICE
from ..schemas import (
    GovernanceModuleItem,
    GovernanceModulesResponse,
    GovernanceRecord,
    GovernanceRecordsResponse,
    GovernanceRecordStatusUpdateRequest,
)
from ..store import DB_URL, get_maintenance_overview, get_model_metrics

_LOCK = Lock()


def _storage_root() -> Path:
    root = Path(
        os.getenv(
            "CTPATH_GOVERNANCE_DIR",
            Path(__file__).resolve().parents[1] / "runtime" / "governance",
        )
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _records_path() -> Path:
    return _storage_root() / "governance_records.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_records() -> list[dict[str, Any]]:
    now = _now_iso()
    return [
        {
            "recordId": "gov-timeline-001",
            "category": "timeline_anomaly",
            "title": "异常时间线待核对",
            "patientId": "PID1007",
            "patientName": "郑丽华",
            "status": "pending",
            "priority": "high",
            "detail": "患者病程事件存在同日重复记录，需管理员核对。",
            "handlingNote": "",
            "updatedBy": "",
            "updatedAt": now,
        },
        {
            "recordId": "gov-archive-001",
            "category": "archive_missing",
            "title": "档案字段待补全",
            "patientId": "PID1008",
            "patientName": "王建国",
            "status": "pending",
            "priority": "medium",
            "detail": "患者主索引缺少 MRN 或知情同意状态。",
            "handlingNote": "",
            "updatedBy": "",
            "updatedAt": now,
        },
    ]


def _load_records() -> list[dict[str, Any]]:
    path = _records_path()
    if not path.exists():
        records = _default_records()
        _save_records(records)
        return records
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            records = [item for item in payload if isinstance(item, dict)]
            if records:
                return records
    except Exception:
        pass
    records = _default_records()
    _save_records(records)
    return records


def _save_records(records: list[dict[str, Any]]) -> None:
    path = _records_path()
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


def _to_public_record(record: dict[str, Any]) -> GovernanceRecord:
    return GovernanceRecord.model_validate(record)


def list_governance_records() -> GovernanceRecordsResponse:
    records = [_to_public_record(record) for record in _load_records()]
    summary = {
        "total": len(records),
        "pending": sum(1 for item in records if item.status == "pending"),
        "needs_supplement": sum(1 for item in records if item.status == "needs_supplement"),
        "resolved": sum(1 for item in records if item.status == "resolved"),
        "ignored": sum(1 for item in records if item.status == "ignored"),
    }
    return GovernanceRecordsResponse(mode="mysql" if DB_URL else "demo", summary=summary, items=records)


def update_governance_record_status(
    record_id: str,
    payload: GovernanceRecordStatusUpdateRequest,
    *,
    updated_by: str,
) -> GovernanceRecord | None:
    with _LOCK:
        records = _load_records()
        for index, record in enumerate(records):
            if str(record.get("recordId") or "") != record_id:
                continue
            updated = dict(record)
            updated["status"] = payload.status
            updated["handlingNote"] = payload.handlingNote.strip()
            updated["updatedBy"] = updated_by
            updated["updatedAt"] = _now_iso()
            records[index] = updated
            _save_records(records)
            return _to_public_record(updated)
    return None


def get_governance_modules() -> GovernanceModulesResponse:
    maintenance = get_maintenance_overview()
    metrics = get_model_metrics()

    items: List[GovernanceModuleItem] = [
        GovernanceModuleItem(
            moduleKey="base-platform",
            title="基础平台",
            domain="Base",
            ownerRole="doctor / archivist",
            status="已连接 MySQL 数据源" if DB_URL else "未连接 MySQL，当前使用内置业务数据",
            tone="healthy",
            description="承接统一入口、角色登录、患者主索引与系统运行状态。",
            capabilities=["统一登录", "角色分流", "数据源状态", "健康检查"],
        ),
        GovernanceModuleItem(
            moduleKey="patient-index",
            title="患者主索引治理",
            domain="PDS / MRMS",
            ownerRole="archivist",
            status=(
                f"缺失 MRN {maintenance.missingMrnCount}，"
                f"待签同意 {maintenance.pendingConsentCount}，"
                f"疑似重复 {maintenance.duplicateRiskCount}"
            ),
            tone="warning"
            if maintenance.missingMrnCount or maintenance.pendingConsentCount or maintenance.duplicateRiskCount
            else "healthy",
            description="围绕患者主数据、建档来源、知情同意与疑似重复信息进行持续治理。",
            capabilities=["MRN 维护", "来源分布", "主数据核对", "档案质控"],
        ),
        GovernanceModuleItem(
            moduleKey="clinical-workspace",
            title="临床评估与预测",
            domain="Clinical",
            ownerRole="doctor",
            status="模型可用" if MODEL_SERVICE.available else "当前处于回退模式",
            tone="healthy" if MODEL_SERVICE.available else "warning",
            description="承接医生端风险研判、预测建议与临床工作台能力。",
            capabilities=[
                "患者评估",
                "结构化事件",
                f"当前模型 {metrics.currentModel.model}",
                "辅助建议",
            ],
        ),
        GovernanceModuleItem(
            moduleKey="followup-collaboration",
            title="随访协同",
            domain="Follow-up",
            ownerRole="doctor / nurse",
            status=f"超期随访 {maintenance.overdueFollowupCount}",
            tone="warning" if maintenance.overdueFollowupCount else "normal",
            description="衔接电话随访、联系记录、门诊任务和复联提醒。",
            capabilities=["随访任务", "联系记录", "门诊联动", "移动端录入"],
        ),
        GovernanceModuleItem(
            moduleKey="api-governance",
            title="接口治理",
            domain="WebAPI",
            ownerRole="doctor / archivist",
            status="FastAPI + RBAC 已接入",
            tone="normal",
            description="对外统一暴露登录、患者、随访、治理和模型能力接口。",
            capabilities=["FastAPI", "RBAC", "治理接口", "统一数据出口"],
        ),
    ]

    return GovernanceModulesResponse(mode="mysql" if DB_URL else "demo", items=items)
