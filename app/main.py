from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.analytics import router as analytics_router
from .api.attachments import router as attachments_router
from .api.audit import router as audit_router
from .api.auth import router as auth_router
from .api.authz import router as authz_router
from .api.drugs import router as drugs_router
from .api.governance import router as governance_router
from .api.patients import router as patients_router
from .api.predictions import router as predictions_router
from .api.worklists import router as worklists_router
from .middleware.exception import GlobalExceptionMiddleware
from .middleware.jwt_auth import JWTAuthMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.trace_id import TraceIdMiddleware


app = FastAPI(
    title="CTpath Chronic Disease API",
    version="0.5.0",
    description="Backend service for the chronic disease assistant system.",
)

# Keep CORS outermost so even middleware-generated error responses carry headers.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(TraceIdMiddleware)
app.add_middleware(GlobalExceptionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


app.include_router(analytics_router)
app.include_router(attachments_router)
app.include_router(auth_router)
app.include_router(authz_router)
app.include_router(audit_router)
app.include_router(drugs_router)
app.include_router(patients_router)
app.include_router(predictions_router)
app.include_router(worklists_router)
app.include_router(governance_router)
