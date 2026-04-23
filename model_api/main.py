from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from .demo_model_seed import MODEL_USERS
from .errors import http_exception_handler, validation_exception_handler
from .middleware import (
    GlobalExceptionMiddleware,
    ModelAuthContextMiddleware,
    RequestTimingMiddleware,
    TraceIdMiddleware,
    limiter,
    rate_limit_exceeded_handler,
)
from .schemas import (
    ModelDashboardResponse,
    ModelDatasetImportRequest,
    ModelDatasetRecord,
    ModelHealthResponse,
    ModelLoginRequest,
    ModelLoginResponse,
    ModelTrainingTaskCreateRequest,
    ModelTrainingTaskRecord,
    ModelVersionListResponse,
)
from .store import (
    MODEL_ACTIVITY_LOG,
    MODEL_LOGIN_COUNT,
    authenticate,
    create_training_task,
    deploy_version,
    get_dashboard_snapshot,
    import_dataset,
    issue_token,
    list_datasets,
    list_training_tasks,
    list_versions,
    rollback_version,
    record_activity,
)


app = FastAPI(
    title="CTpath Model API",
    version="1.1.0",
    description="Dedicated model-management backend for CTpath.",
)

app.state.limiter = limiter
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Requests pass through:
# TraceIdMiddleware -> GlobalExceptionMiddleware -> RequestTimingMiddleware
# -> ModelAuthContextMiddleware -> CORSMiddleware.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:4174",
        "http://localhost:4174",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ModelAuthContextMiddleware)
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(GlobalExceptionMiddleware)
app.add_middleware(TraceIdMiddleware)


def _require_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


def _require_role(request: Request, allowed_roles: set[str]) -> dict:
    user = _require_user(request)
    if user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user


@app.get("/api/health", response_model=ModelHealthResponse)
def health() -> ModelHealthResponse:
    snapshot = get_dashboard_snapshot("system")
    return ModelHealthResponse(**snapshot["health"])


@app.post("/api/login", response_model=ModelLoginResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: ModelLoginRequest) -> ModelLoginResponse:
    user = authenticate(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    global MODEL_LOGIN_COUNT
    MODEL_LOGIN_COUNT += 1
    token = issue_token(user["username"])
    record_activity("login", f"用户 {user['name']} 登录模型管理端", user["username"])
    return ModelLoginResponse(token=token, user=user)


@app.get("/api/me")
def me(request: Request) -> dict:
    return _require_user(request)


@app.get("/api/model/dashboard", response_model=ModelDashboardResponse)
@limiter.limit("60/minute")
def dashboard(request: Request) -> ModelDashboardResponse:
    user = _require_user(request)
    snapshot = get_dashboard_snapshot(user["name"])
    return ModelDashboardResponse(**snapshot)


@app.get("/api/model/datasets", response_model=List[ModelDatasetRecord])
@limiter.limit("60/minute")
def datasets(request: Request) -> List[ModelDatasetRecord]:
    _require_role(request, {"model_admin", "engineer"})
    return [ModelDatasetRecord(**item) for item in list_datasets()]


@app.post("/api/model/datasets/import", response_model=ModelDatasetRecord)
@limiter.limit("20/minute")
def import_dataset_endpoint(request: Request, payload: ModelDatasetImportRequest) -> ModelDatasetRecord:
    user = _require_role(request, {"model_admin", "engineer"})
    record = import_dataset(payload.datasetName, payload.fileName, payload.content, user["name"])
    return ModelDatasetRecord(**record)


@app.get("/api/model/training-tasks", response_model=List[ModelTrainingTaskRecord])
@limiter.limit("60/minute")
def training_tasks(request: Request) -> List[ModelTrainingTaskRecord]:
    _require_role(request, {"model_admin", "engineer"})
    return [ModelTrainingTaskRecord(**item) for item in list_training_tasks()]


@app.post("/api/model/training-tasks", response_model=ModelTrainingTaskRecord)
@limiter.limit("20/minute")
def create_training_task_endpoint(request: Request, payload: ModelTrainingTaskCreateRequest) -> ModelTrainingTaskRecord:
    user = _require_role(request, {"model_admin", "engineer"})
    task = create_training_task(payload.model_dump(), user["name"])
    return ModelTrainingTaskRecord(**task)


@app.get("/api/model/model-versions", response_model=ModelVersionListResponse)
@limiter.limit("60/minute")
def versions(request: Request) -> ModelVersionListResponse:
    _require_role(request, {"model_admin", "engineer"})
    return ModelVersionListResponse(items=list_versions())


@app.post("/api/model/model-versions/{version_id}/deploy", response_model=dict)
@limiter.limit("20/minute")
def deploy(request: Request, version_id: str) -> dict:
    user = _require_role(request, {"model_admin"})
    try:
        version = deploy_version(version_id, user["name"])
    except KeyError:
        raise HTTPException(status_code=404, detail="Version not found") from None
    return version


@app.post("/api/model/model-versions/{version_id}/rollback", response_model=dict)
@limiter.limit("20/minute")
def rollback(request: Request, version_id: str) -> dict:
    user = _require_role(request, {"model_admin"})
    try:
        version = rollback_version(version_id, user["name"])
    except KeyError:
        raise HTTPException(status_code=404, detail="Version not found") from None
    return version


@app.get("/api/model/operations", response_model=dict)
@limiter.limit("60/minute")
def operations(request: Request) -> dict:
    user = _require_role(request, {"model_admin"})
    return {
        "loginCount": MODEL_LOGIN_COUNT,
        "currentUser": user,
        "modelUsers": [{k: v for k, v in item.items() if k != "password"} for item in MODEL_USERS],
        "activityLog": MODEL_ACTIVITY_LOG,
    }
