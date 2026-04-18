from fastapi import APIRouter, Depends

from ..auth.dependencies import require_roles
from ..schemas import FlowBoardResponse, FollowupWorklistResponse
from ..store import get_flow_board, get_followup_worklist


router = APIRouter(tags=["worklists"])


@router.get("/api/worklists/followups", response_model=FollowupWorklistResponse)
def followup_worklist(_: object = Depends(require_roles("doctor", "nurse"))) -> FollowupWorklistResponse:
    return get_followup_worklist()


@router.get("/api/worklists/flow-board", response_model=FlowBoardResponse)
def flow_board(_: object = Depends(require_roles("doctor", "nurse"))) -> FlowBoardResponse:
    return get_flow_board()
