from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ModelUser(BaseModel):
    username: str
    name: str
    title: str
    department: str
    role: Literal["model_admin", "engineer"]


class ModelLoginRequest(BaseModel):
    username: str
    password: str


class ModelLoginResponse(BaseModel):
    token: str
    user: ModelUser


class ModelHealthResponse(BaseModel):
    status: str
    mode: str
    model_available: bool
    model_error: Optional[str] = None
    current_deployment: Optional[str] = None
    last_sync_at: Optional[str] = None


class ModelDatasetRecord(BaseModel):
    datasetId: str
    datasetName: str
    fileName: str
    rowCount: int
    uploadedAt: str
    uploadedBy: str
    status: Literal["ready", "processing", "failed"]
    source: str = Field(default="api")


class ModelDatasetImportRequest(BaseModel):
    datasetName: str
    fileName: str
    content: str


class ModelTrainingParams(BaseModel):
    epochs: int
    batchSize: int
    learningRate: float
    embeddingDim: int
    optimizer: Literal["adam", "sgd", "adamw"]


class ModelTrainingTaskRecord(BaseModel):
    taskId: str
    datasetId: str
    datasetName: str
    modelName: str
    status: Literal["queued", "running", "succeeded", "failed"]
    createdAt: str
    startedAt: Optional[str] = None
    finishedAt: Optional[str] = None
    triggeredBy: str
    params: ModelTrainingParams
    metrics: Optional[dict[str, float]] = None
    logs: list[str]
    source: str = Field(default="api")


class ModelTrainingTaskCreateRequest(BaseModel):
    datasetId: str
    datasetName: str
    modelName: str
    params: ModelTrainingParams


class ModelVersionRecord(BaseModel):
    versionId: str
    versionName: str
    modelName: str
    status: Literal["deployed", "staging", "archived"]
    createdAt: str
    publishedAt: Optional[str] = None
    datasetId: str
    metrics: dict[str, float]
    notes: str
    deployed: bool = False


class ModelVersionListResponse(BaseModel):
    items: list[ModelVersionRecord]


class ModelDashboardResponse(BaseModel):
    loginCount: int
    currentUser: str
    currentDeployment: Optional[str]
    activeDatasetCount: int
    runningTaskCount: int
    deployedVersionCount: int
    latestTaskStatus: str
    latestVersionName: str
    health: ModelHealthResponse

