from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import require_roles
from ..schemas import (
    DoctorPublic,
    DoctorWorkbenchStatusRequest,
    DoctorWorkbenchStatusResponse,
    FlowBoardResponse,
    FollowupWorklistResponse,
)
from ..store import get_flow_board, get_followup_worklist, update_doctor_workbench_status


router = APIRouter(tags=["worklists"])


@router.get("/api/worklists/followups", response_model=FollowupWorklistResponse)
def followup_worklist(_: object = Depends(require_roles("doctor", "nurse"))) -> FollowupWorklistResponse:
    return get_followup_worklist()


@router.get("/api/worklists/flow-board", response_model=FlowBoardResponse)
def flow_board(_: object = Depends(require_roles("doctor", "nurse"))) -> FlowBoardResponse:
    return get_flow_board()


@router.patch("/api/worklists/patients/{patient_id}/status", response_model=DoctorWorkbenchStatusResponse)
def patch_doctor_workbench_status(
    patient_id: str,
    payload: DoctorWorkbenchStatusRequest,
    doctor: DoctorPublic = Depends(require_roles("doctor")),
) -> DoctorWorkbenchStatusResponse:
    request_payload = payload.model_copy(
        update={
            "actorUsername": payload.actorUsername or doctor.username,
            "actorName": payload.actorName or doctor.name,
        }
    )
    result = update_doctor_workbench_status(patient_id, request_payload)
    if result is None:
        raise HTTPException(status_code=404, detail="Patient not found or action unavailable")
    return result
