from __future__ import annotations

import os
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional

try:
    from sqlalchemy import create_engine, text
except Exception:  # pragma: no cover
    create_engine = None
    text = None


_SYSTEM_AUDIT_MAX = 500
_SYSTEM_AUDIT_LOGS: Deque[Dict[str, object]] = deque(maxlen=_SYSTEM_AUDIT_MAX)
_DB_URL = os.getenv("CTPATH_DB_URL", "")
_AUDIT_ENGINE = None


def _audit_engine():
    global _AUDIT_ENGINE
    if _AUDIT_ENGINE is not None:
        return _AUDIT_ENGINE
    if not _DB_URL or not create_engine:
        return None
    try:
        _AUDIT_ENGINE = create_engine(_DB_URL, pool_pre_ping=True, future=True)
    except Exception:
        _AUDIT_ENGINE = None
    return _AUDIT_ENGINE


def _persist_system_audit(record: Dict[str, object]) -> None:
    engine = _audit_engine()
    if engine is None or not text:
        return

    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO system_audit_logs (
                      log_id, action, result, role, username, path, method, detail, client_ip
                    ) VALUES (
                      :log_id, :action, :result, :role, :username, :path, :method, :detail, :client_ip
                    )
                    """
                ),
                {
                    "log_id": record["logId"],
                    "action": record["action"],
                    "result": record["result"],
                    "role": record["role"],
                    "username": record["username"],
                    "path": record["path"],
                    "method": record["method"],
                    "detail": record["detail"],
                    "client_ip": record["clientIp"],
                },
            )
    except Exception:
        return


def record_system_audit(
    *,
    action: str,
    result: str,
    path: str,
    method: str,
    role: Optional[str] = None,
    username: Optional[str] = None,
    detail: str = "",
    client_ip: Optional[str] = None,
) -> None:
    record = {
        "logId": "sys-{0}".format(int(datetime.now(timezone.utc).timestamp() * 1000)),
        "action": action,
        "result": result,
        "role": role,
        "username": username,
        "path": path,
        "method": method,
        "detail": detail,
        "clientIp": client_ip,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    _SYSTEM_AUDIT_LOGS.appendleft(record)
    _persist_system_audit(record)


def list_system_audit_logs(limit: int = 50) -> List[Dict[str, object]]:
    limit = max(1, min(int(limit or 50), 200))
    engine = _audit_engine()
    if engine is None or not text:
        return list(_SYSTEM_AUDIT_LOGS)[:limit]

    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT
                      log_id AS logId,
                      action,
                      result,
                      role,
                      username,
                      path,
                      method,
                      detail,
                      client_ip AS clientIp,
                      DATE_FORMAT(created_at, '%Y-%m-%dT%H:%i:%s') AS createdAt
                    FROM system_audit_logs
                    ORDER BY created_at DESC, log_id DESC
                    LIMIT :limit_value
                    """
                ),
                {"limit_value": limit},
            ).mappings().all()
        return [dict(row) for row in rows]
    except Exception:
        return list(_SYSTEM_AUDIT_LOGS)[:limit]
