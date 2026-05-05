from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..audit.operation_audit import record_operation_audit
from ..auth.dependencies import require_roles
from ..schemas import (
    PharmacyDashboardResponse,
    PharmacyInventoryRecord,
    PharmacyInventoryStatus,
    PharmacyInventoryUpsertRequest,
    PharmacyReviewDecisionRequest,
    PharmacyReviewOrder,
    PharmacyStockAdjustRequest,
    PharmacyTransactionRecord,
)
from ..services.pharmacy_service import (
    adjust_pharmacy_inventory_item,
    get_pharmacy_dashboard,
    get_pharmacy_inventory_item,
    list_pharmacy_inventory,
    list_pharmacy_review_queue,
    list_pharmacy_transactions,
    review_pharmacy_order,
    upsert_pharmacy_inventory_item,
)


router = APIRouter(tags=["pharmacy"])


def _actor_name(current_user: object) -> str:
    return getattr(current_user, "name", None) or getattr(current_user, "username", None) or "system"


@router.get("/api/pharmacy/dashboard", response_model=PharmacyDashboardResponse)
def pharmacy_dashboard(_: object = Depends(require_roles("pharmacist", "archivist", "admin"))) -> PharmacyDashboardResponse:
    return get_pharmacy_dashboard()


@router.get("/api/pharmacy/inventory", response_model=List[PharmacyInventoryRecord])
def pharmacy_inventory(
    keyword: Optional[str] = Query(default=None),
    warehouse: Optional[str] = Query(default=None),
    status: Optional[PharmacyInventoryStatus] = Query(default=None),
    low_stock_only: bool = Query(default=False),
    _: object = Depends(require_roles("pharmacist", "archivist", "admin")),
) -> List[PharmacyInventoryRecord]:
    return list_pharmacy_inventory(keyword=keyword, warehouse=warehouse, status=status, low_stock_only=low_stock_only)


@router.get("/api/pharmacy/inventory/{item_id}", response_model=PharmacyInventoryRecord)
def pharmacy_inventory_item(
    item_id: str,
    _: object = Depends(require_roles("pharmacist", "archivist", "admin")),
) -> PharmacyInventoryRecord:
    return get_pharmacy_inventory_item(item_id)


@router.post("/api/pharmacy/inventory", response_model=PharmacyInventoryRecord, status_code=201)
def create_pharmacy_inventory_item(
    payload: PharmacyInventoryUpsertRequest,
    request: Request,
    current_user: object = Depends(require_roles("pharmacist", "archivist", "admin")),
) -> PharmacyInventoryRecord:
    record = upsert_pharmacy_inventory_item(payload, updated_by=_actor_name(current_user))
    record_operation_audit(
        operation="create",
        resource_type="pharmacy_inventory",
        resource_id=record.itemId,
        request=request,
        actor=current_user,
        extra_detail="drug_id={0}; warehouse={1}".format(record.drugId, record.warehouse),
    )
    return record


@router.put("/api/pharmacy/inventory/{item_id}", response_model=PharmacyInventoryRecord)
def update_pharmacy_inventory_item(
    item_id: str,
    payload: PharmacyInventoryUpsertRequest,
    request: Request,
    current_user: object = Depends(require_roles("pharmacist", "archivist", "admin")),
) -> PharmacyInventoryRecord:
    if payload.itemId.strip() != item_id.strip():
        raise HTTPException(status_code=400, detail="itemId does not match path parameter")
    record = upsert_pharmacy_inventory_item(payload, updated_by=_actor_name(current_user))
    record_operation_audit(
        operation="update",
        resource_type="pharmacy_inventory",
        resource_id=record.itemId,
        request=request,
        actor=current_user,
        extra_detail="drug_id={0}; warehouse={1}".format(record.drugId, record.warehouse),
    )
    return record


@router.patch("/api/pharmacy/inventory/{item_id}/adjust", response_model=PharmacyInventoryRecord)
def adjust_pharmacy_inventory_item_api(
    item_id: str,
    payload: PharmacyStockAdjustRequest,
    request: Request,
    current_user: object = Depends(require_roles("pharmacist", "archivist", "admin")),
) -> PharmacyInventoryRecord:
    operator_name = payload.operatorName or _actor_name(current_user)
    record = adjust_pharmacy_inventory_item(item_id, payload, updated_by=operator_name)
    record_operation_audit(
        operation="adjust",
        resource_type="pharmacy_inventory",
        resource_id=record.itemId,
        request=request,
        actor=current_user,
        extra_detail="direction={0}; change={1}".format(payload.direction, payload.quantity),
    )
    return record


@router.get("/api/pharmacy/transactions", response_model=List[PharmacyTransactionRecord])
def pharmacy_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    _: object = Depends(require_roles("pharmacist", "archivist", "admin")),
) -> List[PharmacyTransactionRecord]:
    return list_pharmacy_transactions(limit=limit)


@router.get("/api/pharmacy/review-queue", response_model=List[PharmacyReviewOrder])
def pharmacy_review_queue(
    status: Optional[str] = Query(default=None),
    _: object = Depends(require_roles("pharmacist", "archivist", "admin")),
) -> List[PharmacyReviewOrder]:
    return list_pharmacy_review_queue(status=status)


@router.patch("/api/pharmacy/review-queue/{patient_id}/{medication_id}", response_model=PharmacyReviewOrder)
def pharmacy_review_order_api(
    patient_id: str,
    medication_id: str,
    payload: PharmacyReviewDecisionRequest,
    request: Request,
    current_user: object = Depends(require_roles("pharmacist", "archivist", "admin")),
) -> PharmacyReviewOrder:
    record = review_pharmacy_order(
        patient_id,
        medication_id,
        review_status=payload.reviewStatus,
        note=payload.note,
        operator_username=payload.operatorUsername or getattr(current_user, "username", None),
        operator_name=payload.operatorName or _actor_name(current_user),
    )
    record_operation_audit(
        operation="review",
        resource_type="pharmacy_review",
        resource_id="{0}:{1}".format(patient_id, medication_id),
        request=request,
        actor=current_user,
        patient_id=patient_id,
        extra_detail="review_status={0}".format(payload.reviewStatus),
    )
    return record
