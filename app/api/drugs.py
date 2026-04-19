from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..auth.dependencies import require_roles
from ..audit.operation_audit import record_operation_audit
from ..schemas import DrugCatalogRecord, DrugCatalogStatus, DrugCatalogUpsertRequest
from ..services.drug_catalog_service import (
    create_drug_catalog_item,
    get_drug_catalog_item,
    list_drug_catalog,
    update_drug_catalog_item,
)
from ..services.drug_permission_service import role_allows_controlled_drug


router = APIRouter(tags=["drugs"])


def _actor_name(current_user: object) -> str:
    return getattr(current_user, "name", None) or getattr(current_user, "username", None) or "system"


def _actor_role(current_user: object) -> str:
    return str(getattr(current_user, "role", "") or "").strip()


def _enforce_controlled_drug_permission(current_user: object, *, touches_controlled_drug: bool) -> None:
    if not touches_controlled_drug:
        return
    if not role_allows_controlled_drug(_actor_role(current_user)):
        raise HTTPException(status_code=403, detail="Controlled drug permission is required for this action")


@router.get("/api/drugs", response_model=List[DrugCatalogRecord])
def get_drug_catalog(
    keyword: Optional[str] = Query(default=None),
    status: Optional[DrugCatalogStatus] = Query(default=None),
    dosage_form: Optional[str] = Query(default=None),
    is_prescription: Optional[bool] = Query(default=None),
    is_controlled: Optional[bool] = Query(default=None),
    _: object = Depends(require_roles("doctor", "archivist")),
) -> List[DrugCatalogRecord]:
    return list_drug_catalog(
        keyword=keyword,
        status=status,
        dosage_form=dosage_form,
        is_prescription=is_prescription,
        is_controlled=is_controlled,
    )


@router.get("/api/drugs/{drug_id}", response_model=DrugCatalogRecord)
def get_drug_catalog_detail(
    drug_id: str,
    _: object = Depends(require_roles("doctor", "archivist")),
) -> DrugCatalogRecord:
    return get_drug_catalog_item(drug_id)


@router.post("/api/drugs", response_model=DrugCatalogRecord, status_code=201)
def create_drug_catalog(
    payload: DrugCatalogUpsertRequest,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "archivist")),
) -> DrugCatalogRecord:
    _enforce_controlled_drug_permission(current_user, touches_controlled_drug=payload.is_controlled)
    updated_by = _actor_name(current_user)
    record = create_drug_catalog_item(payload, updated_by=str(updated_by))
    record_operation_audit(
        operation="create",
        resource_type="drug_catalog",
        resource_id=record.drug_id,
        request=request,
        actor=current_user,
        extra_detail="is_controlled={0}".format(record.is_controlled),
    )
    return record


@router.put("/api/drugs/{drug_id}", response_model=DrugCatalogRecord)
def update_drug_catalog(
    drug_id: str,
    payload: DrugCatalogUpsertRequest,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "archivist")),
) -> DrugCatalogRecord:
    current_record = get_drug_catalog_item(drug_id)
    _enforce_controlled_drug_permission(
        current_user,
        touches_controlled_drug=payload.is_controlled or current_record.is_controlled,
    )
    updated_by = _actor_name(current_user)
    record = update_drug_catalog_item(drug_id, payload, updated_by=str(updated_by))
    record_operation_audit(
        operation="update",
        resource_type="drug_catalog",
        resource_id=record.drug_id,
        request=request,
        actor=current_user,
        extra_detail="is_controlled={0}".format(record.is_controlled),
    )
    return record
