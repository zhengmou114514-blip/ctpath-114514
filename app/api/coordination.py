from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from ..audit.operation_audit import record_operation_audit
from ..auth.dependencies import require_roles
from ..schemas import (
    CoordinationBoardResponse,
    CoordinationCategory,
    CoordinationItem,
    CoordinationItemUpsertRequest,
    CoordinationNoteCreateRequest,
    CoordinationStatus,
    CoordinationStatusUpdateRequest,
)
from ..services.coordination_service import (
    append_coordination_note,
    get_coordination_board,
    get_coordination_item,
    list_coordination_items,
    update_coordination_status,
    upsert_coordination_item,
)


router = APIRouter(tags=["coordination"])


def _actor_name(current_user: object) -> str:
    return getattr(current_user, "name", None) or getattr(current_user, "username", None) or "system"


@router.get("/api/coordination/board", response_model=CoordinationBoardResponse)
def coordination_board(
    status: Optional[CoordinationStatus] = None,
    category: Optional[CoordinationCategory] = None,
    keyword: Optional[str] = None,
    _: object = Depends(require_roles("doctor", "nurse", "pharmacist", "archivist", "admin")),
) -> CoordinationBoardResponse:
    return get_coordination_board(status=status, category=category, keyword=keyword)


@router.get("/api/coordination/items", response_model=List[CoordinationItem])
def coordination_items(
    status: Optional[CoordinationStatus] = None,
    category: Optional[CoordinationCategory] = None,
    keyword: Optional[str] = None,
    _: object = Depends(require_roles("doctor", "nurse", "pharmacist", "archivist", "admin")),
) -> List[CoordinationItem]:
    return list_coordination_items(status=status, category=category, keyword=keyword)


@router.get("/api/coordination/items/{coordination_id}", response_model=CoordinationItem)
def coordination_item(
    coordination_id: str,
    _: object = Depends(require_roles("doctor", "nurse", "pharmacist", "archivist", "admin")),
) -> CoordinationItem:
    return get_coordination_item(coordination_id)


@router.post("/api/coordination/items", response_model=CoordinationItem, status_code=201)
def create_coordination_item(
    payload: CoordinationItemUpsertRequest,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "nurse", "pharmacist", "archivist", "admin")),
) -> CoordinationItem:
    record = upsert_coordination_item(
        payload,
        operator_username=getattr(current_user, "username", ""),
        operator_name=_actor_name(current_user),
        operator_role=str(getattr(current_user, "role", "") or "doctor"),
    )
    record_operation_audit(
        operation="create",
        resource_type="coordination_item",
        resource_id=record.coordinationId,
        request=request,
        actor=current_user,
        patient_id=record.patientId,
        extra_detail="category={0}; status={1}".format(record.category, record.status),
    )
    return record


@router.put("/api/coordination/items/{coordination_id}", response_model=CoordinationItem)
def update_coordination_item(
    coordination_id: str,
    payload: CoordinationItemUpsertRequest,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "nurse", "pharmacist", "archivist", "admin")),
) -> CoordinationItem:
    if payload.coordinationId.strip() != coordination_id.strip():
        raise HTTPException(status_code=400, detail="coordinationId does not match path parameter")
    record = upsert_coordination_item(
        payload,
        operator_username=getattr(current_user, "username", ""),
        operator_name=_actor_name(current_user),
        operator_role=str(getattr(current_user, "role", "") or "doctor"),
    )
    record_operation_audit(
        operation="update",
        resource_type="coordination_item",
        resource_id=record.coordinationId,
        request=request,
        actor=current_user,
        patient_id=record.patientId,
        extra_detail="category={0}; status={1}".format(record.category, record.status),
    )
    return record


@router.patch("/api/coordination/items/{coordination_id}/status", response_model=CoordinationItem)
def update_coordination_item_status(
    coordination_id: str,
    payload: CoordinationStatusUpdateRequest,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "nurse", "pharmacist", "archivist", "admin")),
) -> CoordinationItem:
    record = update_coordination_status(coordination_id, payload)
    record_operation_audit(
        operation="status",
        resource_type="coordination_item",
        resource_id=record.coordinationId,
        request=request,
        actor=current_user,
        patient_id=record.patientId,
        extra_detail="status={0}".format(record.status),
    )
    return record


@router.post("/api/coordination/items/{coordination_id}/notes", response_model=CoordinationItem)
def append_coordination_item_note(
    coordination_id: str,
    payload: CoordinationNoteCreateRequest,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "nurse", "pharmacist", "archivist", "admin")),
) -> CoordinationItem:
    record = append_coordination_note(coordination_id, payload)
    record_operation_audit(
        operation="note",
        resource_type="coordination_item",
        resource_id=record.coordinationId,
        request=request,
        actor=current_user,
        patient_id=record.patientId,
        extra_detail="action={0}".format(payload.action),
    )
    return record
