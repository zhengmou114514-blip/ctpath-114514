from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .middleware.trace_id import get_trace_id


def error_response(
    *,
    request: Request,
    status_code: int,
    detail: Any,
    error_code: str,
    headers: Optional[Dict[str, str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    trace_id = get_trace_id(request)
    content: Dict[str, Any] = {
        "detail": detail,
        "error_code": error_code,
        "trace_id": trace_id,
    }
    if extra:
        content.update(extra)

    response_headers = dict(headers or {})
    response_headers["X-Trace-Id"] = trace_id
    return JSONResponse(status_code=status_code, content=content, headers=response_headers)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return error_response(
        request=request,
        status_code=exc.status_code,
        detail=exc.detail,
        error_code="HTTP_{0}".format(exc.status_code),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(
        request=request,
        status_code=422,
        detail="Request validation failed",
        error_code="VALIDATION_ERROR",
        extra={"errors": exc.errors()},
    )
