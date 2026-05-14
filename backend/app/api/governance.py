from fastapi import APIRouter, Depends, HTTPException, Request

from ..audit.operation_audit import record_operation_audit
from ..auth.dependencies import require_roles
from ..schemas import (
    DoctorPublic,
    GovernanceModuleItem,
    GovernanceModulesResponse,
    GovernanceRecord,
    GovernanceRecordsResponse,
    GovernanceRecordStatusUpdateRequest,
    MaintenanceOverviewResponse,
)
from ..services.governance_service import (
    get_governance_modules,
    list_governance_records,
    update_governance_record_status,
)
from ..store import get_maintenance_overview


router = APIRouter(tags=["governance"])


@router.get("/api/maintenance/overview", response_model=MaintenanceOverviewResponse)
def maintenance_overview(_: object = Depends(require_roles("doctor", "archivist", "admin"))) -> MaintenanceOverviewResponse:
    return get_maintenance_overview()


@router.get("/api/governance/modules", response_model=GovernanceModulesResponse)
def governance_modules(_: object = Depends(require_roles("doctor", "archivist", "admin"))) -> GovernanceModulesResponse:
    return get_governance_modules()


@router.get("/api/governance/records", response_model=GovernanceRecordsResponse)
def governance_records(_: object = Depends(require_roles("admin", "archivist"))) -> GovernanceRecordsResponse:
    return list_governance_records()


@router.patch("/api/governance/records/{record_id}", response_model=GovernanceRecord)
def patch_governance_record(
    record_id: str,
    payload: GovernanceRecordStatusUpdateRequest,
    request: Request,
    admin: DoctorPublic = Depends(require_roles("admin")),
) -> GovernanceRecord:
    updated = update_governance_record_status(
        record_id,
        payload,
        updated_by=payload.actorName or admin.name or admin.username,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Governance record not found")
    record_operation_audit(
        operation="update",
        resource_type="governance_record",
        resource_id=record_id,
        request=request,
        actor=admin,
        extra_detail="status={0}; note={1}".format(updated.status, updated.handlingNote),
    )
    return updated
