from fastapi import APIRouter, Depends

from ..auth.dependencies import require_roles
from ..schemas import GovernanceModulesResponse, MaintenanceOverviewResponse
from ..services.governance_service import get_governance_modules
from ..store import get_maintenance_overview


router = APIRouter(tags=["governance"])


@router.get("/api/maintenance/overview", response_model=MaintenanceOverviewResponse)
def maintenance_overview(_: object = Depends(require_roles("doctor", "archivist"))) -> MaintenanceOverviewResponse:
    return get_maintenance_overview()


@router.get("/api/governance/modules", response_model=GovernanceModulesResponse)
def governance_modules(_: object = Depends(require_roles("doctor", "archivist"))) -> GovernanceModulesResponse:
    return get_governance_modules()
