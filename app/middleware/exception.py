from __future__ import annotations

import logging
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .trace_id import get_trace_id


logger = logging.getLogger(__name__)


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            return await call_next(request)
        except Exception as exc:  # pragma: no cover - exercised in runtime safety path
            trace_id = get_trace_id(request)
            logger.exception("Unhandled API exception trace_id=%s path=%s", trace_id, request.url.path)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "trace_id": trace_id,
                },
                headers={"X-Trace-Id": trace_id},
            )

