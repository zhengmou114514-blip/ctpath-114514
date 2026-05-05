from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/api", tags=["systems"])


SYSTEMS = [
    {
        "key": "admin",
        "name": "后台管理系统",
        "openhisPort": "8001",
        "description": "承接角色权限、系统状态和基础治理配置，不扩展为完整综合 HIS 后台。",
        "sections": ["role-workspaces", "system", "governance"],
        "roles": ["admin", "archivist"],
        "status": "ready",
    },
    {
        "key": "care",
        "name": "医护协同系统",
        "openhisPort": "8003",
        "description": "承接医生工作台、护士随访、当前患者模型辅助、联系记录、病程流转和多角色协同。",
        "sections": ["doctor", "archive", "tasks", "contacts", "flow", "coordination", "insights"],
        "roles": ["admin", "doctor", "nurse"],
        "status": "ready",
    },
    {
        "key": "pharmacy",
        "name": "药房药库系统",
        "openhisPort": "8004",
        "description": "承接药品目录、药品权限和药房药库审核记录，不做完整库存财务闭环。",
        "sections": ["pharmacy", "drug-management", "drug-permission-management"],
        "roles": ["admin", "pharmacist"],
        "status": "ready",
    },
    {
        "key": "emr",
        "name": "电子病历系统",
        "openhisPort": "8005",
        "description": "承接当前患者病程、电子档案附件和病历式时间线展示。",
        "sections": ["emr", "archive"],
        "roles": ["admin", "doctor", "archivist"],
        "status": "ready",
    },
    {
        "key": "archive",
        "name": "病案管理系统",
        "openhisPort": "8008",
        "description": "承接患者主索引、建档状态、附件补全、数据质量和病案治理。",
        "sections": ["archive", "data-quality", "governance"],
        "roles": ["admin", "archivist"],
        "status": "ready",
    },
    {
        "key": "model",
        "name": "模型管理系统",
        "openhisPort": "project",
        "description": "本系统的模型中心，承接模型看板、模型运行台和训练中心；医生只在医护协同系统查看当前患者模型洞察。",
        "sections": ["model-dashboard", "model-operations", "training-center"],
        "roles": ["admin"],
        "status": "ready",
    },
]

EXCLUDED_OPENHIS_SYSTEMS = [
    {"name": "收费管理系统", "openhisPort": "8002", "reason": "慢病辅助诊疗闭环未启用"},
    {"name": "手术管理系统", "openhisPort": "8006", "reason": "慢病辅助诊疗闭环未启用"},
    {"name": "物资耗材系统", "openhisPort": "8007", "reason": "当前系统未启用"},
]


@router.get("/systems")
def get_system_map():
    return {
        "productName": "慢病辅助诊疗通用版",
        "reference": "医院信息系统子系统组织方式",
        "systems": SYSTEMS,
        "excludedSystems": EXCLUDED_OPENHIS_SYSTEMS,
    }
