from __future__ import annotations

from datetime import datetime, timedelta


def iso_days_ago(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).isoformat(timespec="seconds") + "Z"


MODEL_USERS = [
    {
        "username": "model_admin",
        "password": "model123456",
        "name": "模型平台主管",
        "title": "算法负责人",
        "department": "模型中心",
        "role": "model_admin",
    },
    {
        "username": "ml_engineer",
        "password": "ml123456",
        "name": "训练工程师",
        "title": "机器学习工程师",
        "department": "模型中心",
        "role": "engineer",
    },
]

DATASETS = [
    {
        "datasetId": "ds-chronic-2026q1",
        "datasetName": "慢病门诊时序样本集 Q1",
        "fileName": "chronic_q1.csv",
        "rowCount": 1248,
        "uploadedAt": iso_days_ago(14),
        "uploadedBy": "模型平台主管",
        "status": "ready",
        "source": "seed",
    },
    {
        "datasetId": "ds-followup-2026q1",
        "datasetName": "随访闭环标注集 Q1",
        "fileName": "followup_q1.csv",
        "rowCount": 892,
        "uploadedAt": iso_days_ago(7),
        "uploadedBy": "训练工程师",
        "status": "ready",
        "source": "seed",
    },
]

TRAINING_TASKS = [
    {
        "taskId": "task-20260412-001",
        "datasetId": "ds-chronic-2026q1",
        "datasetName": "慢病门诊时序样本集 Q1",
        "modelName": "CTpath Temporal KG",
        "status": "succeeded",
        "createdAt": iso_days_ago(5),
        "startedAt": iso_days_ago(5),
        "finishedAt": iso_days_ago(5),
        "triggeredBy": "模型平台主管",
        "params": {
            "epochs": 32,
            "batchSize": 128,
            "learningRate": 0.001,
            "embeddingDim": 200,
            "optimizer": "adamw",
        },
        "metrics": {"mrr": 0.6124, "hits1": 0.3982, "hits10": 0.8413},
        "logs": [
            "任务创建成功，进入排队队列。",
            "完成训练，生成可发布版本。",
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
        "notes": "当前线上部署版本。",
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

