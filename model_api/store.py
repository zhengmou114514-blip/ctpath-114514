from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha1
from typing import Any
from uuid import uuid4

from .demo_model_seed import DATASETS, MODEL_USERS, MODEL_VERSIONS, SERVICE_HEALTH, TRAINING_TASKS

DATASET_STORE: list[dict[str, Any]] = [dict(item) for item in DATASETS]
TASK_STORE: list[dict[str, Any]] = [dict(item) for item in TRAINING_TASKS]
VERSION_STORE: list[dict[str, Any]] = [dict(item) for item in MODEL_VERSIONS]
HEALTH_STORE: dict[str, Any] = dict(SERVICE_HEALTH)
MODEL_TOKENS: dict[str, str] = {}
MODEL_LOGIN_COUNT = 0
MODEL_ACTIVITY_LOG: list[dict[str, Any]] = []


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _user_map() -> dict[str, dict[str, Any]]:
    return {item["username"]: item for item in MODEL_USERS}


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    user = _user_map().get(username)
    if not user or user["password"] != password:
        return None
    return {
        "username": user["username"],
        "name": user["name"],
        "title": user["title"],
        "department": user["department"],
        "role": user["role"],
    }


def issue_token(username: str) -> str:
    token = sha1(f"{username}:{uuid4().hex}:{_now()}".encode("utf-8")).hexdigest()
    MODEL_TOKENS[token] = username
    return token


def get_user_by_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    username = MODEL_TOKENS.get(token)
    if not username:
        return None
    user = _user_map().get(username)
    if not user:
        return None
    return {
        "username": user["username"],
        "name": user["name"],
        "title": user["title"],
        "department": user["department"],
        "role": user["role"],
    }


def count_csv_rows(text: str) -> int:
    lines = [line for line in text.splitlines() if line.strip()]
    return max(0, len(lines) - 1)


def record_activity(action: str, detail: str, operator: str) -> None:
    MODEL_ACTIVITY_LOG.insert(
        0,
        {
            "id": f"act-{uuid4().hex[:8]}",
            "action": action,
            "detail": detail,
            "operator": operator,
            "createdAt": _now(),
        },
    )
    del MODEL_ACTIVITY_LOG[30:]


def _create_version_from_task(task: dict[str, Any]) -> dict[str, Any]:
    metrics = task.get("metrics") or {"mrr": 0.0, "hits1": 0.0, "hits10": 0.0}
    version_id = f"mv-{task['taskId'][-8:]}"
    version = {
        "versionId": version_id,
        "versionName": f"v{task['taskId'][-8:].replace('-', '')}",
        "modelName": task["modelName"],
        "status": "staging",
        "createdAt": task.get("finishedAt") or task["createdAt"],
        "publishedAt": None,
        "datasetId": task["datasetId"],
        "metrics": metrics,
        "notes": "由训练任务自动生成。",
        "deployed": False,
    }
    if not any(item["versionId"] == version_id for item in VERSION_STORE):
        VERSION_STORE.insert(0, version)
    return version


def advance_training_tasks() -> None:
    now = datetime.utcnow()
    for task in TASK_STORE:
        created = datetime.fromisoformat(task["createdAt"].replace("Z", "+00:00"))
        elapsed = (now - created.replace(tzinfo=None)).total_seconds()

        if task["status"] == "queued" and elapsed > 2:
            task["status"] = "running"
            task["startedAt"] = _now()
            task["logs"].append("训练任务已开始运行。")
        elif task["status"] == "running" and elapsed > 8:
            task["status"] = "succeeded"
            task["finishedAt"] = _now()
            task["metrics"] = {"mrr": 0.6124, "hits1": 0.3982, "hits10": 0.8413}
            task["logs"].append("训练完成，已生成可发布模型版本。")
            _create_version_from_task(task)


def list_datasets() -> list[dict[str, Any]]:
    return sorted(DATASET_STORE, key=lambda item: item["uploadedAt"], reverse=True)


def import_dataset(dataset_name: str, file_name: str, content: str, uploaded_by: str) -> dict[str, Any]:
    row_count = count_csv_rows(content)
    record = {
        "datasetId": f"ds-{uuid4().hex[:10]}",
        "datasetName": dataset_name or file_name.rsplit(".", 1)[0],
        "fileName": file_name,
        "rowCount": row_count,
        "uploadedAt": _now(),
        "uploadedBy": uploaded_by,
        "status": "ready",
        "source": "api",
    }
    DATASET_STORE.insert(0, record)
    record_activity("dataset_import", f"导入数据集 {record['datasetName']}", uploaded_by)
    HEALTH_STORE["last_sync_at"] = _now()
    return record


def list_training_tasks() -> list[dict[str, Any]]:
    advance_training_tasks()
    return sorted(TASK_STORE, key=lambda item: item["createdAt"], reverse=True)


def create_training_task(input_data: dict[str, Any], triggered_by: str) -> dict[str, Any]:
    task = {
        "taskId": f"task-{uuid4().hex[:10]}",
        "datasetId": input_data["datasetId"],
        "datasetName": input_data["datasetName"],
        "modelName": input_data["modelName"],
        "status": "queued",
        "createdAt": _now(),
        "startedAt": None,
        "finishedAt": None,
        "triggeredBy": triggered_by,
        "params": input_data["params"],
        "metrics": None,
        "logs": ["训练任务已创建，等待调度。"],
        "source": "api",
    }
    TASK_STORE.insert(0, task)
    record_activity("training_created", f"创建训练任务 {task['modelName']}", triggered_by)
    HEALTH_STORE["last_sync_at"] = _now()
    return task


def list_versions() -> list[dict[str, Any]]:
    advance_training_tasks()
    return list(VERSION_STORE)


def deploy_version(version_id: str, operator: str) -> dict[str, Any]:
    found = None
    for version in VERSION_STORE:
        if version["versionId"] == version_id:
            found = version
            break
    if not found:
        raise KeyError(version_id)
    for version in VERSION_STORE:
        version["deployed"] = version["versionId"] == version_id
        version["status"] = "deployed" if version["versionId"] == version_id else "staging"
        if version["versionId"] == version_id:
            version["publishedAt"] = _now()
    HEALTH_STORE["current_deployment"] = version_id
    HEALTH_STORE["last_sync_at"] = _now()
    record_activity("version_deploy", f"发布版本 {found['versionName']}", operator)
    return found


def rollback_version(version_id: str, operator: str) -> dict[str, Any]:
    return deploy_version(version_id, operator)


def get_dashboard_snapshot(current_user: str) -> dict[str, Any]:
    tasks = list_training_tasks()
    versions = list_versions()
    deployed = next((item for item in versions if item.get("deployed")), versions[0] if versions else None)
    latest_task = tasks[0] if tasks else None
    return {
        "loginCount": MODEL_LOGIN_COUNT,
        "currentUser": current_user,
        "currentDeployment": HEALTH_STORE.get("current_deployment"),
        "activeDatasetCount": len(DATASET_STORE),
        "runningTaskCount": len([item for item in tasks if item["status"] == "running"]),
        "deployedVersionCount": len([item for item in versions if item.get("deployed")]),
        "latestTaskStatus": latest_task["status"] if latest_task else "无任务",
        "latestVersionName": deployed["versionName"] if deployed else "无版本",
        "health": {
            "status": HEALTH_STORE["status"],
            "mode": HEALTH_STORE["mode"],
            "model_available": HEALTH_STORE["model_available"],
            "model_error": HEALTH_STORE["model_error"],
            "current_deployment": HEALTH_STORE.get("current_deployment"),
            "last_sync_at": HEALTH_STORE.get("last_sync_at"),
        },
    }

