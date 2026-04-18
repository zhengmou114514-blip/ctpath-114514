from fastapi import APIRouter, Depends

from ..auth.dependencies import require_roles
from ..model_service import MODEL_SERVICE
from ..schemas import ModelMetricsResponse
from ..store import DB_URL, get_model_metrics


router = APIRouter(tags=["analytics"])


@router.get("/")
def root() -> dict:
    return {
        "project": "CTpath Chronic Disease Assistant",
        "docs": "http://127.0.0.1:8000/docs",
        "health": "http://127.0.0.1:8000/api/health",
        "mode": "mysql" if DB_URL else "demo",
    }


@router.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "ctpath-fastapi",
        "mode": "mysql" if DB_URL else "demo",
        "model_available": MODEL_SERVICE.available,
        "model_error": MODEL_SERVICE.error,
    }


@router.get("/api/model/metrics", response_model=ModelMetricsResponse)
def model_metrics(_: object = Depends(require_roles("doctor"))) -> ModelMetricsResponse:
    return get_model_metrics()
