"""
Rule-based fallback advice engine.

This module is used when the remote LLM service is unavailable or disabled.
It keeps the interface stable for the rest of the system while returning
readable and clinically conservative suggestions.
"""

from typing import List

from ...schemas import (
    EvidenceSummary,
    PatientQuadruple,
    PatientUpsertRequest,
    PredictionItem,
)


class FallbackEngine:
    """Generate simple fallback advice from patient context and predictions."""

    def __init__(self) -> None:
        self._disease_templates = {
            "diabetes": [
                "建议重点关注血糖控制情况，并结合近期复诊记录评估达标情况。",
                "建议核查用药依从性，并补充 HbA1c、空腹血糖等关键指标。",
                "建议关注糖尿病并发症筛查进展，如眼底、肾功能和足部风险。",
            ],
            "alzheimer": [
                "建议结合近期认知变化与照护记录，评估病情进展与生活支持需求。",
                "建议关注日常功能变化、照护压力和安全风险，及时补充家庭支持信息。",
                "建议围绕行为症状、睡眠和营养情况安排持续随访。",
            ],
            "parkinson": [
                "建议评估运动症状波动及当前治疗方案的稳定性。",
                "建议关注跌倒风险、吞咽情况和非运动症状变化。",
                "建议结合康复训练与家庭照护情况，动态调整随访重点。",
            ],
            "hypertension": [
                "建议复核近期血压控制水平，并结合门诊复诊记录判断管理效果。",
                "建议关注用药依从性及靶器官损害相关检查是否完善。",
                "建议持续强化生活方式干预，并关注心脑血管综合风险。",
            ],
            "copd": [
                "建议结合近期症状变化和急性加重史评估当前稳定性。",
                "建议复核吸入装置使用情况，并加强呼吸康复与戒烟指导。",
                "建议关注呼吸困难、活动耐量下降和再入院风险。",
            ],
        }

        self._stage_templates = {
            "early": [
                "当前更适合以早期干预和规律随访为主，尽量延缓病情进展。",
                "建议尽早完善关键检查与健康教育，提升患者自我管理能力。",
            ],
            "moderate": [
                "当前病情进入中期管理阶段，建议强化复诊、干预和多模块协同。",
                "建议复核现有治疗与随访方案，必要时调整重点管理目标。",
            ],
            "advanced": [
                "当前病情相对复杂，建议强化照护支持与连续性管理。",
                "建议重点关注生活质量、并发症预防和多学科协同。",
            ],
        }

    def generate_fallback_advice(
        self,
        patient: PatientUpsertRequest,
        quadruples: List[PatientQuadruple],
        predictions: List[PredictionItem],
        evidence: EvidenceSummary,
        path_explanation: List[str],
        reason: str = "LLM 服务暂不可用",
    ) -> List[str]:
        """Build a short advice list for degraded mode."""
        advice: List[str] = []

        disease_advice = self._get_disease_advice(patient.primaryDisease)
        advice.extend(disease_advice[:2])

        if predictions:
            top_prediction = predictions[0]
            advice.append(
                f"模型预测最可能的后续状态为 {top_prediction.label}，"
                "建议结合患者当前病情、历史事件与随访结果进一步确认。"
            )

        stage_advice = self._get_stage_advice(quadruples, patient.currentStage)
        if stage_advice:
            advice.extend(stage_advice[:1])

        quality_advice = self._get_data_quality_advice(patient, evidence)
        if quality_advice:
            advice.extend(quality_advice[:1])

        if path_explanation:
            advice.append("系统已识别到关键证据路径，建议结合临床判断综合评估。")

        advice.append(f"[系统提示] 当前使用规则降级建议，原因：{reason}")

        deduped: List[str] = []
        for item in advice:
            if item not in deduped:
                deduped.append(item)
        return deduped[:6]

    def _get_disease_advice(self, primary_disease: str) -> List[str]:
        disease_lower = primary_disease.lower()
        for disease_key, templates in self._disease_templates.items():
            if disease_key in disease_lower:
                return templates
        return [
            "建议结合当前病程、复诊记录和风险等级进行综合评估。",
            "建议制定个体化管理与随访计划，并补足关键诊疗信息。",
            "建议持续关注病情变化，必要时调整检查和干预策略。",
        ]

    def _get_stage_advice(
        self,
        quadruples: List[PatientQuadruple],
        current_stage: str,
    ) -> List[str]:
        stage_candidates = [current_stage.lower().strip()] if current_stage else []

        for quad in quadruples:
            relation_label = quad.relationLabel.lower()
            if "stage" in relation_label or "阶段" in relation_label:
                stage_candidates.append(quad.objectValue.lower().strip())

        for stage_value in stage_candidates:
            for stage_key, templates in self._stage_templates.items():
                if stage_key in stage_value:
                    return templates
        return []

    def _get_data_quality_advice(
        self,
        patient: PatientUpsertRequest,
        evidence: EvidenceSummary,
    ) -> List[str]:
        advice: List[str] = []

        if evidence.supportLevel == "minimal" or patient.dataSupport == "low":
            advice.append("当前结构化数据支持偏弱，建议补充关键诊疗事件和检查结果。")

        if evidence.relationCount < 3:
            advice.append("当前关系信息较少，建议补录检查指标、治疗经过和依从性信息。")

        if not patient.phone or not patient.emergencyContactPhone:
            advice.append("患者联系信息尚不完整，建议补充联系电话与紧急联系人信息。")

        return advice

    def get_disease_templates(self, disease: str) -> List[str]:
        disease_lower = disease.lower()
        for disease_key, templates in self._disease_templates.items():
            if disease_key in disease_lower:
                return templates
        return []

    def add_disease_template(self, disease: str, templates: List[str]) -> None:
        self._disease_templates[disease.lower()] = templates
