from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

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
