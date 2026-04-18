from __future__ import annotations

from typing import Any, Optional

from fastapi import Request

from ..middleware.trace_id import get_trace_id
from .system_audit import record_system_audit


def record_operation_audit(
    *,
    operation: str,
    resource_type: str,
    resource_id: str,
    request: Request,
    actor: Any = None,
    result: str = "success",
    patient_id: Optional[str] = None,
    extra_detail: str = "",
) -> None:
    trace_id = get_trace_id(request)
    detail_parts = [
        "operation={0}".format(operation),
        "resource_type={0}".format(resource_type),
        "resource_id={0}".format(resource_id),
        "trace_id={0}".format(trace_id),
    ]
    if patient_id:
        detail_parts.append("patient_id={0}".format(patient_id))
    if extra_detail:
        detail_parts.append("detail={0}".format(extra_detail))

    record_system_audit(
        action="{0}_{1}".format(resource_type, operation),
        result=result,
        path=request.url.path,
        method=request.method,
        role=getattr(actor, "role", None),
        username=getattr(actor, "username", None) or getattr(actor, "name", None),
        detail="; ".join(detail_parts),
        client_ip=request.client.host if request.client else None,
    )
