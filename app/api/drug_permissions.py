from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request

from ..audit.operation_audit import record_operation_audit
from ..auth.dependencies import require_roles
from ..schemas import DrugPermissionRecord, DrugPermissionRole, DrugPermissionUpsertRequest
from ..services.drug_permission_service import (
    create_drug_permission_item,
    get_drug_permission_item,
    list_drug_permissions,
    update_drug_permission_item,
)


router = APIRouter(tags=["drug-permissions"])


@router.get("/api/drug-permissions", response_model=List[DrugPermissionRecord])
def get_drug_permissions(
    role: Optional[DrugPermissionRole] = Query(default=None),
    _: object = Depends(require_roles("doctor", "nurse", "archivist", "admin")),
) -> List[DrugPermissionRecord]:
    return list_drug_permissions(role=role)


@router.get("/api/drug-permissions/{role}", response_model=DrugPermissionRecord)
def get_drug_permission(
    role: str,
    _: object = Depends(require_roles("doctor", "nurse", "archivist", "admin")),
) -> DrugPermissionRecord:
    return get_drug_permission_item(role)


@router.post("/api/drug-permissions", response_model=DrugPermissionRecord, status_code=201)
def create_drug_permission(
    payload: DrugPermissionUpsertRequest,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "archivist", "admin")),
) -> DrugPermissionRecord:
    record = create_drug_permission_item(payload)
    record_operation_audit(
        action="drug_permission_create",
        result="success",
        path="/api/drug-permissions",
        method="POST",
        actor=current_user,
        detail="role={0}".format(record.role),
        client_ip=request.client.host if request and request.client else None,
    )
    return record


@router.put("/api/drug-permissions/{role}", response_model=DrugPermissionRecord)
def update_drug_permission(
    role: str,
    payload: DrugPermissionUpsertRequest,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "archivist", "admin")),
) -> DrugPermissionRecord:
    record = update_drug_permission_item(role, payload)
    record_operation_audit(
        action="drug_permission_update",
        result="success",
        path="/api/drug-permissions/{0}".format(role),
        method="PUT",
        actor=current_user,
        detail="role={0}".format(record.role),
        client_ip=request.client.host if request and request.client else None,
    )
    return record
