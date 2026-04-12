from fastapi import APIRouter, Depends, HTTPException

from .auth import require_roles
from ..schemas import (
    AdviceGenerateRequest,
    AdviceResponse,
    EvidenceSummary,
    PatientUpsertRequest,
    PredictRequest,
    PredictResponse,
    PredictionItem,
)
from ..services.llm_advice_service import LLM_ADVICE_SERVICE
from ..store import get_patient, get_patient_quadruples, predict_for_patient


router = APIRouter(tags=["predictions"])


@router.post("/api/advice/generate", response_model=AdviceResponse)
def generate_advice(
    payload: AdviceGenerateRequest,
    _: object = Depends(require_roles("doctor")),
) -> AdviceResponse:
    return LLM_ADVICE_SERVICE.generate_advice(
        patient=payload.patient,
        quadruples=payload.quadruples,
        predictions=payload.predictions,
        evidence=payload.evidence,
        path_explanation=payload.pathExplanation,
    )


@router.post("/api/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, _: object = Depends(require_roles("doctor", "nurse"))) -> PredictResponse:
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
    )
    result["advice"] = advice_bundle.advice
    result["adviceMeta"] = advice_bundle.adviceMeta

    return PredictResponse(**result)
