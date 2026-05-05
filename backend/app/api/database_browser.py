from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ..api.deps import require_roles
from ..schemas import DoctorPublic
from ..store import DB_URL

try:
    from sqlalchemy import create_engine, text
except Exception:  # pragma: no cover
    create_engine = None
    text = None


router = APIRouter(prefix="/api/database-browser", tags=["database-browser"])


TABLE_DESCRIPTIONS: dict[str, str] = {
    "doctor_users": "用户账号与角色",
    "roles": "角色字典",
    "patients": "患者主索引与兼容档案字段",
    "patient_events": "病程事件与模型四元组来源",
    "patient_encounter_state": "患者接诊流转状态",
    "outpatient_tasks": "随访与复查任务",
    "outpatient_task_logs": "任务处理日志",
    "patient_contact_logs": "随访联系记录",
    "patient_audit_logs": "患者操作审计",
    "patient_attachments": "电子档案附件",
    "drug_catalog": "药品目录",
    "drug_permissions": "药品角色权限",
    "patient_medications": "患者当前用药",
    "prediction_results": "模型预测结果",
    "governance_records": "数据治理记录",
    "system_audit_logs": "系统审计日志",
}


def _engine():
    if not DB_URL or create_engine is None:
        return None
    return create_engine(DB_URL, pool_pre_ping=True, future=True)


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


@router.get("/tables")
def list_database_tables(_: DoctorPublic = Depends(require_roles("admin"))):
    engine = _engine()
    if engine is None:
        return {
            "connected": False,
            "mode": "demo",
            "message": "未配置 CTPATH_DB_URL，当前未连接 MySQL，无法直接读取数据库表数据。",
            "tables": [
                {
                    "tableName": table_name,
                    "description": description,
                    "rowCount": 0,
                    "columnCount": 0,
                }
                for table_name, description in TABLE_DESCRIPTIONS.items()
            ],
        }

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT TABLE_NAME AS tableName, TABLE_ROWS AS estimatedRows
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                """
            )
        ).mappings().all()
        columns = conn.execute(
            text(
                """
                SELECT TABLE_NAME AS tableName, COUNT(*) AS columnCount
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                GROUP BY TABLE_NAME
                """
            )
        ).mappings().all()

    row_map = {str(row["tableName"]): int(row["estimatedRows"] or 0) for row in rows}
    column_map = {str(row["tableName"]): int(row["columnCount"] or 0) for row in columns}
    tables = [
        {
            "tableName": table_name,
            "description": TABLE_DESCRIPTIONS[table_name],
            "rowCount": row_map.get(table_name, 0),
            "columnCount": column_map.get(table_name, 0),
        }
        for table_name in TABLE_DESCRIPTIONS
        if table_name in row_map
    ]
    return {"connected": True, "mode": "mysql", "message": "已连接 MySQL，可查看白名单业务表。", "tables": tables}


@router.get("/tables/{table_name}")
def preview_database_table(
    table_name: str,
    limit: int = Query(default=50, ge=1, le=100),
    _: DoctorPublic = Depends(require_roles("admin")),
):
    if table_name not in TABLE_DESCRIPTIONS:
        raise HTTPException(status_code=404, detail="Table is not available in the database browser whitelist")

    engine = _engine()
    if engine is None:
        raise HTTPException(status_code=503, detail="CTPATH_DB_URL is not configured; MySQL preview is unavailable")

    with engine.connect() as conn:
        columns = conn.execute(
            text(
                """
                SELECT COLUMN_NAME AS name, DATA_TYPE AS dataType, COLUMN_KEY AS columnKey, IS_NULLABLE AS nullable
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = :table_name
                ORDER BY ORDINAL_POSITION
                """
            ),
            {"table_name": table_name},
        ).mappings().all()
        if not columns:
            raise HTTPException(status_code=404, detail="Table does not exist in the configured MySQL database")

        safe_limit = max(1, min(limit, 100))
        rows = conn.execute(text(f"SELECT * FROM `{table_name}` LIMIT {safe_limit}")).mappings().all()

    return {
        "tableName": table_name,
        "description": TABLE_DESCRIPTIONS[table_name],
        "columns": [dict(column) for column in columns],
        "rows": [{key: _jsonable(value) for key, value in dict(row).items()} for row in rows],
    }
