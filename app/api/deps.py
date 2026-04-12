"""Shared API dependencies."""

from typing import Generator

from fastapi import Depends

from .auth import require_doctor
from ..modules.patients.application import PATIENT_APPLICATION_SERVICE, PatientApplicationService


def get_patient_application_service() -> Generator[PatientApplicationService, None, None]:
    yield PATIENT_APPLICATION_SERVICE


def get_current_user(doctor=Depends(require_doctor)):
    return {
        "user_code": doctor.username,
        "user_name": doctor.name,
        "organize_id": getattr(doctor, "department", "") or "default",
        "role": doctor.role,
    }
