from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from ..audit.operation_audit import record_operation_audit
from ..auth.dependencies import require_roles
from ..schemas import PatientAttachmentRecord, PatientAttachmentType
from ..services.patient_attachment_service import (
    create_patient_attachment,
    delete_patient_attachment,
    get_patient_attachment_file,
    list_patient_attachments,
)
from ..store import get_patient


router = APIRouter(tags=["attachments"])


def _require_patient(patient_id: str) -> None:
    if get_patient(patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")


@router.get("/api/patient/{patient_id}/attachments", response_model=List[PatientAttachmentRecord])
def get_patient_attachments(
    patient_id: str,
    _: object = Depends(require_roles("doctor", "nurse", "pharmacist", "archivist", "admin")),
) -> List[PatientAttachmentRecord]:
    _require_patient(patient_id)
    return list_patient_attachments(patient_id)


@router.post("/api/patient/{patient_id}/attachments", response_model=PatientAttachmentRecord)
async def upload_patient_attachment(
    patient_id: str,
    request: Request,
    attachment_type: PatientAttachmentType = Form(..., alias="type"),
    file: UploadFile = File(...),
    current_user: object = Depends(require_roles("doctor", "nurse", "archivist", "admin")),
) -> PatientAttachmentRecord:
    _require_patient(patient_id)
    uploaded_by = getattr(current_user, "name", None) or getattr(current_user, "username", None) or "current-user"
    file_bytes = await file.read()
    record = create_patient_attachment(
        patient_id=patient_id,
        attachment_type=attachment_type,
        file_name=file.filename or "attachment.bin",
        mime_type=file.content_type or "application/octet-stream",
        file_bytes=file_bytes,
        uploaded_by=str(uploaded_by),
    )
    record_operation_audit(
        operation="upload",
        resource_type="patient_attachment",
        resource_id=record.attachmentId,
        request=request,
        actor=current_user,
        patient_id=patient_id,
        extra_detail="type={0}; file_name={1}; file_size={2}".format(record.type, record.fileName, record.fileSize),
    )
    return record


@router.get("/api/patient/{patient_id}/attachments/{attachment_id}/file")
def download_patient_attachment_file(
    patient_id: str,
    attachment_id: str,
    _: object = Depends(require_roles("doctor", "nurse", "pharmacist", "archivist", "admin")),
) -> FileResponse:
    _require_patient(patient_id)
    path, record = get_patient_attachment_file(patient_id, attachment_id)
    return FileResponse(
        path=path,
        filename=str(record.get("fileName") or path.name),
        media_type=str(record.get("mimeType") or "application/octet-stream"),
        content_disposition_type="inline",
    )


@router.delete("/api/patient/{patient_id}/attachments/{attachment_id}", response_model=PatientAttachmentRecord)
def remove_patient_attachment(
    patient_id: str,
    attachment_id: str,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "nurse", "archivist", "admin")),
) -> PatientAttachmentRecord:
    _require_patient(patient_id)
    record = delete_patient_attachment(patient_id, attachment_id)
    record_operation_audit(
        operation="delete",
        resource_type="patient_attachment",
        resource_id=record.attachmentId,
        request=request,
        actor=current_user,
        patient_id=patient_id,
        extra_detail="type={0}; file_name={1}; file_size={2}".format(record.type, record.fileName, record.fileSize),
    )
    return record
