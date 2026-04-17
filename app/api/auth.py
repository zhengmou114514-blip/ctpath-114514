from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from ..middleware.jwt_auth import create_access_token, extract_bearer_token, resolve_doctor_from_token
from ..schemas import LoginRequest, LoginResponse, RegisterRequest
from ..store import TOKENS, authenticate, register_doctor
from .deps import get_current_doctor, require_roles as deps_require_roles


router = APIRouter(tags=["auth"])


def require_token(authorization: Optional[str] = Header(default=None)) -> str:
    try:
        return extract_bearer_token(authorization)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Missing bearer token") from exc


def require_doctor(token: str = Depends(require_token)):
    doctor = resolve_doctor_from_token(token)
    if doctor is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    return doctor


def require_roles(*allowed_roles: str):
    return deps_require_roles(*allowed_roles)


@router.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    doctor = authenticate(payload.username, payload.password)
    if doctor is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(doctor.username, doctor.role)
    TOKENS[token] = doctor.username
    return LoginResponse(token=token, doctor=doctor)


@router.post("/api/register", response_model=LoginResponse)
def register(payload: RegisterRequest) -> LoginResponse:
    doctor = register_doctor(payload)
    if doctor is None:
        raise HTTPException(status_code=400, detail="Username already exists")

    token = create_access_token(doctor.username, doctor.role)
    TOKENS[token] = doctor.username
    return LoginResponse(token=token, doctor=doctor)


@router.get("/api/me")
def me(doctor=Depends(get_current_doctor)) -> dict:
    return {
        "username": doctor.username,
        "name": doctor.name,
        "title": doctor.title,
        "department": doctor.department,
        "role": doctor.role,
    }
