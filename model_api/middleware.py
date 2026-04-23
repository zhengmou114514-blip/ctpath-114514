from __future__ import annotations

import logging
import time
from typing import Callable
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)
TRACE_ID_HEADER_NAMES = ("x-trace-id", "x-request-id")


def get_trace_id(request: Request) -> str:
    trace_id = getattr(request.state, "trace_id", None)
    if trace_id:
        return str(trace_id)
    return uuid4().hex


def rate_limit_key(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is not None:
        username = user.get("username")
        if username:
            return f"user:{username}"
    if request.client and request.client.host:
        return f"ip:{request.client.host}"
    return "ip:unknown"


limiter = Limiter(key_func=rate_limit_key)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    trace_id = get_trace_id(request)
    retry_after = getattr(exc, "retry_after", None)
    headers = {"X-Trace-Id": trace_id}
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Too many requests",
            "error_code": "RATE_LIMITED",
            "trace_id": trace_id,
        },
        headers=headers,
    )


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        trace_id = None
        for header_name in TRACE_ID_HEADER_NAMES:
            candidate = request.headers.get(header_name)
            if candidate:
                trace_id = candidate.strip()
                break

        request.state.trace_id = trace_id or uuid4().hex
        response = await call_next(request)
        response.headers["X-Trace-Id"] = request.state.trace_id
        return response


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            return await call_next(request)
        except Exception:  # pragma: no cover - runtime safety path
            trace_id = get_trace_id(request)
            logger.exception("Unhandled model-api exception trace_id=%s path=%s", trace_id, request.url.path)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "trace_id": trace_id,
                },
                headers={"X-Trace-Id": trace_id},
            )


class ModelAuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        authorization = request.headers.get("authorization")
        user = None
        if authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
            if token:
                from .store import get_user_by_token

                user = get_user_by_token(token)

        request.state.user = user
        return await call_next(request)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        trace_id = get_trace_id(request)
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        logger.info(
            "model-api request trace_id=%s method=%s path=%s status=%s elapsed_ms=%.2f",
            trace_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
