from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .api.auth import require_roles
from .model_service import MODEL_SERVICE
from .modules.patients.router import router as patient_router
from .schemas import (
    AdviceGenerateRequest,
    AdviceResponse,
    EvidenceSummary,
    FlowBoardResponse,
    FollowupWorklistResponse,
    GovernanceModulesResponse,
    LoginRequest,
    LoginResponse,
    MaintenanceOverviewResponse,
    ModelMetricsResponse,
    PatientUpsertRequest,
    PredictRequest,
    PredictResponse,
    PredictionItem,
    RegisterRequest,
)
from .services.governance_service import get_governance_modules
from .services.llm_advice_service import LLM_ADVICE_SERVICE
from .store import (
    DB_URL,
    authenticate,
    get_flow_board,
    get_followup_worklist,
    get_maintenance_overview,
    get_model_metrics,
    get_patient,
    get_patient_quadruples,
    issue_token,
    predict_for_patient,
    register_doctor,
)


app = FastAPI(
    title="CTpath Chronic Disease API",
    version="0.5.0",
    description="Backend service for the chronic disease assistant system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patient_router)


@app.on_event("startup")
async def load_dataset_on_startup() -> None:
    """Load optional dataset records into demo mode on startup."""
    from . import demo_store
    from .dataset_loader import init_dataset

    print("\n" + "=" * 50)
    print("Loading medical dataset...")
    print("=" * 50)

    loaded_patients = init_dataset()
    if not loaded_patients:
        print("No external dataset loaded, using built-in demo data.")
        print("=" * 50 + "\n")
        return

    existing_ids = {
        str(record.get("patientId"))
        for record in demo_store.PATIENT_RECORDS
        if isinstance(record, dict) and record.get("patientId")
    }
    imported_count = 0

    for patient_id, patient_case in loaded_patients.items():
        if patient_id in existing_ids:
            continue

        demo_store.PATIENT_RECORDS.append(
            {
                "patientId": patient_case.patientId,
                "name": patient_case.name,
                "age": patient_case.age,
                "gender": patient_case.gender,
                "primaryDisease": patient_case.primaryDisease,
                "currentStage": patient_case.currentStage,
                "riskLevel": patient_case.riskLevel,
                "lastVisit": patient_case.lastVisit,
                "summary": f"{patient_case.primaryDisease} patient imported from dataset.",
                "dataSupport": patient_case.dataSupport,
                "events": [
                    {
                        "event_time": event.eventTime,
                        "relation": event.relation,
                        "object_value": event.objectValue,
                        "note": event.note,
                        "source": "dataset",
                    }
                    for event in patient_case.timeline
                ],
                "contactLogs": [],
            }
        )
        imported_count += 1

    print(
        "Dataset load complete: imported {0} patients, total demo patients {1}.".format(
            imported_count,
            len(demo_store.PATIENT_RECORDS),
        )
    )
    print("=" * 50 + "\n")


@app.get("/")
def root() -> dict:
    return {
        "project": "CTpath Chronic Disease Assistant",
        "docs": "http://127.0.0.1:8000/docs",
        "health": "http://127.0.0.1:8000/api/health",
        "mode": "mysql" if DB_URL else "demo",
    }


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "ctpath-fastapi",
        "mode": "mysql" if DB_URL else "demo",
        "model_available": MODEL_SERVICE.available,
        "model_error": MODEL_SERVICE.error,
    }


@app.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    doctor = authenticate(payload.username, payload.password)
    if doctor is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = issue_token(doctor.username)
    return LoginResponse(token=token, doctor=doctor)


@app.post("/api/register", response_model=LoginResponse)
def register(payload: RegisterRequest) -> LoginResponse:
    doctor = register_doctor(payload)
    if doctor is None:
        raise HTTPException(status_code=400, detail="Username already exists")

    token = issue_token(doctor.username)
    return LoginResponse(token=token, doctor=doctor)


@app.post("/api/advice/generate", response_model=AdviceResponse)
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


@app.post("/api/predict", response_model=PredictResponse)
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


@app.get("/api/model/metrics", response_model=ModelMetricsResponse)
def model_metrics(_: object = Depends(require_roles("doctor"))) -> ModelMetricsResponse:
    return get_model_metrics()


@app.get("/api/maintenance/overview", response_model=MaintenanceOverviewResponse)
def maintenance_overview(_: object = Depends(require_roles("doctor", "archivist"))) -> MaintenanceOverviewResponse:
    return get_maintenance_overview()


@app.get("/api/governance/modules", response_model=GovernanceModulesResponse)
def governance_modules(_: object = Depends(require_roles("doctor", "archivist"))) -> GovernanceModulesResponse:
    return get_governance_modules()


@app.get("/api/worklists/followups", response_model=FollowupWorklistResponse)
def followup_worklist(_: object = Depends(require_roles("doctor", "nurse"))) -> FollowupWorklistResponse:
    return get_followup_worklist()


@app.get("/api/worklists/flow-board", response_model=FlowBoardResponse)
def flow_board(_: object = Depends(require_roles("doctor", "nurse"))) -> FlowBoardResponse:
    return get_flow_board()
