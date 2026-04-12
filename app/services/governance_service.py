from __future__ import annotations

from typing import List

from ..model_service import MODEL_SERVICE
from ..schemas import GovernanceModuleItem, GovernanceModulesResponse
from ..store import DB_URL, get_maintenance_overview, get_model_metrics


def get_governance_modules() -> GovernanceModulesResponse:
    maintenance = get_maintenance_overview()
    metrics = get_model_metrics()

    items: List[GovernanceModuleItem] = [
        GovernanceModuleItem(
            moduleKey="base-platform",
            title="基础平台",
            domain="Base",
            ownerRole="doctor / archivist",
            status=f"运行在 {'mysql' if DB_URL else 'demo'} 模式",
            tone="healthy",
            description="承接统一入口、角色登录、患者主索引与系统运行状态。",
            capabilities=["统一登录", "角色分流", "系统模式", "健康检查"],
        ),
        GovernanceModuleItem(
            moduleKey="patient-index",
            title="患者主索引治理",
            domain="PDS / MRMS",
            ownerRole="archivist",
            status=(
                f"缺失 MRN {maintenance.missingMrnCount}，"
                f"待签同意 {maintenance.pendingConsentCount}，"
                f"疑似重复 {maintenance.duplicateRiskCount}"
            ),
            tone="warning"
            if maintenance.missingMrnCount or maintenance.pendingConsentCount or maintenance.duplicateRiskCount
            else "healthy",
            description="围绕患者主数据、建档来源、知情同意与疑似重复信息进行持续治理。",
            capabilities=["MRN 维护", "来源分布", "主数据核对", "档案质控"],
        ),
        GovernanceModuleItem(
            moduleKey="clinical-workspace",
            title="临床评估与预测",
            domain="Clinical",
            ownerRole="doctor",
            status="模型可用" if MODEL_SERVICE.available else "当前处于回退模式",
            tone="healthy" if MODEL_SERVICE.available else "warning",
            description="承接医生端风险研判、预测建议与临床工作台能力。",
            capabilities=[
                "患者评估",
                "结构化事件",
                f"当前模型 {metrics.currentModel.model}",
                "辅助建议",
            ],
        ),
        GovernanceModuleItem(
            moduleKey="followup-collaboration",
            title="随访协同",
            domain="Follow-up",
            ownerRole="doctor / nurse",
            status=f"超期随访 {maintenance.overdueFollowupCount}",
            tone="warning" if maintenance.overdueFollowupCount else "normal",
            description="衔接电话随访、联系记录、门诊任务和复联提醒。",
            capabilities=["随访任务", "联系记录", "门诊联动", "移动端录入"],
        ),
        GovernanceModuleItem(
            moduleKey="api-governance",
            title="接口治理",
            domain="WebAPI",
            ownerRole="doctor / archivist",
            status="FastAPI + RBAC 已接入",
            tone="normal",
            description="对外统一暴露登录、患者、随访、治理和模型能力接口。",
            capabilities=["FastAPI", "RBAC", "治理接口", "统一数据出口"],
        ),
    ]

    return GovernanceModulesResponse(mode="mysql" if DB_URL else "demo", items=items)
