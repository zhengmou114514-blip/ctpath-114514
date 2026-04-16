from __future__ import annotations

from fastapi import APIRouter, Depends
from typing import List

from .auth import require_roles
from ..audit.system_audit import list_system_audit_logs
from ..schemas import PatientAuditLog, SystemAuditLog, SystemAuditResponse
from ..store import get_patient


router = APIRouter(tags=["audit"])


@router.get("/api/audit/system", response_model=SystemAuditResponse)
def system_audit(limit: int = 50, _: object = Depends(require_roles("doctor", "archivist", "admin"))) -> SystemAuditResponse:
    rows = list_system_audit_logs(limit=limit)
    return SystemAuditResponse(items=[SystemAuditLog(**item) for item in rows])


@router.get("/api/audit/patient/{patient_id}", response_model=List[PatientAuditLog])
def patient_audit(
    patient_id: str,
    _: object = Depends(require_roles("doctor", "archivist", "nurse", "admin")),
):
    patient = get_patient(patient_id)
    if not patient:
        return []
    return list(patient.auditLogs)

