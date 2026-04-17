"""Shared API dependencies."""

from __future__ import annotations

from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from ..modules.patients.application import PATIENT_APPLICATION_SERVICE, PatientApplicationService
from ..schemas import DoctorPublic
from ..middleware.jwt_auth import extract_bearer_token, resolve_doctor_from_token


def get_patient_application_service() -> Generator[PatientApplicationService, None, None]:
    yield PATIENT_APPLICATION_SERVICE


def get_bearer_token(authorization: Optional[str] = Header(default=None)) -> str:
    try:
        return extract_bearer_token(authorization)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token") from exc


def get_current_doctor(
    request: Request,
    token: str = Depends(get_bearer_token),
) -> DoctorPublic:
    cached_user = getattr(request.state, "user", None)
    if isinstance(cached_user, DoctorPublic):
        return cached_user

    doctor = resolve_doctor_from_token(token)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    request.state.user = doctor
    request.state.user_role = doctor.role
    return doctor


def get_current_user(doctor: DoctorPublic = Depends(get_current_doctor)):
    return {
        "user_code": doctor.username,
        "user_name": doctor.name,
        "organize_id": getattr(doctor, "department", "") or "default",
        "role": doctor.role,
    }


def require_roles(*allowed_roles: str):
    def dependency(doctor: DoctorPublic = Depends(get_current_doctor)):
        if doctor.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role not allowed for this action")
        return doctor

    return dependency
