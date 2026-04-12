"""Compatibility controller that keeps an openhis-like response envelope."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ...api.auth import require_doctor
from ...modules.patients.application import PATIENT_APPLICATION_SERVICE


router = APIRouter(prefix="/api/v1/patients", tags=["patients-v1"])


@router.get("")
def get_patient_list(
    status: str = Query("waiting"),
    keyword: Optional[str] = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    _: object = Depends(require_doctor),
):
    result = PATIENT_APPLICATION_SERVICE.paginate_patients(
        page=page,
        page_size=page_size,
        search=keyword,
    )

    rows = []
    for item in result.items:
        patient = PATIENT_APPLICATION_SERVICE.get_patient_case(item.patientId)
        if patient is None:
            continue
        if status and patient.encounterStatus != status:
            continue
        rows.append(patient.model_dump())

    return {
        "code": 200,
        "msg": "success",
        "data": {
            "rows": rows,
            "page": page,
            "pageSize": page_size,
            "total": result.total,
        },
    }


@router.get("/{patient_id}")
def get_patient_detail(patient_id: str, _: object = Depends(require_doctor)):
    patient = PATIENT_APPLICATION_SERVICE.get_patient_case(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "code": 200,
        "msg": "success",
        "data": patient.model_dump(),
    }
