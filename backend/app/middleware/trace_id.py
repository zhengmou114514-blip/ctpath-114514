from __future__ import annotations

from typing import Callable
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


TRACE_ID_HEADER_NAMES = ("x-trace-id", "x-request-id")


def get_trace_id(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    if trace_id:
        return str(trace_id)
    return uuid4().hex


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        trace_id = None
        for header_name in TRACE_ID_HEADER_NAMES:
            candidate = request.headers.get(header_name)
            if candidate:
                trace_id = candidate.strip()
                break

        if not trace_id:
            trace_id = uuid4().hex

        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response

