import os

from fastapi import APIRouter, Depends, HTTPException, Request

from ..auth.dependencies import require_roles
from ..middleware.rate_limit import limiter
from ..schemas import (
    AdviceGenerateRequest,
    AdviceResponse,
    EvidenceSummary,
    PatientUpsertRequest,
    PredictRequest,
    PredictResponse,
    PredictionItem,
    RiskAssessmentListResponse,
    RiskAssessmentRecord,
)
from ..services.llm_advice_service import LLM_ADVICE_SERVICE
from ..store import (
    get_patient,
    get_patient_quadruples,
    latest_risk_assessment,
    list_risk_assessments,
    predict_for_patient,
    refresh_risk_assessment,
)


router = APIRouter(tags=["predictions"])


def _env_flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@router.post("/api/advice/generate", response_model=AdviceResponse)
@limiter.limit("3/minute")
def generate_advice(
    request: Request,
    payload: AdviceGenerateRequest,
    _: object = Depends(require_roles("doctor")),
) -> AdviceResponse:
    return LLM_ADVICE_SERVICE.generate_advice(
        patient=payload.patient,
        quadruples=payload.quadruples,
        predictions=payload.predictions,
        evidence=payload.evidence,
        path_explanation=payload.pathExplanation,
        allow_remote=True,
    )


@router.post("/api/predict", response_model=PredictResponse)
@limiter.limit("20/minute")
def predict(
    request: Request,
    payload: PredictRequest,
    _: object = Depends(require_roles("doctor", "nurse")),
) -> PredictResponse:
    patient = get_patient(payload.patientId)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    quadruples = get_patient_quadruples(payload.patientId)
    if quadruples is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    result = predict_for_patient(payload.patientId, payload.topk, payload.asOfTime)
    if result is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    advice_bundle = LLM_ADVICE_SERVICE.generate_advice(
        patient=PatientUpsertRequest(
            patientId=patient.patientId,
            name=patient.name,
            age=patient.age,
            gender=patient.gender,
            primaryDisease=patient.primaryDisease,
            currentStage=patient.currentStage,
            riskLevel=patient.riskLevel,
            lastVisit=patient.lastVisit,
            summary=patient.summary,
            dataSupport=patient.dataSupport,
        ),
        quadruples=quadruples,
        predictions=[PredictionItem(**item) for item in result["topk"]],
        evidence=EvidenceSummary(**result["evidence"]),
        path_explanation=result["pathExplanation"],
        allow_remote=_env_flag("CTPATH_LLM_REMOTE_ON_PREDICT"),
    )
    result["advice"] = advice_bundle.advice
    result["adviceMeta"] = advice_bundle.adviceMeta

    return PredictResponse(**result)


@router.get("/api/patients/{patient_id}/risk-assessments", response_model=RiskAssessmentListResponse)
def get_risk_assessments(
    patient_id: str,
    _: object = Depends(require_roles("doctor", "admin")),
) -> RiskAssessmentListResponse:
    items = list_risk_assessments(patient_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return RiskAssessmentListResponse(patientId=patient_id, items=items)


@router.get("/api/patients/{patient_id}/risk-assessments/latest", response_model=RiskAssessmentRecord)
def get_latest_risk_assessment(
    patient_id: str,
    _: object = Depends(require_roles("doctor", "admin")),
) -> RiskAssessmentRecord:
    item = latest_risk_assessment(patient_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Patient or risk assessment not found")
    return item


@router.post("/api/patients/{patient_id}/risk-assessments/refresh", response_model=RiskAssessmentRecord)
@limiter.limit("20/minute")
def refresh_patient_risk_assessment(
    patient_id: str,
    request: Request,
    current_user: object = Depends(require_roles("doctor")),
) -> RiskAssessmentRecord:
    item = refresh_risk_assessment(patient_id, topk=3, actor_name=getattr(current_user, "name", None))
    if item is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return item
