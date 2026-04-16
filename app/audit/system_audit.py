from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional


_SYSTEM_AUDIT_MAX = 500
_SYSTEM_AUDIT_LOGS: Deque[Dict[str, object]] = deque(maxlen=_SYSTEM_AUDIT_MAX)


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
    _SYSTEM_AUDIT_LOGS.appendleft(
        {
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
    )


def list_system_audit_logs(limit: int = 50) -> List[Dict[str, object]]:
    limit = max(1, min(int(limit or 50), 200))
    return list(_SYSTEM_AUDIT_LOGS)[:limit]

