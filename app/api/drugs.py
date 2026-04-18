from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request

from ..auth.dependencies import require_roles
from ..audit.operation_audit import record_operation_audit
from ..schemas import DrugCatalogRecord, DrugCatalogStatus, DrugCatalogUpsertRequest
from ..services.drug_catalog_service import (
    create_drug_catalog_item,
    get_drug_catalog_item,
    list_drug_catalog,
    update_drug_catalog_item,
)


router = APIRouter(tags=["drugs"])


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
    updated_by = getattr(current_user, "name", None) or getattr(current_user, "username", None) or "system"
    record = create_drug_catalog_item(payload, updated_by=str(updated_by))
    record_operation_audit(
        action="drug_catalog_create",
        result="success",
        path="/api/drugs",
        method="POST",
        actor=current_user,
        detail="drug_id={0}".format(record.drug_id),
        client_ip=request.client.host if request and request.client else None,
    )
    return record


@router.put("/api/drugs/{drug_id}", response_model=DrugCatalogRecord)
def update_drug_catalog(
    drug_id: str,
    payload: DrugCatalogUpsertRequest,
    request: Request,
    current_user: object = Depends(require_roles("doctor", "archivist")),
) -> DrugCatalogRecord:
    updated_by = getattr(current_user, "name", None) or getattr(current_user, "username", None) or "system"
    record = update_drug_catalog_item(drug_id, payload, updated_by=str(updated_by))
    record_operation_audit(
        action="drug_catalog_update",
        result="success",
        path="/api/drugs/{0}".format(drug_id),
        method="PUT",
        actor=current_user,
        detail="drug_id={0}".format(record.drug_id),
        client_ip=request.client.host if request and request.client else None,
    )
    return record
