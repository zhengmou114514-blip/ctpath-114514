from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from ..schemas import LoginRequest, LoginResponse, RegisterRequest
from ..store import authenticate, get_doctor_by_token, is_token_valid, issue_token, register_doctor


router = APIRouter(tags=["auth"])


def require_token(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.replace("Bearer ", "", 1).strip()
    if not is_token_valid(token):
        raise HTTPException(status_code=401, detail="Invalid token")

    return token


def require_doctor(token: str = Depends(require_token)):
    doctor = get_doctor_by_token(token)
    if doctor is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    return doctor


def require_roles(*allowed_roles: str):
    def dependency(doctor=Depends(require_doctor)):
        if doctor.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Role not allowed for this action")
        return doctor

    return dependency


@router.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    doctor = authenticate(payload.username, payload.password)
    if doctor is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = issue_token(doctor.username)
    return LoginResponse(token=token, doctor=doctor)


@router.post("/api/register", response_model=LoginResponse)
def register(payload: RegisterRequest) -> LoginResponse:
    doctor = register_doctor(payload)
    if doctor is None:
        raise HTTPException(status_code=400, detail="Username already exists")

    token = issue_token(doctor.username)
    return LoginResponse(token=token, doctor=doctor)


@router.get("/api/me")
def me(doctor=Depends(require_doctor)) -> dict:
    return {
        "username": doctor.username,
        "name": doctor.name,
        "title": doctor.title,
        "department": doctor.department,
        "role": doctor.role,
    }
