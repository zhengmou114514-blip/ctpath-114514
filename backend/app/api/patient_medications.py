from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..audit.operation_audit import record_operation_audit
from ..auth.dependencies import get_current_doctor, require_roles
from ..schemas import (
    DoctorPublic,
    MedicationAdequacyAssessment,
    MedicationAssessmentRequest,
    PatientEventCreateRequest,
    PatientMedicationRecord,
    PatientMedicationReviewDecisionRequest,
    PatientMedicationUpsertRequest,
    PharmacyReviewDecisionRequest,
    PharmacyReviewOrder,
)
from ..services.drug_catalog_service import get_drug_catalog_item
from ..services.drug_catalog_service import list_drug_catalog
from ..services.drug_permission_service import get_drug_permission_item
from ..services.medication_assessment_service import assess_patient_medication_adequacy
from ..services.patient_medication_service import (
    create_patient_medication,
    list_patient_medication_reviews,
    list_patient_medications,
    review_patient_medication,
    update_patient_medication,
)
from ..store import add_patient_event, get_patient

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


def _review_order_from_record(record: PatientMedicationRecord) -> PharmacyReviewOrder:
    patient = get_patient(record.patient_id)
    return PharmacyReviewOrder(
        patientId=record.patient_id,
        patientName=patient.name if patient else record.patient_id,
        medicationId=record.medication_id,
        drugId=record.drug_id,
        drugNameSnapshot=record.drug_name_snapshot,
        dosage=record.dosage,
        frequency=record.frequency,
        route=record.route,
        reviewStatus=record.review_status,
        status=record.status,
        prescribedBy=record.prescribed_by,
        note=record.review_note or record.note,
        createdAt=record.created_at,
        updatedAt=record.updated_at,
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


@router.post("/api/patient/{patient_id}/medication-assessment", response_model=MedicationAdequacyAssessment)
def assess_patient_medications(
    patient_id: str,
    payload: MedicationAssessmentRequest,
    current_doctor: object = Depends(get_current_doctor),
) -> MedicationAdequacyAssessment:
    patient = get_patient(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    permission = _resolve_medication_permission(getattr(current_doctor, "role", ""))
    if not permission.allow_view:
        raise HTTPException(status_code=403, detail="Role not allowed to view patient medications")

    return assess_patient_medication_adequacy(
        patient=patient,
        medications=list_patient_medications(patient_id),
        model_advice=payload.modelAdvice,
        drug_catalog=list_drug_catalog(status="active"),
    )


@router.post("/api/patient/{patient_id}/medications", response_model=PatientMedicationRecord, status_code=201)
def create_patient_medication_record(
    patient_id: str,
    payload: PatientMedicationUpsertRequest,
    request: Request,
    current_doctor: object = Depends(get_current_doctor),
) -> PatientMedicationRecord:
    _require_patient(patient_id)
    permission = _resolve_medication_permission(getattr(current_doctor, "role", ""))
    if not (permission.allow_prescribe or permission.allow_review):
        raise HTTPException(status_code=403, detail="Role not allowed to modify patient medications")

    drug = get_drug_catalog_item(payload.drug_id)
    if drug.is_controlled and not permission.allow_controlled_drug:
        raise HTTPException(status_code=403, detail="Controlled drug not allowed for this role")

    record = create_patient_medication(
        patient_id,
        payload,
        prescribed_by=_current_actor_name(current_doctor),
    )
    record_operation_audit(
        operation="create",
        resource_type="patient_medication",
        resource_id=record.medication_id,
        request=request,
        actor=current_doctor,
        patient_id=patient_id,
        extra_detail="drug_id={0}".format(record.drug_id),
    )
    return record


@router.get("/api/patient-medication-reviews", response_model=List[PatientMedicationRecord])
def get_patient_medication_reviews(
    status: Optional[str] = Query(default=None),
    _: DoctorPublic = Depends(require_roles("pharmacist", "admin")),
) -> List[PatientMedicationRecord]:
    return list_patient_medication_reviews(status=status)


@router.get("/api/pharmacy/review-queue", response_model=List[PharmacyReviewOrder])
def get_pharmacy_review_queue(
    status: Optional[str] = Query(default=None),
    _: DoctorPublic = Depends(require_roles("pharmacist", "admin")),
) -> List[PharmacyReviewOrder]:
    return [_review_order_from_record(record) for record in list_patient_medication_reviews(status=status)]


@router.patch(
    "/api/patient-medication-reviews/{patient_id}/{medication_id}",
    response_model=PatientMedicationRecord,
)
def patch_patient_medication_review(
    patient_id: str,
    medication_id: str,
    payload: PatientMedicationReviewDecisionRequest,
    request: Request,
    reviewer: DoctorPublic = Depends(require_roles("pharmacist", "admin")),
) -> PatientMedicationRecord:
    _require_patient(patient_id)
    if payload.review_status not in {"approved", "rejected", "pending"}:
        raise HTTPException(status_code=400, detail="Invalid review status")
    permission = _resolve_medication_permission(getattr(reviewer, "role", ""))
    if not permission.allow_review:
        raise HTTPException(status_code=403, detail="Role not allowed to review patient medications")

    reviewer_name = payload.actorName or reviewer.name or reviewer.username
    record = review_patient_medication(
        patient_id,
        medication_id,
        payload,
        reviewed_by=reviewer_name,
    )
    record_operation_audit(
        operation="review",
        resource_type="patient_medication_review",
        resource_id=record.medication_id,
        request=request,
        actor=reviewer,
        patient_id=patient_id,
        extra_detail="review_status={0}".format(record.review_status),
    )
    add_patient_event(
        patient_id,
        PatientEventCreateRequest(
            eventTime=datetime.now(timezone.utc).date().isoformat(),
            relation="medication_review",
            objectValue=record.review_status,
            note=payload.review_note or "Medication review status updated.",
            source="patient-medication-review",
            actorUsername=payload.actorUsername or reviewer.username,
            actorName=reviewer_name,
        ),
    )
    return record


@router.patch(
    "/api/pharmacy/review-queue/{patient_id}/{medication_id}",
    response_model=PharmacyReviewOrder,
)
def patch_pharmacy_review_queue(
    patient_id: str,
    medication_id: str,
    payload: PharmacyReviewDecisionRequest,
    request: Request,
    reviewer: DoctorPublic = Depends(require_roles("pharmacist", "admin")),
) -> PharmacyReviewOrder:
    record = patch_patient_medication_review(
        patient_id=patient_id,
        medication_id=medication_id,
        payload=PatientMedicationReviewDecisionRequest(
            review_status=payload.reviewStatus,
            review_note=payload.note,
            actorUsername=payload.operatorUsername,
            actorName=payload.operatorName,
        ),
        request=request,
        reviewer=reviewer,
    )
    return _review_order_from_record(record)


@router.put("/api/patient/{patient_id}/medications/{medication_id}", response_model=PatientMedicationRecord)
def update_patient_medication_record(
    patient_id: str,
    medication_id: str,
    payload: PatientMedicationUpsertRequest,
    request: Request,
    current_doctor: object = Depends(get_current_doctor),
) -> PatientMedicationRecord:
    _require_patient(patient_id)
    permission = _resolve_medication_permission(getattr(current_doctor, "role", ""))
    if not (permission.allow_prescribe or permission.allow_review):
        raise HTTPException(status_code=403, detail="Role not allowed to modify patient medications")

    drug = get_drug_catalog_item(payload.drug_id)
    if drug.is_controlled and not permission.allow_controlled_drug:
        raise HTTPException(status_code=403, detail="Controlled drug not allowed for this role")

    record = update_patient_medication(
        patient_id,
        medication_id,
        payload,
        prescribed_by=_current_actor_name(current_doctor),
    )
    record_operation_audit(
        operation="update",
        resource_type="patient_medication",
        resource_id=record.medication_id,
        request=request,
        actor=current_doctor,
        patient_id=patient_id,
        extra_detail="drug_id={0}".format(record.drug_id),
    )
    return record
