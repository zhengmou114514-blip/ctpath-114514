from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Callable, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from .jwt_auth import is_protected_path
from .trace_id import get_trace_id


def rate_limit_key(request: Request) -> str:
    if getattr(request.state, "user", None) is not None:
        user = request.state.user
        username = getattr(user, "username", None) or getattr(user, "name", None)
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


@dataclass(frozen=True)
class RateLimitRule:
    limit: int
    period_seconds: int


DEFAULT_RULE = RateLimitRule(limit=120, period_seconds=60)
LOGIN_RULE = RateLimitRule(limit=8, period_seconds=60)
MODEL_RULE = RateLimitRule(limit=20, period_seconds=60)
UPLOAD_RULE = RateLimitRule(limit=12, period_seconds=60)


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def consume(self, key: str, rule: RateLimitRule) -> tuple[bool, int]:
        now = monotonic()
        with self._lock:
            bucket = self._buckets[key]
            while bucket and now - bucket[0] >= rule.period_seconds:
                bucket.popleft()

            if len(bucket) >= rule.limit:
                retry_after = max(1, int(rule.period_seconds - (now - bucket[0]))) if bucket else rule.period_seconds
                return False, retry_after

            bucket.append(now)
            if not bucket:
                self._buckets.pop(key, None)
            return True, 0


RATE_LIMITER = InMemoryRateLimiter()


def _client_identifier(request: Request) -> str:
    if getattr(request.state, "user", None) is not None:
        user = request.state.user
        username = getattr(user, "username", None) or getattr(user, "name", None)
        if username:
            return f"user:{username}"
    if request.client and request.client.host:
        return f"ip:{request.client.host}"
    return "ip:unknown"


def _match_rule(path: str) -> Optional[RateLimitRule]:
    if path.startswith("/api/login") or path.startswith("/api/register"):
        return LOGIN_RULE
    if path.startswith("/api/predict") or path.startswith("/api/advice"):
        return MODEL_RULE
    if path.startswith("/api/upload"):
        return UPLOAD_RULE
    if path.startswith("/api/") or is_protected_path(path):
        return DEFAULT_RULE
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        rule = _match_rule(request.url.path)
        if rule is None:
            return await call_next(request)

        trace_id = get_trace_id(request)
        key = f"{request.method}:{request.url.path}:{_client_identifier(request)}"
        allowed, retry_after = RATE_LIMITER.consume(key, rule)
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "error_code": "RATE_LIMITED",
                    "retry_after": retry_after,
                    "trace_id": trace_id,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-Trace-Id": trace_id,
                },
            )

        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response
