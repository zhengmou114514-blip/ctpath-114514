from __future__ import annotations

from datetime import datetime, timedelta


def iso_days_ago(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).isoformat(timespec="seconds") + "Z"


MODEL_USERS = [
    {
        "username": "model_admin",
        "password": "model123456",
        "name": "陈若宁",
        "title": "模型平台主管",
        "department": "模型治理中心",
        "role": "model_admin",
    },
    {
        "username": "ml_engineer",
        "password": "ml123456",
        "name": "林予川",
        "title": "机器学习工程师",
        "department": "模型治理中心",
        "role": "engineer",
    },
]

DATASETS = [
    {
        "datasetId": "ds-chronic-2026q1",
        "datasetName": "慢病时序知识图谱训练集 2026Q1",
        "fileName": "chronic_q1.csv",
        "rowCount": 1248,
        "uploadedAt": iso_days_ago(14),
        "uploadedBy": "陈若宁",
        "status": "ready",
        "source": "seed",
    },
    {
        "datasetId": "ds-followup-2026q1",
        "datasetName": "随访质控标注集 2026Q1",
        "fileName": "followup_q1.csv",
        "rowCount": 892,
        "uploadedAt": iso_days_ago(7),
        "uploadedBy": "林予川",
        "status": "ready",
        "source": "seed",
    },
]

TRAINING_TASKS = [
    {
        "taskId": "task-20260412-001",
        "datasetId": "ds-chronic-2026q1",
        "datasetName": "慢病时序知识图谱训练集 2026Q1",
        "modelName": "CTpath Temporal KG",
        "status": "succeeded",
        "createdAt": iso_days_ago(5),
        "startedAt": iso_days_ago(5),
        "finishedAt": iso_days_ago(5),
        "triggeredBy": "陈若宁",
        "params": {
            "epochs": 32,
            "batchSize": 128,
            "learningRate": 0.001,
            "embeddingDim": 200,
            "optimizer": "adamw",
        },
        "metrics": {"mrr": 0.6124, "hits1": 0.3982, "hits10": 0.8413},
        "logs": [
            "任务已排队，等待 GPU 训练资源。",
            "训练完成，已生成候选模型版本。",
        ],
        "source": "seed",
    }
]

MODEL_VERSIONS = [
    {
        "versionId": "mv-20260412-001",
        "versionName": "v2026.04.12",
        "modelName": "CTpath Temporal KG",
        "status": "deployed",
        "createdAt": iso_days_ago(5),
        "publishedAt": iso_days_ago(4),
        "datasetId": "ds-chronic-2026q1",
        "metrics": {"mrr": 0.6124, "hits1": 0.3982, "hits10": 0.8413},
        "notes": "基于 2026Q1 慢病时序数据完成训练，并通过离线评估。",
        "deployed": True,
    }
]

SERVICE_HEALTH = {
    "status": "healthy",
    "mode": "model",
    "model_available": True,
    "model_error": None,
    "current_deployment": "mv-20260412-001",
    "last_sync_at": iso_days_ago(1),
}
