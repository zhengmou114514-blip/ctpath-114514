from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .model_service import MODEL_SERVICE
from .schemas import (
    LoginRequest,
    LoginResponse,
    ModelMetricsResponse,
    PatientCase,
    PatientEventCreateRequest,
    PatientSummary,
    PatientUpsertRequest,
    PredictRequest,
    PredictResponse,
    TimelineResponse,
)
from .store import (
    DB_URL,
    add_patient_event,
    authenticate,
    get_model_metrics,
    get_patient,
    get_timeline,
    is_token_valid,
    issue_token,
    list_patients,
    predict_for_patient,
    save_patient,
)


app = FastAPI(
    title="CTpath Chronic Disease API",
    version="0.2.0",
    description="Backend service for the chronic disease assistant system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_token(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.replace("Bearer ", "", 1).strip()
    if not is_token_valid(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token


@app.get("/")
def root() -> dict:
    return {
        "project": "基于时序知识图谱的慢性病辅助诊疗系统",
        "docs": "http://127.0.0.1:8000/docs",
        "health": "http://127.0.0.1:8000/api/health",
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


@app.get("/api/model/metrics", response_model=ModelMetricsResponse)
def model_metrics(_: str = Depends(require_token)) -> ModelMetricsResponse:
    return get_model_metrics()


@app.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    doctor = authenticate(payload.username, payload.password)
    if doctor is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = issue_token(doctor.username)
    return LoginResponse(token=token, doctor=doctor)


@app.get("/api/patients", response_model=List[PatientSummary])
def patients(_: str = Depends(require_token)) -> List[PatientSummary]:
    return [PatientSummary(**item) for item in list_patients()]


@app.get("/api/patient/{patient_id}", response_model=PatientCase)
def patient_detail(patient_id: str, _: str = Depends(require_token)) -> PatientCase:
    patient = get_patient(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.post("/api/patient", response_model=PatientCase)
def create_patient(payload: PatientUpsertRequest, _: str = Depends(require_token)) -> PatientCase:
    patient = save_patient(payload)
    if patient is None:
        raise HTTPException(status_code=500, detail="Unable to save patient")
    return patient


@app.put("/api/patient/{patient_id}", response_model=PatientCase)
def update_patient(patient_id: str, payload: PatientUpsertRequest, _: str = Depends(require_token)) -> PatientCase:
    merged = payload.model_copy(update={"patientId": patient_id})
    patient = save_patient(merged)
    if patient is None:
        raise HTTPException(status_code=500, detail="Unable to update patient")
    return patient


@app.post("/api/patient/{patient_id}/event", response_model=PatientCase)
def create_patient_event(
    patient_id: str,
    payload: PatientEventCreateRequest,
    _: str = Depends(require_token),
) -> PatientCase:
    patient = add_patient_event(patient_id, payload)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.get("/api/timeline/{patient_id}", response_model=TimelineResponse)
def patient_timeline(patient_id: str, _: str = Depends(require_token)) -> TimelineResponse:
    items = get_timeline(patient_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return TimelineResponse(patientId=patient_id, items=items)


@app.post("/api/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, _: str = Depends(require_token)) -> PredictResponse:
    result = predict_for_patient(payload.patientId, payload.topk)
    if result is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PredictResponse(**result)
