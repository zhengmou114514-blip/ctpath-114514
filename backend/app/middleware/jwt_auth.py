from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..schemas import DoctorPublic
from ..store import TOKENS, get_doctor, get_doctor_by_token
from .trace_id import get_trace_id


logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("CTPATH_JWT_SECRET", "ctpath-dev-secret")
JWT_ISSUER = "ctpath"
JWT_AUDIENCE = "ctpath-chronic-disease-api"
JWT_EXPIRES_SECONDS = int(os.getenv("CTPATH_JWT_EXPIRES_SECONDS", "43200"))

PUBLIC_PATHS = {
    "/",
    "/api/health",
    "/api/login",
    "/api/register",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/metrics",
}

PROTECTED_PREFIXES = (
    "/api/advice",
    "/api/audit",
    "/api/authz",
    "/api/governance",
    "/api/maintenance",
    "/api/model",
    "/api/patient",
    "/api/patients",
    "/api/predict",
    "/api/timeline",
    "/api/upload",
    "/api/v1/patients",
    "/api/worklists",
)


class JWTError(ValueError):
    pass


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign(message: bytes) -> str:
    digest = hmac.new(JWT_SECRET.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(digest)


def create_access_token(username: str, role: str, *, expires_seconds: int = JWT_EXPIRES_SECONDS) -> str:
    now = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + max(60, expires_seconds),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "jti": uuid4().hex,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64url_encode(json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = _sign(signing_input)
    return f"{encoded_header}.{encoded_payload}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise JWTError("Token is not a JWT")

    encoded_header, encoded_payload, signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    expected_signature = _sign(signing_input)
    if not hmac.compare_digest(signature, expected_signature):
        raise JWTError("Invalid token signature")

    try:
        payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive decode path
        raise JWTError("Invalid token payload") from exc

    now = int(datetime.now(timezone.utc).timestamp())
    if payload.get("iss") != JWT_ISSUER:
        raise JWTError("Invalid token issuer")
    if payload.get("aud") != JWT_AUDIENCE:
        raise JWTError("Invalid token audience")
    if int(payload.get("exp", 0)) < now:
        raise JWTError("Token expired")
    if not payload.get("sub"):
        raise JWTError("Missing subject")
    return payload


def extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise JWTError("Missing bearer token")
    token = authorization.replace("Bearer ", "", 1).strip()
    if not token:
        raise JWTError("Missing bearer token")
    return token


def resolve_doctor_from_token(token: str) -> Optional[DoctorPublic]:
    try:
        payload = decode_access_token(token)
    except JWTError:
        legacy_doctor = get_doctor_by_token(token)
        return legacy_doctor

    username = str(payload.get("sub") or "").strip()
    if not username:
        return None
    doctor = get_doctor(username)
    if doctor is None:
        return None
    return doctor


def is_public_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    if path.startswith("/docs") or path.startswith("/redoc"):
        return True
    return False


def is_protected_path(path: str) -> bool:
    return path.startswith(PROTECTED_PREFIXES)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        authorization = request.headers.get("Authorization")

        if authorization:
            try:
                token = extract_bearer_token(authorization)
                doctor = resolve_doctor_from_token(token)
            except JWTError:
                if is_protected_path(path) and not is_public_path(path):
                    trace_id = get_trace_id(request)
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "detail": "Invalid token",
                            "error_code": "UNAUTHORIZED",
                            "trace_id": trace_id,
                        },
                        headers={
                            "WWW-Authenticate": "Bearer",
                            "X-Trace-Id": trace_id,
                        },
                    )
                doctor = None

            if doctor is not None:
                request.state.user = doctor
                request.state.user_role = doctor.role

        if is_protected_path(path) and not is_public_path(path):
            if not getattr(request.state, "user", None):
                trace_id = get_trace_id(request)
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Missing bearer token",
                        "error_code": "UNAUTHORIZED",
                        "trace_id": trace_id,
                    },
                    headers={
                        "WWW-Authenticate": "Bearer",
                        "X-Trace-Id": trace_id,
                    },
                )

        return await call_next(request)

