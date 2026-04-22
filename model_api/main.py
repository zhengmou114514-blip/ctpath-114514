from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .demo_model_seed import MODEL_USERS
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
    get_user_by_token,
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
    version="1.0.0",
    description="Dedicated model-management backend for CTpath.",
)

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


def _current_user(authorization: str | None) -> dict | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return get_user_by_token(token)


@app.get("/api/health", response_model=ModelHealthResponse)
def health() -> ModelHealthResponse:
    snapshot = get_dashboard_snapshot("system")
    health_snapshot = snapshot["health"]
    return ModelHealthResponse(**health_snapshot)


@app.post("/api/login", response_model=ModelLoginResponse)
def login(payload: ModelLoginRequest) -> ModelLoginResponse:
    user = authenticate(payload.username, payload.password)
    if not user:
      raise HTTPException(status_code=401, detail="Invalid username or password")

    global MODEL_LOGIN_COUNT
    MODEL_LOGIN_COUNT += 1
    token = issue_token(user["username"])
    record_activity("login", f"模型端登录：{user['name']}", user["username"])
    return ModelLoginResponse(token=token, user=user)


@app.get("/api/me")
def me(authorization: str | None = Header(default=None)) -> dict:
    user = _current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


@app.get("/api/model/dashboard", response_model=ModelDashboardResponse)
def dashboard(authorization: str | None = Header(default=None)) -> ModelDashboardResponse:
    user = _current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    snapshot = get_dashboard_snapshot(user["name"])
    return ModelDashboardResponse(**snapshot)


@app.get("/api/model/datasets", response_model=list[ModelDatasetRecord])
def datasets(authorization: str | None = Header(default=None)) -> list[ModelDatasetRecord]:
    user = _current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return [ModelDatasetRecord(**item) for item in list_datasets()]


@app.post("/api/model/datasets/import", response_model=ModelDatasetRecord)
def import_dataset_endpoint(
    payload: ModelDatasetImportRequest,
    authorization: str | None = Header(default=None),
) -> ModelDatasetRecord:
    user = _current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    record = import_dataset(payload.datasetName, payload.fileName, payload.content, user["name"])
    return ModelDatasetRecord(**record)


@app.get("/api/model/training-tasks", response_model=list[ModelTrainingTaskRecord])
def training_tasks(authorization: str | None = Header(default=None)) -> list[ModelTrainingTaskRecord]:
    user = _current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return [ModelTrainingTaskRecord(**item) for item in list_training_tasks()]


@app.post("/api/model/training-tasks", response_model=ModelTrainingTaskRecord)
def create_training_task_endpoint(
    payload: ModelTrainingTaskCreateRequest,
    authorization: str | None = Header(default=None),
) -> ModelTrainingTaskRecord:
    user = _current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    task = create_training_task(payload.model_dump(), user["name"])
    return ModelTrainingTaskRecord(**task)


@app.get("/api/model/model-versions", response_model=ModelVersionListResponse)
def versions(authorization: str | None = Header(default=None)) -> ModelVersionListResponse:
    user = _current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return ModelVersionListResponse(items=list_versions())


@app.post("/api/model/model-versions/{version_id}/deploy", response_model=dict)
def deploy(version_id: str, authorization: str | None = Header(default=None)) -> dict:
    user = _current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        version = deploy_version(version_id, user["name"])
    except KeyError:
        raise HTTPException(status_code=404, detail="Version not found") from None
    return version


@app.post("/api/model/model-versions/{version_id}/rollback", response_model=dict)
def rollback(version_id: str, authorization: str | None = Header(default=None)) -> dict:
    user = _current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        version = rollback_version(version_id, user["name"])
    except KeyError:
        raise HTTPException(status_code=404, detail="Version not found") from None
    return version


@app.get("/api/model/operations", response_model=dict)
def operations(authorization: str | None = Header(default=None)) -> dict:
    user = _current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "loginCount": MODEL_LOGIN_COUNT,
        "currentUser": user,
        "modelUsers": [
            {k: v for k, v in item.items() if k != "password"} for item in MODEL_USERS
        ],
        "activityLog": MODEL_ACTIVITY_LOG,
    }
