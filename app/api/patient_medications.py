from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_current_doctor
from ..schemas import PatientMedicationRecord, PatientMedicationUpsertRequest
from ..services.drug_catalog_service import get_drug_catalog_item
from ..services.drug_permission_service import get_drug_permission_item
from ..services.patient_medication_service import (
    create_patient_medication,
    list_patient_medications,
    update_patient_medication,
)
from ..store import get_patient

router = APIRouter(tags=["patient-medications"])


def _require_patient(patient_id: str) -> None:
    if get_patient(patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")


def _resolve_medication_permission(role: str):
    permission = get_drug_permission_item(role)
    if permission is None:
        raise HTTPException(status_code=403, detail="Medication permission not configured")
    return permission


def _current_actor_name(current_doctor: object) -> str:
    return (
        getattr(current_doctor, "name", None)
        or getattr(current_doctor, "username", None)
        or "current-user"
    )


@router.get("/api/patient/{patient_id}/medications", response_model=List[PatientMedicationRecord])
def get_patient_medications(
    patient_id: str,
    current_doctor: object = Depends(get_current_doctor),
) -> List[PatientMedicationRecord]:
    _require_patient(patient_id)
    permission = _resolve_medication_permission(getattr(current_doctor, "role", ""))
    if not permission.allow_view:
        raise HTTPException(status_code=403, detail="Role not allowed to view patient medications")
    return list_patient_medications(patient_id)


@router.post("/api/patient/{patient_id}/medications", response_model=PatientMedicationRecord, status_code=201)
def create_patient_medication_record(
    patient_id: str,
    payload: PatientMedicationUpsertRequest,
    current_doctor: object = Depends(get_current_doctor),
) -> PatientMedicationRecord:
    _require_patient(patient_id)
    permission = _resolve_medication_permission(getattr(current_doctor, "role", ""))
    if not (permission.allow_prescribe or permission.allow_review):
        raise HTTPException(status_code=403, detail="Role not allowed to modify patient medications")

    drug = get_drug_catalog_item(payload.drug_id)
    if drug.is_controlled and not permission.allow_controlled_drug:
        raise HTTPException(status_code=403, detail="Controlled drug not allowed for this role")

    return create_patient_medication(
        patient_id,
        payload,
        prescribed_by=_current_actor_name(current_doctor),
    )


@router.put("/api/patient/{patient_id}/medications/{medication_id}", response_model=PatientMedicationRecord)
def update_patient_medication_record(
    patient_id: str,
    medication_id: str,
    payload: PatientMedicationUpsertRequest,
    current_doctor: object = Depends(get_current_doctor),
) -> PatientMedicationRecord:
    _require_patient(patient_id)
    permission = _resolve_medication_permission(getattr(current_doctor, "role", ""))
    if not (permission.allow_prescribe or permission.allow_review):
        raise HTTPException(status_code=403, detail="Role not allowed to modify patient medications")

    drug = get_drug_catalog_item(payload.drug_id)
    if drug.is_controlled and not permission.allow_controlled_drug:
        raise HTTPException(status_code=403, detail="Controlled drug not allowed for this role")

    return update_patient_medication(
        patient_id,
        medication_id,
        payload,
        prescribed_by=_current_actor_name(current_doctor),
    )
