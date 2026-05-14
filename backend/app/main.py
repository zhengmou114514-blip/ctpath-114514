from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.analytics import router as analytics_router
from .api.attachments import router as attachments_router
from .api.audit import router as audit_router
from .api.auth import router as auth_router
from .api.authz import router as authz_router
from .api.coordination import router as coordination_router
from .api.database_browser import router as database_browser_router
from .api.drug_permissions import router as drug_permissions_router
from .api.drugs import router as drugs_router
from .api.governance import router as governance_router
from .api.patient_medications import router as patient_medications_router
from .api.patients import router as patients_router
from .api.predictions import router as predictions_router
from .api.systems import router as systems_router
from .api.worklists import router as worklists_router
from .errors import http_exception_handler, validation_exception_handler
from .middleware.exception import GlobalExceptionMiddleware
from .middleware.jwt_auth import JWTAuthMiddleware
from .middleware.rate_limit import limiter, rate_limit_exceeded_handler
from .middleware.timing import RequestTimingMiddleware
from .middleware.trace_id import TraceIdMiddleware
from .auth.rbac_middleware import RBACMiddleware


app = FastAPI(
    title="Chronic Disease Assistant API",
    version="0.5.0",
    description="Backend service for the chronic disease assistant system.",
)

app.state.limiter = limiter
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# FastAPI/Starlette wraps middleware in reverse add order. Requests pass through:
# TraceIdMiddleware -> GlobalExceptionMiddleware -> RequestTimingMiddleware -> JWTAuthMiddleware -> RBACMiddleware -> CORSMiddleware.
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
app.add_middleware(RBACMiddleware)
app.add_middleware(JWTAuthMiddleware)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(GlobalExceptionMiddleware)
app.add_middleware(TraceIdMiddleware)


@app.on_event("startup")
async def load_dataset_on_startup() -> None:
    from .dataset_loader import init_dataset

    print("\n" + "=" * 50)
    print("[startup] checking external medical dataset...")
    print("=" * 50)

    loaded_patients = init_dataset()
    if not loaded_patients:
        print("[startup] no external dataset loaded.")
        print("=" * 50 + "\n")
        return

    print("[startup] external dataset detected: {0} patients available for downstream services.".format(len(loaded_patients)))
    print("=" * 50 + "\n")


app.include_router(analytics_router)
app.include_router(attachments_router)
app.include_router(auth_router)
app.include_router(authz_router)
app.include_router(audit_router)
app.include_router(coordination_router)
app.include_router(database_browser_router)
app.include_router(drug_permissions_router)
app.include_router(drugs_router)
app.include_router(patient_medications_router)
app.include_router(patients_router)
app.include_router(predictions_router)
app.include_router(systems_router)
app.include_router(worklists_router)
app.include_router(governance_router)
