from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from ..auth.dependencies import require_roles
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
    current_user: object = Depends(require_roles("doctor", "archivist")),
) -> DrugCatalogRecord:
    updated_by = getattr(current_user, "name", None) or getattr(current_user, "username", None) or "system"
    return create_drug_catalog_item(payload, updated_by=str(updated_by))


@router.put("/api/drugs/{drug_id}", response_model=DrugCatalogRecord)
def update_drug_catalog(
    drug_id: str,
    payload: DrugCatalogUpsertRequest,
    current_user: object = Depends(require_roles("doctor", "archivist")),
) -> DrugCatalogRecord:
    updated_by = getattr(current_user, "name", None) or getattr(current_user, "username", None) or "system"
    return update_drug_catalog_item(drug_id, payload, updated_by=str(updated_by))
