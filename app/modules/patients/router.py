from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ...api.auth import require_doctor, require_roles
from ...schemas import (
    ContactLogCreateRequest,
    EncounterStatusUpdateRequest,
    MedicationPlanGenerateRequest,
    MedicationPlanResponse,
    OutpatientTaskCreateRequest,
    OutpatientTaskStatusUpdateRequest,
    PatientCase,
    PatientEventCreateRequest,
    PatientSummary,
    PatientUpsertRequest,
    QuadrupleResponse,
    TimelineResponse,
)
from .application import PATIENT_APPLICATION_SERVICE


router = APIRouter(tags=["patients"])


@router.get("/api/patients", response_model=List[PatientSummary])
def list_patients(_: object = Depends(require_doctor)) -> List[PatientSummary]:
    return PATIENT_APPLICATION_SERVICE.list_patients()


@router.get("/api/patients/paginated")
def paginate_patients_legacy(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    disease: Optional[str] = Query(default=None),
    _: object = Depends(require_doctor),
) -> dict:
    result = PATIENT_APPLICATION_SERVICE.paginate_patients(
        page=page,
        page_size=page_size,
        search=search,
        risk_level=risk_level,
        disease=disease,
    )
    return result.to_legacy_payload()


@router.get("/api/patient/{patient_id}", response_model=PatientCase)
def get_patient_case(patient_id: str, _: object = Depends(require_doctor)) -> PatientCase:
    patient = PATIENT_APPLICATION_SERVICE.get_patient_case(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("/api/patient", response_model=PatientCase)
def create_patient(
    payload: PatientUpsertRequest,
    _: object = Depends(require_roles("doctor", "archivist")),
) -> PatientCase:
    patient = PATIENT_APPLICATION_SERVICE.create_patient(payload)
    if patient is None:
        raise HTTPException(status_code=500, detail="Unable to save patient")
    return patient


@router.put("/api/patient/{patient_id}", response_model=PatientCase)
def update_patient(
    patient_id: str,
    payload: PatientUpsertRequest,
    _: object = Depends(require_roles("doctor", "archivist")),
) -> PatientCase:
    patient = PATIENT_APPLICATION_SERVICE.update_patient(patient_id, payload)
    if patient is None:
        raise HTTPException(status_code=500, detail="Unable to update patient")
    return patient


@router.post("/api/patient/{patient_id}/event", response_model=PatientCase)
def create_patient_event(
    patient_id: str,
    payload: PatientEventCreateRequest,
    _: object = Depends(require_roles("doctor")),
) -> PatientCase:
    patient = PATIENT_APPLICATION_SERVICE.create_patient_event(patient_id, payload)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("/api/patient/{patient_id}/contact-log", response_model=PatientCase)
def create_contact_log(
    patient_id: str,
    payload: ContactLogCreateRequest,
    _: object = Depends(require_roles("doctor", "nurse")),
) -> PatientCase:
    patient = PATIENT_APPLICATION_SERVICE.create_contact_log(patient_id, payload)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.patch("/api/patient/{patient_id}/encounter-status", response_model=PatientCase)
def patch_encounter_status(
    patient_id: str,
    payload: EncounterStatusUpdateRequest,
    _: object = Depends(require_roles("doctor", "nurse")),
) -> PatientCase:
    patient = PATIENT_APPLICATION_SERVICE.update_encounter_status(patient_id, payload)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("/api/patient/{patient_id}/outpatient-task", response_model=PatientCase)
def create_outpatient_task(
    patient_id: str,
    payload: OutpatientTaskCreateRequest,
    _: object = Depends(require_roles("doctor")),
) -> PatientCase:
    patient = PATIENT_APPLICATION_SERVICE.create_outpatient_task(patient_id, payload)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.patch("/api/patient/{patient_id}/outpatient-task/{task_id}", response_model=PatientCase)
def patch_outpatient_task_status(
    patient_id: str,
    task_id: str,
    payload: OutpatientTaskStatusUpdateRequest,
    _: object = Depends(require_roles("doctor", "nurse")),
) -> PatientCase:
    patient = PATIENT_APPLICATION_SERVICE.update_outpatient_task_status(patient_id, task_id, payload)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient or task not found")
    return patient


@router.post("/api/patient/{patient_id}/medication-plan/generate", response_model=MedicationPlanResponse)
def generate_medication_plan(
    patient_id: str,
    payload: MedicationPlanGenerateRequest,
    _: object = Depends(require_roles("doctor", "nurse")),
) -> MedicationPlanResponse:
    plan = PATIENT_APPLICATION_SERVICE.generate_medication_plan(patient_id, payload)
    if plan is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return plan


@router.get("/api/timeline/{patient_id}", response_model=TimelineResponse)
def get_patient_timeline(patient_id: str, _: object = Depends(require_doctor)) -> TimelineResponse:
    timeline = PATIENT_APPLICATION_SERVICE.get_timeline(patient_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return timeline


@router.get("/api/patient/{patient_id}/quadruples", response_model=QuadrupleResponse)
def get_patient_quadruples(patient_id: str, _: object = Depends(require_doctor)) -> QuadrupleResponse:
    quadruples = PATIENT_APPLICATION_SERVICE.get_quadruples(patient_id)
    if quadruples is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return quadruples


@router.get("/api/v2/patients/stats/overview")
def get_patient_stats(_: object = Depends(require_doctor)) -> dict:
    return PATIENT_APPLICATION_SERVICE.get_stats_overview()


@router.get("/api/v2/patients")
def paginate_patients_v2(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default=None),
    sort_order: str = Query("desc"),
    _: object = Depends(require_doctor),
) -> dict:
    result = PATIENT_APPLICATION_SERVICE.paginate_patients(
        page=page,
        page_size=page_size,
        search=search,
        risk_level=risk_level,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return result.to_v2_payload()


@router.get("/api/v2/patients/{patient_id}", response_model=PatientCase)
def get_patient_case_v2(patient_id: str, _: object = Depends(require_doctor)) -> PatientCase:
    patient = PATIENT_APPLICATION_SERVICE.get_patient_case(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
