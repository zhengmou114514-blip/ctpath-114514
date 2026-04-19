from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..audit.operation_audit import record_operation_audit
from ..auth.dependencies import require_roles
from ..schemas import DrugPermissionRecord, DrugPermissionRole, DrugPermissionUpsertRequest
from ..services.drug_permission_service import (
    create_drug_permission_item,
    get_drug_permission_item,
    list_drug_permissions,
    role_allows_controlled_drug,
    update_drug_permission_item,
)


router = APIRouter(tags=["drug-permissions"])


def _actor_role(current_user: object) -> str:
    return str(getattr(current_user, "role", "") or "").strip()


def _enforce_controlled_permission_grant(current_user: object, payload: DrugPermissionUpsertRequest) -> None:
    if not payload.allow_controlled_drug:
        return
    if not role_allows_controlled_drug(_actor_role(current_user)):
        raise HTTPException(status_code=403, detail="Controlled drug permission is required to grant this capability")


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
    _enforce_controlled_permission_grant(current_user, payload)
    record = create_drug_permission_item(payload)
    record_operation_audit(
        operation="create",
        resource_type="drug_permission",
        resource_id=record.role,
        request=request,
        actor=current_user,
        extra_detail="allow_controlled_drug={0}".format(record.allow_controlled_drug),
    )
    return record


@router.put("/api/drug-permissions/{role}", response_model=DrugPermissionRecord)
def update_drug_permission(
    role: str,
    payload: DrugPermissionUpsertRequest,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "archivist", "admin")),
) -> DrugPermissionRecord:
    _enforce_controlled_permission_grant(current_user, payload)
    record = update_drug_permission_item(role, payload)
    record_operation_audit(
        operation="update",
        resource_type="drug_permission",
        resource_id=record.role,
        request=request,
        actor=current_user,
        extra_detail="allow_controlled_drug={0}".format(record.allow_controlled_drug),
    )
    return record
