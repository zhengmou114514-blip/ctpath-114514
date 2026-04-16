"""
Auth state middleware.

Populate request.state with authenticated user context so that RBAC middleware
can enforce permissions consistently.
"""

from __future__ import annotations

from typing import Callable, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..store import get_doctor_by_token


class AuthStateMiddleware(BaseHTTPMiddleware):
    """
    Resolve Bearer token into user context.

    - If Authorization: Bearer <token> is present and valid, set:
      - request.state.user_role
      - request.state.user (DoctorPublic)
    """

    async def dispatch(self, request: Request, call_next: Callable):
        authorization = request.headers.get("Authorization") or ""
        token: Optional[str] = None
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "", 1).strip() or None

        if token:
            doctor = get_doctor_by_token(token)
            if doctor is not None:
                request.state.user_role = doctor.role
                request.state.user = doctor

        return await call_next(request)

