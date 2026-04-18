from __future__ import annotations

from typing import Any, Optional

from .system_audit import record_system_audit


def record_operation_audit(
    *,
    action: str,
    result: str,
    path: str,
    method: str,
    actor: Any = None,
    detail: str = "",
    client_ip: Optional[str] = None,
) -> None:
    record_system_audit(
        action=action,
        result=result,
        path=path,
        method=method,
        role=getattr(actor, "role", None),
        username=getattr(actor, "username", None) or getattr(actor, "name", None),
        detail=detail,
        client_ip=client_ip,
    )
