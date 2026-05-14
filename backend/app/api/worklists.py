from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import require_roles
from ..schemas import (
    DoctorPublic,
    DoctorWorkbenchStatusRequest,
    DoctorWorkbenchStatusResponse,
    FlowBoardResponse,
    FollowupTaskCreateRequest,
    FollowupTaskRow,
    FollowupTaskUpdateRequest,
    FollowupWorklistResponse,
    OutpatientTaskCreateRequest,
    OutpatientTaskStatusUpdateRequest,
)
from ..store import (
    create_outpatient_task,
    get_flow_board,
    get_followup_worklist,
    get_patient,
    list_patients,
    update_doctor_workbench_status,
    update_outpatient_task_status,
)


router = APIRouter(tags=["worklists"])


@router.get("/api/worklists/followups", response_model=FollowupWorklistResponse)
def followup_worklist(_: object = Depends(require_roles("doctor", "nurse"))) -> FollowupWorklistResponse:
    return get_followup_worklist()


def _followup_row_from_patient(patient_id: str, task_id: str) -> Optional[FollowupTaskRow]:
    patient = get_patient(patient_id)
    if not patient:
        return None
    for task in patient.outpatientTasks:
        if task.taskId != task_id:
            continue
        return FollowupTaskRow(
            taskId=task.taskId,
            patientId=patient.patientId,
            patientName=patient.name,
            primaryDisease=patient.primaryDisease,
            riskLevel=patient.riskLevel,
            dataSupport=patient.dataSupport,
            dueDate=task.dueDate,
            owner=task.owner,
            priority=task.priority,
            taskType="随访任务",
            status=task.status,
            source="outpatient-task",
            lastActionBy=task.updatedBy,
            lastActionAt=task.updatedAt,
        )
    return None


def _find_task_patient_id(task_id: str) -> Optional[str]:
    for patient in list_patients():
        patient_case = get_patient(patient["patientId"])
        if patient_case and any(task.taskId == task_id for task in patient_case.outpatientTasks):
            return patient_case.patientId
    return None


@router.post("/api/worklists/followups", response_model=FollowupTaskRow)
def create_followup_worklist_task(
    payload: FollowupTaskCreateRequest,
    doctor: DoctorPublic = Depends(require_roles("doctor")),
) -> FollowupTaskRow:
    updated = create_outpatient_task(
        payload.patientId,
        OutpatientTaskCreateRequest(
            category="followup",
            title=payload.title,
            owner=payload.owner,
            dueDate=payload.dueDate,
            priority=payload.priority,
            note=payload.note,
            status=payload.status,
            source=payload.source,
            actorUsername=payload.actorUsername or doctor.username,
            actorName=payload.actorName or doctor.name,
        ),
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    created = next(
        (
            task
            for task in updated.outpatientTasks
            if task.category == "followup" and task.title == payload.title
        ),
        None,
    )
    if created is None:
        raise HTTPException(status_code=500, detail="Follow-up task was not created")
    row = _followup_row_from_patient(updated.patientId, created.taskId)
    if row is None:
        raise HTTPException(status_code=500, detail="Follow-up task was not readable")
    return row


@router.patch("/api/worklists/followups/{task_id}", response_model=FollowupTaskRow)
def patch_followup_worklist_task(
    task_id: str,
    payload: FollowupTaskUpdateRequest,
    nurse: DoctorPublic = Depends(require_roles("nurse")),
) -> FollowupTaskRow:
    patient_id = _find_task_patient_id(task_id)
    if patient_id is None:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    updated = update_outpatient_task_status(
        patient_id,
        task_id,
        OutpatientTaskStatusUpdateRequest(
            status=payload.status,
            note=payload.note,
            actorUsername=payload.actorUsername or nurse.username,
            actorName=payload.actorName or nurse.name,
        ),
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    row = _followup_row_from_patient(patient_id, task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Follow-up task not found")
    return row


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
