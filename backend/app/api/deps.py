"""Shared API dependencies."""

from __future__ import annotations

from typing import Generator

from ..auth.dependencies import get_current_doctor, get_current_user, require_doctor, require_roles, require_token
from ..modules.patients.application import PATIENT_APPLICATION_SERVICE, PatientApplicationService


def get_patient_application_service() -> Generator[PatientApplicationService, None, None]:
    yield PATIENT_APPLICATION_SERVICE


__all__ = [
    "get_current_doctor",
    "get_current_user",
    "get_patient_application_service",
    "require_doctor",
    "require_roles",
    "require_token",
]
