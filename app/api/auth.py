from fastapi import APIRouter, Depends, HTTPException, Request

from ..auth.dependencies import get_current_doctor
from ..middleware.jwt_auth import create_access_token
from ..middleware.rate_limit import limiter
from ..schemas import LoginRequest, LoginResponse, RegisterRequest
from ..store import TOKENS, authenticate, register_doctor


router = APIRouter(tags=["auth"])


@router.post("/api/login", response_model=LoginResponse)
@limiter.limit("8/minute")
def login(request: Request, payload: LoginRequest) -> LoginResponse:
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
